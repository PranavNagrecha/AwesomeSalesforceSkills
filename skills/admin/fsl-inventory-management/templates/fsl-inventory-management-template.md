# FSL Inventory Management — Configuration Checklist

Use this template when configuring or reviewing FSL Inventory Management in an org.

---

## Scope

**Skill:** `fsl-inventory-management`

**Request summary:** (fill in what the user asked for — e.g., "Set up van stock and replenishment for 30 technicians", "Diagnose why QuantityOnHand is wrong on van ProductItems", "Build cycle count reconciliation process")

---

## Context Gathered

Record the answers to the Before Starting questions from SKILL.md here.

- FSL package installed and Field Service enabled? (Yes / No):
- Location records exist for all stocking points? (Yes / No / List gaps):
- Van/truck Location records have `IsMobile = true`? (Yes / No / Partial):
- ProductItem records exist for all Product2/Location combinations? (Yes / No / Partial):
- ProductItemTransaction records intact and untouched by custom DML? (Yes / No / Unknown):
- Replenishment trigger: (Manual / Threshold automation / Work Order completion / Other):
- Mobile technicians need offline inventory access? (Yes / No):

---

## Inventory Object Inventory

| Object | Records Exist? | Notes |
|---|---|---|
| Location (warehouses) | | |
| Location (vans — IsMobile = true) | | |
| ProductItem (warehouse) | | |
| ProductItem (van) | | |
| ProductTransfer (open/in-transit) | | Count of transfers NOT yet marked Received |
| ProductRequest (open) | | |
| ProductConsumed (recent WOs) | | |

---

## Location Records

| Location Name | Type | IsMobile | ProductItems Count | Notes |
|---|---|---|---|---|
| | | | | |
| | | | | |
| | | | | |

---

## Replenishment Workflow

| Step | Responsible Role | Automated? | Notes |
|---|---|---|---|
| Identify low stock | | | |
| Create ProductRequest | | | |
| Create ProductRequestLineItem(s) | | | |
| Create ProductTransfer | | | |
| Mark ProductTransfer Received | | | |
| Verify QuantityOnHand updated | | | |

---

## Parts Consumption Workflow (Work Order)

| Step | Responsible Role | Notes |
|---|---|---|
| Identify parts used on WO | | |
| Create ProductConsumed record | | |
| Verify QuantityOnHand decremented on van ProductItem | | |
| Verify ProductItemTransaction record created | | |

---

## Cycle Count Process

*(Complete only if physical inventory reconciliation is required)*

| Item | Detail |
|---|---|
| Cycle count frequency | |
| Custom solution type | Screen Flow / LWC / External App / Not yet built |
| Adjustment mechanism | Adjusting ProductTransfer to "Inventory Adjustment" Location |
| Audit log approach | Custom object / Notes field on ProductTransfer / Not defined |

---

## Approach

Which pattern from SKILL.md applies?

- [ ] Van Stock Replenishment via ProductRequest and ProductTransfer
- [ ] Recording Parts Consumption on a Work Order
- [ ] Custom Cycle Count Reconciliation
- [ ] Other (describe):

---

## Review Checklist

- [ ] All van/truck Location records have `IsMobile = true`
- [ ] ProductItem records exist for every Product2/Location combination that technicians stock or consume
- [ ] Opening QuantityOnHand was set via ProductTransfer (Received), not via direct field edit
- [ ] ProductItemTransaction records exist and match expected audit history for all tested ProductItems
- [ ] ProductConsumed on Work Orders decrements the correct ProductItem QuantityOnHand
- [ ] ProductTransfer QuantityOnHand update fires on Received status, not on creation
- [ ] No custom Apex, Flow, or Data Loader jobs directly write to QuantityOnHand or ProductItemTransaction
- [ ] Replenishment workflow (ProductRequest → ProductTransfer → Received) has been end-to-end tested
- [ ] Cycle count process documented if physical inventory reconciliation is a business requirement

---

## Notes

Record any deviations from the standard pattern and why, plus any open questions for the client.

- 
- 
