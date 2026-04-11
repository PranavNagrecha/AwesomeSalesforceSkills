# Wealth Management Architecture — Work Template

Use this template when working on tasks in this area.

## Scope

**Skill:** `wealth-management-architecture`

**Request summary:** (fill in what the user asked for)

**Org:** (target org alias or environment — sandbox, scratch, production)

## Context Gathered

Record the answers to the Before Starting questions from SKILL.md here before proceeding.

- **FSC license type confirmed:** (base FSC / FSC + CRM Plus / other)
- **CRM Plus present (for Scoring Framework):** (yes / no / not verified)
- **Custodian data sources:** (list each, include volume estimate and update cadence)
- **Compliant Data Sharing scope:** (list object types that require CDS enrollment)
- **Features required:** (check all that apply)
  - [ ] AI Portfolio Insights (`enableWealthManagementAIPref`)
  - [ ] Financial Deal Management (`enableDealManagement`)
  - [ ] Compliant Data Sharing
  - [ ] Scoring Framework / Advisor Analytics
  - [ ] Client Portal (Experience Cloud)

## IndustriesSettings Audit

Current state of `Industries.settings-meta.xml` (retrieved from target org):

```xml
<!-- Paste retrieved XML here -->
```

Flags to change:

| Flag | Current State | Required State | Action |
|---|---|---|---|
| `enableWealthManagementAIPref` | (true/false/unknown) | (true/false) | (deploy / no change) |
| `enableDealManagement` | (true/false/unknown) | (true/false) | (deploy / no change) |

## Compliant Data Sharing Plan

| Object Type | CDS Currently Active | Records Exist | Recalculation Batch Needed | Maintenance Window Required |
|---|---|---|---|---|
| Account | (yes/no) | (yes/no) | (yes/no) | (yes/no) |
| Opportunity | (yes/no) | (yes/no) | (yes/no) | (yes/no) |
| Interaction | (yes/no) | (yes/no) | (yes/no) | (yes/no) |
| Interaction Summary | (yes/no) | (yes/no) | (yes/no) | (yes/no) |
| (custom object) | (yes/no) | (yes/no) | (yes/no) | (yes/no) |

## Custodian Integration Design

| Custodian | Feed Cadence | Est. Record Volume | Pattern Selected | Error Handling |
|---|---|---|---|---|
| (Custodian A) | (nightly / real-time) | (est. count) | (Bulk API 2.0 / Remote Call-In) | (dead-letter queue / retry) |
| (Custodian B) | (nightly / real-time) | (est. count) | (Bulk API 2.0 / Remote Call-In) | (dead-letter queue / retry) |

**Post-load rollup recalculation trigger:**
(describe how rollup recalculation will be triggered after each Bulk API 2.0 ingest job completes)

## Approach

Which pattern from SKILL.md applies? Why?

(Describe the primary integration pattern, CDS enrollment sequence, and feature flag deployment plan.)

## Review Checklist

Copy from SKILL.md and tick items as completed:

- [ ] CRM Plus license confirmed present if Scoring Framework is in scope
- [ ] All required IndustriesSettings flags deployed via Metadata API (not toggled manually)
- [ ] IndustriesSettings retrieved before deployment to avoid overwriting existing flags
- [ ] Compliant Data Sharing enrollment completed for each required object type
- [ ] CDS sharing recalculation batch run and verified after each object enrollment
- [ ] Custodian integration pattern documented with error handling defined
- [ ] Post-load rollup recalculation trigger documented and tested
- [ ] FSC rollup rules validated against test portfolio records in sandbox
- [ ] Advisor workspace page layouts reviewed against enabled feature flags
- [ ] Client portal Experience Cloud permissions verified (if in scope)

## Deviations from Standard Pattern

(Record any decisions that diverge from the SKILL.md guidance and why.)

## Handoff Notes

(Record org-specific decisions, edge cases, and anything the next engineer needs to know.)
