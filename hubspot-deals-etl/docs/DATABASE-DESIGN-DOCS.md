# 🗄️ HubSpot Deals ETL - Database Schema Design

This document provides the complete database schema for the HubSpot Deals ETL service with multi-tenant support, optimized indexes, and ETL metadata tracking.

---

## 📋 Overview

The HubSpot Deals ETL database schema consists of three main tables:

1. **scan_jobs** - Scan job management and status tracking
2. **hubspot_deals** - Extracted deal data with full property mappings
3. **deal_properties_metadata** (Optional) - Schema metadata for dynamic property discovery

### Multi-Tenant Architecture
- Each tenant (HubSpot portal) is isolated using `_tenant_id` field
- Separate schemas per tenant: `hubspot_deals_{tenant_id}`
- Row-level security for data isolation

---

## 🏗️ Table Schemas

### 1. Scan Jobs Table

**Purpose**: Track extraction jobs across all tenants with progress monitoring

**Schema**: `public.scan_jobs` (shared across all tenants)

```sql
CREATE TABLE IF NOT EXISTS public.scan_jobs (
    -- Primary Identification
    id VARCHAR(255) PRIMARY KEY,
    scan_id VARCHAR(255) NOT NULL UNIQUE,
    
    -- Tenant Isolation
    organization_id VARCHAR(255) NOT NULL,  -- HubSpot Portal ID
    
    -- Job Configuration
    scan_type VARCHAR(50) NOT NULL DEFAULT 'deals',
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    config JSONB NOT NULL,
    
    -- Progress Tracking
    total_items INTEGER DEFAULT 0,
    processed_items INTEGER DEFAULT 0,
    failed_items INTEGER DEFAULT 0,
    success_rate DECIMAL(5,2),
    
    -- Timing Information
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    -- Error Handling
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    
    -- ETL Metadata
    batch_size INTEGER DEFAULT 100,
    checkpoint_data JSONB,
    
    -- Constraints
    CONSTRAINT check_valid_status 
        CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled', 'paused')),
    CONSTRAINT check_positive_counts 
        CHECK (total_items >= 0 AND processed_items >= 0 AND failed_items >= 0)
);

-- Indexes for scan_jobs
CREATE INDEX idx_scan_jobs_scan_id ON public.scan_jobs(scan_id);
CREATE INDEX idx_scan_jobs_org_id ON public.scan_jobs(organization_id);
CREATE INDEX idx_scan_jobs_status ON public.scan_jobs(status);
CREATE INDEX idx_scan_jobs_org_status ON public.scan_jobs(organization_id, status);
CREATE INDEX idx_scan_jobs_created_at ON public.scan_jobs(created_at DESC);
CREATE INDEX idx_scan_jobs_status_created ON public.scan_jobs(status, created_at DESC);

-- Trigger for auto-updating updated_at
CREATE OR REPLACE FUNCTION update_scan_jobs_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_scan_jobs_updated_at
    BEFORE UPDATE ON public.scan_jobs
    FOR EACH ROW
    EXECUTE FUNCTION update_scan_jobs_updated_at();

-- Comments
COMMENT ON TABLE public.scan_jobs IS 'Tracks all HubSpot deal extraction jobs across tenants';
COMMENT ON COLUMN public.scan_jobs.organization_id IS 'HubSpot Portal ID for tenant isolation';
COMMENT ON COLUMN public.scan_jobs.checkpoint_data IS 'Stores cursor/checkpoint for resuming failed jobs';
```

---

### 2. HubSpot Deals Table (Main Data Table)

**Purpose**: Store extracted deal data with complete HubSpot property mappings

**Schema**: `hubspot_deals_{tenant_id}.deals` (tenant-specific)

```sql
-- Create schema for tenant (if not exists)
CREATE SCHEMA IF NOT EXISTS hubspot_deals_{tenant_id};

-- Main deals table
CREATE TABLE IF NOT EXISTS hubspot_deals_{tenant_id}.deals (
    -- ========================================
    -- PRIMARY IDENTIFICATION
    -- ========================================
    id VARCHAR(255) PRIMARY KEY,  -- Internal UUID
    hs_object_id VARCHAR(100) NOT NULL UNIQUE,  -- HubSpot Deal ID
    
    -- ========================================
    -- ETL METADATA (Required for all extractions)
    -- ========================================
    _tenant_id VARCHAR(255) NOT NULL,  -- HubSpot Portal ID
    _scan_id VARCHAR(255) NOT NULL,  -- Links to scan_jobs.scan_id
    _extracted_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    _source_system VARCHAR(50) NOT NULL DEFAULT 'hubspot',
    _api_version VARCHAR(20) DEFAULT 'v3',
    
    -- ========================================
    -- BASIC DEAL INFORMATION
    -- ========================================
    dealname VARCHAR(500),  -- Deal name
    amount NUMERIC(15,2),  -- Deal value (supports up to 999,999,999,999.99)
    amount_in_home_currency NUMERIC(15,2),  -- Deal value in portal currency
    pipeline VARCHAR(255) DEFAULT 'default',  -- Pipeline ID/name
    dealstage VARCHAR(255),  -- Current stage in pipeline
    dealtype VARCHAR(100),  -- newbusiness, existingbusiness, etc.
    description TEXT,  -- Deal description
    
    -- ========================================
    -- DATE FIELDS
    -- ========================================
    closedate TIMESTAMP WITH TIME ZONE,  -- Expected/actual close date
    createdate TIMESTAMP WITH TIME ZONE,  -- Deal creation date
    hs_lastmodifieddate TIMESTAMP WITH TIME ZONE,  -- Last modification timestamp
    hs_createdate TIMESTAMP WITH TIME ZONE,  -- HubSpot system creation date
    
    -- Stage entry/exit timestamps (for velocity analysis)
    hs_date_entered_appointmentscheduled TIMESTAMP WITH TIME ZONE,
    hs_date_exited_appointmentscheduled TIMESTAMP WITH TIME ZONE,
    hs_date_entered_qualifiedtobuy TIMESTAMP WITH TIME ZONE,
    hs_date_exited_qualifiedtobuy TIMESTAMP WITH TIME ZONE,
    hs_date_entered_presentationscheduled TIMESTAMP WITH TIME ZONE,
    hs_date_exited_presentationscheduled TIMESTAMP WITH TIME ZONE,
    hs_date_entered_decisionmakerboughtin TIMESTAMP WITH TIME ZONE,
    hs_date_exited_decisionmakerboughtin TIMESTAMP WITH TIME ZONE,
    hs_date_entered_contractsent TIMESTAMP WITH TIME ZONE,
    hs_date_exited_contractsent TIMESTAMP WITH TIME ZONE,
    hs_date_entered_closedwon TIMESTAMP WITH TIME ZONE,
    hs_date_entered_closedlost TIMESTAMP WITH TIME ZONE,
    
    -- ========================================
    -- FINANCIAL FIELDS
    -- ========================================
    hs_arr NUMERIC(15,2),  -- Annual Recurring Revenue
    hs_mrr NUMERIC(15,2),  -- Monthly Recurring Revenue
    hs_tcv NUMERIC(15,2),  -- Total Contract Value
    hs_acv NUMERIC(15,2),  -- Annual Contract Value
    deal_currency_code VARCHAR(10) DEFAULT 'USD',
    
    -- ========================================
    -- FORECASTING & PROBABILITY
    -- ========================================
    hs_forecast_amount NUMERIC(15,2),  -- Forecasted amount
    hs_forecast_probability NUMERIC(5,4),  -- Win probability (0.0000 to 1.0000)
    hs_manual_forecast_category VARCHAR(100),  -- Manual forecast category
    hs_is_closed BOOLEAN DEFAULT FALSE,  -- Is deal closed
    hs_is_closed_won BOOLEAN DEFAULT FALSE,  -- Is deal closed won
    
    -- ========================================
    -- OWNERSHIP & ASSIGNMENT
    -- ========================================
    hubspot_owner_id VARCHAR(100),  -- Owner user ID
    hubspot_owner_assigneddate TIMESTAMP WITH TIME ZONE,  -- When owner was assigned
    hubspot_team_id VARCHAR(100),  -- Team ID
    hs_all_owner_ids TEXT,  -- All owners (current and historical)
    hs_all_team_ids TEXT,  -- All teams (current and historical)
    
    -- ========================================
    -- SOURCE & ATTRIBUTION
    -- ========================================
    hs_analytics_source VARCHAR(255),  -- Original source (ORGANIC_SEARCH, PAID_SEARCH, etc.)
    hs_analytics_source_data_1 VARCHAR(255),  -- Drill-down 1
    hs_analytics_source_data_2 VARCHAR(255),  -- Drill-down 2
    hs_campaign VARCHAR(255),  -- Marketing campaign
    hs_latest_source VARCHAR(255),  -- Most recent source
    hs_latest_source_data_1 VARCHAR(255),
    hs_latest_source_data_2 VARCHAR(255),
    
    -- ========================================
    -- DEAL METRICS & ENGAGEMENT
    -- ========================================
    num_associated_contacts INTEGER DEFAULT 0,  -- Number of contacts
    num_contacted_notes INTEGER DEFAULT 0,  -- Number of notes
    num_notes INTEGER DEFAULT 0,  -- Total notes
    hs_num_of_associated_line_items INTEGER DEFAULT 0,  -- Line items count
    hs_time_in_dealstage BIGINT,  -- Time in current stage (seconds)
    hs_days_to_close INTEGER,  -- Days from creation to close
    hs_deal_stage_probability NUMERIC(5,2),  -- Stage-based probability
    
    -- ========================================
    -- DEAL STATUS FLAGS
    -- ========================================
    archived BOOLEAN DEFAULT FALSE,  -- Is deal archived
    hs_is_active_shared_deal BOOLEAN DEFAULT FALSE,
    hs_priority VARCHAR(50),  -- Deal priority (LOW, MEDIUM, HIGH)
    
    -- ========================================
    -- USER TRACKING
    -- ========================================
    hs_created_by_user_id VARCHAR(100),  -- User who created the deal
    hs_updated_by_user_id VARCHAR(100),  -- User who last updated
    hs_user_ids_of_all_owners TEXT,  -- All user IDs with ownership
    
    -- ========================================
    -- NEXT STEPS & ACTIVITY
    -- ========================================
    hs_next_step VARCHAR(500),  -- Next action to take
    hs_date_entered_next_step TIMESTAMP WITH TIME ZONE,
    hs_last_sales_activity_date TIMESTAMP WITH TIME ZONE,
    hs_last_sales_activity_timestamp TIMESTAMP WITH TIME ZONE,
    hs_sales_email_last_replied TIMESTAMP WITH TIME ZONE,
    
    -- ========================================
    -- DEAL PROPERTIES
    -- ========================================
    deal_type_id VARCHAR(100),
    deal_probability NUMERIC(5,2),  -- Custom probability field
    hs_closed_amount NUMERIC(15,2),  -- Actual closed amount
    hs_closed_amount_in_home_currency NUMERIC(15,2),
    hs_projected_amount NUMERIC(15,2),
    hs_projected_amount_in_home_currency NUMERIC(15,2),
    
    -- ========================================
    -- CUSTOM PROPERTIES (Flexible JSONB storage)
    -- ========================================
    custom_properties JSONB,  -- Store all unmapped custom properties
    
    -- ========================================
    -- SYSTEM METADATA
    -- ========================================
    hubspot_created_at TIMESTAMP WITH TIME ZONE,  -- From HubSpot API
    hubspot_updated_at TIMESTAMP WITH TIME ZONE,  -- From HubSpot API
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),  -- Local DB timestamp
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),  -- Local DB timestamp
    
    -- ========================================
    -- CONSTRAINTS
    -- ========================================
    CONSTRAINT check_amount_positive CHECK (amount IS NULL OR amount >= 0),
    CONSTRAINT check_probability_range CHECK (
        hs_forecast_probability IS NULL OR 
        (hs_forecast_probability >= 0 AND hs_forecast_probability <= 1)
    )
);

-- ========================================
-- PERFORMANCE INDEXES
-- ========================================

-- Primary lookup indexes
CREATE INDEX idx_deals_hs_object_id ON hubspot_deals_{tenant_id}.deals(hs_object_id);
CREATE INDEX idx_deals_tenant_id ON hubspot_deals_{tenant_id}.deals(_tenant_id);
CREATE INDEX idx_deals_scan_id ON hubspot_deals_{tenant_id}.deals(_scan_id);

-- Multi-tenant query patterns
CREATE INDEX idx_deals_tenant_scan ON hubspot_deals_{tenant_id}.deals(_tenant_id, _scan_id);
CREATE INDEX idx_deals_tenant_stage ON hubspot_deals_{tenant_id}.deals(_tenant_id, dealstage);
CREATE INDEX idx_deals_tenant_owner ON hubspot_deals_{tenant_id}.deals(_tenant_id, hubspot_owner_id);
CREATE INDEX idx_deals_tenant_pipeline ON hubspot_deals_{tenant_id}.deals(_tenant_id, pipeline);

-- Date-based queries (for reporting and analytics)
CREATE INDEX idx_deals_closedate ON hubspot_deals_{tenant_id}.deals(closedate) WHERE closedate IS NOT NULL;
CREATE INDEX idx_deals_createdate ON hubspot_deals_{tenant_id}.deals(createdate);
CREATE INDEX idx_deals_modified_date ON hubspot_deals_{tenant_id}.deals(hs_lastmodifieddate DESC);
CREATE INDEX idx_deals_extracted_at ON hubspot_deals_{tenant_id}.deals(_extracted_at DESC);

-- Stage and status queries
CREATE INDEX idx_deals_stage ON hubspot_deals_{tenant_id}.deals(dealstage) WHERE dealstage IS NOT NULL;
CREATE INDEX idx_deals_pipeline_stage ON hubspot_deals_{tenant_id}.deals(pipeline, dealstage);
CREATE INDEX idx_deals_closed_status ON hubspot_deals_{tenant_id}.deals(hs_is_closed, hs_is_closed_won);
CREATE INDEX idx_deals_archived ON hubspot_deals_{tenant_id}.deals(archived) WHERE archived = FALSE;

-- Financial reporting indexes
CREATE INDEX idx_deals_amount ON hubspot_deals_{tenant_id}.deals(amount) WHERE amount IS NOT NULL;
CREATE INDEX idx_deals_tenant_amount ON hubspot_deals_{tenant_id}.deals(_tenant_id, amount DESC) WHERE amount IS NOT NULL;
CREATE INDEX idx_deals_forecast_amount ON hubspot_deals_{tenant_id}.deals(hs_forecast_amount) WHERE hs_forecast_amount IS NOT NULL;

-- Owner and team queries
CREATE INDEX idx_deals_owner ON hubspot_deals_{tenant_id}.deals(hubspot_owner_id) WHERE hubspot_owner_id IS NOT NULL;
CREATE INDEX idx_deals_team ON hubspot_deals_{tenant_id}.deals(hubspot_team_id) WHERE hubspot_team_id IS NOT NULL;

-- Source attribution analysis
CREATE INDEX idx_deals_source ON hubspot_deals_{tenant_id}.deals(hs_analytics_source) WHERE hs_analytics_source IS NOT NULL;

-- Custom properties JSONB index (GIN index for flexible queries)
CREATE INDEX idx_deals_custom_props ON hubspot_deals_{tenant_id}.deals USING GIN (custom_properties);

-- Composite index for common dashboard queries
CREATE INDEX idx_deals_dashboard ON hubspot_deals_{tenant_id}.deals(
    _tenant_id, dealstage, closedate
) WHERE archived = FALSE;

-- ========================================
-- TRIGGERS
-- ========================================

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_deals_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_deals_updated_at
    BEFORE UPDATE ON hubspot_deals_{tenant_id}.deals
    FOR EACH ROW
    EXECUTE FUNCTION update_deals_updated_at();

-- ========================================
-- TABLE COMMENTS
-- ========================================
COMMENT ON TABLE hubspot_deals_{tenant_id}.deals IS 'HubSpot deals data with complete property mappings';
COMMENT ON COLUMN hubspot_deals_{tenant_id}.deals._tenant_id IS 'HubSpot Portal ID for multi-tenant isolation';
COMMENT ON COLUMN hubspot_deals_{tenant_id}.deals._scan_id IS 'References the extraction job that created this record';
COMMENT ON COLUMN hubspot_deals_{tenant_id}.deals._extracted_at IS 'Timestamp when this record was extracted from HubSpot';
COMMENT ON COLUMN hubspot_deals_{tenant_id}.deals.custom_properties IS 'JSONB storage for unmapped custom HubSpot properties';
COMMENT ON COLUMN hubspot_deals_{tenant_id}.deals.hs_object_id IS 'Unique HubSpot deal ID from API';
```

---

### 3. Deal Properties Metadata Table (Optional)

**Purpose**: Store property schema information for dynamic mapping and validation

**Schema**: `public.deal_properties_metadata` (shared across tenants)

```sql
CREATE TABLE IF NOT EXISTS public.deal_properties_metadata (
    -- Identification
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(255) NOT NULL,  -- HubSpot Portal ID
    
    -- Property Definition
    property_name VARCHAR(255) NOT NULL,
    property_label VARCHAR(500),
    property_description TEXT,
    property_type VARCHAR(50),  -- string, number, datetime, enumeration, bool
    field_type VARCHAR(50),  -- text, textarea, number, date, select, etc.
    
    -- Property Metadata
    group_name VARCHAR(255),
    display_order INTEGER,
    is_calculated BOOLEAN DEFAULT FALSE,
    is_hidden BOOLEAN DEFAULT FALSE,
    is_required BOOLEAN DEFAULT FALSE,
    has_unique_value BOOLEAN DEFAULT FALSE,
    
    -- Options for enumeration fields
    options JSONB,  -- Array of {label, value} objects
    
    -- Modification Metadata
    is_read_only BOOLEAN DEFAULT FALSE,
    is_archivable BOOLEAN DEFAULT TRUE,
    
    -- Tracking
    discovered_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    last_seen_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    -- Constraints
    UNIQUE(tenant_id, property_name)
);

-- Indexes for properties metadata
CREATE INDEX idx_props_tenant ON public.deal_properties_metadata(tenant_id);
CREATE INDEX idx_props_name ON public.deal_properties_metadata(property_name);
CREATE INDEX idx_props_tenant_name ON public.deal_properties_metadata(tenant_id, property_name);
CREATE INDEX idx_props_type ON public.deal_properties_metadata(property_type);
CREATE INDEX idx_props_group ON public.deal_properties_metadata(group_name);

-- Comments
COMMENT ON TABLE public.deal_properties_metadata IS 'Metadata about HubSpot deal properties for schema discovery';
COMMENT ON COLUMN public.deal_properties_metadata.options IS 'For enumeration fields, stores available options';
```

---

## 🔗 Relationships

### Table Relationships

```
┌──────────────────┐
│  scan_jobs       │
│  (public)        │
└────────┬─────────┘
         │ 1
         │
         │ N
┌────────┴─────────────────────────┐
│  deals                           │
│  (hubspot_deals_{tenant_id})    │
└──────────────────────────────────┘

┌──────────────────────────────────┐
│  deal_properties_metadata        │
│  (public, optional)              │
└──────────────────────────────────┘
```

### Foreign Key Relationships

```sql
-- Add foreign key from deals to scan_jobs (optional, for referential integrity)
ALTER TABLE hubspot_deals_{tenant_id}.deals
    ADD CONSTRAINT fk_deals_scan_job
    FOREIGN KEY (_scan_id)
    REFERENCES public.scan_jobs(scan_id)
    ON DELETE CASCADE;
```

**Note**: In high-volume ETL scenarios, foreign keys may impact performance. Consider using application-level validation instead.

---

## 📊 HubSpot to PostgreSQL Type Mappings

### Property Type Mapping Reference

| HubSpot Type | HubSpot FieldType | PostgreSQL Type | Notes |
|--------------|-------------------|-----------------|-------|
| `string` | `text`, `textarea` | `VARCHAR(500)` or `TEXT` | Use TEXT for long content |
| `number` | `number` | `NUMERIC(15,2)` | For currency/amounts |
| `number` | `number` (integer) | `INTEGER` or `BIGINT` | For counts |
| `datetime` | `date` | `TIMESTAMP WITH TIME ZONE` | Always use timezone |
| `enumeration` | `select`, `radio` | `VARCHAR(255)` | Store as string |
| `bool` | `booleancheckbox` | `BOOLEAN` | True/False |
| `phone_number` | `phonenumber` | `VARCHAR(50)` | International format |
| `calculation` | `calculation` | `NUMERIC` or `TEXT` | Depends on calculation |
| `json` | N/A | `JSONB` | For custom/unmapped properties |

### Mapping Examples

```sql
-- String properties
dealname VARCHAR(500)  -- Short to medium text
description TEXT       -- Long text content

-- Numeric properties
amount NUMERIC(15,2)   -- Currency with 2 decimal places
num_associated_contacts INTEGER  -- Whole numbers

-- Date/Time properties
closedate TIMESTAMP WITH TIME ZONE  -- Dates with timezone
createdate TIMESTAMP WITH TIME ZONE

-- Boolean properties
hs_is_closed BOOLEAN DEFAULT FALSE
archived BOOLEAN DEFAULT FALSE

-- Enumeration properties (stored as strings)
dealstage VARCHAR(255)  -- appointmentscheduled, qualifiedtobuy, etc.
pipeline VARCHAR(255)   -- default, sales_pipeline, etc.
dealtype VARCHAR(100)   -- newbusiness, existingbusiness

-- Probability/Percentage (use NUMERIC for precision)
hs_forecast_probability NUMERIC(5,4)  -- 0.0000 to 1.0000
deal_probability NUMERIC(5,2)          -- 0.00 to 100.00

-- IDs (always string in HubSpot)
hs_object_id VARCHAR(100)      -- HubSpot deal ID
hubspot_owner_id VARCHAR(100)  -- User ID
```

---

## 🏢 Multi-Tenant Data Isolation Strategy

### Approach 1: Schema-Level Isolation (Recommended)

**Benefits**:
- Strong isolation between tenants
- Easy to backup/restore individual tenants
- Clear security boundaries
- Simple to implement row-level security

**Implementation**:
```sql
-- Create schema per tenant
CREATE SCHEMA IF NOT EXISTS hubspot_deals_portal_12345;
CREATE SCHEMA IF NOT EXISTS hubspot_deals_portal_67890;

-- Each tenant gets their own deals table
CREATE TABLE hubspot_deals_portal_12345.deals (...);
CREATE TABLE hubspot_deals_portal_67890.deals (...);
```

**Query Pattern**:
```sql
-- Dynamic schema selection based on tenant
SET search_path TO hubspot_deals_portal_12345, public;
SELECT * FROM deals WHERE dealstage = 'closedwon';
```

### Approach 2: Row-Level Security (Alternative)

**Benefits**:
- Single table for all tenants
- Easier to aggregate cross-tenant analytics
- Simpler schema management

**Implementation**:
```sql
-- Enable RLS on deals table
ALTER TABLE hubspot_deals.deals ENABLE ROW LEVEL SECURITY;

-- Create policy for tenant isolation
CREATE POLICY tenant_isolation ON hubspot_deals.deals
    USING (_tenant_id = current_setting('app.current_tenant_id'));

-- Set tenant context before queries
SET app.current_tenant_id = 'portal_12345';
SELECT * FROM hubspot_deals.deals;  -- Only sees portal_12345 data
```

### Approach 3: Hybrid (Best for Large Scale)

**Implementation**:
```sql
-- Use schemas for isolation
CREATE SCHEMA hubspot_deals_portal_12345;

-- Still include _tenant_id for validation
CREATE TABLE hubspot_deals_portal_12345.deals (
    ...
    _tenant_id VARCHAR(255) NOT NULL,
    ...
    CONSTRAINT check_tenant_id CHECK (_tenant_id = 'portal_12345')
);
```

---

## 🚀 Performance Optimization

### Index Strategy Summary

| Query Pattern | Index | Purpose |
|--------------|-------|---------|
| Lookup by HubSpot ID | `idx_deals_hs_object_id` | Fast single deal retrieval |
| Filter by tenant | `idx_deals_tenant_id` | Multi-tenant queries |
| Filter by stage | `idx_deals_stage` | Pipeline reporting |
| Date range queries | `idx_deals_closedate` | Win/loss analysis |
| Owner reports | `idx_deals_owner` | Sales performance |
| Amount sorting | `idx_deals_tenant_amount` | Revenue reporting |
| Dashboard queries | `idx_deals_dashboard` | Composite index for common UI queries |
| Custom properties | `idx_deals_custom_props` | Flexible JSONB queries |

### Query Optimization Examples

```sql
-- Efficient tenant + stage query (uses idx_deals_tenant_stage)
SELECT dealname, amount, closedate
FROM hubspot_deals_portal_12345.deals
WHERE _tenant_id = 'portal_12345'
  AND dealstage = 'closedwon'
  AND archived = FALSE;

-- Efficient date range with amount (uses idx_deals_closedate)
SELECT SUM(amount) as total_revenue
FROM hubspot_deals_portal_12345.deals
WHERE closedate BETWEEN '2024-01-01' AND '2024-12-31'
  AND hs_is_closed_won = TRUE;

-- Custom property query (uses idx_deals_custom_props GIN index)
SELECT dealname, custom_properties->>'industry'
FROM hubspot_deals_portal_12345.deals
WHERE custom_properties @> '{"industry": "Technology"}';
```

### Partitioning Strategy (For Large Datasets)

```sql
-- Partition by close date (monthly partitions)
CREATE TABLE hubspot_deals_portal_12345.deals (
    -- ... all columns ...
) PARTITION BY RANGE (closedate);

-- Create partitions
CREATE TABLE hubspot_deals_portal_12345.deals_2024_01 
    PARTITION OF hubspot_deals_portal_12345.deals
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

CREATE TABLE hubspot_deals_portal_12345.deals_2024_02 
    PARTITION OF hubspot_deals_portal_12345.deals
    FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');

-- Queries automatically use correct partition
SELECT * FROM hubspot_deals_portal_12345.deals
WHERE closedate BETWEEN '2024-01-01' AND '2024-01-31';
```

---

## 📈 Common Queries

### Scan Job Management

```sql
-- Create new scan job
INSERT INTO public.scan_jobs (
    id, scan_id, organization_id, scan_type, status, config, batch_size
) VALUES (
    gen_random_uuid()::text,
    'hubspot-deals-scan-001',
    'portal_12345',
    'deals',
    'pending',
    '{"properties": ["dealname", "amount", "dealstage"], "limit": 100}'::jsonb,
    100
);

-- Update scan progress
UPDATE public.scan_jobs
SET processed_items = processed_items + 50,
    status = 'running',
    updated_at = NOW()
WHERE scan_id = 'hubspot-deals-scan-001';

-- Mark scan as completed
UPDATE public.scan_jobs
SET status = 'completed',
    completed_at = NOW(),
    success_rate = ROUND((processed_items::numeric / total_items * 100), 2)
WHERE scan_id = 'hubspot-deals-scan-001';
```

### Deal Data Queries

```sql
-- Insert deal data
INSERT INTO hubspot_deals_portal_12345.deals (
    id, hs_object_id, _tenant_id, _scan_id, _extracted_at,
    dealname, amount, dealstage, pipeline, closedate, hubspot_owner_id
) VALUES (
    gen_random_uuid()::text,
    '12345678901',
    'portal_12345',
    'hubspot-deals-scan-001',
    NOW(),
    'Enterprise Deal - Acme Corp',
    50000.00,
    'qualifiedtobuy',
    'default',
    '2024-12-31',
    'owner_123'
);

-- Get deals by stage
SELECT 
    dealname,
    amount,
    closedate,
    hubspot_owner_id,
    hs_forecast_probability
FROM hubspot_deals_portal_12345.deals
WHERE _tenant_id = 'portal_12345'
  AND dealstage = 'qualifiedtobuy'
  AND archived = FALSE
ORDER BY amount DESC;

-- Revenue by month
SELECT 
    DATE_TRUNC('month', closedate) as month,
    COUNT(*) as deals_closed,
    SUM(amount) as total_revenue,
    AVG(amount) as avg_deal_size
FROM hubspot_deals_portal_12345.deals
WHERE hs_is_closed_won = TRUE
  AND closedate >= DATE_TRUNC('year', CURRENT_DATE)
GROUP BY DATE_TRUNC('month', closedate)
ORDER BY month;

-- Deals by owner
SELECT 
    hubspot_owner_id,
    COUNT(*) as total_deals,
    SUM(CASE WHEN hs_is_closed_won THEN 1 ELSE 0 END) as won_deals,
    SUM(amount) FILTER (WHERE hs_is_closed_won) as total_revenue
FROM hubspot_deals_portal_12345.deals
WHERE _tenant_id = 'portal_12345'
  AND createdate >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY hubspot_owner_id;

-- Pipeline velocity (average time in each stage)
SELECT 
    dealstage,
    COUNT(*) as deal_count,
    AVG(hs_time_in_dealstage) / 86400 as avg_days_in_stage
FROM hubspot_deals_portal_12345.deals
WHERE dealstage IS NOT NULL
GROUP BY dealstage
ORDER BY avg_days_in_stage DESC;

-- Get custom properties
SELECT 
    dealname,
    amount,
    custom_properties->>'custom_field_1' as custom_field_1,
    custom_properties->>'industry' as industry
FROM hubspot_deals_portal_12345.deals
WHERE custom_properties ? 'industry';
```

### Property Metadata Queries

```sql
-- Insert property metadata
INSERT INTO public.deal_properties_metadata (
    tenant_id, property_name, property_label, property_type, 
    field_type, group_name, display_order
) VALUES (
    'portal_12345',
    'custom_industry',
    'Industry Vertical',
    'enumeration',
    'select',
    'dealinformation',
    100
) ON CONFLICT (tenant_id, property_name) 
DO UPDATE SET last_seen_at = NOW();

-- Get all properties for tenant
SELECT 
    property_name,
    property_label,
    property_type,
    field_type,
    group_name
FROM public.deal_properties_metadata
WHERE tenant_id = 'portal_12345'
ORDER BY group_name, display_order;
```

---

## 🛡️ Data Integrity & Constraints

### Check Constraints

```sql
-- Ensure valid data
ALTER TABLE hubspot_deals_{tenant_id}.deals
    ADD CONSTRAINT check_amount_positive 
    CHECK (amount IS NULL OR amount >= 0);

ALTER TABLE hubspot_deals_{tenant_id}.deals
    ADD CONSTRAINT check_probability_range 
    CHECK (hs_forecast_probability IS NULL OR 
           (hs_forecast_probability >= 0 AND hs_forecast_probability <= 1));

ALTER TABLE public.scan_jobs
    ADD CONSTRAINT check_valid_status 
    CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled', 'paused'));
```

### Unique Constraints

```sql
-- Ensure no duplicate deals
ALTER TABLE hubspot_deals_{tenant_id}.deals
    ADD CONSTRAINT unique_hs_object_id UNIQUE (hs_object_id);

-- Tenant + HubSpot ID uniqueness
ALTER TABLE hubspot_deals_{tenant_id}.deals
    ADD CONSTRAINT unique_tenant_deal UNIQUE (_tenant_id, hs_object_id);
```

---

## 🔧 Maintenance Operations

### Data Cleanup

```sql
-- Archive old scans
CREATE TABLE public.scan_jobs_archive (LIKE public.scan_jobs INCLUDING ALL);

INSERT INTO public.scan_jobs_archive
SELECT * FROM public.scan_jobs
WHERE status = 'completed'
  AND completed_at < CURRENT_DATE - INTERVAL '90 days';

DELETE FROM public.scan_jobs
WHERE status = 'completed'
  AND completed_at < CURRENT_DATE - INTERVAL '90 days';

-- Clean up old deal data
DELETE FROM hubspot_deals_portal_12345.deals
WHERE _extracted_at < CURRENT_DATE - INTERVAL '365 days'
  AND archived = TRUE;
```

### Vacuum and Analyze

```sql
-- Regular maintenance
VACUUM ANALYZE public.scan_jobs;
VACUUM ANALYZE hubspot_deals_portal_12345.deals;

-- Reindex for performance
REINDEX TABLE hubspot_deals_portal_12345.deals;
```

### Statistics Update

```sql
-- Update table statistics for query planner
ANALYZE public.scan_jobs;
ANALYZE hubspot_deals_portal_12345.deals;
ANALYZE public.deal_properties_metadata;
```

---

## 📊 Schema Deployment Script

### Complete Deployment

```sql
-- ========================================
-- HUBSPOT DEALS ETL - COMPLETE SCHEMA DEPLOYMENT
-- ========================================

-- Set up extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ========================================
-- 1. CREATE SCAN JOBS TABLE (PUBLIC SCHEMA)
-- ========================================

CREATE TABLE IF NOT EXISTS public.scan_jobs (
    id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    scan_id VARCHAR(255) NOT NULL UNIQUE,
    organization_id VARCHAR(255) NOT NULL,
    scan_type VARCHAR(50) NOT NULL DEFAULT 'deals',
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    config JSONB NOT NULL,
    total_items INTEGER DEFAULT 0,
    processed_items INTEGER DEFAULT 0,
    failed_items INTEGER DEFAULT 0,
    success_rate DECIMAL(5,2),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    batch_size INTEGER DEFAULT 100,
    checkpoint_data JSONB,
    CONSTRAINT check_valid_status CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled', 'paused')),
    CONSTRAINT check_positive_counts CHECK (total_items >= 0 AND processed_items >= 0 AND failed_items >= 0)
);

CREATE INDEX IF NOT EXISTS idx_scan_jobs_scan_id ON public.scan_jobs(scan_id);
CREATE INDEX IF NOT EXISTS idx_scan_jobs_org_id ON public.scan_jobs(organization_id);
CREATE INDEX IF NOT EXISTS idx_scan_jobs_status ON public.scan_jobs(status);
CREATE INDEX IF NOT EXISTS idx_scan_jobs_org_status ON public.scan_jobs(organization_id, status);
CREATE INDEX IF NOT EXISTS idx_scan_jobs_created_at ON public.scan_jobs(created_at DESC);

-- ========================================
-- 2. CREATE TENANT SCHEMA AND DEALS TABLE
-- Replace {tenant_id} with actual tenant ID
-- ========================================

-- Example: CREATE SCHEMA IF NOT EXISTS hubspot_deals_portal_12345;

-- Use this template for each tenant
-- CREATE TABLE IF NOT EXISTS hubspot_deals_{tenant_id}.deals (
--     ... (full schema from above) ...
-- );

-- ========================================
-- 3. CREATE PROPERTY METADATA TABLE (OPTIONAL)
-- ========================================

CREATE TABLE IF NOT EXISTS public.deal_properties_metadata (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(255) NOT NULL,
    property_name VARCHAR(255) NOT NULL,
    property_label VARCHAR(500),
    property_description TEXT,
    property_type VARCHAR(50),
    field_type VARCHAR(50),
    group_name VARCHAR(255),
    display_order INTEGER,
    is_calculated BOOLEAN DEFAULT FALSE,
    is_hidden BOOLEAN DEFAULT FALSE,
    is_required BOOLEAN DEFAULT FALSE,
    has_unique_value BOOLEAN DEFAULT FALSE,
    options JSONB,
    is_read_only BOOLEAN DEFAULT FALSE,
    is_archivable BOOLEAN DEFAULT TRUE,
    discovered_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    last_seen_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    UNIQUE(tenant_id, property_name)
);

CREATE INDEX IF NOT EXISTS idx_props_tenant ON public.deal_properties_metadata(tenant_id);
CREATE INDEX IF NOT EXISTS idx_props_name ON public.deal_properties_metadata(property_name);

-- ========================================
-- 4. CREATE TRIGGERS
-- ========================================

CREATE OR REPLACE FUNCTION update_updated_at_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_scan_jobs_updated_at
    BEFORE UPDATE ON public.scan_jobs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_timestamp();

-- ========================================
-- DEPLOYMENT COMPLETE
-- ========================================
```

---

## 📝 Best Practices

### ETL Metadata Best Practices
1. **Always populate `_tenant_id`**: Essential for multi-tenant isolation
2. **Link to scan job**: Use `_scan_id` to trace data lineage
3. **Record extraction time**: `_extracted_at` for data freshness tracking
4. **Store source info**: Track `_source_system` and `_api_version`

### Indexing Best Practices
1. **Index tenant queries**: Always index `_tenant_id` for isolation
2. **Composite indexes**: Create for common query patterns
3. **Partial indexes**: Use `WHERE` clauses for frequently filtered columns
4. **Monitor index usage**: Remove unused indexes

### Schema Evolution
1. **Use ALTER TABLE**: Add columns without downtime
2. **Default values**: Provide defaults for new columns
3. **Backward compatibility**: Don't remove columns immediately
4. **Version control**: Track schema changes in migrations

---

**Database Schema Version**: 1.0  
**Last Updated**: December 2025  
**PostgreSQL Version**: 14+  
**Maintained By**: HubSpot Deals ETL Team
