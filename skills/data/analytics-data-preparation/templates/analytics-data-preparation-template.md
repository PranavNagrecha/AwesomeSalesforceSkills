# Analytics Data Preparation (XMD) — Work Template

Use this template when updating CRM Analytics dataset XMD metadata or adding external data augmentation to a recipe.

---

## Scope

**Dataset API Name:** _______________
**Dataset ID:** _______________
**Task:** [ ] XMD field label/format update  [ ] External CSV augmentation  [ ] Dimension/measure reclassification

---

## XMD Update

**Pre-PATCH backup:**
- [ ] `GET /wave/datasets/{id}/xmds/main` executed
- [ ] Response saved to: _______________

**Fields to update:**

| Field API Name | Change Type | New Value |
|---|---|---|
| | | |

**PATCH endpoint:** `PATCH /wave/datasets/{id}/xmds/main`

---

## External Augmentation

**CSV file name:** _______________
**Salesforce File ContentDocumentId:** _______________
**Join key field (in primary dataset):** _______________
**Join key field (in CSV):** _______________
**Join type:** [ ] Left outer  [ ] Inner

**CSV refresh process:** _______________

---

## Validation

- [ ] HTTP 200 confirmed (XMD)
- [ ] Labels visible in Analytics Studio lens
- [ ] Augment node join key verified same data type in both sources
