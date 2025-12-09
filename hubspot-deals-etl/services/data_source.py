import dlt
import logging
import uuid
import decimal
from typing import Dict, List, Any, Iterator, Optional, Callable
from datetime import datetime, timezone
from decimal import Decimal
from .hubspot_api_service import HubSpotAPIService
from loki_logger import get_logger, log_business_event, log_security_event


def _convert_to_datetime(value: Any) -> Optional[datetime]:
    """Convert various date formats to datetime object"""
    if not value:
        return None
    
    if isinstance(value, datetime):
        return value
    
    try:
        # Handle ISO 8601 format from HubSpot
        if isinstance(value, str):
            # Remove 'Z' suffix if present and parse
            value = value.replace('Z', '+00:00')
            return datetime.fromisoformat(value)
    except (ValueError, AttributeError):
        pass
    
    return None


def _convert_to_decimal(value: Any) -> Optional[Decimal]:
    """Convert string or number to Decimal for financial fields"""
    if not value:
        return None
    
    try:
        return Decimal(str(value))
    except (ValueError, TypeError, decimal.InvalidOperation):
        return None


def _convert_to_bool(value: Any) -> Optional[bool]:
    """Convert various boolean representations to Python bool"""
    if value is None:
        return None
    
    if isinstance(value, bool):
        return value
    
    if isinstance(value, str):
        return value.lower() in ('true', '1', 'yes')
    
    return bool(value)


def _convert_to_int(value: Any) -> Optional[int]:
    """Convert string or number to int"""
    if not value:
        return None
    
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def _transform_deal_record(
    record: Dict[str, Any],
    scan_id: str,
    organization_id: str,
    page_number: int
) -> Dict[str, Any]:
    """
    Transform HubSpot deal record to match database schema
    
    Args:
        record: Raw HubSpot deal record
        scan_id: Scan job ID
        organization_id: Organization/tenant ID
        page_number: Current page number
        
    Returns:
        Transformed deal record matching database schema
    """
    # Extract properties from HubSpot response structure
    deal_id = record.get('id')
    properties = record.get('properties', {})
    
    # Generate UUID for primary key
    record_id = str(uuid.uuid4())
    
    # Build transformed record with mapped fields
    transformed = {
        # Primary identification
        'id': record_id,
        'hs_object_id': deal_id,
        
        # ETL metadata (required)
        '_tenant_id': organization_id,
        '_scan_id': scan_id,
        '_extracted_at': datetime.now(timezone.utc).isoformat(),
        '_source_system': 'hubspot',
        '_api_version': 'v3',
        '_page_number': page_number,
        '_organization_id': organization_id,
        
        # Basic deal information
        'dealname': properties.get('dealname'),
        'amount': _convert_to_decimal(properties.get('amount')),
        'amount_in_home_currency': _convert_to_decimal(properties.get('amount_in_home_currency')),
        'pipeline': properties.get('pipeline', 'default'),
        'dealstage': properties.get('dealstage'),
        'dealtype': properties.get('dealtype'),
        'description': properties.get('description'),
        
        # Date fields
        'closedate': _convert_to_datetime(properties.get('closedate')),
        'createdate': _convert_to_datetime(properties.get('createdate')),
        'hs_lastmodifieddate': _convert_to_datetime(properties.get('hs_lastmodifieddate')),
        'hs_createdate': _convert_to_datetime(properties.get('hs_createdate')),
        
        # Stage date tracking
        'hs_date_entered_appointmentscheduled': _convert_to_datetime(properties.get('hs_date_entered_appointmentscheduled')),
        'hs_date_exited_appointmentscheduled': _convert_to_datetime(properties.get('hs_date_exited_appointmentscheduled')),
        'hs_date_entered_qualifiedtobuy': _convert_to_datetime(properties.get('hs_date_entered_qualifiedtobuy')),
        'hs_date_exited_qualifiedtobuy': _convert_to_datetime(properties.get('hs_date_exited_qualifiedtobuy')),
        'hs_date_entered_presentationscheduled': _convert_to_datetime(properties.get('hs_date_entered_presentationscheduled')),
        'hs_date_exited_presentationscheduled': _convert_to_datetime(properties.get('hs_date_exited_presentationscheduled')),
        'hs_date_entered_decisionmakerboughtin': _convert_to_datetime(properties.get('hs_date_entered_decisionmakerboughtin')),
        'hs_date_exited_decisionmakerboughtin': _convert_to_datetime(properties.get('hs_date_exited_decisionmakerboughtin')),
        'hs_date_entered_contractsent': _convert_to_datetime(properties.get('hs_date_entered_contractsent')),
        'hs_date_exited_contractsent': _convert_to_datetime(properties.get('hs_date_exited_contractsent')),
        'hs_date_entered_closedwon': _convert_to_datetime(properties.get('hs_date_entered_closedwon')),
        'hs_date_entered_closedlost': _convert_to_datetime(properties.get('hs_date_entered_closedlost')),
        
        # Financial fields
        'hs_arr': _convert_to_decimal(properties.get('hs_arr')),
        'hs_mrr': _convert_to_decimal(properties.get('hs_mrr')),
        'hs_tcv': _convert_to_decimal(properties.get('hs_tcv')),
        'hs_acv': _convert_to_decimal(properties.get('hs_acv')),
        'deal_currency_code': properties.get('deal_currency_code', 'USD'),
        
        # Forecasting & probability
        'hs_forecast_amount': _convert_to_decimal(properties.get('hs_forecast_amount')),
        'hs_forecast_probability': _convert_to_decimal(properties.get('hs_forecast_probability')),
        'hs_manual_forecast_category': properties.get('hs_manual_forecast_category'),
        'hs_is_closed': _convert_to_bool(properties.get('hs_is_closed')),
        'hs_is_closed_won': _convert_to_bool(properties.get('hs_is_closed_won')),
        
        # Ownership & assignment
        'hubspot_owner_id': properties.get('hubspot_owner_id'),
        'hubspot_owner_assigneddate': _convert_to_datetime(properties.get('hubspot_owner_assigneddate')),
        'hubspot_team_id': properties.get('hubspot_team_id'),
        'hs_all_owner_ids': properties.get('hs_all_owner_ids'),
        'hs_all_team_ids': properties.get('hs_all_team_ids'),
        
        # Source & attribution
        'hs_analytics_source': properties.get('hs_analytics_source'),
        'hs_analytics_source_data_1': properties.get('hs_analytics_source_data_1'),
        'hs_analytics_source_data_2': properties.get('hs_analytics_source_data_2'),
        'hs_campaign': properties.get('hs_campaign'),
        'hs_latest_source': properties.get('hs_latest_source'),
        'hs_latest_source_data_1': properties.get('hs_latest_source_data_1'),
        'hs_latest_source_data_2': properties.get('hs_latest_source_data_2'),
        
        # Deal metrics & engagement
        'num_associated_contacts': _convert_to_int(properties.get('num_associated_contacts')),
        'num_contacted_notes': _convert_to_int(properties.get('num_contacted_notes')),
        'num_notes': _convert_to_int(properties.get('num_notes')),
        'hs_num_of_associated_line_items': _convert_to_int(properties.get('hs_num_of_associated_line_items')),
        'hs_time_in_dealstage': _convert_to_int(properties.get('hs_time_in_dealstage')),
        'hs_days_to_close': _convert_to_int(properties.get('hs_days_to_close')),
        'hs_deal_stage_probability': _convert_to_decimal(properties.get('hs_deal_stage_probability')),
        
        # Deal status flags
        'archived': _convert_to_bool(record.get('archived', False)),
        'hs_is_active_shared_deal': _convert_to_bool(properties.get('hs_is_active_shared_deal')),
        'hs_priority': properties.get('hs_priority'),
        
        # User tracking
        'hs_created_by_user_id': properties.get('hs_created_by_user_id'),
        'hs_updated_by_user_id': properties.get('hs_updated_by_user_id'),
        'hs_user_ids_of_all_owners': properties.get('hs_user_ids_of_all_owners'),
        
        # Next steps & activity
        'hs_next_step': properties.get('hs_next_step'),
        'hs_date_entered_next_step': _convert_to_datetime(properties.get('hs_date_entered_next_step')),
        'hs_last_sales_activity_date': _convert_to_datetime(properties.get('hs_last_sales_activity_date')),
        'hs_last_sales_activity_timestamp': _convert_to_datetime(properties.get('hs_last_sales_activity_timestamp')),
        'hs_sales_email_last_replied': _convert_to_datetime(properties.get('hs_sales_email_last_replied')),
        
        # Deal properties
        'deal_type_id': properties.get('deal_type_id'),
        'deal_probability': _convert_to_decimal(properties.get('deal_probability')),
        'hs_closed_amount': _convert_to_decimal(properties.get('hs_closed_amount')),
        'hs_closed_amount_in_home_currency': _convert_to_decimal(properties.get('hs_closed_amount_in_home_currency')),
        'hs_projected_amount': _convert_to_decimal(properties.get('hs_projected_amount')),
        'hs_projected_amount_in_home_currency': _convert_to_decimal(properties.get('hs_projected_amount_in_home_currency')),
        
        # System metadata from HubSpot
        'hubspot_created_at': _convert_to_datetime(record.get('createdAt')),
        'hubspot_updated_at': _convert_to_datetime(record.get('updatedAt')),
    }
    
    # Store unmapped custom properties in JSONB field
    # Define known/mapped properties to exclude from custom_properties
    mapped_properties = {
        'dealname', 'amount', 'amount_in_home_currency', 'pipeline', 'dealstage', 'dealtype', 'description',
        'closedate', 'createdate', 'hs_lastmodifieddate', 'hs_createdate',
        'hs_date_entered_appointmentscheduled', 'hs_date_exited_appointmentscheduled',
        'hs_date_entered_qualifiedtobuy', 'hs_date_exited_qualifiedtobuy',
        'hs_date_entered_presentationscheduled', 'hs_date_exited_presentationscheduled',
        'hs_date_entered_decisionmakerboughtin', 'hs_date_exited_decisionmakerboughtin',
        'hs_date_entered_contractsent', 'hs_date_exited_contractsent',
        'hs_date_entered_closedwon', 'hs_date_entered_closedlost',
        'hs_arr', 'hs_mrr', 'hs_tcv', 'hs_acv', 'deal_currency_code',
        'hs_forecast_amount', 'hs_forecast_probability', 'hs_manual_forecast_category',
        'hs_is_closed', 'hs_is_closed_won',
        'hubspot_owner_id', 'hubspot_owner_assigneddate', 'hubspot_team_id',
        'hs_all_owner_ids', 'hs_all_team_ids',
        'hs_analytics_source', 'hs_analytics_source_data_1', 'hs_analytics_source_data_2',
        'hs_campaign', 'hs_latest_source', 'hs_latest_source_data_1', 'hs_latest_source_data_2',
        'num_associated_contacts', 'num_contacted_notes', 'num_notes',
        'hs_num_of_associated_line_items', 'hs_time_in_dealstage', 'hs_days_to_close',
        'hs_deal_stage_probability', 'hs_is_active_shared_deal', 'hs_priority',
        'hs_created_by_user_id', 'hs_updated_by_user_id', 'hs_user_ids_of_all_owners',
        'hs_next_step', 'hs_date_entered_next_step', 'hs_last_sales_activity_date',
        'hs_last_sales_activity_timestamp', 'hs_sales_email_last_replied',
        'deal_type_id', 'deal_probability', 'hs_closed_amount',
        'hs_closed_amount_in_home_currency', 'hs_projected_amount',
        'hs_projected_amount_in_home_currency'
    }
    
    custom_properties = {
        k: v for k, v in properties.items()
        if k not in mapped_properties and v is not None
    }
    
    if custom_properties:
        transformed['custom_properties'] = custom_properties
    
    return transformed


def create_data_source(
    job_config: Dict[str, Any],
    auth_config: Dict[str, Any],
    filters: Dict[str, Any],
    checkpoint_callback: Optional[Callable] = None,
    check_cancel_callback: Optional[Callable] = None,
    check_pause_callback: Optional[Callable] = None,
    resume_from: Optional[Dict[str, Any]] = None,
):
    """
    Create DLT source function for HubSpot deals extraction with checkpoint support
    """
    logger = get_logger(__name__)
    api_service = HubSpotAPIService(base_url="https://api.hubapi.com")

    access_token = auth_config.get("accessToken")
    if not access_token:
        raise ValueError("No access token found in auth configuration")

    organization_id = job_config.get("organizationId")
    if not organization_id:
        raise ValueError("No organization ID found in job configuration")

    logger.info(
        "Starting HubSpot deals data extraction",
        extra={
            "organization_id": organization_id,
            "filters": filters,
        },
    )

    @dlt.resource(name="hubspot_deals", write_disposition="replace", primary_key="id")
    def get_main_data() -> Iterator[Dict[str, Any]]:
        """
        Extract HubSpot deals with checkpoint support and proper data transformation
        """

        # Initialize state
        if resume_from:
            after = resume_from.get("cursor")
            page_count = resume_from.get("page_number", 0)
            total_records = resume_from.get("records_processed", 0)
            logger.info(
                "Resuming data extraction",
                extra={
                    "operation": "data_extraction",
                    "page_number": page_count + 1,
                    "total_processed": total_records,
                },
            )
        else:
            after = None
            page_count = 0
            total_records = 0
            logger.info(
                "Starting fresh data extraction",
                extra={"operation": "data_extraction", "source": "hubspot_deals"},
            )

        # Configuration
        checkpoint_interval = 10
        cancel_check_interval = 1
        pause_check_interval = 1
        job_id = filters.get("scan_id", "unknown")
        
        # Get properties to request from filters
        properties = filters.get("properties") if filters.get("properties") else None

        while page_count < 1000:  # Safety limit
            try:
                # Check for cancellation
                if page_count % cancel_check_interval == 0:
                    if check_cancel_callback and check_cancel_callback(job_id):
                        logger.info(
                            "Extraction cancelled by user",
                            extra={
                                "operation": "data_extraction",
                                "job_id": job_id,
                                "page_number": page_count + 1,
                                "total_processed": total_records,
                            },
                        )

                        # Save cancellation checkpoint
                        if checkpoint_callback:
                            try:
                                cancel_checkpoint = {
                                    "phase": "main_data_cancelled",
                                    "records_processed": total_records,
                                    "cursor": after,
                                    "page_number": page_count,
                                    "batch_size": 100,
                                    "checkpoint_data": {
                                        "cancellation_reason": "user_requested",
                                        "cancelled_at_page": page_count,
                                        "service": "hubspot_deals",
                                    },
                                }
                                checkpoint_callback(job_id, cancel_checkpoint)
                            except Exception as e:
                                logger.warning(
                                    "Failed to save cancellation checkpoint",
                                    extra={"job_id": job_id, "error": str(e)},
                                )
                        break

                # Check for pause request
                if page_count % pause_check_interval == 0:
                    if check_pause_callback and check_pause_callback(job_id):
                        logger.info(
                            "Extraction paused by user",
                            extra={
                                "operation": "data_extraction",
                                "job_id": job_id,
                                "page_number": page_count + 1,
                                "total_processed": total_records,
                            },
                        )

                        # Save pause checkpoint
                        if checkpoint_callback:
                            try:
                                pause_checkpoint = {
                                    "phase": "main_data_paused",
                                    "records_processed": total_records,
                                    "cursor": after,
                                    "page_number": page_count,
                                    "batch_size": 100,
                                    "checkpoint_data": {
                                        "pause_reason": "user_requested",
                                        "paused_at_page": page_count,
                                        "paused_at": datetime.now(timezone.utc).isoformat(),
                                        "service": "hubspot_deals",
                                    },
                                }
                                checkpoint_callback(job_id, pause_checkpoint)

                                logger.info(
                                    "Pause checkpoint saved",
                                    extra={
                                        "operation": "data_extraction",
                                        "job_id": job_id,
                                        "page_number": page_count,
                                        "total_processed": total_records,
                                    },
                                )
                            except Exception as e:
                                logger.warning(
                                    "Failed to save pause checkpoint",
                                    extra={"job_id": job_id, "error": str(e)},
                                )

                        # Exit gracefully
                        break

                logger.debug(
                    "Fetching deals page",
                    extra={
                        "operation": "data_extraction",
                        "job_id": job_id,
                        "page_number": page_count + 1,
                    },
                )

                # Call HubSpot API to get deals
                data = api_service.get_deals(
                    access_token=access_token,
                    limit=100,
                    after=after,
                    properties=properties
                )

                page_records = 0

                # Process deals from response
                if "results" in data and data["results"]:
                    for record in data["results"]:
                        # Check for pause/cancel during record processing
                        if check_pause_callback and check_pause_callback(job_id):
                            logger.info(
                                "Extraction paused mid-page",
                                extra={
                                    "operation": "data_extraction",
                                    "job_id": job_id,
                                    "page_number": page_count + 1,
                                    "records_in_page": page_records,
                                    "total_processed": total_records + page_records,
                                },
                            )

                            # Save mid-page pause checkpoint
                            if checkpoint_callback:
                                try:
                                    mid_page_checkpoint = {
                                        "phase": "main_data_paused_mid_page",
                                        "records_processed": total_records + page_records,
                                        "cursor": after,
                                        "page_number": page_count,
                                        "batch_size": 100,
                                        "checkpoint_data": {
                                            "pause_reason": "user_requested_mid_page",
                                            "paused_at_page": page_count,
                                            "records_completed_in_page": page_records,
                                            "paused_at": datetime.now(timezone.utc).isoformat(),
                                            "service": "hubspot_deals",
                                        },
                                    }
                                    checkpoint_callback(job_id, mid_page_checkpoint)
                                except Exception as e:
                                    logger.warning(
                                        "Failed to save mid-page pause checkpoint",
                                        extra={"job_id": job_id, "error": str(e)},
                                    )
                            return  # Exit the generator

                        # Transform deal record to match database schema
                        transformed_record = _transform_deal_record(
                            record=record,
                            scan_id=job_id,
                            organization_id=organization_id,
                            page_number=page_count + 1
                        )

                        yield transformed_record
                        page_records += 1

                # Update counters
                total_records += page_records
                page_count += 1

                # Save checkpoint periodically
                if checkpoint_callback and page_count % checkpoint_interval == 0:
                    try:
                        # Get next cursor from HubSpot pagination
                        next_cursor = None
                        if (
                            data.get("paging")
                            and data["paging"].get("next")
                            and data["paging"]["next"].get("after")
                        ):
                            next_cursor = data["paging"]["next"]["after"]

                        checkpoint_data = {
                            "phase": "main_data",
                            "records_processed": total_records,
                            "cursor": next_cursor,
                            "page_number": page_count,
                            "batch_size": 100,
                            "checkpoint_data": {
                                "pages_processed": page_count,
                                "last_page_records": page_records,
                                "service": "hubspot_deals",
                            },
                        }

                        checkpoint_callback(job_id, checkpoint_data)

                        logger.debug(
                            "Checkpoint saved",
                            extra={
                                "operation": "data_extraction",
                                "job_id": job_id,
                                "page_number": page_count,
                                "total_records": total_records,
                            },
                        )

                    except Exception as checkpoint_error:
                        logger.warning(
                            "Failed to save checkpoint",
                            extra={
                                "operation": "data_extraction",
                                "job_id": job_id,
                                "error": str(checkpoint_error),
                            },
                        )

                # Handle HubSpot cursor-based pagination
                if (
                    data.get("paging")
                    and data["paging"].get("next")
                    and data["paging"]["next"].get("after")
                ):
                    after = data["paging"]["next"]["after"]
                else:
                    # No more pages - extraction complete
                    if checkpoint_callback:
                        try:
                            final_checkpoint = {
                                "phase": "main_data_completed",
                                "records_processed": total_records,
                                "cursor": None,
                                "page_number": page_count,
                                "batch_size": 100,
                                "checkpoint_data": {
                                    "completion_status": "success",
                                    "total_pages": page_count,
                                    "final_total": total_records,
                                    "service": "hubspot_deals",
                                },
                            }
                            checkpoint_callback(job_id, final_checkpoint)
                        except Exception as e:
                            logger.warning(
                                "Failed to save final checkpoint",
                                extra={"job_id": job_id, "error": str(e)},
                            )

                    logger.info(
                        "Data extraction completed",
                        extra={
                            "operation": "data_extraction",
                            "job_id": job_id,
                            "total_records": total_records,
                            "total_pages": page_count,
                        },
                    )
                    break

            except Exception as e:
                logger.error(
                    "Error fetching data page",
                    extra={
                        "operation": "data_extraction",
                        "job_id": job_id,
                        "page_number": page_count + 1,
                        "error": str(e),
                    },
                    exc_info=True,
                )

                # Save error checkpoint for debugging
                if checkpoint_callback:
                    try:
                        error_checkpoint = {
                            "phase": "main_data_error",
                            "records_processed": total_records,
                            "cursor": after,
                            "page_number": page_count,
                            "batch_size": 100,
                            "checkpoint_data": {
                                "error": str(e),
                                "error_page": page_count + 1,
                                "recovery_cursor": after,
                                "service": "hubspot_deals",
                            },
                        }
                        checkpoint_callback(job_id, error_checkpoint)
                    except:
                        pass

                raise e

    return [get_main_data]
