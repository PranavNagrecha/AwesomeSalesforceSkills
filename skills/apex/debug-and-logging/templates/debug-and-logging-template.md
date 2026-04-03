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
