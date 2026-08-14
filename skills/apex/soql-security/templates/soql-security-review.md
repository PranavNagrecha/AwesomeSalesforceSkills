# SOQL Security Review — [ClassName]

## Review Metadata

| Property | Value |
|----------|-------|
| **Class Name** | TODO |
| **Class Type** | TODO: @AuraEnabled / REST / Batch / Trigger Handler / Service |
| **`apiVersion`** | TODO: from the `.cls-meta.xml`, not the org's release — it decides the default access mode and which idioms compile |
| **Sharing Model** | TODO: `with sharing` / `without sharing` / `inherited sharing` (no keyword = without sharing at ≤ 66.0, with sharing at 67.0+) |
| **Reviewed By** | TODO |
| **Date** | TODO: YYYY-MM-DD |

---

## Injection Findings

| Line | Code Pattern | Risk | Remediation |
|------|-------------|------|-------------|
| TODO | `Database.query('...' + userVar)` | HIGH | Replace with bind variable |
| TODO | `ORDER BY ' + sortParam` | HIGH | Implement allowlist |
| TODO | None found | — | — |

---

## FLS / CRUD Findings

| Line | Method / Query | Issue | Remediation |
|------|---------------|-------|-------------|
| TODO | `@AuraEnabled` query without `WITH USER_MODE` | Medium (≤ 66.0; at 67.0+ user mode is already the default) | Add `WITH USER_MODE` |
| TODO | DML without `stripInaccessible` | Medium | Wrap in `stripInaccessible(UPDATABLE)` |
| TODO | None found | — | — |

---

## Sharing Model Assessment

| Finding | Detail |
|---------|--------|
| Class declared | `with sharing` / `without sharing` / `inherited sharing` |
| Is `without sharing` intentional? | TODO: Yes/No — reason: |
| Calls into `without sharing` classes? | TODO: List class names |

---

## Dynamic SOQL Inventory

List every `Database.query()` call:

| Line | Query String | User-Controlled Variables? | Allowlist in Place? |
|------|-------------|--------------------------|-------------------|
| TODO | TODO | Yes / No | Yes / No / N/A |

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
| TODO | TODO | TODO |
