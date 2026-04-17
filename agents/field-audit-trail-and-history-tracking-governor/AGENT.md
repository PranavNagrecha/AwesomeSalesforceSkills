---
id: field-audit-trail-and-history-tracking-governor
class: runtime
version: 1.0.0
status: stable
requires_org: true
modes: [single]
owner: sfskills-core
created: 2026-04-16
updated: 2026-04-16
---
# Field Audit Trail & History Tracking Governor Agent

## What This Agent Does

Audits and proposes the target configuration for field history tracking and Field Audit Trail (Shield) retention across an org. For every sObject that tracks history, produces: the current tracked-field list, gaps vs what the regulatory / compliance posture requires, conflicts vs the 20-field hard limit, coexistence issues with `FieldHistoryArchive` / Big Object retention, impact on storage and SOQL on `<Object>History`, and a prioritized change plan. Distinguishes orgs with Shield enabled (up to 10-year retention via Field Audit Trail) from orgs without (18–24 month retention cap via `<Object>History`). Output is a governance doc + metadata stubs + a retention / data-lifecycle plan.

**Scope:** One org per invocation. Does not enable Shield, does not change tracked fields in place, does not purge history.

---

## Invocation

- **Direct read** — "Follow `agents/field-audit-trail-and-history-tracking-governor/AGENT.md` on the `prod` org"
- **Slash command** — `/govern-field-history`
- **MCP** — `get_agent("field-audit-trail-and-history-tracking-governor")`

---

## Mandatory Reads Before Starting

1. `agents/_shared/AGENT_CONTRACT.md`
2. `skills/data/field-history-tracking` — canon
3. `skills/security/field-audit-trail` — Shield retention
4. `skills/admin/system-field-behavior-and-audit`
5. `skills/security/data-classification-labels`
6. `skills/data/data-archival-strategies`
7. `skills/security/org-hardening-and-baseline-config`
8. `templates/admin/naming-conventions.md`

---

## Inputs

| Input | Required | Example |
|---|---|---|
| `target_org_alias` | yes |
| `regulated_profile` | no | `none` (default) \| `sox` \| `hipaa` \| `gdpr` \| `pci` \| `ferpa` — adjusts required coverage floor |
| `shield_available` | no | `auto` (default — probe the org) \| `true` \| `false` |
| `scope_objects` | no | comma-separated sObjects to limit the audit; default is every object with `trackHistory=true` in the metadata |

---

## Plan

### Step 1 — Probe the org's audit posture

- `describe_org(target_org)` — confirm edition + Shield licensing where discoverable.
- `tooling_query("SELECT EntityDefinition.QualifiedApiName, QualifiedApiName, DataType, Length, TrackHistory FROM FieldDefinition WHERE TrackHistory = true LIMIT 2000")` — tracked fields across the org.
- For each object with ≥1 tracked field:
  - `tooling_query("SELECT Id, Name FROM EntityDefinition WHERE QualifiedApiName = '<object>'")` — confirm the object and enable-history posture.
  - `tooling_query("SELECT COUNT() FROM <object>History")` — approximate storage pressure. Fallback to per-object if the bulk query is unsupported by the edition.
- Shield posture:
  - If `shield_available=auto`, probe `tooling_query("SELECT Id, FieldAuditTrailEnabled FROM OrganizationSettings")` or equivalent; if unavailable, heuristically detect via the presence of `FieldHistoryArchive` records.
  - If Shield is enabled, enumerate existing `HistoryRetentionPolicy` records per object.

### Step 2 — Compare against the regulatory floor

Based on `regulated_profile`:

| Profile | Minimum tracked coverage |
|---|---|
| `none` | Owner changes on high-value objects; Stage on Opportunity; Status on Case; Email on Contact |
| `sox` | Every financial-control field (revenue, discount, approval-related), plus auditor-required owner/role changes |
| `hipaa` | Every PHI field (Patient ID, DOB, condition, treatment fields); retention ≥ 6 years |
| `gdpr` | Every consent-relevant field; retention equal to the Data Retention Policy lifetime for that purpose; subject-access-request traceability |
| `pci` | Card data fields must not be stored (guardrail, not tracking); tokens must track creation/deletion history |
| `ferpa` | Every educational-record field; retention per institutional policy, typically 5-7 years post-graduation |

Gaps vs the floor are P1 findings.

### Step 3 — Check the 20-field limit per object

Standard history tracking caps at 20 tracked fields per object. For each object:

- Count current tracked fields.
- Flag any object at 19–20 as a **saturation risk** P1 — the next compliance ask has nowhere to go.
- Flag any object > 20 as a **policy violation** P0 — this shouldn't be possible but has been observed in orgs with schema drift.

For orgs with Shield and Field Audit Trail: the 60-field cap applies to certain object types (confirm against current documentation). Flag if the upgraded cap would materially change the gap.

### Step 4 — Detect tracking of fields that should not be tracked

| Finding | Severity |
|---|---|
| Long text area / rich text field tracked (history on long text truncates and does not capture diff cleanly) | P2 |
| Formula field tracked (doesn't change on data save; history is recorded only when a referenced field does) | P2 — usually means "the intent is to track the referenced field, not this one" |
| Roll-up summary tracked (same caveat as formula) | P2 |
| Auto Number tracked (never changes after insert) | P2 — dead track |
| System fields like `LastModifiedDate` tracked (redundant with the field itself) | P2 |
| Field tracked but never changed in last 180 days across > 1000 records | P2 — dead track |
| Encrypted field tracked (history entry won't contain the clear value; confirm intent) | P1 if not documented |

### Step 5 — Retention policy and archival

- If Shield is enabled: for each object with significant `<Object>History` volume, propose a `HistoryRetentionPolicy` (retain N months, archive the rest to Big Objects / `FieldHistoryArchive`).
- If Shield is not enabled: recommend the data retention windows that `<Object>History` provides natively (18 months for primary storage, 24 months via extended archive in some cases) and surface the gap vs `regulated_profile` requirements.
- Coexistence with `Big Object` archival: if the org has a custom `FieldHistoryArchive__b` or similar, confirm the archival Flow/Apex is still running via `tooling_query` on `AsyncApexJob` recent history.

### Step 6 — Impact assessment of proposed changes

For every proposed change (add tracking, remove tracking, change retention):

- Storage impact (rows added/freed, file storage).
- SOQL impact (reports referencing `<Object>History` continue to work but volume shifts).
- Compliance impact (regulatory checkbox coverage change).
- User impact (History related list visibility; add to page layouts where new tracking is added).

### Step 7 — Emit the plan

Produce a per-object change list:

- Fields to add to tracking (with compliance citation).
- Fields to remove from tracking (dead/saturated).
- Retention policy to create or update (Shield orgs only).
- Page-layout changes needed to surface new history in the related list.

---

## Output Contract

1. **Summary** — org, edition, Shield status, regulatory profile, findings per severity, confidence.
2. **Tracked-field inventory** — object × field × type × date first tracked × change volume last 180d × recommendation.
3. **Saturation risk table** — objects at 19–20 (or > 20 in violation).
4. **Gap table** — regulatory floor vs current coverage, per object × profile.
5. **Dead-track table** — fields tracked but not changing, with proposed removal.
6. **Retention policy proposal** — per object (Shield orgs) or retention-window confirmation (non-Shield).
7. **Impact assessment** — storage, SOQL, page-layout changes.
8. **Metadata stubs** — fenced XML for any `HistoryRetentionPolicy` proposals and for the layout / object metadata snippets reflecting tracked-field changes.
9. **Process Observations**:
   - **What was healthy** — clear tracking on compliance-critical fields, regular archival Flow runs, page layouts showing History lists.
   - **What was concerning** — formula/roll-up fields tracked (an old anti-pattern), Shield licensed but never configured with retention policies, `<Object>History` volumes trending toward storage pressure.
   - **What was ambiguous** — regulatory profile not specified by the customer; encrypted fields tracked without explicit design intent.
   - **Suggested follow-up agents** — `security-scanner` (if encrypted-field tracking is observed), `data-model-reviewer` (if dead tracks correlate with retired processes), `sharing-audit-agent` (if History related lists surface data to unintended profiles), `field-impact-analyzer` (before removing any tracking).
10. **Citations**.

---

## Escalation / Refusal Rules

- Org's edition does not support History Tracking at all (rare; Group Edition-level) → `REFUSAL_FEATURE_DISABLED`.
- `shield_available=true` declared but no Shield artifacts detected → `REFUSAL_INPUT_AMBIGUOUS`; clarify.
- Scope has > 50 objects with ≥1 tracked field → return top-30 by `<Object>History` row count + `REFUSAL_OVER_SCOPE_LIMIT`.
- `regulated_profile=hipaa|pci|ferpa` on an org with no Shield license AND no apparent archival pipeline → warn that the org likely does not meet retention requirements and flag the finding at P0.
- `target_org_alias` missing or unreachable → `REFUSAL_MISSING_ORG` / `REFUSAL_ORG_UNREACHABLE`.

---

## What This Agent Does NOT Do

- Does not toggle `trackHistory` on fields.
- Does not create or update `HistoryRetentionPolicy` records.
- Does not purge `<Object>History` or Big Object archives.
- Does not enable Shield / Event Monitoring.
- Does not classify PII — relies on `regulated_profile` + `skills/security/data-classification-labels` guidance.
- Does not auto-chain.
