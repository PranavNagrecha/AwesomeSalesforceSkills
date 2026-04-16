# Einstein Analytics Data Model (XMD) — Work Template

Use this template when updating CRM Analytics dataset field metadata via the XMD REST API.

---

## Scope

**Dataset API Name:** _______________
**Dataset ID:** _______________
**Change type:** [ ] Field label rename  [ ] Format change  [ ] Dimension/measure reclassification
**Scope:** [ ] Org-wide (main XMD)  [ ] Personal (user XMD)

---

## Pre-Change Backup

- [ ] `GET /wave/datasets/{id}/xmds/main` executed
- [ ] Response saved to: `xmd-backup-{dataset}-{date}.json`

---

## Fields to Update

| Field API Name | Current Label | New Label | Current Classification | New Classification |
|---|---|---|---|---|
| | | | | |

---

## PATCH Payload

```json
{
  "dimensions": [],
  "measures": []
}
```

---

## Post-PATCH Validation

- [ ] HTTP 200 confirmed
- [ ] Field label verified in Analytics Studio lens
- [ ] No fields orphaned by this change
