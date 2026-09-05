# Apex Logging Review Worksheet

## Context

| Item | Value |
|---|---|
| Execution type | Sync / Trigger / Queueable / Batch / REST |
| Temporary debug or durable logging need? | |
| Current log sink | Debug log / Custom object / Platform event / External |
| Sensitive data risk | Low / Medium / High |

## Review Questions

- [ ] Are `System.debug` statements temporary and targeted?
- [ ] Does production-critical code write durable logs somewhere support can query?
- [ ] Are severity levels meaningful?
- [ ] Are correlation IDs or job IDs captured for async flows?
- [ ] Are secrets and sensitive payloads excluded?

## Actions

- Remove temporary debug lines:
- Add structured logging for:
- Add async correlation for:

## Sink Decision (fill one row per severity)

| Severity | Sink chosen | Survives rollback? | Meter it spends | Justification |
|---|---|---|---|---|
| INFO | `Application_Log__c` / event / debug only | No | DML statements | |
| WARN | | | | |
| ERROR | | | | |
| FATAL | | | | |

## Pre-Deploy Gate

- [ ] `Logger_Setting__mdt` has a `Default` record in the target org (absent = logger falls back to INFO).
- [ ] Any logging platform event declares `<publishBehavior>PublishImmediately</publishBehavior>` explicitly.
- [ ] A `PlatformEventSubscriberConfig` names the running user for every log-event trigger.
- [ ] `apexEmailNotifications` was **retrieved** before it was edited (deploying replaces the whole list).
- [ ] Every test that asserts on a subscriber calls `Test.getEventBus().deliver()` inside start/stopTest.
- [ ] `check_debug_and_logging.py --manifest-dir <source>` exits 0, or every finding is signed off.
- [ ] No class traced at `FINEST` handles credentials or personal data.
