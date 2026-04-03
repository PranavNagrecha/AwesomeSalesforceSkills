# Exception Handling Review Template

## Context

| Item | Value |
|---|---|
| Entry point | Trigger / `@AuraEnabled` / REST / Queueable / Batch / Invocable |
| Operation | Insert / Update / Delete / Callout / Query / Transformation |
| Partial success allowed? | Yes / No |
| User-facing? | Yes / No |
| Logging destination | Custom object / Platform event / External monitor / None |

## Failure Classification

| Failure Type | Expected? | Handling Pattern | Notes |
|---|---|---|---|
| Validation/business rule | Yes | `addError` or custom domain exception | |
| DML row failure | Sometimes | `Database.SaveResult[]` review | |
| External system timeout | Sometimes | Catch, log, retry strategy | |
| Programmer defect / unexpected null | No | Log at boundary and rethrow | |

## Catch Block Review

- [ ] Catch type is specific (`DmlException`, `QueryException`, `CalloutException`) where possible
- [ ] Catch block does more than `System.debug`
- [ ] User-facing boundaries convert known failures to safe messages
- [ ] Background jobs preserve correlation IDs or record IDs in logs
- [ ] Partial-success DML paths inspect every `SaveResult`

## Remediation Notes

**Current smell:**  
Describe the specific swallow, rethrow, or partial-success problem being reviewed.

**Recommended pattern:**  
State whether this should use `addError`, `Database.SaveResult[]`, custom exception mapping, or boundary rethrow.

**What must be logged:**  
Capture record IDs, operation name, exception type, message, and correlation identifier if available.
