# Agent Handoff Design

## Triggers

| Trigger Category | Condition | Destination | User Message |
|---|---|---|---|
| User-initiated |   |   |   |
| Confidence |   |   |   |
| Scope |   |   |   |
| Policy |   |   |   |
| Authorization |   |   |   |
| Technical |   |   |   |

## Context Package Schema

| Field | Source | Required? |
|---|---|---|
| User intent |   | Y |
| Attempt summary |   | Y |
| Related records (account/case/etc.) |   |   |
| Transcript link |   | Y |
| Handoff reason |   | Y |

## Destinations

| Destination | Type (queue/workflow/agent) | Presence-aware fallback |
|---|---|---|
|   |   |   |

## Hand-Back (if applicable)

- Trigger to resume:
- Context handed back:
- Resumption UX:

## Sign-Off

- [ ] Every trigger has a destination.
- [ ] Every destination has a fallback.
- [ ] Every handoff has user-facing text.
- [ ] Context package avoids raw transcript dump.
