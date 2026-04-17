# Examples — Private Connect Setup

## Example 1: Snowflake private

**Context:** SFDC → Snowflake BYOC

**Problem:** Public callout didn't meet compliance

**Solution:**

Private Connect outbound to Snowflake PrivateLink endpoint; Named Credential updated to private DNS

**Why it works:** Traffic stays within AWS fabric


---

## Example 2: Partner inbound

**Context:** Bank callback

**Problem:** Partner required no-public-internet

**Solution:**

Private Connect inbound from partner VPC to SFDC Experience Cloud

**Why it works:** Satisfies partner security policy

