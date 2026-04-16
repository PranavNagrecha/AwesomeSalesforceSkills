# Sandbox Refresh Data Strategies — Planning Template

Use this template when designing the data readiness strategy for a sandbox refresh.

---

## Scope

**Sandbox name:** _______________
**Sandbox type:** [ ] Developer  [ ] Developer Pro  [ ] Partial  [ ] Full
**Purpose:** [ ] Developer testing  [ ] QA / Regression  [ ] UAT  [ ] Performance testing

---

## Data Classification

Classify all data required for testing in this sandbox:

| Data Category | Objects | Source | Mechanism |
|---|---|---|---|
| Reference data (static lookups) | | | SandboxPostCopy Queueable |
| Scenario data (test records) | | | Data Seeding or scripts |
| Live-like data (production subset) | | | Partial sandbox copy |
| Files / Big Objects | | | SFDMU / Data Loader (post-refresh) |

---

## SandboxPostCopy Design

- [ ] `runApexClass()` only enqueues first Queueable — no direct DML
- [ ] Queueable chain designed for batch size: ___ records per job
- [ ] Estimated number of Queueable jobs for full reference data load: ___
- [ ] AsyncApexJob monitoring query documented

---

## Data Seeding Template

- [ ] Template created in Setup > Data Seeding
- [ ] Root node object: _______________
- [ ] Child node objects (confirm NOT in exclusion list): _______________
- [ ] Generation count: _______________
- [ ] Template linked to this sandbox definition

**Exclusion check** — confirm none of these are in the template:
- [ ] Big Objects — excluded
- [ ] ContentDocument / Files — excluded
- [ ] Chatter content — excluded
- [ ] External objects — excluded
- [ ] AgentWork — excluded

---

## PII / Data Privacy

- [ ] Sandbox type allows production data copy (Partial or Full only)
- [ ] PII masking step planned before QA access: _______________
- [ ] Applicable regulations reviewed: [ ] GDPR  [ ] CCPA  [ ] HIPAA  [ ] Other

---

## Post-Refresh Validation

Queries to confirm data is present after refresh:

```soql
SELECT COUNT() FROM <reference object> -- expected: ___
SELECT COUNT() FROM <scenario object> -- expected: ___
```

---

## Estimated Time to Test-Ready

Manual effort after refresh: ___ hours
Automated (SandboxPostCopy + Data Seeding) time: ___ minutes
