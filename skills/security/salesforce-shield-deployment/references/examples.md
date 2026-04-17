# Examples — Salesforce Shield Deployment

## Example 1: PCI program Shield rollout

**Context:** Retailer with PAN tokenized externally but transaction amounts must be encrypted at rest.

**Problem:** Encryption of Amount__c broke existing reports.

**Solution:**

Use deterministic encryption for Amount__c (required for bucketing reports); turn on FHR 7-year retention; wire EventLogFile daily to S3 with Athena on top.

**Why it works:** Deterministic preserves equality-filter reports while still protecting at rest.


---

## Example 2: Zero-trust log monitoring

**Context:** Fraud detection team needs suspicious login alerts.

**Problem:** Log consumer poll was hourly.

**Solution:**

Subscribe to LoginEventStream via CometD or the Pub/Sub API; forward to SIEM in real time.

**Why it works:** Streams arrive within seconds of login; EventLogFile has 3-6h latency.

