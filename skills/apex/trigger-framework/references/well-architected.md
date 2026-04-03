# Well-Architected Mapping: Apex Trigger Framework

---

## Pillars Addressed

### Scalability
Single-trigger + handler pattern ensures all records in a bulk operation are processed in one handler invocation. SOQL and DML are batched outside loops. The pattern scales to 200 records without hitting governor limits by design.

- WAF check: One trigger per object?
- WAF check: Bulkified — all SOQL before loops, all DML on collections?

### Reliability
Recursion guard prevents infinite loops. Activation bypass enables disabling without deployment during incidents or data migrations. Clear before/after-save boundaries prevent forbidden DML errors.

- WAF check: Recursion guard present and tested?
- WAF check: Activation bypass exists — can this trigger be disabled in 30 seconds without a deploy?

### Operational Excellence
Handler pattern makes logic testable in isolation. Activation bypass via Custom Metadata means configuration is deployable across environments. Static recursion guard reset method prevents test order dependencies.

- WAF check: Handler class is independently testable?
- WAF check: Activation config is in Custom Metadata (deployable) not Custom Setting (manual per env)?

## Official Sources Used

- Salesforce Well-Architected Overview — reliability and operability framing for trigger architecture
- Apex Developer Guide — trigger behavior, testing, and transaction guidance
- Apex Reference Guide — trigger context and Apex API reference confirmation
