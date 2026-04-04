# Custom Logging and Monitoring — Framework Design Template

## Logging Requirements

- **Minimum log level for production:** DEBUG / INFO / WARN / ERROR
- **Retention by level:**
  - DEBUG: ___ days
  - INFO: ___ days
  - WARN: ___ days
  - ERROR: ___ days
- **Rollback-safe logging needed:** Yes / No
- **External forwarding needed:** Yes (target: ___) / No

## Log sObject Schema

Object: `Log__c`

| Field API Name | Type | Required | Notes |
|---|---|---|---|
| `Level__c` | Picklist | Yes | DEBUG, INFO, WARN, ERROR |
| `Source__c` | Text(255) | Yes | ClassName.methodName |
| `Message__c` | Long Text(32768) | Yes | Log content |
| `Correlation_Id__c` | Text(50), External ID | No | Batch/async job linkage |
| `Transaction_Id__c` | Text(50) | No | Groups same-transaction logs |
| `Retention_Date__c` | Date, Indexed | Yes | Purge cutoff — set on insert |

## Custom Metadata Configuration

Type: `Logger_Config__mdt`

| Field | Type | Notes |
|---|---|---|
| `Minimum_Level__c` | Picklist | Configurable per env without deployment |
| `Debug_Retention_Days__c` | Number | |
| `Error_Retention_Days__c` | Number | |

## Platform Event for Rollback-Safe Logging

Event: `Log_Event__e`

- [ ] Log_Event__e created with same fields as Log__c
- [ ] Subscriber trigger on Log_Event__e inserts Log__c records
- [ ] Error logs in catch blocks use EventBus.publish() not direct DML

## Purge Job

- [ ] LogPurger batch queries `WHERE Retention_Date__c < TODAY`
- [ ] LogPurgerSchedulable wraps batch for scheduling
- [ ] Scheduled at low-traffic time: `'0 0 1 * * ?'` (1 AM daily)

## External Forwarding (if required)

- [ ] Named Credential configured for SIEM endpoint
- [ ] Scheduled batch POSTs recent Log__c records to SIEM REST API
- [ ] Message field sanitized before forwarding (remove PII/secrets)

## Testing Checklist

- [ ] LoggerService.reset() method exists for test isolation
- [ ] Test: flush() uses Database.insert(buffer, false) — confirmed no throw on validation error
- [ ] Test: PE-based log survives transaction rollback
- [ ] Test: level gating — DEBUG logs not persisted when minimum is WARN
- [ ] Test: LogPurger deletes records with Retention_Date__c in the past
