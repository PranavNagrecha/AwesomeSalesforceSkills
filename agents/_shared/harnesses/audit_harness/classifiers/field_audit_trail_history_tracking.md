# Classifier: field_audit_trail_history_tracking

## Purpose

Audit and propose the target configuration for field history tracking and Field Audit Trail (Shield) retention across an org. For every sObject that tracks history, surface the current tracked-field list, gaps vs a regulatory profile, the 20-field-per-object limit pressure, dead tracks (fields that never change or can't usefully be tracked), retention-policy gaps on Shield-enabled orgs, and storage / SOQL impact. Not for enabling Shield, not for purging history, not for classifying PII.

## Replaces

`field-audit-trail-and-history-tracking-governor` (now a deprecation stub pointing at `audit-router --domain field_audit_trail_history_tracking`).

## Inputs

| Input | Required | Example |
|---|---|---|
| `regulated_profile` | no | `none` (default) \| `sox` \| `hipaa` \| `gdpr` \| `pci` \| `ferpa` |
| `shield_available` | no | `auto` (default — probe) \| `true` \| `false` |
| `scope_objects` | no | comma-separated sObjects; default = every object with `TrackHistory=true` |

## Inventory Probe

1. `describe_org(target_org)` — edition + Shield licensing heuristic.
2. `tooling_query("SELECT EntityDefinition.QualifiedApiName, QualifiedApiName, DataType, Length, TrackHistory FROM FieldDefinition WHERE TrackHistory = true LIMIT 2000")` — tracked fields.
3. Per object with ≥1 tracked field:
   - `tooling_query("SELECT Id, Name FROM EntityDefinition WHERE QualifiedApiName = '<object>'")` — confirm enable-history posture.
   - `tooling_query("SELECT COUNT() FROM <object>History")` — storage pressure.
4. Shield posture: probe `FieldHistoryArchive` records if present; where discoverable, enumerate `HistoryRetentionPolicy` per object.
5. Change-volume sample: `tooling_query("SELECT COUNT() FROM <object>History WHERE CreatedDate = LAST_N_DAYS:180 AND Field = '<field>'")` for each tracked field (sampled on large objects).

Inventory columns (beyond id/name/active): `field_count_tracked`, `field_count_limit` (20 or 60 w/ Shield), `object_history_row_count`, `has_retention_policy`, `regulatory_floor_met`.

## Rule Table

| code | severity | check | evidence_shape | suggested_fix |
|---|---|---|---|---|
| `FAT_REGULATORY_GAP` | P1 | `regulated_profile` floor not met for at least one required field on this object | object + profile + missing fields | Add tracking on the required fields (if under 20-field cap) |
| `FAT_NONSHIELD_REGULATED` | P0 | `regulated_profile` in {hipaa, pci, ferpa} AND no Shield license AND no archival pipeline detected | org + profile | Org likely does not meet retention requirements — compliance review required |
| `FAT_FIELD_LIMIT_SATURATION` | P1 | Object at 19 or 20 tracked fields (no headroom for next compliance ask) | object + current count | Retire a dead track OR schedule Shield enablement to lift cap |
| `FAT_FIELD_LIMIT_VIOLATION` | P0 | Object > 20 tracked fields (shouldn't be possible; schema drift) | object + count | Hard untracking required |
| `FAT_LONG_TEXT_TRACKED` | P2 | Long Text Area or Rich Text tracked (history truncates, doesn't capture clean diff) | field + data type | Untrack; document alternative (audit log via Apex) |
| `FAT_FORMULA_TRACKED` | P2 | Formula field tracked (fires only when referenced field changes) | field | Untrack formula; track the referenced field instead |
| `FAT_ROLLUP_TRACKED` | P2 | Roll-up summary field tracked | field | Untrack; same reasoning as formula |
| `FAT_AUTO_NUMBER_TRACKED` | P2 | Auto Number field tracked (never changes post-insert) | field | Untrack dead track |
| `FAT_SYSTEM_FIELD_TRACKED` | P2 | `LastModifiedDate` / similar system field tracked (redundant with the field itself) | field | Untrack |
| `FAT_DEAD_TRACK` | P2 | Tracked field has zero changes in last 180 days across > 1000 records | field + change count | Untrack on next cleanup |
| `FAT_ENCRYPTED_UNDOCUMENTED` | P1 | Encrypted (Shield Platform Encryption) field tracked but intent not documented | field | Document the intent OR untrack — history won't contain clear values |
| `FAT_NO_RETENTION_POLICY` | P1 | Shield enabled but object has no `HistoryRetentionPolicy` despite significant `<Object>History` volume | object + history row count | Create retention policy per `skills/security/field-audit-trail` |
| `FAT_ARCHIVE_PIPELINE_STALE` | P1 | Custom `FieldHistoryArchive__b` Flow/Apex job hasn't completed successfully in > 30 days | last job run + object | Investigate pipeline health |

## Patches

### FAT_DEAD_TRACK / FAT_FIELD_LIMIT_SATURATION patch template

Generate a field-metadata delta turning `trackHistory` off for the dead field. Cites `skills/data/field-history-tracking`.

```xml
<!-- target: force-app/main/default/objects/{Object}/fields/{Field}.field-meta.xml -->
<!-- addresses: FAT_DEAD_TRACK on {Object}.{Field} -->
<!-- cites: skills/data/field-history-tracking -->
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>{Field}</fullName>
    <trackHistory>false</trackHistory>
    <!-- preserve all other field attributes; only trackHistory changes -->
</CustomField>
```

### FAT_NO_RETENTION_POLICY patch template

Emit the `HistoryRetentionPolicy` stub for Shield orgs. Cites `skills/security/field-audit-trail`.

```xml
<!-- target: force-app/main/default/objects/{Object}/historyRetentionPolicies/{PolicyName}.historyRetentionPolicy-meta.xml -->
<!-- addresses: FAT_NO_RETENTION_POLICY on {Object} -->
<!-- cites: skills/security/field-audit-trail -->
<HistoryRetentionPolicy xmlns="http://soap.sforce.com/2006/04/metadata">
    <archiveAfterMonths>{retain_months}</archiveAfterMonths>
    <archiveRetentionYears>{archive_years}</archiveRetentionYears>
    <description>Retention for {Object} per {regulated_profile} policy</description>
</HistoryRetentionPolicy>
```

## Mandatory Reads

- `skills/data/field-history-tracking`
- `skills/security/field-audit-trail`
- `skills/admin/system-field-behavior-and-audit`
- `skills/security/data-classification-labels`
- `skills/data/data-archival-strategies`
- `skills/security/org-hardening-and-baseline-config`

## Escalation / Refusal Rules

- Org edition lacks History Tracking entirely (Group Edition) → `REFUSAL_FEATURE_DISABLED`.
- `shield_available=true` declared but no Shield artifacts detected → `REFUSAL_INPUT_AMBIGUOUS`.
- Scope has > 50 objects with ≥1 tracked field → top-30 by `<Object>History` row count + `REFUSAL_OVER_SCOPE_LIMIT`.
- `regulated_profile=hipaa|pci|ferpa` + no Shield + no archival pipeline → `FAT_NONSHIELD_REGULATED` P0; full audit still runs.

## What This Classifier Does NOT Do

- Does not toggle `trackHistory` on fields.
- Does not create / update `HistoryRetentionPolicy` records.
- Does not purge `<Object>History` or Big Object archives.
- Does not enable Shield or Event Monitoring.
- Does not classify PII — depends on `regulated_profile` input.
