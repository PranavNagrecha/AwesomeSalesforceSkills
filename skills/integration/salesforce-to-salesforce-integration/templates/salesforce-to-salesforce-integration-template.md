# Salesforce-to-Salesforce Integration — Work Template

Use this template when designing or implementing cross-org Salesforce integration.

## Scope

**Skill:** `salesforce-to-salesforce-integration`

**Source Org:** (fill in — instance URL or alias)
**Target Org:** (fill in — instance URL or alias)
**Objects to Sync/Share:** (list)
**Sync Direction:** One-way (Source → Target) / Bidirectional
**Volume (records/day estimated):** ______
**Pattern Selected:** Native S2S / REST API sync / Platform Event bridge / Salesforce Connect

---

## Native S2S Status Check

```bash
# Check if S2S is enabled in both orgs
sf data query --query "SELECT Id, ConnectionStatus FROM PartnerNetworkConnection" --target-org source-org
sf data query --query "SELECT Id, ConnectionStatus FROM PartnerNetworkConnection" --target-org target-org
```

S2S enabled in source: Yes / No
S2S enabled in target: Yes / No
Action: Use existing S2S / Implement API-based pattern (recommended)

---

## API-Based Sync Configuration (if chosen)

**Target Org:**
- Connected App Name: ______
- OAuth Flow: Client Credentials / JWT Bearer
- Scopes: api, refresh_token (minimum)

**Source Org:**
- Named Credential Name: ______
- URL: (target org instance URL)
- Authentication: OAuth2 (Client Credentials)

**External ID field for idempotency:** ______

---

## Sync Job Design (if REST API pattern)

| Job Name | Objects | Frequency | Volume | Pattern |
|---|---|---|---|---|
| | | Scheduled / Trigger-based | | Queueable / Batch / Bulk API 2.0 |

---

## Review Checklist

- [ ] Native S2S status checked in both orgs
- [ ] If native S2S NOT yet enabled: explicitly decided NOT to enable (use API-based)
- [ ] If native S2S enabled: irreversibility documented; team accepted
- [ ] Cross-org pattern selected based on volume and direction
- [ ] Connected App and Named Credential configured for API-based pattern
- [ ] Idempotency key (External ID) designed for sync jobs
- [ ] Error handling: status code handling + retry on 4xx/5xx from target
- [ ] Monitoring: alerting on sync failures configured
