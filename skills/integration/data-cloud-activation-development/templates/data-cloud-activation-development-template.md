# Data Cloud Activation Development — Work Template

Use this template when building or troubleshooting Data Cloud Data Action Targets or Data Cloud-Triggered Flows.

## Scope

**Skill:** `data-cloud-activation-development`

**Request summary:** (fill in: what event should trigger which action in which target system)

## Surface Selection

- [ ] **Data Action Target** — event-level, near-real-time (webhook, Platform Event, Marketing Cloud)
- [ ] **Data Cloud-Triggered Flow** — DMO insert triggers a Salesforce autolaunched Flow
- [ ] **Activation Target** — segment-level batch publishing (admin configuration, not this skill)

## Data Action Target Configuration (if applicable)

- **Target type:** [ ] Webhook  [ ] Platform Event  [ ] Marketing Cloud
- **Endpoint URL (webhook):**
- **HMAC-SHA256 secret key configured:** [ ] Yes — NEVER leave blank
- **Streaming Insight condition defined:** [ ] Yes
- **Streaming Insight linked to target:** [ ] Yes

## Data Cloud-Triggered Flow Configuration (if applicable)

- **Autolaunched Flow name:**
- **Flow activated:** [ ] Yes
- **DMO name for trigger:**
- **Data Cloud-Triggered Flow binding created:** [ ] Yes
- **Binding activated:** [ ] Yes
- **DMO trigger event is INSERT (not update):** [ ] Confirmed

## Failure Handling

- **HMAC verification implemented in receiver:** [ ] Yes
- **Dead-letter queue or retry mechanism:** [ ] Yes  [ ] N/A for Triggered Flows
- **4-day event retention window factored into monitoring:** [ ] Yes

## Checklist

- [ ] Correct surface selected (Data Action Target vs. Triggered Flow vs. Activation Target)
- [ ] HMAC key configured if webhook target
- [ ] Streaming Insight linked to Data Action Target
- [ ] Flow is autolaunched and activated before binding
- [ ] Triggered Flows handle insert-only — update scenarios use re-insert pattern
- [ ] External retry/dead-letter handling for webhook delivery failures

## Notes

(Record any deviations from the standard pattern and why)
