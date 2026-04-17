# Examples — Mutual TLS Callouts

## Example 1: Bank ACH partner

**Context:** Daily batch callout

**Problem:** Partner added mTLS mandate

**Solution:**

CSR in Salesforce → partner signs → import → Named Credential → Apex callout uses `callout:BankACH`

**Why it works:** Private key never leaves SFDC


---

## Example 2: Expiry monitor

**Context:** Prevent cert outage

**Problem:** Cert expired Friday evening previously

**Solution:**

Scheduled Apex queries Certificate where ValidTo < today+30; posts Slack

**Why it works:** Proactive rotation window

