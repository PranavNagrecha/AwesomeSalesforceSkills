# Mock deploy — milestone M2 in progress (validation only, nothing deployed)

## Run 1 — 2026-09-11, source mode, M1-S01 + M1-S02 + M2-S01..M2-S04 as built

`python3 scripts/mock_deploy.py plan.json --org-alias sfskills-dev --step M1-S01 --step M1-S02 --step M2-S01 --step M2-S02 --step M2-S03 --step M2-S04`

**Failed — 30 components, 21 ok, 10 errors.** All 12 M1 components, the M2-S01 custom permission and permission set,
and the M2-S04 queues and groups validate. The failures:

| Component | Error |
|---|---|
| PermissionSet ×4 (Case_Agent_Core, Case_Tier1, Case_Tier2, Case_Billing) | `Description: data value too large … (max length=255)` |
| Profile ×3 (Acme Support Tier 1 / Tier 2 / Billing) | `Description: data value too large … (max length=255)` |
| PermissionSetGroup ×3 | `permission set names are invalid` — cascade from the four permission-set failures |

**F-15 (HIGH, new).** `PermissionSet.description` and `Profile.description` are limited to 255 characters. The builders
wrote 300–450-character rationales into the description element, following the cited skills' examples, which carry
long descriptions and no length rule. M2-S01's permission set (244 chars) passed by luck. No checker enforces the limit.
Remedy: the cited skills (`admin/permission-set-architecture`, `admin/permission-sets-vs-profiles`, the profile owner)
get a 255-char rule in their examples and checkers; rationale moves to `deploy-order.md`; M2-S02 and M2-S03 are rebuilt.

## Run 2 — 2026-09-11, source mode, same six steps after the F-15 rebuilds

After the three access skills gained DESC-01/02 rules (4da8e6c92) and M2-S02 / M2-S03 were rebuilt with descriptions
under 200 characters (everything else byte-identical, hashes in each step's `deploy-order.md`):

**Succeeded — 30 components, 0 errors.** F-15 closed at the source and proven by the org. Every M1 and M2 artefact
built so far (object model, layouts, custom permission, 5 permission sets, 3 PSGs, 3 profiles, 3 queues, 3 groups)
validates unmodified.

## Run 3 — 2026-09-11, source mode, M1 + all five M2 steps

`python3 scripts/mock_deploy.py plan.json --org-alias sfskills-dev --step M1-S01 --step M1-S02 --step M2-S01 --step M2-S02 --step M2-S03 --step M2-S04 --step M2-S05`

**Succeeded — 32 components, 0 errors.** The M2-S05 sharing rule (`SharingCriteriaRule Case.Support_Cases_To_Tier_2`,
criteria `RecordTypeId equals Support` in bare developer-name form) validated — the value format the builder marked
as its likeliest failure did not fail validation. Every artefact of milestones 1 and 2 validates unmodified.
