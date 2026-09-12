# Case visibility model — M2-S05

Filled from `skills/admin/sharing-and-visibility/templates/sharing-model-template.md`, one object
per copy. Built by `agents/metadata-builder` under `agents/build-step-runner`. Nothing here was
deployed.

**The one sentence this document exists for:** a Tier 1 agent cannot open a Billing case because
`Case` carries `<sharingModel>Private</sharingModel>` in
`artefacts/M1-S01/objects/Case/Case.object-meta.xml`, which grants a non-owner nothing, and the
only sharing rule in this build — `Support_Cases_To_Tier_2` in
`artefacts/M2-S05/sharingRules/Case.sharingRules-meta.xml` — matches `RecordTypeId equals Support`
and shares to `Support_Tier_2`, so no rule names the Billing record type or the `Billing_Team`
group as a target and nothing lifts a Billing case above the Private default for Tier 1.

---

## Object Overview

| Property | Value |
|----------|-------|
| Object (API name) | `Case` (standard) |
| Data sensitivity | High for the Billing record type (finance queries), Medium for Support — assumption A1 |
| Business owner | Process owner (support operations) |
| Admin owner | Security architect (this step), CRM admin lead (groups, M2-S04) |
| Internal users only? | Yes — customer portal is out of scope in `requirement.md` |
| External users involved? | No. `externalSharingModel` is `Private` on `Case.object-meta.xml` anyway |
| Master-detail child? | No. `Case` has an Owner field, a `CaseShare` table, queues and sharing rules |

## Baseline Access

| Layer | Design | File |
|-------|--------|------|
| Object access (CRUD) | `Case_Agent_Core`, `Case_Tier1`, `Case_Tier2`, `Case_Billing`, composed into `PSG_Tier1_Prod` / `PSG_Tier2_Prod` / `PSG_Billing_Prod` | `artefacts/M2-S02/permissionsets/`, `artefacts/M2-S02/permissionsetgroups/` |
| OWD — `sharingModel` | `Private` | `artefacts/M1-S01/objects/Case/Case.object-meta.xml` |
| External OWD — `externalSharingModel` | `Private` | same file |
| Ownership pattern | Intake creates the case under the automated-process / integration identity (`Case_Intake_Integration`, M2-S01), then assignment rules (M3-S04) transfer ownership to `Tier_1_General`, `Tier_2_Engineering` or `Billing` | `artefacts/M2-S04/queues/` |
| Role hierarchy assumptions | **None are made.** No role developer name exists anywhere in this build — not in `requirement.md`, not in the 97 clarifications, not in an upstream artefact. Q13 is deferred, so the model does not lean on inheritance it cannot name. See "Layers deliberately not used" below | `roles/` — no file in this build |

## Sharing Grants

Each row is one deployable grant. `accessLevel` must be strictly more permissive than the OWD
above (`Private`), or the share row is not stored.

| Mechanism | Who gets access (`sharedTo`) | Access level | Why | File |
|-----------|------------------------------|--------------|-----|------|
| Criteria-based rule `Support_Cases_To_Tier_2` | `<group>Support_Tier_2</group>` | `Edit` | Tier 2 works escalated Support cases they do not own (`requirement.md`: "Anything untouched for 8 business hours escalates to Tier 2"). `includeRecordsOwnedByAll` is `true` because intake cases are owned by the automated-process identity until assignment lands | `artefacts/M2-S05/sharingRules/Case.sharingRules-meta.xml` |
| Owner-based rule | — | — | None written. The access this build needs is described by a criterion on the record (`RecordTypeId`), not by who owns it — `standards/decision-trees/sharing-selection.md` Q3, decision D5 | — |
| Team access (Case Teams) | — | — | Rejected in D5's `alternatives_rejected` | — |
| Sharing set (external) | — | — | No external users in scope | — |
| Apex managed sharing | — | — | Rejected in D5. The decision tree's own rule: "Try criteria-based sharing first" | — |
| Manual sharing | — | — | Exception layer only; no standing use, and no reviewer named yet (see Risk Checks) | — |

### How each team actually reaches a case

| Team | Support case | Billing case |
|---|---|---|
| Tier 1 (`Support_Tier_1`) | As **owner** once the assignment rule transfers the case to the `Tier_1_General` queue and a member takes it; queue-owned records are visible to queue members | **No access.** Not the owner, not a queue member for `Billing`, and no sharing rule targets `Billing_Team` or the Billing record type. This is assumption A1 |
| Tier 2 (`Support_Tier_2`) | By the criteria-based rule above (`Edit`), plus ownership via `Tier_2_Engineering` | No access — the rule filters on `RecordTypeId equals Support` |
| Billing (`Billing_Team`) | No standing access — no rule targets them | As **owner**, through the `Billing` queue built in M2-S04. **This is queue ownership, not a sharing rule.** No sharing rule was written for Billing, because A1's conservative reading is about keeping others *out*, and the Billing team's own access already exists through the queue |

## Bypasses and Narrowing

| Grant | Held by | Justification | Reviewed |
|-------|---------|---------------|----------|
| Object `View All` on Case | Nobody | Deliberate. `check_sharing_model.py` scans every profile and permission set in `artefacts/` for `viewAllRecords` / `modifyAllRecords` and reports none | This step |
| Object `Modify All` on Case | Nobody | Same | This step |
| `View All Data` / `Modify All Data` | Nobody in this build's metadata | Same scan, `userPermissions` block | This step |
| Restriction rule | None | Not available on Case: `standards/decision-trees/sharing-selection.md` Q8 lists the eligible objects (custom, external, contract, event, quote, task, time sheet, time sheet entry) and Case is not among them. If Q13 resolves toward *removing* access, the remedy is the OWD and the sharing layer, not a restriction rule | — |

## Layers deliberately not used, and what would change if Q13 came back differently

1. **No `Role` files.** A role hierarchy would grant Billing-case visibility upward automatically,
   which is exactly what A1 says must not happen by accident. More practically: no role name is on
   file, so writing one would be inventing a hierarchy nobody described.
2. **No field-level masking.** Q13 asked whether the Billing restriction is record-level or
   field-level and was **deferred**; A1 takes the record-level reading. If the answer turns out to
   be field-level, this step is **re-planned, not patched** (D5's stated consequence): the OWD
   might relax, this rule set changes, and FLS on the Billing fields becomes the mechanism.
3. **No rule extending Billing cases to Tier 1.** Stated as an absence on purpose — the manual
   acceptance test on this step is ticked by confirming the absence, not by finding a file.

## Risk Checks

- [x] OWD is the most restrictive the business can live with (`Private`), and the one grant (`Edit`) is strictly more permissive than it
- [x] `doesIncludeBosses` is set deliberately on `Support_Tier_2` — `true`, set in M2-S04 and labelled a skill default there. **It widens this grant to everyone above a Tier 2 engineer in the role hierarchy.** With no roles in this build that is currently inert; it stops being inert the day a hierarchy is loaded
- [x] `includeRecordsOwnedByAll` decided per criteria rule: `true`, because the intake identity owns the case first. It **cannot be edited after the rule is created** — changing it means deleting and recreating the rule
- [x] No unnecessary `View All` / `Modify All` anywhere in the build's metadata
- [x] Repeated manual sharing pattern ruled out — there is no existing manual-share practice to replace; this is a greenfield intake build
- [ ] **Public group membership exists in the target org** — it does not. "Members of the public group aren't migrated when you deploy the group type." `Support_Tier_2` deploys empty and this rule then grants nobody anything. The `GroupMember` load is a post-deploy data step, tracked in `artefacts/M2-S04/queue-retirement-runbook.md` § 6
- [ ] Experience Cloud sharing set — not applicable, portal out of scope
- [ ] **Access proved with a `UserRecordAccess` query** — deferred to M5, where a sandbox exists. The query to run is in the deploy-order note
- [x] Troubleshooting path documented for both directions: too much access → check `View All` / `Modify All` and `doesIncludeBosses` before the rule; too little → check group membership before the rule

## Verification a human runs after deploy

Not run by any agent in this loop. Both queries are copied from
`skills/admin/sharing-and-visibility/references/metadata-examples.md` § 7.

```sql
-- 1. Does a Tier 1 agent actually have no access to a Billing case?
SELECT RecordId, HasReadAccess, HasEditAccess, MaxAccessLevel
FROM UserRecordAccess
WHERE UserId = '<a Tier 1 agent user id>'
  AND RecordId = '<a Billing case id>'
-- Expect MaxAccessLevel = None.

-- 2. Why does a Tier 2 engineer have access to a Support case?
SELECT Id, CaseId, UserOrGroupId, CaseAccessLevel, RowCause
FROM CaseShare
WHERE CaseId = '<a Support case id>'
-- Expect a row with RowCause = 'Rule' for the Support_Tier_2 group.
```

Two documented limits on that evidence, both of which look like bugs if you do not expect them:
`UserRecordAccess` reports **pre-restriction-rule** access and caps at **200 ids**; and an empty
share table does not prove there is no access, because `ImplicitChild` rows are not returned once
faster account sharing recalculation is on. Query 1 is the authority on *whether*; query 2 only
explains *why*.
