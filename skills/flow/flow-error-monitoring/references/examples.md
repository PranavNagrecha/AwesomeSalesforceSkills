# Examples — Flow Error Monitoring

## Example 1: Fault-email routing by domain

**Context:** 80 active flows. Every flow creator's inbox is drowning in fault emails; nobody sees them.

**Solution:** Set Flow Exception Email recipient via Setup → Process Automation Settings → one email alias per business domain (ops-sales@, ops-service@). Each domain's ops team monitors their alias.

---

## Example 2: Central log + dashboard

**Context:** Leadership wants to see weekly flow health metrics.

**Solution:** Integration_Log__c with Severity + Source fields, filled via fault-path Create Records in every flow. Report: Errors by Source (last 7 days), summarized into a Home Page dashboard component.

---

## Example 3: External Splunk bridge

**Context:** Security team requires all platform errors in Splunk.

**Solution:** After-Insert trigger on Integration_Log__c publishes `Integration_Error__e`. A Splunk Pub/Sub API subscriber consumes. Salesforce team doesn't manage the Splunk side; security team owns alerts in their platform.

---

## Anti-Pattern: Single inbox for all fault emails

All 80 flows email one address. It becomes noise; nobody reads it. Fix: route by domain or severity.

---

## Anti-Pattern: Log object with no severity field

Logs can't be filtered — P0 alerts mixed with debug traces. Fix: required Severity__c picklist with CRITICAL/ERROR/WARNING/INFO.
