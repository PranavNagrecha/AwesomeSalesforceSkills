# Gotchas — Einstein Analytics Data Model (XMD)

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: System XMD Is Immutable — PATCH Returns HTTP 400

**What happens:** Practitioners PATCH `xmds/system` expecting to change field labels. The API returns HTTP 400 with no clear error message.

**Impact:** Practitioners conclude the XMD API doesn't work and spend significant time troubleshooting.

**How to avoid:** Always target `xmds/main` for customizations. System XMD is read-only.

---

## Gotcha 2: Main XMD Has No Version History — PATCH Is Destructive

**What happens:** A PATCH immediately overwrites existing values. There is no automatic backup or undo.

**Impact:** A malformed PATCH can corrupt field labels for all users with no recovery path.

**How to avoid:** Always GET and save main XMD JSON to a file before any PATCH operation.

---

## Gotcha 3: WaveXmd Is Not SOQL-Queryable

**What happens:** Developers attempt `SELECT Id FROM WaveXmd`. Throws `INVALID_TYPE: sObject type 'WaveXmd' is not supported`.

**Impact:** Code that queries WaveXmd via SOQL fails at runtime.

**How to avoid:** Use the Wave REST API exclusively for XMD operations. SOQL cannot access CRM Analytics metadata objects.

---

## Gotcha 4: Schema Drift Orphans Main XMD Customizations Silently

**What happens:** A recipe run removes a field from the schema. Main XMD still has the customization but the field no longer exists in system XMD for the new version. No error is thrown.

**Impact:** Fields "disappear" from dashboard components after recipe runs, with no clear failure message.

**How to avoid:** After recipe schema changes, compare system XMD field list against main XMD. Remove orphaned entries.
