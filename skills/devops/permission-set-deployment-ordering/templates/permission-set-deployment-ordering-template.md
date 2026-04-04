# Permission Set Deployment Ordering — Work Template

Use this template when planning a deployment that includes permission sets or permission set groups.

## Scope

**Skill:** `permission-set-deployment-ordering`

**Request summary:** (describe what needs to be deployed and to which target org)

## Context Gathered

- **Target org:** (production / full sandbox / partial sandbox / scratch org)
- **Permission sets being deployed:** (list each PS name)
- **Permission set groups being deployed:** (list each PSG name)
- **Constituent PSets for each PSG:** (list which PSets each PSG contains)
- **Connected apps in same batch:** (yes / no — if yes, list them)
- **Do these PSets already exist in the target org?** (yes / no / some)

## Deployment Sequence Plan

### Stage 1 — Prerequisites (custom objects, fields, Apex classes)
Metadata to deploy first:
- [ ] (list object and field metadata that must exist before PSets)

### Stage 2 — Constituent Permission Sets
Permission sets to deploy before any PSG:
- [ ] PermissionSet: ___
- [ ] PermissionSet: ___

### Stage 3 — Permission Set Groups
PSGs that depend on Stage 2:
- [ ] PermissionSetGroup: ___

### Stage 4 — Connected App (if applicable, deploy before PSets referencing it)
> Note: if a ConnectedApp is being deployed AND a PS references it, deploy the ConnectedApp in this stage and move the PS to Stage 5.
- [ ] ConnectedApp: ___

### Stage 5 — Permission Sets referencing Connected Apps (if split required)
- [ ] PermissionSet: ___ (references ConnectedApp from Stage 4)

## Retrieve-First Checklist

For each PS or PSG that already exists in the target org:

- [ ] Retrieved current state: `sf project retrieve start --metadata "PermissionSet:<name>" --target-org <alias>`
- [ ] Verified no permissions will be removed by comparing retrieved XML to deploy XML
- [ ] Merged new permissions into retrieved XML baseline

## Post-Deploy Verification

- [ ] Retrieved deployed PSets from target org and confirmed expected permissions are present
- [ ] Verified PSG membership is correct in target org
- [ ] Verified no field-level security grants were silently removed

## Notes

(Record any deviations from the standard pattern and why)
