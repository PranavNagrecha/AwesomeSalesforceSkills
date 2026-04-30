# Classic Email Template Migration — Work Template

Use this template when planning and executing the migration of Classic email templates to Lightning Email Templates.

---

## Scope

**Skill:** `classic-email-template-migration`

**Template count by type:**

```sql
SELECT TemplateType, COUNT(Id) cnt FROM EmailTemplate WHERE UiType='Aloha' GROUP BY TemplateType
```

| TemplateType | Count |
|---|---|
| text | |
| html | |
| custom | |
| visualforce | |

---

## Per-Template Decision Matrix

| Template Name | Type | Decision | Lightning Equivalent | OWA Sender |
|---|---|---|---|---|
| | text | Migrate | Lightning text template | |
| | html | Migrate | Lightning + Enhanced Letterhead | |
| | custom | Migrate | Lightning HTML | |
| | visualforce | Retain VF | n/a | |

Decision values: `Migrate`, `Retain VF`, `Retire (no replacement)`.

---

## Brand / Letterhead Plan

| Enhanced Letterhead Name | Used By Templates | Header Image URL | Footer Image URL |
|---|---|---|---|
| Corporate | (list) | | |
| Transactional / No-reply | (list) | | |

---

## Merge Field Audit

For each template body, find non-translatable patterns:

```bash
# Pseudocode — adapt to your retrieval mechanism
for template in classic_templates:
    if '{!IF(' in body or '{!CASE(' in body:
        flag('Conditional logic — pre-compute on a record formula field')
    if '{!$Setup.' in body:
        flag('Custom Setting merge — surface via record field instead')
    if '{!System.' in body:
        flag('System merge — no Lightning equivalent')
```

| Template | Pattern Found | Mitigation |
|---|---|---|
| | | |

---

## Migration Map

| Old (Classic) ID | Old DeveloperName | New (Lightning) ID | New DeveloperName | Status |
|---|---|---|---|---|
| | | | | |

Persist this in a `Email_Template_Migration_Map__c` custom object for ongoing audit.

---

## Downstream Consumer Audit

| Consumer Type | Count Referencing Old Templates | Update Mechanism | Verified |
|---|---|---|---|
| Email Alerts (`WorkflowAlert.TemplateId`) | | Metadata API bulk | [ ] |
| Flows (`Send Email` action) | | Flow XML edit | [ ] |
| Process Builder | | Migrate to Flow first | [ ] |
| Apex `setTemplateId()` | | Code change | [ ] |
| Approval Process emails | | Approval XML edit | [ ] |
| External marketing tools | | External integration update | [ ] |

---

## Sign-Off Checklist

- [ ] All Classic templates have decision: Migrated / Retained VF / Retired
- [ ] Enhanced Letterhead(s) tested in Outlook + Gmail + Apple Mail
- [ ] Merge field translation completed; non-translatable patterns mitigated
- [ ] Folder structure replicated with sharing
- [ ] Email Alerts updated via Metadata API; verification SOQL returns zero references to old IDs
- [ ] OrgWideEmailAddress sender pairings re-set on each downstream consumer
- [ ] Test send completed for each Email Alert
- [ ] Classic templates set to `IsActive=false` (not deleted) post-verification
