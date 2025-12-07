# 📋 HubSpot Deals ETL - Integration with HubSpot CRM API v3

This document explains the HubSpot CRM API v3 endpoints required by the HubSpot Deals ETL service to extract deal data from HubSpot instances.

---

## 📋 Overview

The HubSpot Deals ETL service integrates with HubSpot CRM API v3 endpoints to extract deal information. Below are the required and optional endpoints:

### ✅ **Required Endpoint (Essential)**
| **API Endpoint**                    | **Purpose**                          | **Version** | **Required Permissions** | **Usage**    |
|-------------------------------------|--------------------------------------|-------------|--------------------------|--------------|
| `/crm/v3/objects/deals`             | Search and list deals                | v3          | crm.objects.deals.read   | **Required** |

### 🔧 **Optional Endpoints (Advanced Features)**
| **API Endpoint**                    | **Purpose**                          | **Version** | **Required Permissions** | **Usage**    |
|-------------------------------------|--------------------------------------|-------------|--------------------------|--------------|
| `/crm/v3/objects/deals/{dealId}`    | Get detailed deal information        | v3          | crm.objects.deals.read   | Optional     |
| `/crm/v3/properties/deals`          | Get available deal properties        | v3          | crm.schemas.deals.read   | Optional     |
| `/crm/v4/objects/deals/{dealId}/associations/{toObjectType}` | Get deal associations | v4 | crm.objects.deals.read | Optional |
| `/crm/v3/objects/deals/batch/read`  | Batch read multiple deals            | v3          | crm.objects.deals.read   | Optional     |

### 🎯 **Recommendation**
**Start with only the required endpoint.** The `/crm/v3/objects/deals` endpoint provides all essential deal data needed for basic deal analytics and extraction.

---

## 🔐 Authentication Requirements

### **Private App Access Token Authentication**
HubSpot uses Private App Access Tokens for authentication. Create a Private App in your HubSpot account to obtain an access token.

```http
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json
```

### **Setting Up a Private App**
1. Navigate to **Settings** > **Integrations** > **Private Apps** in your HubSpot account
2. Click **Create a private app**
3. Configure basic information:
   - **Name**: HubSpot Deals ETL Service
   - **Description**: Extract deal data for analytics and reporting
4. Set required scopes (see below)
5. Click **Create app** and copy the access token

### **Required Scopes (Permissions)**
- **crm.objects.deals.read**: Read deals and their properties
- **crm.schemas.deals.read**: Read deal property definitions (optional, for schema discovery)

### **Optional Scopes (Advanced Features)**
- **crm.objects.contacts.read**: Read contact associations
- **crm.objects.companies.read**: Read company associations
- **crm.objects.owners.read**: Read owner information

---

## 🌐 HubSpot CRM API Endpoints

### 🎯 **PRIMARY ENDPOINT (Required for Basic Deal Extraction)**

### 1. **List Deals** - `/crm/v3/objects/deals` ✅ **REQUIRED**

**Purpose**: Get paginated list of all deals - **THIS IS ALL YOU NEED FOR BASIC DEAL EXTRACTION**

**Method**: `GET`

**URL**: `https://api.hubapi.com/crm/v3/objects/deals`

**Query Parameters**:
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `limit` | integer | No | 10 | Number of results per page (1-100) |
| `after` | string | No | - | Paging cursor token for next page |
| `properties` | string | No | - | Comma-separated list of properties to return |
| `propertiesWithHistory` | string | No | - | Comma-separated list of properties to return with history |
| `associations` | string | No | - | Comma-separated list of object types to retrieve associations for |
| `archived` | boolean | No | false | Whether to return only archived deals |

**Request Example**:
```http
GET https://api.hubapi.com/crm/v3/objects/deals?limit=50&properties=dealname,amount,dealstage,pipeline,closedate
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json
```

**Response Structure** (Contains ALL essential deal data):
```json
{
  "results": [
    {
      "id": "12345678901",
      "properties": {
        "amount": "50000",
        "closedate": "2024-12-31T00:00:00.000Z",
        "createdate": "2024-01-15T14:30:00.000Z",
        "dealname": "New Enterprise Deal - Acme Corp",
        "dealstage": "qualifiedtobuy",
        "hs_lastmodifieddate": "2024-12-01T10:15:30.000Z",
        "hs_object_id": "12345678901",
        "pipeline": "default"
      },
      "createdAt": "2024-01-15T14:30:00.000Z",
      "updatedAt": "2024-12-01T10:15:30.000Z",
      "archived": false
    },
    {
      "id": "12345678902",
      "properties": {
        "amount": "25000",
        "closedate": "2024-11-15T00:00:00.000Z",
        "createdate": "2024-02-20T09:00:00.000Z",
        "dealname": "Professional Services - Beta Inc",
        "dealstage": "closedwon",
        "hs_lastmodifieddate": "2024-11-15T16:45:00.000Z",
        "hs_object_id": "12345678902",
        "pipeline": "default"
      },
      "createdAt": "2024-02-20T09:00:00.000Z",
      "updatedAt": "2024-11-15T16:45:00.000Z",
      "archived": false
    }
  ],
  "paging": {
    "next": {
      "after": "12345678902",
      "link": "https://api.hubapi.com/crm/v3/objects/deals?limit=50&after=12345678902"
    }
  }
}
```

**✅ This endpoint provides ALL the default deal fields:**
- Deal ID (`id`, `hs_object_id`)
- Deal name, amount, stage, pipeline
- Close date and creation date
- Last modified timestamp
- Archived status
- Custom properties (if specified in `properties` parameter)

**Rate Limit**: 100 requests per 10 seconds per access token

---

## 🔧 **OPTIONAL ENDPOINTS (Advanced Features Only)**

> **⚠️ Note**: These endpoints are NOT required for basic deal extraction. Only implement if you need advanced deal analytics like individual deal details, property schemas, or associations.

### 2. **Get Deal by ID** - `/crm/v3/objects/deals/{dealId}` 🔧 **OPTIONAL**

**Purpose**: Get detailed information for a specific deal

**When to use**: Only if you need to fetch individual deal details by ID

**Method**: `GET`

**URL**: `https://api.hubapi.com/crm/v3/objects/deals/{dealId}`

**Path Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `dealId` | string | Yes | The ID of the deal to retrieve |

**Query Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `properties` | string | No | Comma-separated list of properties to return |
| `propertiesWithHistory` | string | No | Properties to return with full history |
| `associations` | string | No | Object types to retrieve associations for |

**Request Example**:
```http
GET https://api.hubapi.com/crm/v3/objects/deals/12345678901?properties=dealname,amount,dealstage,pipeline,hs_analytics_source
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json
```

**Response Structure**:
```json
{
  "id": "12345678901",
  "properties": {
    "amount": "50000",
    "closedate": "2024-12-31T00:00:00.000Z",
    "createdate": "2024-01-15T14:30:00.000Z",
    "dealname": "New Enterprise Deal - Acme Corp",
    "dealstage": "qualifiedtobuy",
    "dealtype": "newbusiness",
    "hs_analytics_source": "ORGANIC_SEARCH",
    "hs_forecast_amount": "50000",
    "hs_forecast_probability": "0.4",
    "hs_lastmodifieddate": "2024-12-01T10:15:30.000Z",
    "hs_object_id": "12345678901",
    "hubspot_owner_id": "123456",
    "pipeline": "default"
  },
  "createdAt": "2024-01-15T14:30:00.000Z",
  "updatedAt": "2024-12-01T10:15:30.000Z",
  "archived": false
}
```

---

### 3. **Get Deal Properties** - `/crm/v3/properties/deals` 🔧 **OPTIONAL**

**Purpose**: Get schema information for all available deal properties

**When to use**: Only if you need to discover available properties dynamically or validate property definitions

**Method**: `GET`

**URL**: `https://api.hubapi.com/crm/v3/properties/deals`

**Query Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `archived` | boolean | No | Include archived properties |

**Request Example**:
```http
GET https://api.hubapi.com/crm/v3/properties/deals
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json
```

**Response Structure**:
```json
{
  "results": [
    {
      "name": "dealname",
      "label": "Deal Name",
      "type": "string",
      "fieldType": "text",
      "description": "The name given to this deal",
      "groupName": "dealinformation",
      "options": [],
      "displayOrder": 1,
      "calculated": false,
      "externalOptions": false,
      "hasUniqueValue": false,
      "hidden": false,
      "modificationMetadata": {
        "archivable": false,
        "readOnlyDefinition": true,
        "readOnlyValue": false
      }
    },
    {
      "name": "amount",
      "label": "Amount",
      "type": "number",
      "fieldType": "number",
      "description": "The total value of the deal in the deal's currency",
      "groupName": "dealinformation",
      "options": [],
      "displayOrder": 2,
      "calculated": false,
      "externalOptions": false,
      "hasUniqueValue": false,
      "hidden": false,
      "modificationMetadata": {
        "archivable": false,
        "readOnlyDefinition": true,
        "readOnlyValue": false
      }
    }
  ]
}
```

---

### 4. **Get Deal Associations** - `/crm/v4/objects/deals/{dealId}/associations/{toObjectType}` 🔧 **OPTIONAL**

**Purpose**: Get associations between a deal and other CRM objects (contacts, companies, line items)

**When to use**: Only if you need to analyze relationships between deals and other objects

**Method**: `GET`

**URL**: `https://api.hubapi.com/crm/v4/objects/deals/{dealId}/associations/{toObjectType}`

**Path Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `dealId` | string | Yes | The ID of the deal |
| `toObjectType` | string | Yes | The object type to get associations for (contacts, companies, line_items) |

**Request Example**:
```http
GET https://api.hubapi.com/crm/v4/objects/deals/12345678901/associations/contacts
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json
```

**Response Structure**:
```json
{
  "results": [
    {
      "toObjectId": "987654321",
      "associationTypes": [
        {
          "category": "HUBSPOT_DEFINED",
          "typeId": 3,
          "label": "Deal to Contact"
        }
      ]
    },
    {
      "toObjectId": "987654322",
      "associationTypes": [
        {
          "category": "HUBSPOT_DEFINED",
          "typeId": 3,
          "label": "Deal to Contact"
        }
      ]
    }
  ],
  "paging": {
    "next": {
      "after": "987654322"
    }
  }
}
```

---

### 5. **Batch Read Deals** - `/crm/v3/objects/deals/batch/read` 🔧 **OPTIONAL**

**Purpose**: Retrieve multiple deals by ID in a single request

**When to use**: Only if you have specific deal IDs and need to fetch them efficiently

**Method**: `POST`

**URL**: `https://api.hubapi.com/crm/v3/objects/deals/batch/read`

**Request Body**:
```json
{
  "properties": ["dealname", "amount", "dealstage", "pipeline", "closedate"],
  "propertiesWithHistory": [],
  "inputs": [
    {"id": "12345678901"},
    {"id": "12345678902"},
    {"id": "12345678903"}
  ]
}
```

**Request Example**:
```http
POST https://api.hubapi.com/crm/v3/objects/deals/batch/read
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json

{
  "properties": ["dealname", "amount", "dealstage"],
  "inputs": [
    {"id": "12345678901"},
    {"id": "12345678902"}
  ]
}
```

**Response Structure**:
```json
{
  "status": "COMPLETE",
  "results": [
    {
      "id": "12345678901",
      "properties": {
        "amount": "50000",
        "dealname": "Enterprise Deal - Acme Corp",
        "dealstage": "qualifiedtobuy"
      },
      "createdAt": "2024-01-15T14:30:00.000Z",
      "updatedAt": "2024-12-01T10:15:30.000Z",
      "archived": false
    },
    {
      "id": "12345678902",
      "properties": {
        "amount": "25000",
        "dealname": "Professional Services - Beta Inc",
        "dealstage": "closedwon"
      },
      "createdAt": "2024-02-20T09:00:00.000Z",
      "updatedAt": "2024-11-15T16:45:00.000Z",
      "archived": false
    }
  ]
}
```

---

## 📊 Data Extraction Flow

### 🎯 **SIMPLE FLOW (Recommended - Using Only Required Endpoint)**

### **Single Endpoint Approach - `/crm/v3/objects/deals` Only**
```python
import requests
from typing import List, Dict, Any

def extract_all_deals_simple(access_token: str, properties: List[str] = None) -> List[Dict[str, Any]]:
    """Extract all deals using only the /crm/v3/objects/deals endpoint"""
    base_url = "https://api.hubapi.com"
    endpoint = "/crm/v3/objects/deals"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # Default properties to fetch
    if properties is None:
        properties = [
            "dealname", "amount", "dealstage", "pipeline", "closedate",
            "createdate", "hs_lastmodifieddate", "dealtype", "hubspot_owner_id"
        ]
    
    all_deals = []
    after = None
    limit = 100  # Maximum allowed
    
    while True:
        # Build query parameters
        params = {
            "limit": limit,
            "properties": ",".join(properties)
        }
        
        if after:
            params["after"] = after
        
        # Make API request
        response = requests.get(
            f"{base_url}{endpoint}",
            headers=headers,
            params=params
        )
        
        if response.status_code != 200:
            raise Exception(f"API Error: {response.status_code} - {response.text}")
        
        data = response.json()
        deals = data.get("results", [])
        
        if not deals:  # No more deals
            break
            
        all_deals.extend(deals)
        
        # Check if there's a next page
        paging = data.get("paging", {})
        next_page = paging.get("next", {})
        after = next_page.get("after")
        
        if not after:  # No more pages
            break
    
    return all_deals

# This gives you ALL essential deal data:
# - Deal ID, name, amount, stage, pipeline
# - Close date, create date, last modified date
# - Deal type and owner information
# - Custom properties (if specified)
```

---

### 🔧 **ADVANCED FLOW (Optional - Multiple Endpoints)**

> **⚠️ Only use this if you need property schemas, individual deal details, or associations**

### **Step 1: Get Available Properties (Optional)**
```python
def get_deal_properties(access_token: str) -> List[Dict[str, Any]]:
    """Get all available deal properties"""
    response = requests.get(
        "https://api.hubapi.com/crm/v3/properties/deals",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    return response.json()["results"]
```

### **Step 2: Batch Deal Retrieval**
```python
def get_deals_paginated(access_token: str, limit: int = 100) -> List[Dict[str, Any]]:
    """Get deals in batches with pagination"""
    all_deals = []
    after = None
    
    while True:
        params = {"limit": limit}
        if after:
            params["after"] = after
        
        response = requests.get(
            "https://api.hubapi.com/crm/v3/objects/deals",
            headers={"Authorization": f"Bearer {access_token}"},
            params=params
        )
        
        data = response.json()
        deals = data.get("results", [])
        all_deals.extend(deals)
        
        # Get next page cursor
        after = data.get("paging", {}).get("next", {}).get("after")
        if not after:
            break
    
    return all_deals
```

### **Step 3: Get Deal Associations (Optional)**
```python
def get_deal_associations(access_token: str, deal_id: str, object_type: str) -> List[Dict[str, Any]]:
    """Get associations for a specific deal"""
    response = requests.get(
        f"https://api.hubapi.com/crm/v4/objects/deals/{deal_id}/associations/{object_type}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    return response.json().get("results", [])
```

### **Step 4: Batch Read Specific Deals (Optional)**
```python
def batch_read_deals(access_token: str, deal_ids: List[str], properties: List[str]) -> List[Dict[str, Any]]:
    """Read multiple deals by ID in one request"""
    payload = {
        "properties": properties,
        "inputs": [{"id": deal_id} for deal_id in deal_ids]
    }
    
    response = requests.post(
        "https://api.hubapi.com/crm/v3/objects/deals/batch/read",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        },
        json=payload
    )
    
    return response.json().get("results", [])
```

---

## ⚡ Performance Considerations

### **Rate Limiting**
- **Default Limit**: 100 requests per 10 seconds per access token
- **Burst Limit**: 150 requests per 10 seconds (short duration)
- **Daily Limit**: Varies by HubSpot subscription tier
- **Best Practice**: Implement exponential backoff on 429 responses

### **Rate Limit Headers**
HubSpot includes rate limit information in response headers:
```http
X-HubSpot-RateLimit-Daily: 250000
X-HubSpot-RateLimit-Daily-Remaining: 249900
X-HubSpot-RateLimit-Interval-Milliseconds: 10000
X-HubSpot-RateLimit-Max: 100
X-HubSpot-RateLimit-Remaining: 99
X-HubSpot-RateLimit-Secondly: 10
X-HubSpot-RateLimit-Secondly-Remaining: 9
```

### **Batch Processing**
- **Recommended Page Size**: 100 deals per request (maximum)
- **Concurrent Requests**: Max 3-5 parallel requests to avoid rate limits
- **Request Interval**: 100ms between requests minimum
- **Batch Read**: Up to 100 deals per batch/read request

### **Error Handling**
```http
# Rate limit exceeded
HTTP/429 Too Many Requests
X-HubSpot-RateLimit-Remaining: 0
Retry-After: 10

# Authentication failed  
HTTP/401 Unauthorized
{
  "status": "error",
  "message": "The access token provided is invalid",
  "correlationId": "abc-123-def-456"
}

# Insufficient permissions
HTTP/403 Forbidden
{
  "status": "error",
  "message": "This access token does not have proper permissions",
  "correlationId": "abc-123-def-456"
}

# Deal not found
HTTP/404 Not Found
{
  "status": "error",
  "message": "resource not found",
  "correlationId": "abc-123-def-456"
}
```

### **Retry Logic Example**
```python
import time
import random

def make_request_with_retry(url: str, headers: dict, max_retries: int = 3):
    """Make API request with exponential backoff retry"""
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers)
            
            if response.status_code == 429:
                # Rate limited - wait and retry
                retry_after = int(response.headers.get('Retry-After', 10))
                wait_time = retry_after + random.uniform(0, 1)
                time.sleep(wait_time)
                continue
            
            if response.status_code >= 500:
                # Server error - exponential backoff
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                time.sleep(wait_time)
                continue
            
            # Success or client error (don't retry)
            return response
            
        except requests.RequestException as e:
            if attempt == max_retries - 1:
                raise
            wait_time = (2 ** attempt) + random.uniform(0, 1)
            time.sleep(wait_time)
    
    raise Exception(f"Max retries ({max_retries}) exceeded")
```

---

## 🔒 Security Requirements

### **API Token Permissions**

#### ✅ **Required (Minimum Permissions)**
```
Required Scopes:
- crm.objects.deals.read (for reading deals)
```

#### 🔧 **Optional (Advanced Features)**
```
Additional Scopes (only if using optional endpoints):
- crm.schemas.deals.read (for property schema information)
- crm.objects.contacts.read (for contact associations)
- crm.objects.companies.read (for company associations)
- crm.objects.owners.read (for owner information)
```

### **Private App Setup**

#### ✅ **Required (Minimum)**
The Private App must have:
- **crm.objects.deals.read** scope

#### 🔧 **Optional (Advanced Features)**
Additional scopes (only if using optional endpoints):
- **crm.schemas.deals.read** (for property definitions)
- **crm.objects.contacts.read** (for contact associations)
- **crm.objects.companies.read** (for company associations)

### **Access Token Security**
- Store access tokens securely (environment variables, secrets manager)
- Never commit tokens to version control
- Rotate tokens periodically
- Use separate tokens for dev/staging/production
- Monitor token usage for suspicious activity

---

## 📊 Available Deal Properties

### **Standard Deal Properties**

#### **Basic Information**
| Property Name | Type | Description |
|--------------|------|-------------|
| `dealname` | string | The name of the deal |
| `amount` | number | The total value of the deal in the deal's currency |
| `pipeline` | string | The pipeline the deal is in |
| `dealstage` | string | The current stage of the deal in its pipeline |
| `dealtype` | enumeration | The type of deal (newbusiness, existingbusiness, etc.) |
| `description` | string | A description of the deal |

#### **Date Fields**
| Property Name | Type | Description |
|--------------|------|-------------|
| `createdate` | datetime | When the deal was created |
| `closedate` | datetime | The expected close date of the deal |
| `hs_lastmodifieddate` | datetime | Most recent modification timestamp |
| `hs_date_entered_{stagename}` | datetime | When deal entered specific stage |
| `hs_date_exited_{stagename}` | datetime | When deal exited specific stage |

#### **Financial Fields**
| Property Name | Type | Description |
|--------------|------|-------------|
| `amount` | number | Deal value in deal currency |
| `amount_in_home_currency` | number | Deal value in portal's currency |
| `hs_arr` | number | Annual Recurring Revenue |
| `hs_mrr` | number | Monthly Recurring Revenue |
| `hs_tcv` | number | Total Contract Value |
| `hs_acv` | number | Annual Contract Value |

#### **Forecasting**
| Property Name | Type | Description |
|--------------|------|-------------|
| `hs_forecast_amount` | number | Forecasted deal amount |
| `hs_forecast_probability` | number | Win probability (0-1) |
| `hs_manual_forecast_category` | enumeration | Manual forecast category |

#### **Ownership & Assignment**
| Property Name | Type | Description |
|--------------|------|-------------|
| `hubspot_owner_id` | string | ID of the deal owner |
| `hubspot_owner_assigneddate` | datetime | When owner was assigned |
| `hubspot_team_id` | string | ID of the team that owns the deal |

#### **Source & Attribution**
| Property Name | Type | Description |
|--------------|------|-------------|
| `hs_analytics_source` | enumeration | Original source of the deal |
| `hs_analytics_source_data_1` | string | Drill-down 1 for the source |
| `hs_analytics_source_data_2` | string | Drill-down 2 for the source |
| `hs_campaign` | string | Associated marketing campaign |

#### **System Fields**
| Property Name | Type | Description |
|--------------|------|-------------|
| `hs_object_id` | string | Unique identifier for the deal |
| `hs_created_by_user_id` | string | ID of user who created the deal |
| `hs_updated_by_user_id` | string | ID of user who last updated |
| `hs_all_owner_ids` | string | All owners (current and historical) |
| `hs_all_team_ids` | string | All teams (current and historical) |

#### **Deal Stages & Pipeline**
| Property Name | Type | Description |
|--------------|------|-------------|
| `dealstage` | enumeration | Current deal stage |
| `pipeline` | enumeration | Pipeline the deal belongs to |
| `hs_is_closed` | bool | Whether the deal is closed |
| `hs_is_closed_won` | bool | Whether the deal is closed won |
| `hs_days_to_close` | number | Days from creation to close |

#### **Engagement Metrics**
| Property Name | Type | Description |
|--------------|------|-------------|
| `num_associated_contacts` | number | Number of contacts associated |
| `num_contacted_notes` | number | Number of notes on deal |
| `num_notes` | number | Total number of notes |
| `hs_num_of_associated_line_items` | number | Number of line items |
| `hs_time_in_dealstage` | number | Time in current stage (seconds) |

### **Getting All Available Properties**

To retrieve a complete list of all properties (including custom properties):

```bash
curl -X GET \
  "https://api.hubapi.com/crm/v3/properties/deals" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

This will return all standard and custom deal properties with their:
- Name and label
- Data type
- Description
- Field type
- Group name
- Options (for enumeration fields)

---

## 📈 Monitoring & Debugging

### **Request Headers for Debugging**
```http
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json
User-Agent: HubSpotDealsETL/1.0
X-Request-ID: deal-scan-001-batch-1
```

### **Response Validation**
```python
def validate_deal_response(deal_data: dict) -> bool:
    """Validate deal response structure"""
    required_fields = ["id", "properties", "createdAt", "updatedAt"]
    
    for field in required_fields:
        if field not in deal_data:
            raise ValueError(f"Missing required field: {field}")
    
    # Validate properties exist
    properties = deal_data.get("properties", {})
    if not properties:
        raise ValueError("Deal has no properties")
    
    return True
```

### **API Usage Metrics**
Monitor these metrics for optimal performance:
- **Requests per 10 seconds**: Track against 100 request limit
- **Response times**: Average should be < 500ms
- **Error rates**: Should be < 1% of requests
- **Rate limit remaining**: Monitor X-HubSpot-RateLimit-Remaining header
- **Daily usage**: Track against subscription tier limits

### **Logging Best Practices**
```python
import logging

logger = logging.getLogger(__name__)

def log_api_call(endpoint: str, status_code: int, duration_ms: float, deal_count: int = None):
    """Log API call metrics"""
    logger.info(
        f"HubSpot API Call",
        extra={
            "endpoint": endpoint,
            "status_code": status_code,
            "duration_ms": duration_ms,
            "deal_count": deal_count,
            "timestamp": datetime.utcnow().isoformat()
        }
    )
```

---

## 🧪 Testing API Integration

### **Test Authentication**
```bash
curl -X GET \
  "https://api.hubapi.com/crm/v3/objects/deals?limit=1" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json"
```

**Expected Response**: 200 OK with deal data or empty results

### **Test Deal Retrieval**
```bash
curl -X GET \
  "https://api.hubapi.com/crm/v3/objects/deals?limit=5&properties=dealname,amount,dealstage" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json"
```

### **Test Pagination**
```bash
# Get first page
curl -X GET \
  "https://api.hubapi.com/crm/v3/objects/deals?limit=10" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# Get next page using 'after' cursor from previous response
curl -X GET \
  "https://api.hubapi.com/crm/v3/objects/deals?limit=10&after=CURSOR_VALUE" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### **Test Deal Properties**
```bash
curl -X GET \
  "https://api.hubapi.com/crm/v3/properties/deals" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### **Python Test Script**
```python
import requests

def test_hubspot_connection(access_token: str):
    """Test HubSpot API connection"""
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Test 1: Authentication
    print("Testing authentication...")
    response = requests.get(
        "https://api.hubapi.com/crm/v3/objects/deals?limit=1",
        headers=headers
    )
    print(f"Auth test: {response.status_code}")
    
    # Test 2: Get deals
    print("\nTesting deal retrieval...")
    response = requests.get(
        "https://api.hubapi.com/crm/v3/objects/deals?limit=5",
        headers=headers
    )
    data = response.json()
    print(f"Retrieved {len(data.get('results', []))} deals")
    
    # Test 3: Get properties
    print("\nTesting property retrieval...")
    response = requests.get(
        "https://api.hubapi.com/crm/v3/properties/deals",
        headers=headers
    )
    properties = response.json().get('results', [])
    print(f"Found {len(properties)} deal properties")
    
    return True

# Run tests
if __name__ == "__main__":
    access_token = "YOUR_ACCESS_TOKEN"
    test_hubspot_connection(access_token)
```

---

## 🚨 Common Issues & Solutions

### **Issue**: 401 Unauthorized
**Solution**: Verify your access token is valid and not expired
```bash
# Test token validity
curl -X GET \
  "https://api.hubapi.com/crm/v3/objects/deals?limit=1" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```
- Check that you're using the correct token
- Verify the Private App hasn't been deleted
- Ensure token is properly formatted: `Bearer YOUR_ACCESS_TOKEN`

### **Issue**: 403 Forbidden
**Solution**: Check that your Private App has the required scopes
- Navigate to Settings > Integrations > Private Apps
- Select your app and check the Scopes tab
- Ensure `crm.objects.deals.read` is enabled
- If you just added scopes, generate a new access token

### **Issue**: 429 Too Many Requests (Rate Limited)
**Solution**: Implement retry with exponential backoff
```python
import time
import random

def handle_rate_limit(response):
    """Handle 429 rate limit response"""
    if response.status_code == 429:
        retry_after = int(response.headers.get('Retry-After', 10))
        wait_time = retry_after + random.uniform(0, 1)
        print(f"Rate limited. Waiting {wait_time} seconds...")
        time.sleep(wait_time)
        return True
    return False
```

### **Issue**: Empty Deal List
**Solution**: Verify there are deals in the HubSpot portal
- Check that deals exist in the portal
- Verify the access token's portal has deals
- Check if `archived=true` parameter is needed
- Ensure user has permission to view deals

### **Issue**: Missing Custom Properties
**Solution**: Explicitly request custom properties in the `properties` parameter
```python
# Include custom properties in request
properties = [
    "dealname", "amount", "dealstage",
    "custom_property_1", "custom_property_2"  # Add your custom properties
]
params = {"properties": ",".join(properties)}
```

### **Issue**: Slow Performance
**Solution**: Optimize pagination and concurrency
- Use maximum `limit=100` to reduce request count
- Implement concurrent requests (3-5 parallel)
- Use batch read endpoint for specific IDs
- Request only needed properties, not all

### **Issue**: Property Values Are Null
**Solution**: Check property configuration and deal data
- Some properties may be empty for specific deals
- Verify property exists in the portal
- Check if property is available for the deal's object type
- Use `/crm/v3/properties/deals` to see available properties

---

## 💡 **Implementation Recommendations**

### 🎯 **Phase 1: Start Simple (Recommended)**
1. Implement only `/crm/v3/objects/deals` endpoint
2. Extract basic deal data (name, amount, stage, pipeline, dates)
3. Use pagination with `after` cursor
4. This covers 95% of deal analytics needs

### 🔧 **Phase 2: Add Advanced Features (If Needed)**
1. Add `/crm/v3/properties/deals` for dynamic property discovery
2. Add `/crm/v3/objects/deals/{dealId}` for individual deal details
3. Add `/crm/v4/objects/deals/{dealId}/associations/{toObjectType}` for relationships
4. Add `/crm/v3/objects/deals/batch/read` for efficient bulk retrieval

### ⚡ **Performance Tips**
- **Simple approach**: 1 API call per 100 deals (max efficiency)
- **Advanced approach**: 1 + N API calls (N = number of additional details needed)
- **Start simple** to minimize API usage and complexity
- **Use batch read** when fetching specific deals by ID
- **Implement caching** for property schemas (they rarely change)

### 🔐 **Security Best Practices**
- Store access tokens in environment variables or secrets manager
- Use separate tokens for dev/staging/production
- Implement token rotation strategy
- Monitor token usage for anomalies
- Log all API access for audit trails

---

## 📞 Support Resources

- **HubSpot API Documentation**: https://developers.hubspot.com/docs/api/crm/deals
- **CRM Objects Overview**: https://developers.hubspot.com/docs/api/crm/understanding-the-crm
- **Rate Limiting Guide**: https://developers.hubspot.com/docs/api/usage-details
- **Authentication Guide**: https://developers.hubspot.com/docs/api/private-apps
- **Deal Properties Reference**: https://developers.hubspot.com/docs/api/crm/properties
- **Developer Community**: https://community.hubspot.com/t5/APIs-Integrations/ct-p/apis
- **API Status Page**: https://status.hubspot.com/

---

**Document Version**: 1.0  
**Last Updated**: December 2025  
**API Version**: HubSpot CRM API v3  
**Maintained By**: HubSpot Deals ETL Team
