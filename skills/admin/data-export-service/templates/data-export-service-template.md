# Data Export Service — Work Template

Use this template when configuring or auditing a Data Export Service runbook.

## Scope

**Skill:** `admin/data-export-service`

**Request summary:** _(why is the team using Data Export — real backup, evidence archive, one-time snapshot, compliance request?)_

## Obligation Restate (do this first)

| Question | Answer |
|---|---|
| What is the actual obligation? | _(regulatory backup / evidence archive / ad-hoc / discovery)_ |
| Required RPO | _(hours / days / weeks / N/A)_ |
| Required RTO | _(hours / days / N/A)_ |
| Restore granularity expected | _(record-level / object-level / org-level / none)_ |
| If RPO/RTO is named, is Data Export the right tool? | yes / **no — escalate to Backup and Restore or third-party** |

## Configuration

| Setting | Value | Notes |
|---|---|---|
| Cadence | weekly / monthly | constrained by edition |
| Object scope | all-data / explicit list | document the list if explicit |
| Include images / documents / attachments | YES / NO | NO unless specific consumer named |
| Include Salesforce Files | YES / NO | NO unless specific consumer named |
| Include Chatter Files | YES / NO | NO unless specific consumer named |
| File-size split | 256 MB / 512 MB | 512 MB default; smaller for slow-link recipients |
| Notification recipient | _(distribution list)_ | use a list, not a person |

## Acknowledged Gaps

- [ ] Big Objects excluded
- [ ] External Objects excluded
- [ ] Metadata excluded (Git / Metadata API covers this)
- [ ] Recycle Bin records past retention not retrievable
- [ ] No restore path — this is not a backup product

## Operator Runbook

| Step | Owner | SLA | Recorded in |
|---|---|---|---|
| Receive notification email | primary operator | within 12 hours of email | ticket |
| Download ZIP set | primary operator | within 24 hours of email | ticket + checksums |
| Verify sha256 of every ZIP | primary operator | before upload | ledger |
| Upload to long-term archive | primary operator | within 48 hours of email | ledger + archive object IDs |
| Review and reconcile gap | backup operator | within 48 hours of upload | ticket |

## Long-Term Archive Destination

- Storage: _(S3 / Azure Blob / on-prem)_
- Encryption at rest: _(SSE-KMS / CMK / FDE)_
- Access control: _(IAM role / RBAC group)_
- Retention: _(years; immutable / WORM if required)_
- Cross-region replication: yes / no

## Restore Drill

- [ ] Quarterly drill scheduled
- [ ] Drill destination: sandbox `_(name)_`
- [ ] Drill loads via Data Loader / Bulk API
- [ ] Drill outcome ticket: `_(URL)_`

## Documented Gap Statement (for architecture doc)

> _(Paste the explicit framing: "this is evidence archive, not record-level backup; record-level recovery is out of scope of this control; Backup and Restore licensing tracked under <ticket>".)_

## Notes

_(deviations, edge cases, history)_
