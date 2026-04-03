# SOQL Security Review — [ClassName]

## Review Metadata

| Property | Value |
|----------|-------|
| **Class Name** | TODO |
| **Class Type** | TODO: @AuraEnabled / REST / Batch / Trigger Handler / Service |
| **Sharing Model** | TODO: `with sharing` / `without sharing` / `inherited sharing` |
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
| TODO | `@AuraEnabled` query without `WITH USER_MODE` | Medium | Add `WITH USER_MODE` |
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
- [ ] All `@AuraEnabled` methods use `WITH USER_MODE` or `WITH SECURITY_ENFORCED`
- [ ] All `without sharing` classes have inline comment documenting why system context is required
- [ ] PMD suppression annotations include justification
- [ ] DML in service classes uses `stripInaccessible()` for user-initiated mutations

---

## Sign-Off

| Reviewer | Date | Notes |
|----------|------|-------|
| TODO | TODO | TODO |
