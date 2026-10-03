# SOQL Security Review — [ClassName]

## Review Metadata

| Property | Value |
|----------|-------|
| **Class Name** | <fill in> |
| **Class Type** | <fill in> @AuraEnabled / REST / Batch / Trigger Handler / Service |
| **`apiVersion`** | <fill in> from the `.cls-meta.xml`, not the org's release, it decides the default access mode and which idioms compile |
| **Sharing Model** | <fill in> `with sharing` / `without sharing` / `inherited sharing` (no keyword at 66.0 and earlier: with sharing for an Aura controller or an @AuraEnabled method called from LWC, the caller's mode for a non-entry-point class, otherwise without sharing; with sharing at 67.0+) |
| **Reviewed By** | <fill in> |
| **Date** | <fill in> YYYY-MM-DD |

---

## Injection Findings

| Line | Code Pattern | Risk | Remediation |
|------|-------------|------|-------------|
| <fill in> | `Database.query('...' + userVar)` | HIGH | Replace with bind variable |
| <fill in> | `ORDER BY ' + sortParam` | HIGH | Implement allowlist |
| <fill in> | None found | n/a | n/a |

---

## FLS / CRUD Findings

| Line | Method / Query | Issue | Remediation |
|------|---------------|-------|-------------|
| <fill in> | `@AuraEnabled` query without `WITH USER_MODE` | Medium (≤ 66.0; at 67.0+ user mode is already the default) | Add `WITH USER_MODE` |
| <fill in> | DML without `stripInaccessible` | Medium | Wrap in `stripInaccessible(UPDATABLE)` |
| <fill in> | None found | n/a | n/a |

---

## Sharing Model Assessment

| Finding | Detail |
|---------|--------|
| Class declared | `with sharing` / `without sharing` / `inherited sharing` |
| Is `without sharing` intentional? | <fill in> Yes/No, reason: |
| Calls into `without sharing` classes? | <fill in> List class names |

---

## Dynamic SOQL Inventory

List every `Database.query()` call:

| Line | Query String | User-Controlled Variables? | Allowlist in Place? |
|------|-------------|--------------------------|-------------------|
| <fill in> | <fill in> | Yes / No | Yes / No / N/A |

---

## Remediation Checklist

- [ ] All `Database.query()` calls use bind variables for user-controlled values
- [ ] All `ORDER BY`, `LIMIT`, field name, and object name dynamic values validated against allowlist
- [ ] All `@AuraEnabled` methods use `WITH USER_MODE` (no `WITH SECURITY_ENFORCED` — legacy below `apiVersion` 67.0, a compile failure at or above it)
- [ ] All `without sharing` classes have inline comment documenting why system context is required
- [ ] PMD suppression annotations include justification
- [ ] DML in service classes uses `stripInaccessible()` for user-initiated mutations

---

## Sign-Off

| Reviewer | Date | Notes |
|----------|------|-------|
| <fill in> | <fill in> | <fill in> |
