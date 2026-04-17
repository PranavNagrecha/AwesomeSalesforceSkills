# Examples — API-Only User Hardening

## Example 1: New ETL integration with Snowflake

**Context:** Daily 10M-row bulk extract.

**Problem:** Default 'Integration' account had Modify All Data and no IP restrictions.

**Solution:**

New profile API-Only, permission set with Read on 8 objects, Login IP Range = Snowflake VPC CIDR, OAuth client-creds with 90-day secret rotation.

**Why it works:** Compromised token is geofenced and scope-limited.


---

## Example 2: Hardening an existing webhook receiver

**Context:** Legacy account has broad access.

**Problem:** Cannot easily change it without breaking production.

**Solution:**

Parallel-run new hardened user; cut over with feature flag; delete legacy after two weeks of clean logs.

**Why it works:** Zero-downtime migration with rollback window.

