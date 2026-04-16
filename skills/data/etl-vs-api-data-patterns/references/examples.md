# Examples — ETL vs API Data Patterns

## Example 1: Selecting Informatica for Large-Volume Daily Sync

**Context:** A financial services company needed to sync 5 million account records daily from a data warehouse to Salesforce and back, with data quality profiling and regulatory lineage documentation requirements.

**Problem:** The team initially built the sync using MuleSoft Anypoint calling standard REST API endpoints. Within the first run, they exhausted the daily REST API limit (150,000+ calls for the volume) and had no data quality profiling or lineage report.

**Solution:**
1. Migrated the sync to Informatica Cloud Services using the Salesforce Connector (which uses Bulk API 2.0 under the hood).
2. Added data quality transformations in Informatica: phone number normalization, address standardization, duplicate detection.
3. Configured Informatica's lineage catalog to document source-to-target field mapping for compliance.
4. Daily limit exhaustion resolved: Bulk API 2.0 has a separate 150M row budget from the REST API daily limit.

**Why it works:** Informatica is the appropriate tool for large-volume batch ETL with data quality and lineage requirements. MuleSoft REST API calls were architecturally wrong for this volume.

---

## Example 2: MuleSoft for Real-Time Customer Record Sync

**Context:** A retail company needed customer profile updates from an e-commerce platform to appear in Salesforce within 30 seconds of the customer changing their address or email.

**Problem:** The initial design used a nightly ETL job. Customer service representatives were working from stale addresses for up to 24 hours after a customer updated their profile.

**Solution:**
1. The e-commerce platform was configured to publish a webhook event on profile update.
2. A MuleSoft Experience API received the webhook, transformed the payload, and called the Salesforce REST API to upsert the Contact record.
3. End-to-end latency: < 10 seconds.

**Why it works:** MuleSoft API integration is designed for real-time event-driven connectivity. An ETL tool with batch scheduling cannot achieve sub-minute latency. The latency requirement drove the architecture choice, not the data volume.
