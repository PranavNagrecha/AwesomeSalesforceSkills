# OmniScript Session Design

## OmniScript

- Name:
- Steps:
- Typical duration:
- External users (Experience Cloud)? Y/N

## Store

- [ ] Native OmniScript tracking
- [ ] Custom object `Session__c`
- [ ] Big Object
- [ ] Platform Cache (Session)

## State Schema

| Field | Type | Sensitive? | Encrypted? |
|---|---|---|---|
|   |   |   |   |

Always include: `userId`, `createdAt`, `lastUpdatedAt`, `version`, `stepId`, `expiresAt`.

## Save Cadence

- [ ] Step transition
- [ ] Debounced in-step save (justify)

## Resume URL

- Token type (JWT / signed blob):
- Expiry:
- Re-auth required on load: Y/N

## Concurrency

- Version field in place
- Conflict UX:

## Retention

- Tier (1 sensitive / 2 non-sensitive / 3 non-PII):
- Expiry duration:
- Purge mechanism:

## Sign-Off

- [ ] PII encrypted or tokenized.
- [ ] URL carries token only, no data.
- [ ] Version-based conflict detection.
- [ ] Expiry + purge scheduled.
