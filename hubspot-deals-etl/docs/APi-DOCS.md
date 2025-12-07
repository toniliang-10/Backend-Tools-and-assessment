# HubSpot Deals ETL Service - API Documentation

## 📋 Table of Contents
1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Base URLs](#base-urls)
4. [Common Response Formats](#common-response-formats)
5. [Scan Endpoints](#scan-endpoints)
6. [Results Endpoints](#results-endpoints)
7. [Pipeline & Maintenance Endpoints](#pipeline--maintenance-endpoints)
8. [Health & Stats Endpoints](#health--stats-endpoints)
9. [Error Handling](#error-handling)
10. [Request/Response Examples](#requestresponse-examples)
11. [Rate Limiting](#rate-limiting)

---

## 🔍 Overview

The HubSpot Deals ETL Service is a RESTful API for extracting, transforming, and loading deal data from HubSpot CRM into a PostgreSQL database with multi-tenant support.

### API Version
- **Version**: 1.0.0
- **Base Path**: `/api/v1`
- **Content Type**: `application/json`
- **Documentation**: Available at `/docs` (Swagger UI)
- **OpenAPI Spec**: Available at `/swagger.json`

### Key Features
- **Asynchronous Deal Extraction**: Non-blocking scan operations with real-time progress tracking
- **Multi-Tenant Support**: Isolated data storage per HubSpot portal
- **Checkpoint & Resume**: Automatically resume failed extractions from last checkpoint
- **Flexible Filtering**: Extract specific properties and deal segments
- **Progress Monitoring**: Real-time status updates and progress tracking
- **Data Export**: Export results in JSON, CSV, or Excel formats
- **Rate Limit Handling**: Automatic retry with exponential backoff

---

## 🔐 Authentication

The service requires **HubSpot Private App Access Tokens** to authenticate requests to the HubSpot API.

### Authentication Flow

1. **Create a Private App** in your HubSpot account
2. **Obtain Access Token** from the Private App settings
3. **Include Token** in scan request configuration

### Required HubSpot Scopes

The HubSpot Private App must have the following scopes:

- `crm.objects.deals.read` - **Required** for reading deals
- `crm.schemas.deals.read` - Optional for property schema discovery
- `crm.objects.contacts.read` - Optional for contact associations
- `crm.objects.companies.read` - Optional for company associations

### Request Headers

```http
Content-Type: application/json
```

**Note**: This service does not require authentication headers for its own API. Authentication is provided via the HubSpot access token in the scan configuration.

---

## 🌐 Base URLs

### Development
```
http://localhost:5200
```

### Staging
```
http://localhost:5201
```

### Production
```
http://localhost:5202
```

### Swagger Documentation
```
http://localhost:5200/docs
```

**Note**: Update these URLs based on your deployment configuration.

---

## 📊 Common Response Formats

### Success Response
```json
{
  "status": "success",
  "message": "Operation completed successfully",
  "data": {},
  "timestamp": "2024-12-07T10:30:00Z"
}
```

### Error Response (Validation)
```json
{
  "status": "error",
  "message": "Input validation failed",
  "errors": {
    "config.auth.accessToken": "This field is required",
    "config.scanId": "Must be alphanumeric with hyphens/underscores only"
  },
  "timestamp": "2024-12-07T10:30:00Z"
}
```

### Error Response (Application Logic)
```json
{
  "status": "error",
  "error_code": "SCAN_ALREADY_RUNNING",
  "message": "A scan with this ID is already in progress",
  "details": {
    "scan_id": "hubspot-deals-scan-001",
    "current_status": "running"
  },
  "timestamp": "2024-12-07T10:30:00Z"
}
```

### Pagination Response
```json
{
  "pagination": {
    "current_page": 1,
    "page_size": 100,
    "total_items": 1500,
    "total_pages": 15,
    "has_next": true,
    "has_previous": false,
    "next_page": 2,
    "previous_page": null
  }
}
```

---

## 🔍 Scan Endpoints

### 1. Start Deal Extraction

**POST** `/api/v1/scan/start`

Initiates a new deal extraction process from HubSpot CRM.

#### Request Body Schema

```json
{
  "config": {
    "scanId": "string (required)",
    "organizationId": "string (required)",
    "type": ["deals"],
    "auth": {
      "accessToken": "string (required)"
    },
    "filters": {
      "properties": ["array of property names"],
      "dealstage": "string",
      "pipeline": "string",
      "includeArchived": "boolean",
      "dateRange": {
        "startDate": "YYYY-MM-DD",
        "endDate": "YYYY-MM-DD"
      }
    },
    "options": {
      "batchSize": "integer (1-100)",
      "maxRetries": "integer"
    }
  }
}
```

#### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `config.scanId` | string | Yes | Unique identifier for the scan (alphanumeric, hyphens, underscores, max 255 chars) |
| `config.organizationId` | string | Yes | HubSpot Portal ID (Hub ID) |
| `config.type` | array | Yes | Must be `["deals"]` |
| `config.auth.accessToken` | string | Yes | HubSpot Private App access token |
| `config.filters.properties` | array | No | Specific deal properties to extract (default: all standard properties) |
| `config.filters.dealstage` | string | No | Filter by specific deal stage |
| `config.filters.pipeline` | string | No | Filter by specific pipeline |
| `config.filters.includeArchived` | boolean | No | Include archived deals (default: false) |
| `config.filters.dateRange` | object | No | Filter by date range |
| `config.options.batchSize` | integer | No | Number of deals per API request (1-100, default: 100) |
| `config.options.maxRetries` | integer | No | Max retry attempts for failed requests (default: 3) |

#### Request Example

```json
{
  "config": {
    "scanId": "hubspot-deals-dec-2024",
    "organizationId": "12345678",
    "type": ["deals"],
    "auth": {
      "accessToken": "pat-na1-11111111-2222-3333-4444-555555555555"
    },
    "filters": {
      "properties": [
        "dealname",
        "amount",
        "dealstage",
        "pipeline",
        "closedate",
        "hubspot_owner_id"
      ],
      "includeArchived": false,
      "dateRange": {
        "startDate": "2024-01-01",
        "endDate": "2024-12-31"
      }
    },
    "options": {
      "batchSize": 100,
      "maxRetries": 3
    }
  }
}
```

#### Response (202 Accepted)

```json
{
  "status": "success",
  "message": "Deal extraction started successfully",
  "data": {
    "scanId": "hubspot-deals-dec-2024",
    "organizationId": "12345678",
    "status": "pending",
    "jobId": "550e8400-e29b-41d4-a716-446655440000",
    "startedAt": "2024-12-07T10:30:00Z"
  },
  "timestamp": "2024-12-07T10:30:00Z"
}
```

#### Status Codes
- **202 Accepted**: Extraction started successfully
- **400 Bad Request**: Invalid request data or missing required fields
- **409 Conflict**: Scan with same ID already in progress
- **422 Unprocessable Entity**: HubSpot authentication failed
- **500 Internal Server Error**: Server error

---

### 2. Get Extraction Status

**GET** `/api/v1/scan/{scan_id}/status`

Retrieves the current status and progress of a deal extraction.

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `scan_id` | string | Yes | Unique scan identifier |

#### Response (200 OK)

```json
{
  "status": "success",
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "scanId": "hubspot-deals-dec-2024",
    "organizationId": "12345678",
    "status": "running",
    "progress": {
      "totalDeals": 1500,
      "processedDeals": 750,
      "failedDeals": 5,
      "percentComplete": 50.0,
      "dealsPerSecond": 12.5
    },
    "timing": {
      "startedAt": "2024-12-07T10:30:00Z",
      "completedAt": null,
      "elapsedSeconds": 60,
      "estimatedRemainingSeconds": 60
    },
    "checkpoint": {
      "lastProcessedId": "12345678901",
      "cursor": "MTIzNDU2Nzg5MDE=",
      "pageNumber": 8
    },
    "errorMessage": null,
    "createdAt": "2024-12-07T10:30:00Z",
    "updatedAt": "2024-12-07T10:31:00Z"
  },
  "timestamp": "2024-12-07T10:31:00Z"
}
```

#### Status Values

| Status | Description |
|--------|-------------|
| `pending` | Scan queued but not started |
| `running` | Extraction in progress |
| `completed` | Extraction finished successfully |
| `failed` | Extraction failed with error |
| `cancelled` | Extraction cancelled by user |
| `paused` | Extraction paused (can be resumed) |

#### Status Codes
- **200 OK**: Status retrieved successfully
- **404 Not Found**: Scan ID not found

---

### 3. Cancel Extraction

**POST** `/api/v1/scan/{scan_id}/cancel`

Cancels an ongoing deal extraction process.

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `scan_id` | string | Yes | Unique scan identifier |

#### Response (200 OK)

```json
{
  "status": "success",
  "message": "Extraction cancelled successfully",
  "data": {
    "scanId": "hubspot-deals-dec-2024",
    "status": "cancelled",
    "processedDeals": 750,
    "cancelledAt": "2024-12-07T10:35:00Z"
  },
  "timestamp": "2024-12-07T10:35:00Z"
}
```

#### Status Codes
- **200 OK**: Extraction cancelled successfully
- **400 Bad Request**: Extraction cannot be cancelled (not in running/pending state)
- **404 Not Found**: Scan ID not found

---

### 4. Remove Extraction

**DELETE** `/api/v1/scan/{scan_id}/remove`

Removes a scan job and all associated deal data.

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `scan_id` | string | Yes | Unique scan identifier |

#### Response (200 OK)

```json
{
  "status": "success",
  "message": "Extraction and 1,500 deals removed successfully",
  "data": {
    "scanId": "hubspot-deals-dec-2024",
    "dealsRemoved": 1500,
    "status": "removed"
  },
  "timestamp": "2024-12-07T10:40:00Z"
}
```

#### Status Codes
- **200 OK**: Extraction removed successfully
- **400 Bad Request**: Cannot remove running extraction
- **404 Not Found**: Scan ID not found

---

### 5. List All Scans

**GET** `/api/v1/scan/list`

Retrieves a paginated list of all scan jobs.

#### Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `organizationId` | string | No | - | Filter by HubSpot Portal ID |
| `status` | string | No | - | Filter by status (pending, running, completed, failed) |
| `limit` | integer | No | 50 | Number of results per page (1-100) |
| `offset` | integer | No | 0 | Number of results to skip |

#### Response (200 OK)

```json
{
  "status": "success",
  "data": {
    "scans": [
      {
        "scanId": "hubspot-deals-dec-2024",
        "organizationId": "12345678",
        "status": "completed",
        "totalDeals": 1500,
        "processedDeals": 1500,
        "startedAt": "2024-12-07T10:30:00Z",
        "completedAt": "2024-12-07T10:35:00Z",
        "duration": "5m 15s"
      },
      {
        "scanId": "hubspot-deals-nov-2024",
        "organizationId": "12345678",
        "status": "completed",
        "totalDeals": 1200,
        "processedDeals": 1200,
        "startedAt": "2024-11-07T08:00:00Z",
        "completedAt": "2024-11-07T08:04:00Z",
        "duration": "4m 10s"
      }
    ],
    "pagination": {
      "current_page": 1,
      "page_size": 50,
      "total_items": 25,
      "total_pages": 1,
      "has_next": false,
      "has_previous": false
    }
  },
  "timestamp": "2024-12-07T10:45:00Z"
}
```

#### Status Codes
- **200 OK**: Scans retrieved successfully

---

### 6. Get Scan Statistics

**GET** `/api/v1/scan/statistics`

Retrieves aggregated statistics across all scans for a tenant.

#### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `organizationId` | string | Yes | HubSpot Portal ID |

#### Response (200 OK)

```json
{
  "status": "success",
  "data": {
    "organizationId": "12345678",
    "totalScans": 12,
    "completedScans": 10,
    "failedScans": 1,
    "cancelledScans": 1,
    "totalDealsExtracted": 18500,
    "averageDealsPerScan": 1541,
    "averageScanDuration": "4m 30s",
    "lastScanDate": "2024-12-07T10:30:00Z",
    "successRate": 83.33
  },
  "timestamp": "2024-12-07T10:50:00Z"
}
```

#### Status Codes
- **200 OK**: Statistics retrieved successfully
- **400 Bad Request**: Missing organizationId parameter

---

## 📥 Results Endpoints

### 7. Get Available Tables

**GET** `/api/v1/results/{scan_id}/tables`

Retrieves list of available data tables for a completed scan.

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `scan_id` | string | Yes | Unique scan identifier |

#### Response (200 OK)

```json
{
  "status": "success",
  "data": {
    "scanId": "hubspot-deals-dec-2024",
    "organizationId": "12345678",
    "tables": [
      {
        "name": "deals",
        "rowCount": 1500,
        "schema": "hubspot_deals_12345678"
      }
    ]
  },
  "timestamp": "2024-12-07T11:00:00Z"
}
```

#### Status Codes
- **200 OK**: Tables retrieved successfully
- **404 Not Found**: Scan ID not found

---

### 8. Get Extraction Results

**GET** `/api/v1/results/{scan_id}/result`

Retrieves paginated deal data from a completed extraction.

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `scan_id` | string | Yes | Unique scan identifier |

#### Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `tableName` | string | No | deals | Table name to query |
| `limit` | integer | No | 100 | Number of results per page (1-1000) |
| `offset` | integer | No | 0 | Number of results to skip |

#### Response (200 OK)

```json
{
  "status": "success",
  "data": {
    "scanId": "hubspot-deals-dec-2024",
    "tableName": "deals",
    "results": [
      {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "hs_object_id": "12345678901",
        "dealname": "Enterprise Deal - Acme Corp",
        "amount": 50000.00,
        "dealstage": "qualifiedtobuy",
        "pipeline": "default",
        "closedate": "2024-12-31T00:00:00Z",
        "hubspot_owner_id": "123456",
        "_tenant_id": "12345678",
        "_scan_id": "hubspot-deals-dec-2024",
        "_extracted_at": "2024-12-07T10:32:15Z",
        "created_at": "2024-01-15T14:30:00Z",
        "updated_at": "2024-12-01T10:15:30Z"
      },
      {
        "id": "550e8400-e29b-41d4-a716-446655440001",
        "hs_object_id": "12345678902",
        "dealname": "Professional Services - Beta Inc",
        "amount": 25000.00,
        "dealstage": "closedwon",
        "pipeline": "default",
        "closedate": "2024-11-15T00:00:00Z",
        "hubspot_owner_id": "123457",
        "_tenant_id": "12345678",
        "_scan_id": "hubspot-deals-dec-2024",
        "_extracted_at": "2024-12-07T10:32:20Z",
        "created_at": "2024-02-20T09:00:00Z",
        "updated_at": "2024-11-15T16:45:00Z"
      }
    ],
    "pagination": {
      "current_page": 1,
      "page_size": 100,
      "total_items": 1500,
      "total_pages": 15,
      "has_next": true,
      "has_previous": false,
      "next_page": 2,
      "previous_page": null
    },
    "totalCount": 1500
  },
  "timestamp": "2024-12-07T11:05:00Z"
}
```

#### Status Codes
- **200 OK**: Results retrieved successfully
- **404 Not Found**: Scan ID not found
- **400 Bad Request**: Invalid pagination parameters

---

### 9. Download Extraction Results

**GET** `/api/v1/results/{scan_id}/download/{format}`

Downloads extraction results in the specified format.

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `scan_id` | string | Yes | Unique scan identifier |
| `format` | string | Yes | Download format: `json`, `csv`, or `excel` |

#### Supported Formats

| Format | Content-Type | File Extension |
|--------|-------------|----------------|
| `json` | application/json | .json |
| `csv` | text/csv | .csv |
| `excel` | application/vnd.openxmlformats-officedocument.spreadsheetml.sheet | .xlsx |

#### Response (200 OK)

File download with appropriate Content-Disposition header:

```http
Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
Content-Disposition: attachment; filename="hubspot-deals-dec-2024.xlsx"
```

#### Status Codes
- **200 OK**: File download initiated
- **400 Bad Request**: Invalid format specified
- **404 Not Found**: Scan ID not found or no data available
- **500 Internal Server Error**: Error generating file

---

## 🔧 Pipeline & Maintenance Endpoints

### 10. Get Pipeline Info

**GET** `/api/v1/pipeline/info`

Retrieves information about the DLT pipeline configuration.

#### Response (200 OK)

```json
{
  "status": "success",
  "data": {
    "pipelineName": "hubspot_deals_pipeline_dev",
    "destination": "postgres",
    "workingDirectory": "/app/.dlt",
    "database": {
      "host": "postgres_dev",
      "port": 5432,
      "database": "hubspot_deals_data_dev",
      "schema": "hubspot_deals_dev"
    },
    "version": "0.4.0",
    "state": {
      "lastRun": "2024-12-07T10:35:00Z",
      "totalRuns": 12
    }
  },
  "timestamp": "2024-12-07T11:10:00Z"
}
```

#### Status Codes
- **200 OK**: Pipeline info retrieved successfully

---

### 11. Cleanup Old Scans

**POST** `/api/v1/maintenance/cleanup`

Removes old completed scan jobs and their associated data.

#### Request Body

```json
{
  "daysOld": 90,
  "organizationId": "12345678",
  "dryRun": false
}
```

#### Request Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `daysOld` | integer | Yes | - | Remove scans older than this many days |
| `organizationId` | string | No | - | Filter by specific organization |
| `dryRun` | boolean | No | false | Preview what would be deleted without deleting |

#### Response (200 OK)

```json
{
  "status": "success",
  "message": "Cleanup completed successfully",
  "data": {
    "scansRemoved": 5,
    "dealsRemoved": 7500,
    "spaceSaved": "125 MB",
    "dryRun": false
  },
  "timestamp": "2024-12-07T11:15:00Z"
}
```

#### Status Codes
- **200 OK**: Cleanup completed successfully
- **400 Bad Request**: Invalid parameters

---

### 12. Detect Crashed Jobs

**POST** `/api/v1/maintenance/detect-crashed`

Detects and marks jobs that have crashed or timed out.

#### Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `timeoutMinutes` | integer | No | 60 | Consider jobs crashed after this many minutes without updates |

#### Response (200 OK)

```json
{
  "status": "success",
  "message": "Detected 2 crashed jobs",
  "data": {
    "crashedJobs": [
      {
        "scanId": "hubspot-deals-crashed-001",
        "organizationId": "12345678",
        "lastUpdate": "2024-12-07T08:00:00Z",
        "minutesStale": 180
      },
      {
        "scanId": "hubspot-deals-crashed-002",
        "organizationId": "12345678",
        "lastUpdate": "2024-12-07T07:30:00Z",
        "minutesStale": 210
      }
    ],
    "markedAsFailed": 2
  },
  "timestamp": "2024-12-07T11:20:00Z"
}
```

#### Status Codes
- **200 OK**: Detection completed successfully

---

## 🏥 Health & Stats Endpoints

### 13. Health Check

**GET** `/health`

Returns the overall health status of the service.

#### Response (200 OK - Healthy)

```json
{
  "status": "healthy",
  "timestamp": "2024-12-07T11:25:00Z",
  "service": "HubSpot Deals ETL Service",
  "version": "1.0.0",
  "checks": {
    "database": "healthy",
    "dlt_pipeline": "healthy",
    "disk_space": "healthy"
  },
  "details": {
    "database": {
      "connected": true,
      "responseTime": "5ms"
    },
    "disk_space": {
      "available": "50 GB",
      "usage": "60%"
    }
  }
}
```

#### Response (503 Service Unavailable - Unhealthy)

```json
{
  "status": "unhealthy",
  "timestamp": "2024-12-07T11:25:00Z",
  "service": "HubSpot Deals ETL Service",
  "version": "1.0.0",
  "checks": {
    "database": "unhealthy: connection timeout",
    "dlt_pipeline": "healthy",
    "disk_space": "degraded: low disk space"
  },
  "details": {
    "database": {
      "connected": false,
      "error": "Connection timeout after 5 seconds"
    },
    "disk_space": {
      "available": "2 GB",
      "usage": "95%",
      "warning": "Low disk space"
    }
  }
}
```

#### Status Codes
- **200 OK**: Service is healthy
- **503 Service Unavailable**: Service is unhealthy

---

### 14. Service Statistics

**GET** `/stats`

Returns comprehensive service statistics and performance metrics.

#### Response (200 OK)

```json
{
  "status": "success",
  "data": {
    "service": {
      "name": "HubSpot Deals ETL Service",
      "version": "1.0.0",
      "uptime": "7 days, 3 hours, 24 minutes",
      "startedAt": "2024-11-30T08:00:00Z"
    },
    "scans": {
      "total": 125,
      "running": 3,
      "completed": 110,
      "failed": 8,
      "cancelled": 4
    },
    "deals": {
      "totalExtracted": 187500,
      "averagePerScan": 1500
    },
    "performance": {
      "averageScanDuration": "4m 45s",
      "averageDealsPerSecond": 5.26,
      "successRate": 88.0
    },
    "system": {
      "memoryUsage": "512 MB",
      "cpuUsage": "15%",
      "diskUsage": "60%",
      "activeConnections": 23
    }
  },
  "timestamp": "2024-12-07T11:30:00Z"
}
```

#### Status Codes
- **200 OK**: Statistics retrieved successfully

---

## ⚠️ Error Handling

### Error Response Format

All errors follow a consistent structure:

```json
{
  "status": "error",
  "error_code": "ERROR_CODE",
  "message": "Human-readable error message",
  "details": {},
  "timestamp": "2024-12-07T11:35:00Z"
}
```

### Common Error Codes

| HTTP Status | Error Code | Description |
|------------|------------|-------------|
| 400 | `VALIDATION_ERROR` | Input validation failed |
| 400 | `INVALID_SCAN_ID` | Invalid scan ID format |
| 400 | `INVALID_DATE_RANGE` | Invalid date range specified |
| 401 | `UNAUTHORIZED` | Authentication required |
| 403 | `FORBIDDEN` | Insufficient permissions |
| 404 | `SCAN_NOT_FOUND` | Scan ID not found |
| 409 | `SCAN_ALREADY_RUNNING` | Scan with same ID already in progress |
| 422 | `HUBSPOT_AUTH_FAILED` | HubSpot authentication failed |
| 422 | `HUBSPOT_INVALID_TOKEN` | Invalid HubSpot access token |
| 422 | `HUBSPOT_INSUFFICIENT_SCOPES` | Missing required HubSpot scopes |
| 429 | `RATE_LIMIT_EXCEEDED` | Too many requests |
| 500 | `INTERNAL_ERROR` | Server error |
| 503 | `SERVICE_UNAVAILABLE` | Service temporarily unavailable |

### Error Examples

#### Validation Error (400)

```json
{
  "status": "error",
  "error_code": "VALIDATION_ERROR",
  "message": "Input validation failed",
  "errors": {
    "config.scanId": "This field is required",
    "config.auth.accessToken": "This field is required",
    "config.organizationId": "Must be a valid HubSpot Portal ID"
  },
  "timestamp": "2024-12-07T11:40:00Z"
}
```

#### HubSpot Authentication Error (422)

```json
{
  "status": "error",
  "error_code": "HUBSPOT_AUTH_FAILED",
  "message": "Failed to authenticate with HubSpot API",
  "details": {
    "hubspotError": "The access token provided is invalid",
    "suggestion": "Verify your HubSpot Private App access token is correct and not expired"
  },
  "timestamp": "2024-12-07T11:45:00Z"
}
```

#### Scan Already Running (409)

```json
{
  "status": "error",
  "error_code": "SCAN_ALREADY_RUNNING",
  "message": "A scan with this ID is already in progress",
  "details": {
    "scanId": "hubspot-deals-dec-2024",
    "currentStatus": "running",
    "startedAt": "2024-12-07T10:30:00Z",
    "suggestion": "Wait for the current scan to complete or use a different scan ID"
  },
  "timestamp": "2024-12-07T11:50:00Z"
}
```

#### Rate Limit Error (429)

```json
{
  "status": "error",
  "error_code": "RATE_LIMIT_EXCEEDED",
  "message": "Too many requests",
  "details": {
    "retryAfter": 60,
    "limit": 100,
    "window": "10 seconds"
  },
  "timestamp": "2024-12-07T11:55:00Z"
}
```

---

## 📚 Request/Response Examples

### Complete Extraction Workflow

#### Step 1: Start Extraction

**Request:**
```bash
curl -X POST "http://localhost:5200/api/v1/scan/start" \
  -H "Content-Type: application/json" \
  -d '{
    "config": {
      "scanId": "hubspot-deals-q4-2024",
      "organizationId": "12345678",
      "type": ["deals"],
      "auth": {
        "accessToken": "pat-na1-11111111-2222-3333-4444-555555555555"
      },
      "filters": {
        "properties": [
          "dealname",
          "amount",
          "dealstage",
          "pipeline",
          "closedate",
          "hubspot_owner_id",
          "hs_forecast_probability"
        ],
        "dateRange": {
          "startDate": "2024-10-01",
          "endDate": "2024-12-31"
        },
        "includeArchived": false
      },
      "options": {
        "batchSize": 100,
        "maxRetries": 3
      }
    }
  }'
```

**Response:**
```json
{
  "status": "success",
  "message": "Deal extraction started successfully",
  "data": {
    "scanId": "hubspot-deals-q4-2024",
    "organizationId": "12345678",
    "status": "pending",
    "jobId": "550e8400-e29b-41d4-a716-446655440000",
    "startedAt": "2024-12-07T12:00:00Z"
  },
  "timestamp": "2024-12-07T12:00:00Z"
}
```

---

#### Step 2: Monitor Progress

**Request:**
```bash
curl "http://localhost:5200/api/v1/scan/hubspot-deals-q4-2024/status"
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "scanId": "hubspot-deals-q4-2024",
    "organizationId": "12345678",
    "status": "running",
    "progress": {
      "totalDeals": 1000,
      "processedDeals": 650,
      "failedDeals": 0,
      "percentComplete": 65.0,
      "dealsPerSecond": 10.83
    },
    "timing": {
      "startedAt": "2024-12-07T12:00:00Z",
      "completedAt": null,
      "elapsedSeconds": 60,
      "estimatedRemainingSeconds": 32
    },
    "checkpoint": {
      "lastProcessedId": "12345678650",
      "cursor": "MTIzNDU2Nzg2NTA=",
      "pageNumber": 7
    },
    "errorMessage": null,
    "createdAt": "2024-12-07T12:00:00Z",
    "updatedAt": "2024-12-07T12:01:00Z"
  },
  "timestamp": "2024-12-07T12:01:00Z"
}
```

---

#### Step 3: Get Results

**Request:**
```bash
curl "http://localhost:5200/api/v1/results/hubspot-deals-q4-2024/result?limit=5"
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "scanId": "hubspot-deals-q4-2024",
    "tableName": "deals",
    "results": [
      {
        "id": "uuid-1",
        "hs_object_id": "12345678901",
        "dealname": "Enterprise Deal - Acme Corp",
        "amount": 50000.00,
        "dealstage": "qualifiedtobuy",
        "pipeline": "default",
        "closedate": "2024-12-31T00:00:00Z",
        "hubspot_owner_id": "123456",
        "hs_forecast_probability": 0.4000,
        "_tenant_id": "12345678",
        "_scan_id": "hubspot-deals-q4-2024",
        "_extracted_at": "2024-12-07T12:01:30Z"
      }
    ],
    "pagination": {
      "current_page": 1,
      "page_size": 5,
      "total_items": 1000,
      "total_pages": 200,
      "has_next": true,
      "has_previous": false
    },
    "totalCount": 1000
  },
  "timestamp": "2024-12-07T12:05:00Z"
}
```

---

#### Step 4: Download Results

**Request:**
```bash
# Download as Excel
curl "http://localhost:5200/api/v1/results/hubspot-deals-q4-2024/download/excel" \
  -o "hubspot_deals_q4_2024.xlsx"

# Download as CSV
curl "http://localhost:5200/api/v1/results/hubspot-deals-q4-2024/download/csv" \
  -o "hubspot_deals_q4_2024.csv"

# Download as JSON
curl "http://localhost:5200/api/v1/results/hubspot-deals-q4-2024/download/json" \
  -o "hubspot_deals_q4_2024.json"
```

---

### PowerShell Examples

#### Start Extraction
```powershell
$body = @{
  config = @{
    scanId = "hubspot-deals-powershell-001"
    organizationId = "12345678"
    type = @("deals")
    auth = @{
      accessToken = "pat-na1-11111111-2222-3333-4444-555555555555"
    }
    filters = @{
      properties = @(
        "dealname",
        "amount",
        "dealstage"
      )
      includeArchived = $false
    }
  }
} | ConvertTo-Json -Depth 10

$response = Invoke-RestMethod `
  -Uri "http://localhost:5200/api/v1/scan/start" `
  -Method Post `
  -Body $body `
  -ContentType "application/json"

Write-Output $response
```

#### Get Status
```powershell
$scanId = "hubspot-deals-powershell-001"
$status = Invoke-RestMethod `
  -Uri "http://localhost:5200/api/v1/scan/$scanId/status" `
  -Method Get

Write-Output "Status: $($status.data.status)"
Write-Output "Progress: $($status.data.progress.percentComplete)%"
```

#### Download Results
```powershell
$scanId = "hubspot-deals-powershell-001"
Invoke-WebRequest `
  -Uri "http://localhost:5200/api/v1/results/$scanId/download/excel" `
  -OutFile "deals_export.xlsx"
```

---

### Python Examples

#### Start Extraction
```python
import requests

url = "http://localhost:5200/api/v1/scan/start"
payload = {
    "config": {
        "scanId": "hubspot-deals-python-001",
        "organizationId": "12345678",
        "type": ["deals"],
        "auth": {
            "accessToken": "pat-na1-11111111-2222-3333-4444-555555555555"
        },
        "filters": {
            "properties": [
                "dealname",
                "amount",
                "dealstage",
                "pipeline",
                "closedate"
            ],
            "includeArchived": False
        }
    }
}

response = requests.post(url, json=payload)
print(response.json())
```

#### Monitor Progress
```python
import requests
import time

scan_id = "hubspot-deals-python-001"
url = f"http://localhost:5200/api/v1/scan/{scan_id}/status"

while True:
    response = requests.get(url)
    data = response.json()["data"]
    
    status = data["status"]
    progress = data.get("progress", {})
    percent = progress.get("percentComplete", 0)
    
    print(f"Status: {status} - Progress: {percent:.1f}%")
    
    if status in ["completed", "failed", "cancelled"]:
        break
    
    time.sleep(5)  # Check every 5 seconds

print("Extraction finished!")
```

#### Get Paginated Results
```python
import requests

scan_id = "hubspot-deals-python-001"
base_url = f"http://localhost:5200/api/v1/results/{scan_id}/result"

all_deals = []
page = 1
page_size = 100

while True:
    params = {"limit": page_size, "offset": (page - 1) * page_size}
    response = requests.get(base_url, params=params)
    
    if response.status_code == 200:
        data = response.json()["data"]
        deals = data["results"]
        all_deals.extend(deals)
        
        pagination = data["pagination"]
        if not pagination["has_next"]:
            break
        
        page += 1
    else:
        print(f"Error: {response.status_code}")
        break

print(f"Total deals retrieved: {len(all_deals)}")
```

#### Download Results
```python
import requests

scan_id = "hubspot-deals-python-001"
formats = ["json", "csv", "excel"]

for fmt in formats:
    url = f"http://localhost:5200/api/v1/results/{scan_id}/download/{fmt}"
    response = requests.get(url)
    
    if response.status_code == 200:
        ext = "xlsx" if fmt == "excel" else fmt
        filename = f"deals_export.{ext}"
        
        with open(filename, "wb") as f:
            f.write(response.content)
        
        print(f"Downloaded {filename}")
    else:
        print(f"Failed to download {fmt}: {response.status_code}")
```

---

## 🚦 Rate Limiting

### Service Rate Limits

The service itself has no rate limiting, but be aware of HubSpot API rate limits:

#### HubSpot API Limits
- **100 requests per 10 seconds** per access token
- **Daily limits** vary by subscription tier
- **Burst limit**: 150 requests per 10 seconds (short duration)

### Rate Limit Headers

When the service makes requests to HubSpot, it monitors these headers:

```http
X-HubSpot-RateLimit-Max: 100
X-HubSpot-RateLimit-Remaining: 95
X-HubSpot-RateLimit-Interval-Milliseconds: 10000
```

### Automatic Retry

The service automatically handles HubSpot rate limits with:
- **Exponential backoff**: Waits progressively longer between retries
- **Max retries**: Configurable (default: 3)
- **Retry-After header**: Respects HubSpot's retry guidance

### Best Practices

1. **Set appropriate batch size**: Use `batchSize: 100` (max) for faster extraction
2. **Monitor progress**: Check status periodically rather than continuously
3. **Avoid concurrent scans**: Limit to 3-5 concurrent scans per portal
4. **Space out scans**: Wait 1-2 minutes between starting new scans

---

## 📝 API Changelog

### Version 1.0.0 (2024-12-07)

**Initial Release**
- Deal extraction from HubSpot CRM API v3
- Multi-tenant support with schema isolation
- Checkpoint and resume functionality
- Progress monitoring and status tracking
- Data export in JSON, CSV, and Excel formats
- Automatic rate limit handling
- Health checks and service statistics

---

**API Documentation Version**: 1.0.0  
**Last Updated**: December 2024  
**Service Version**: 1.0.0  
**Maintained By**: HubSpot Deals ETL Team
