# Territory Design Requirements — Work Template

Use this template when gathering and documenting requirements for a Salesforce Enterprise Territory Management (ETM) territory model design. Complete all sections before handing off to `admin/enterprise-territory-management` for configuration.

This is the prose half of the package. The machine-lintable half is `templates/territory-design.yaml` — fill both, and run `python3 scripts/check_territory_design_requirements.py --file territory-design.yaml` before sign-off. A worked pair is in `references/worked-examples.md`.

---

## Scope

**Project / Request:** (describe the business context — new model, redesign, expansion)

**Go-to-Market Motion:** (Geographic | Named Account | Industry Overlay | Hybrid)

**Salesforce Edition:** (Enterprise | Performance | Unlimited — affects territory limit)

**Territory-Based Forecasting Required:** (Yes | No)

---

## Team and Account Inventory

| Metric | Value |
|---|---|
| Total active sales users requiring territory coverage | |
| Total active accounts in org | |
| Accounts with reliable BillingState/BillingCountry populated | |
| Accounts with no billing location data | |
| Named accounts to be managed separately (if applicable) | |
| Expected territory count (initial design) | |
| User-to-territory ratio (territory count divided by user count) | |

**Ratio flag:** Territories divided by active users. The ~3 target is a field heuristic, not a documented Salesforce figure (UNVERIFIED 2026-09-05) — treat an outlier as a prompt to check the two numbers that decide: **accounts per leaf territory** and **users per leaf territory**. Record all three.

---

## Coverage Model Selection

**Primary coverage model type:** (Geographic | Named Account | Hybrid)

**Overlay model required:** (Yes | No — if Yes, describe below)

**Overlay description:** (e.g., Industry Overlay for Healthcare vertical across all geo territories)

**Rationale:** (why this coverage model fits the go-to-market motion)

---

## Territory Hierarchy Design

**Proposed hierarchy depth:** (number of levels — the test is a named forecast reader per level, not a number; the "3-5 levels" figure is UNVERIFIED 2026-09-05)

**Hierarchy levels:**

| Level | Name | Example Node | Purpose / Forecast Consumer |
|---|---|---|---|
| 1 | (e.g., National) | (e.g., United States) | (e.g., VP of Sales forecast rollup) |
| 2 | (e.g., Region) | (e.g., US West) | (e.g., Regional VP forecast rollup) |
| 3 | (e.g., Rep Territory) | (e.g., California) | (e.g., Individual rep coverage) |

**Independence from role hierarchy confirmed:** (Yes | No — note any intentional alignment)

---

## Territory Types

| Territory Type Name | Priority Value | Coverage Purpose |
|---|---|---|
| (e.g., Geographic) | (e.g., 20) | (e.g., Primary geographic coverage) |
| (e.g., Industry Overlay) | (e.g., 30) | (e.g., Healthcare vertical access) |
| (e.g., Named Account) | (e.g., 40) | (e.g., Strategic account overlay — wins OTA) |

**Priority values:** the **HIGHEST** integer wins Opportunity Territory Assignment, and every type's integer must be unique — "The account-assigned territory whose territory type priority is highest is then assigned to the opportunity. The `priority` field value on each territory type must be unique" (Metadata API Developer Guide, `Territory2Type` › `priority`). Space the integers by 10 so a type can be inserted later without renumbering.

**Same-type tie check:** two territories of the *same* type on one account assign **no** territory to the opportunity at all. State here how that is prevented:

| Type | Can one account land in two territories of this type? | How it is prevented |
|---|---|---|
| (e.g., Named Account) | (Yes / No) | (e.g., one book per account, enforced by the flag field + a monthly review) |

---

## Assignment Rule Criteria

For each rule, document the criteria. Verify:
- Every field is a real Account field, by API name, with a known population rate
- Every operation is in the documented enum: `equals`, `notEqual`, `lessThan`, `greaterThan`, `lessOrEqual`, `greaterOrEqual`, `contains`, `notContain`, `startsWith`, `includes`, `excludes`, `within` (DISTANCE criteria only)
- Criteria at the same hierarchy level are mutually exclusive for primary coverage
- **No rule has more than 10 rule items** — "A territory rule can have up to 10 rule items" (Metadata API Developer Guide, `Territory2Rule` › Usage). This is a hard ceiling on the rule, not a performance guideline
- Item order is positional, and any `booleanFilter` numbering "must start at 1 and must be contiguous"

| Rule name | Territories served | Field | Operation | Value | `booleanFilter` | Items | Inherited? |
|---|---|---|---|---|---|---|---|
| (e.g., US_West_CA_Rule) | (US West - California) | BillingState | equals | CA | — | 1 | false |
| (e.g., US_West_PNW_Rule) | (US West - Pacific NW) | BillingState | includes | OR;WA;AK;HI | — | 1 | false |
| ... | | | | | | | |

`Inherited?` is `ruleAssociations.inherited` on the territory: true flows the rule to descendant territories, false keeps it local. A rule with no territory in the second column deploys cleanly and assigns nothing.

**Criteria audit:**

- [ ] Every criteria field confirmed to exist on Account, by API name, with its population rate recorded
- [ ] Every operation is in the documented enum
- [ ] No rule exceeds 10 rule items
- [ ] Date-based segmentation, if requested, is replaced by a derived picklist — a date predicate is only as fresh as the last record edit or the last manual rule run. (Whether ETM rejects Date fields outright is UNVERIFIED 2026-09-05; see `references/gotchas.md` Gotcha 1)

**Date field proxy fields required:**

| Proposed Date Criterion | Proxy Field Name | Field Type | Population Method |
|---|---|---|---|
| (e.g., ContractRenewalDate__c) | (e.g., RenewalQuarter__c) | (e.g., Picklist) | (e.g., Flow on contract update) |

---

## Catch-All Territory

**Catch-all territory defined:** (Yes | No)

**Catch-all territory name:** (e.g., "Unassigned US")

**Catch-all territory level:** (which hierarchy level — typically top or regional)

**Accounts expected in catch-all:** (estimate and business intent)

---

## Named Account Handling (if applicable)

**Named account list size:** (number of accounts)

**Change frequency:** (Static | Annual | Quarterly | Monthly)

**Assignment method:**

- [ ] Rule-based (exact-match rules) — recommended for static lists only
- [ ] Custom flag field (e.g., IsNamedAccount__c checkbox) with single rule per territory
- [ ] Manual assignment — recommended for frequently-changing lists

**Named account field / mechanism:** (describe the field or process)

---

## Access and Sharing Pre-Conditions

**Current OWD — record all four, they constrain which access values are legal:**

| Object | OWD today | Consequence for the design |
|---|---|---|
| Account | (Public Read/Write \| Private \| Public Read Only) | With Public Read/Write, "valid values are only `Edit` and `All`" for `accountAccessLevel` |
| Opportunity | | Omit `opportunityAccessLevel` if the case/opportunity model is Public Read/Write |
| Contact | | Omit `contactAccessLevel` if the model is Public Read/Write or Controlled By Parent |
| Case | | Omit `caseAccessLevel` if the case/opportunity model is Public Read/Write |

**Per-territory access decisions (Metadata API spelling, not Setup labels):**

| Territory | `accountAccessLevel` (Read/Edit/All) | `opportunityAccessLevel` (None/Read/Edit) | `caseAccessLevel` | `contactAccessLevel` |
|---|---|---|---|---|
| | | | | |

**Note:** ETM access is additive — a territory grants access to records "that are assigned to this territory and are otherwise inaccessible" (`Territory2` › `accountAccessLevel`). If reps must be restricted to territory accounts only, Account OWD must be Private. Document this as a pre-condition for `admin/sharing-and-visibility`.

**Access restriction requirement:** (Yes | No)

**If Yes — OWD change required:** (Yes | No — if Yes, raise as a separate sharing-and-visibility workstream)

---

## Territory Limit Check

**Ceiling in effect for this org:** ___ (UNVERIFIED 2026-09-05 — the commonly cited 1,000-per-model figure is not in the Salesforce App Limits Cheat Sheet, the Metadata API guide or the Object Reference. Confirm with Salesforce and record who confirmed it, and when.)

**Confirmed by / on:** ___

**Projected territory count (full build-out):** ___

**Limit increase required:** (Yes | No | Unknown pending confirmation)

**If Yes — Salesforce Support case raised:** (Yes | No | Pending)

---

## Open Decisions and Dependencies

| Decision | Owner | Due Date | Blocking? |
|---|---|---|---|
| (e.g., Confirm named account list) | (Sales Ops) | | Yes |
| (e.g., Confirm BillingState data quality) | (Admin) | | Yes |
| (e.g., ETM territory limit increase) | (Salesforce Support) | | Yes |

---

## Sign-Off Checklist

- [ ] Coverage model type confirmed with sales leadership
- [ ] Every hierarchy level has a named forecast reader; levels without one were removed
- [ ] Every criteria field confirmed to exist on Account with its population rate recorded
- [ ] Every rule operation is in the documented enum, and no rule exceeds 10 rule items
- [ ] Territory type priorities are unique, and the type intended to win OTA carries the highest integer
- [ ] No account can land in two territories of the same type (a tie assigns no territory)
- [ ] Mutual exclusivity of primary coverage criteria verified
- [ ] Named account handling approach agreed, with an owner for the list
- [ ] All four OWDs recorded, and the per-territory access values are legal for them
- [ ] Projected territory count is inside whatever ceiling was confirmed, with the confirmation recorded
- [ ] Coverage ratios recorded: territories/users, accounts per leaf, users per leaf
- [ ] Catch-all territory is defined, with an owner who reviews it
- [ ] Realignment plan names the model states, the rule runner and the cutover date
- [ ] Acceptance tests over `ObjectTerritory2Association` / `UserTerritory2Association` are written
- [ ] `territory-design.yaml` is filled and `python3 scripts/check_territory_design_requirements.py --file territory-design.yaml` reports no ERRORs
- [ ] Release path is a source deploy — Sales Territories components cannot travel in a change set
- [ ] Open decisions are resolved or have owners and dates
- [ ] Requirements document is complete and ready for `admin/enterprise-territory-management`

---

## Notes and Deviations

(Record any deviations from standard patterns, unusual business requirements, or decisions that override default guidance — include the business rationale.)

---

## Realignment Plan

Archiving a territory model is one-way, and a model with the same developer name sitting in `Archived` in the target org blocks a future deploy of that name outright (`Territory2Model` › Usage). Plan the re-cut before the first model is activated.

**Cadence:** (annual | semi-annual | ad hoc)

**Model developer name for this cycle:** (stamp it, e.g. `FY27_Alignment`)

**Cutover date:** ___

**Rule runner (must hold Manage Territories — "Rules can't be run via Metadata API"):** ___

**Rollback position:** (e.g. outgoing model left un-archived until the first forecast period closes)

| When | Step | Owner | Done when |
|---|---|---|---|
| T-28 | Build the new model in `Planning` | | |
| T-21 | Run rules against the Planning model, diff assignments | | |
| T-14 | Load `UserTerritory2Association` | | |
| T-7 | Freeze rule and criteria-field changes | | |
| T-0 | Activate; confirm state reaches `Active`, not `Activation Failed` | | |
| T-0 +2h | Run the acceptance tests | | |
| T+30 | Archive the outgoing model | | |

---

## Acceptance Tests

The queries that prove the build matches this design. Write them here before build starts; `references/worked-examples.md` §7 has the seven that cover a hybrid model.

| # | What it proves | Query | Pass condition |
|---|---|---|---|
| 1 | The rule run finished | `SELECT Id, Status, StartTime, EndTime, RunAs.Name FROM Territory2AlignmentLog WHERE Territory2ModelId = :modelId ORDER BY StartTime DESC` | A row with an `EndTime` and a terminal status |
| 2 | No same-type double assignment | `SELECT ObjectId, COUNT(Id) FROM ObjectTerritory2Association WHERE SobjectType = 'Account' AND Territory2Id IN :sameTypeIds GROUP BY ObjectId HAVING COUNT(Id) > 1` | Zero rows |
| 3 | Rule vs manual split matches the design | `SELECT AssociationCause, COUNT(Id) FROM ObjectTerritory2Association WHERE SobjectType = 'Account' GROUP BY AssociationCause` | Matches the manual-assignment rows in the design |
| 4 | Membership is populated | `SELECT Territory2Id, COUNT(Id) FROM UserTerritory2Association WHERE IsActive = true GROUP BY Territory2Id` | Every territory that should have members has them |
| 5 | Access materialised | `SELECT RowCause, COUNT(Id) FROM AccountShare WHERE RowCause IN ('Territory', 'Territory2AssociationManual') GROUP BY RowCause` | Both causes present as the design predicts |
