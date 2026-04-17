# Examples — Salesforce Data Pipeline / ETL

## Example 1: Snowflake mirror

**Context:** Finance analytics

**Problem:** Nightly polling missed late updates

**Solution:**

Bulk snapshot + CDC via Pub/Sub → Snowflake Streams + Tasks for merge

**Why it works:** Exactly-once capture


---

## Example 2: Gap-fill handler

**Context:** CDC gap after outage

**Problem:** Missing 2h of deltas

**Solution:**

On GAP_FILL event receive re-query affected record Ids via SOQL

**Why it works:** Platform signals; pipeline reacts

