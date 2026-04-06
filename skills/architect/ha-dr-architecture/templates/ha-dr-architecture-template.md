# HA/DR Architecture — [Org / Project Name]

## Metadata

| Field | Value |
|-------|-------|
| Org Name | |
| Salesforce Instance | |
| Edition | |
| Hyperforce | Yes / No |
| Prepared By | |
| Date | |
| Review Cycle | Annual / Semi-Annual |

---

## 1. Shared Responsibility Boundary

Document the division of HA/DR responsibility between Salesforce and the customer.

| Control Area | Salesforce Responsibility | Customer Responsibility |
|---|---|---|
| Infrastructure availability | Data-center redundancy, network failover, instance patching | — |
| Data recovery | Infrastructure-level replication | Backup tooling selection, configuration, testing |
| Metadata recovery | — | Source control, deployment pipeline, restore procedures |
| Integration availability | Platform API availability | Circuit breakers, durable queues, retry logic |
| Incident detection | Trust site status updates | Automated monitoring, alerting, on-call rotation |
| Runbook execution | — | Incident commander, escalation chain, runbook documentation |

---

## 2. Trust Site Monitoring Plan

| Field | Value |
|-------|-------|
| Production Instance Key | (e.g., NA152) |
| Sandbox Instance Keys | |
| Monitoring Tool | |
| Polling Method | API polling / Webhook subscription |
| Alert Destination | |
| Alert Severity | |
| Runbook Link in Alert | Yes / No |

**Status API Endpoint:**
`https://api.status.salesforce.com/v1/instances/{instance}/status`

**Monitoring validation checklist:**
- [ ] Polling or webhook confirmed working end-to-end
- [ ] Alert fires on simulated status change
- [ ] On-call rotation receives the alert
- [ ] Runbook URL is reachable from the alert body
- [ ] Sandbox instance keys verified after last refresh on: ___________

---

## 3. RTO and RPO Targets

Define targets by data category. These are business-driven inputs, not platform defaults.

| Data Category | RTO Target | RPO Target | Current Capability | Gap |
|---|---|---|---|---|
| Salesforce records (Account, Contact, etc.) | | | | |
| Custom object records | | | | |
| Files and attachments | | | | |
| Metadata (Apex, flows, configuration) | | | | |
| Integration state (queue, event log) | | | | |
| User authentication config (SSO, MFA) | | | | |

**Gap resolution plan:**
- TODO: Document what tooling or process changes close each identified gap.

---

## 4. Backup Strategy

### Record and File Backup

| Field | Value |
|-------|-------|
| Tool | (e.g., Salesforce Backup and Restore, OwnBackup, Veeam) |
| Backup Frequency | |
| Objects Covered | |
| Files/Attachments Covered | Yes / No |
| Retention Period | |
| Last Restore Test Date | |
| Restore Test Result | |

### Metadata Backup

| Field | Value |
|-------|-------|
| Source Control System | |
| Retrieve Automation | Yes / No — describe: |
| Last Metadata Recovery Test Date | |
| Recovery Test Result | |

---

## 5. Integration Failover Design

For each integration, document the failover pattern.

### Integration: [Name]

| Field | Value |
|-------|-------|
| Direction | Inbound to Salesforce / Outbound from Salesforce |
| External System | |
| Current Pattern | Synchronous callout / Platform Events / Async queue |
| Failover Pattern | Circuit breaker / Durable external queue / Graceful degradation |
| Queue Tool | (e.g., AWS SQS, Azure Service Bus, Anypoint MQ) |
| Queue TTL | |
| Drain Procedure Documented | Yes / No |
| Drain Tested | Yes / No |
| Idempotency Handling | |
| Rate Limit Awareness | |

---

## 6. DR Runbook

### Incident Declaration

**Trigger criteria (any of the following):**
- Trust site status for production instance moves to non-OK
- Salesforce API error rate exceeds ___% over ___ minutes
- Business stakeholder reports inability to access org

**Incident Commander:** _______________
**Backup Incident Commander:** _______________
**Escalation Contact (Salesforce Support):** _______________
**Case Priority for Outages:** P1 — Critical

---

### Recovery Steps

#### Step 1: Confirm Outage Scope (Target: complete within ___ minutes of declaration)

- [ ] Check Trust site for instance status and any posted incident
- [ ] Confirm scope: full outage, partial degradation, specific features only
- [ ] Notify stakeholders: _______________

#### Step 2: Activate Integration Fallback (Target: complete within ___ minutes)

- [ ] Confirm circuit breakers are open (middleware/monitoring dashboard)
- [ ] Confirm inbound queues are buffering (verify queue depth is growing, not erroring)
- [ ] Confirm no integration is retrying synchronously against a degraded org

#### Step 3: Business Process Continuity (Target: complete within ___ minutes)

- [ ] Notify affected user groups with estimated impact window (from Trust site incident timeline)
- [ ] Activate compensating manual processes for: _______________
- [ ] Update internal status page

#### Step 4: Salesforce Recovery Confirmed

- [ ] Trust site status returns to OK
- [ ] Confirm API access restored via test REST call: `GET /services/data/`
- [ ] Notify stakeholders of recovery

#### Step 5: Integration Drain (Target: complete within ___ minutes of recovery)

- [ ] Resume integration consumers in sequence: _______________
- [ ] Monitor queue depth — confirm draining not erroring
- [ ] Verify idempotency: check for duplicate records using: _______________
- [ ] Confirm data integrity with business stakeholder

#### Step 6: Post-Incident Review (Target: schedule within 48 hours)

- [ ] Capture timeline of incident and response actions
- [ ] Identify what worked and what did not
- [ ] Update runbook with findings
- [ ] Update RTO/RPO gap analysis if actual recovery time differed from target

---

## 7. Business Continuity Checklist

- [ ] RTO and RPO defined for all data categories
- [ ] Trust site monitoring automated and tested
- [ ] Backup tooling covers records, files, and attachments
- [ ] Metadata version-controlled in Git
- [ ] Integration circuit breakers documented and tested
- [ ] Inbound queue drain procedures documented and tested
- [ ] Compensating manual processes identified for critical Salesforce-dependent workflows
- [ ] Incident commander role and escalation chain assigned
- [ ] Annual tabletop DR exercise scheduled
- [ ] Sandbox refresh procedure includes Trust site monitoring key validation

---

## 8. Hyperforce Considerations

| Field | Value |
|-------|-------|
| Org on Hyperforce | Yes / No |
| Cloud Provider | AWS / Azure / GCP / N/A |
| Region | |
| Data Residency Requirement | Yes / No — jurisdiction: |
| Region Paired Failover Available | Confirm with Salesforce account team |

---

## Revision History

| Date | Author | Changes |
|------|--------|---------|
| | | Initial version |
