import requests
import logging
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from loki_logger import get_logger, log_api_call


class HubSpotAPIService:
    """
    Service for interacting with HubSpot CRM API v3
    Handles authentication, deal retrieval, rate limiting, and error handling
    """
    
    def __init__(self, base_url: str = "https://api.hubapi.com"):
        """
        Initialize HubSpot API service
        
        Args:
            base_url: HubSpot API base URL (default: https://api.hubapi.com)
        """
        self.base_url = base_url.rstrip('/')
        self.logger = get_logger(__name__)
        self.session = requests.Session()
        
        # Set default headers
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'HubSpot-Deals-ETL-Service/1.0'
        })
        
        self.logger.info(
            "HubSpot API service initialized",
            extra={
                'operation': 'hubspot_api_init',
                'base_url': base_url
            }
        )
    
    def set_access_token(self, token: str):
        """
        Set the HubSpot API access token for authentication
        
        Args:
            token: HubSpot Private App access token
        """
        self.session.headers.update({
            'Authorization': f'Bearer {token}'
        })
        self.logger.debug(
            "Access token configured",
            extra={'operation': 'set_access_token'}
        )
    
    def get_deals(
        self,
        access_token: str,
        limit: int = 100,
        after: Optional[str] = None,
        properties: Optional[List[str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Get deals from HubSpot CRM API with pagination support
        
        Args:
            access_token: HubSpot access token
            limit: Number of results per page (1-100, default: 100)
            after: Pagination cursor for next page
            properties: List of deal properties to return
            **kwargs: Additional query parameters
            
        Returns:
            Dictionary containing deals results and pagination info
            
        Raises:
            requests.exceptions.RequestException: On API errors
        """
        start_time = datetime.utcnow()
        
        try:
            self.logger.info(
                "Fetching deals from HubSpot",
                extra={
                    'operation': 'get_deals',
                    'limit': limit,
                    'has_cursor': after is not None,
                    'properties_count': len(properties) if properties else 0
                }
            )
            
            # Set authentication headers
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            # Build query parameters
            params = {
                'limit': min(limit, 100),  # HubSpot max limit is 100
            }
            
            if after:
                params['after'] = after
            
            if properties:
                params['properties'] = ','.join(properties)
            
            # Add additional parameters
            for key, value in kwargs.items():
                if key not in params:
                    params[key] = value
            
            # Call HubSpot CRM API
            url = f"{self.base_url}/crm/v3/objects/deals"
            
            response = self._make_request_with_retry(
                url=url,
                headers=headers,
                params=params,
                method='GET'
            )
            
            duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            result = response.json()
            
            self.logger.info(
                "Deals retrieved successfully",
                extra={
                    'operation': 'get_deals',
                    'status_code': response.status_code,
                    'duration_ms': round(duration_ms, 2),
                    'deals_count': len(result.get('results', [])),
                    'has_more': 'paging' in result and 'next' in result.get('paging', {})
                }
            )
            
            log_api_call(
                self.logger,
                "hubspot_get_deals",
                method='GET',
                status_code=response.status_code,
                duration_ms=round(duration_ms, 2)
            )
            
            return result
            
        except requests.exceptions.RequestException as e:
            duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            self.logger.error(
                "Error fetching deals from HubSpot",
                extra={
                    'operation': 'get_deals',
                    'error': str(e),
                    'duration_ms': round(duration_ms, 2),
                    'status_code': getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None
                },
                exc_info=True
            )
            
            log_api_call(
                self.logger,
                "hubspot_get_deals",
                method='GET',
                status_code=getattr(e.response, 'status_code', None) if hasattr(e, 'response') else 500,
                duration_ms=round(duration_ms, 2)
            )
            
            raise
    
    def _make_request_with_retry(
        self,
        url: str,
        headers: Dict[str, str],
        params: Dict[str, Any],
        method: str = 'GET',
        max_retries: int = 3
    ) -> requests.Response:
        """
        Make API request with rate limiting and retry logic
        
        Args:
            url: API endpoint URL
            headers: Request headers
            params: Query parameters
            method: HTTP method
            max_retries: Maximum number of retry attempts
            
        Returns:
            Response object
            
        Raises:
            requests.exceptions.RequestException: On failure after retries
        """
        for attempt in range(max_retries):
            try:
                response = self.session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params
                )
                
                # Handle rate limiting (429)
                if response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', 10))
                    
                    self.logger.warning(
                        "Rate limit exceeded, retrying",
                        extra={
                            'operation': 'rate_limit_handler',
                            'status_code': 429,
                            'retry_after': retry_after,
                            'attempt': attempt + 1,
                            'max_retries': max_retries,
                            'rate_limit_remaining': response.headers.get('X-HubSpot-RateLimit-Remaining'),
                            'rate_limit_max': response.headers.get('X-HubSpot-RateLimit-Max')
                        }
                    )
                    
                    if attempt < max_retries - 1:
                        time.sleep(retry_after)
                        continue
                    else:
                        self._handle_error_response(response)
                
                # Handle other errors
                if response.status_code >= 400:
                    self._handle_error_response(response)
                
                # Log rate limit info on success
                if response.status_code == 200:
                    rate_limit_remaining = response.headers.get('X-HubSpot-RateLimit-Remaining')
                    if rate_limit_remaining:
                        self.logger.debug(
                            "Rate limit status",
                            extra={
                                'operation': 'rate_limit_check',
                                'remaining': rate_limit_remaining,
                                'max': response.headers.get('X-HubSpot-RateLimit-Max'),
                                'interval_ms': response.headers.get('X-HubSpot-RateLimit-Interval-Milliseconds')
                            }
                        )
                
                return response
                
            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                    self.logger.warning(
                        "Request failed, retrying with exponential backoff",
                        extra={
                            'operation': 'retry_handler',
                            'error': str(e),
                            'attempt': attempt + 1,
                            'max_retries': max_retries,
                            'wait_time': wait_time
                        }
                    )
                    time.sleep(wait_time)
                else:
                    self.logger.error(
                        "Request failed after all retries",
                        extra={
                            'operation': 'retry_handler',
                            'error': str(e),
                            'attempts': max_retries
                        }
                    )
                    raise
        
        # This should not be reached, but just in case
        raise requests.exceptions.RequestException("Max retries exceeded")
    
    def _handle_error_response(self, response: requests.Response):
        """
        Handle error responses from HubSpot API
        
        Args:
            response: Response object with error status code
            
        Raises:
            requests.exceptions.HTTPError: With appropriate error message
        """
        try:
            error_data = response.json()
            error_message = error_data.get('message', 'Unknown error')
            correlation_id = error_data.get('correlationId', 'N/A')
        except Exception:
            error_message = response.text or 'Unknown error'
            correlation_id = 'N/A'
        
        # Log specific error types
        if response.status_code == 401:
            self.logger.error(
                "Authentication failed - Invalid access token",
                extra={
                    'operation': 'error_handler',
                    'error_type': 'authentication_error',
                    'status_code': 401,
                    'correlation_id': correlation_id,
                    'message': error_message
                }
            )
        elif response.status_code == 403:
            self.logger.error(
                "Permission denied - Insufficient scopes",
                extra={
                    'operation': 'error_handler',
                    'error_type': 'permission_error',
                    'status_code': 403,
                    'correlation_id': correlation_id,
                    'message': error_message
                }
            )
        elif response.status_code == 404:
            self.logger.warning(
                "Resource not found",
                extra={
                    'operation': 'error_handler',
                    'error_type': 'not_found',
                    'status_code': 404,
                    'correlation_id': correlation_id,
                    'message': error_message
                }
            )
        elif response.status_code == 429:
            self.logger.warning(
                "Rate limit exceeded",
                extra={
                    'operation': 'error_handler',
                    'error_type': 'rate_limit_error',
                    'status_code': 429,
                    'correlation_id': correlation_id,
                    'message': error_message,
                    'retry_after': response.headers.get('Retry-After')
                }
            )
        elif response.status_code >= 500:
            self.logger.error(
                "HubSpot server error",
                extra={
                    'operation': 'error_handler',
                    'error_type': 'server_error',
                    'status_code': response.status_code,
                    'correlation_id': correlation_id,
                    'message': error_message
                }
            )
        else:
            self.logger.error(
                "HubSpot API error",
                extra={
                    'operation': 'error_handler',
                    'error_type': 'api_error',
                    'status_code': response.status_code,
                    'correlation_id': correlation_id,
                    'message': error_message
                }
            )
        
        # Raise the error
        response.raise_for_status()
    
    def validate_credentials(self, access_token: str) -> bool:
        """
        Validate HubSpot access token by making a test API call
        
        Args:
            access_token: HubSpot access token to validate
            
        Returns:
            True if credentials are valid, False otherwise
        """
        try:
            self.logger.info(
                "Validating HubSpot credentials",
                extra={'operation': 'validate_credentials'}
            )
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            # Test with minimal request to deals endpoint
            url = f"{self.base_url}/crm/v3/objects/deals"
            params = {'limit': 1}
            
            response = self.session.get(url, headers=headers, params=params)
            
            is_valid = response.status_code == 200
            
            if is_valid:
                self.logger.info(
                    "Credential validation successful",
                    extra={
                        'operation': 'validate_credentials',
                        'status': 'valid'
                    }
                )
            else:
                self.logger.warning(
                    "Credential validation failed",
                    extra={
                        'operation': 'validate_credentials',
                        'status': 'invalid',
                        'status_code': response.status_code
                    }
                )
            
            return is_valid
            
        except requests.exceptions.RequestException as e:
            self.logger.error(
                "Error during credential validation",
                extra={
                    'operation': 'validate_credentials',
                    'error': str(e),
                    'status': 'error'
                },
                exc_info=True
            )
            return False

