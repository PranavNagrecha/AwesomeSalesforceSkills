---
name: territory-design-requirements
description: "Requirements for a Salesforce Enterprise Territory Management (ETM) territory design: alignment criteria, coverage model selection, assignment rule logic, hierarchy depth and breadth, and user-to-territory ratios. Trigger keywords: territory design, territory alignment, territory model requirements, sales coverage model, territory criteria, geographic territory, named account territory, overlay territory. NOT for ETM setup steps — use admin/enterprise-territory-management. NOT for loading territory assignment data — use data/territory-data-alignment. Trigger keywords: territory design questionnaire, territory requirements document, assignment rule matrix, territory type priority, realignment plan, territory access level decision, accountAccessLevel, opportunityAccessLevel, ObjectTerritory2Association, UserTerritory2Association, Planning state model, territory acceptance tests."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Scalability
  - Operational Excellence
triggers:
  - "how should we design our territory structure before we configure ETM"
  - "what are the requirements for building a good territory model for our sales team"
  - "we need to decide whether to use geographic territories or named account territories"
  - "how many territories should we create and how deep should the hierarchy be"
  - "what information do I need to gather before setting up territory management"
  - "our territory alignment criteria need to be documented before implementation"
  - "territory alignment isn't working"
  - "we're having issues with territory alignment"
  - "which territory type priority wins when an account is in a geo and a named-account territory"
  - "how many rule items can one territory assignment rule have"
  - "write the territory design requirements document before we build the model"
  - "sales wants to segment territories by renewal date - can assignment rules do that"
  - "plan next year's territory realignment without breaking the forecast"
  - "decide the account and opportunity access levels for each territory"
  - "build the assignment rule matrix for a B2B SaaS coverage model"
  - "our overlay reps need access to accounts they do not own"
  - "how do we prove the territory build matches the signed-off design"
tags:
  - territory-design
  - territory-alignment
  - coverage-model
  - sales-territories
  - assignment-rules
  - etm
  - requirements
inputs:
  - go-to-market motion (geographic, named account, industry overlay, or hybrid)
  - number of sales reps and managers requiring territory coverage
  - account segmentation criteria (geography, industry, revenue, employee count)
  - existing territory boundaries or coverage maps if redesigning
  - forecast rollup requirements (territory-based vs role-based)
  - org edition (Enterprise, Performance, or Unlimited — affects territory limits)
  - current org-wide defaults for Account, Opportunity, Contact and Case
  - realignment cadence and the fiscal calendar it must land against
outputs:
  - territory design requirements document capturing alignment criteria and hierarchy shape
  - recommended coverage model type (geographic, named account, overlay, or hybrid)
  - assignment rule criteria list with field-level specifications
  - hierarchy depth and breadth recommendations
  - user-to-territory ratio analysis and recommendations
  - checklist of requirements to hand off to the ETM configuration skill
  - machine-lintable territory-design YAML (territories, types, rules, access levels, realignment plan)
  - acceptance tests as SOQL over ObjectTerritory2Association and UserTerritory2Association
dependencies: []
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-09-05
---

# Territory Design Requirements

This skill activates when a practitioner needs to gather, evaluate, or document the requirements for a Salesforce Enterprise Territory Management (ETM) territory design before configuration begins. It covers alignment criteria selection, coverage model type, assignment rule logic, geographic considerations, hierarchy depth and breadth, per-object access-level decisions, realignment planning, and user-to-territory ratio targets. Use this skill before invoking `admin/enterprise-territory-management` for configuration.

The deliverable is a design that survives contact with the metadata. Every decision below has a field it lands in, and that field is named.

---

## Before Starting

Gather this context before working on anything in this domain:

- **ETM is the target platform.** ETM is not Legacy Territory Management. The metadata types the design must land in are `Territory2Model`, `Territory2Type`, `Territory2`, `Territory2Rule` and `Territory2Settings` (Metadata API Developer Guide). A design expressed only in slide boxes cannot be checked against them.
- **The most common wrong assumption is that territory hierarchy mirrors role hierarchy.** ETM hierarchy is independent of role hierarchy. Territory hierarchy drives the `Territory` and `TerritoryAndSubordinates` sharing groups and territory forecast rollups; role hierarchy drives manager visibility in the standard pipeline. Conflating them produces a structure that has to be re-cut every time the org chart moves.
- **A territory assignment rule holds at most 10 rule items.** "A territory rule can have up to 10 rule items" (Metadata API Developer Guide, `Territory2Rule` › Usage). This is a hard ceiling on the *rule*, not a soft performance guideline — a segmentation that needs an eleventh predicate needs a proxy field on Account instead.
- **Territory type priority: the highest integer wins, and it must be unique.** "The account-assigned territory whose territory type priority is highest is then assigned to the opportunity. The `priority` field value on each territory type must be unique." (`Territory2Type` › `priority`). A tie assigns *no* territory to the opportunity.
- **Territory access is always additive.** Access levels grant users access to records "that are assigned to this territory and are otherwise inaccessible" (`Territory2` › `accountAccessLevel`). ETM cannot restrict below the org-wide default — a design that relies on territories to limit access belongs in `admin/sharing-and-visibility`.
- **Territory count ceilings: UNVERIFIED (2026-09-05).** The commonly cited "1,000 territories per model, higher on request" figure does not appear in the Salesforce App Limits Cheat Sheet (a case-insensitive `grep` for "territor" across it returns zero lines) nor in the `Territory2*` sections of the Metadata API guide or Object Reference. Confirm the current allocation with Salesforce before designing to a ceiling; treat any number you carry into the requirements document as an assumption with an owner.

---

## Questions to Ask Before Configuring

Ask these before writing a single territory name. Each maps to a documented platform behaviour that otherwise surfaces after the model is Active and the recalculation is already running.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Which dimensions actually decide who covers an account — and which are just how you report on it?" | Only a dimension that is a field on Account can become a `Territory2Rule` rule item; a reporting dimension does not need a territory | A short list of real Account fields, separated from the dimensions that belong in a report grouping |
| "For each dimension, name the Account field, its API name, and how populated it is today." | `Territory2RuleItem.field` operates on a standard or custom object field; a null field silently matches nothing and the account lands nowhere | Field API names plus a populated-row count, which sizes the catch-all territory before it is needed |
| "Can one account be covered by two teams at once, and if so is that deliberate?" | An account matching two rules is assigned to both territories, and two territories of the *same* type on one account assign no territory to the opportunity at all | An explicit overlay decision plus a unique priority integer per type |
| "What are the org-wide defaults for Account, Opportunity, Contact and Case today?" | OWD narrows which access-level values are legal — with Public Read/Write on accounts the only valid `accountAccessLevel` values are `Edit` and `All`, and for some objects the element must be omitted | A per-object access decision written in Metadata API spelling, not Setup labels |
| "Does the forecast roll up by territory, and who reads it at each level?" | Territory forecast rollup follows the hierarchy of the *active* model, so a hierarchy level with no reader is a level that exists only to be maintained | One named forecast consumer per hierarchy level, or that level deleted |
| "How often does this alignment change, and what is the cutover window?" | A model is created in `Planning`, only `Planning` or `Active` models can be deployed, and archiving is one-way — realignment is a build-alongside-then-cut-over exercise, not an edit | A realignment cadence, a named runner for the rule run, and a fiscal date the cutover must precede |
| "Who is allowed to change a territory after go-live, and at which node?" | `TerritoryAdminAssignment` (API 63.0+) delegates hierarchy, membership and record-association rights per territory subtree to a user holding Administer Territory Operations | A delegation table, instead of every change queueing behind one system administrator |

What a proper configuration adds over just doing it: the design arrives at build time as named Account fields, unique type priorities, legal access-level values and a dated cutover plan, so the ETM build is a transcription rather than a second round of discovery — and the acceptance tests are already written when the rule run finishes.

---

## Core Concepts

### Coverage Model Types

ETM supports four coverage patterns, and most orgs run a combination:

**Geographic:** Territories defined by location criteria — `BillingState`, `BillingCountry`, `BillingPostalCode`, or a custom region picklist. Best for field sales organisations with clear geographic accountability. The `Territory2RuleItem` operation enum also carries `within`, documented as "DISTANCE criteria only", so radius-style criteria exist where a geolocation field does.

**Named Account:** Specific accounts assigned to specific reps regardless of location. Implemented via an Account field (a named-account flag is cheaper than an Account Name match list) or by manual assignment, which lands as `ObjectTerritory2Association.AssociationCause = Territory2Manual` rather than `Territory2AssignmentRule`.

**Industry Overlay:** Cross-functional coverage granting additional visibility across other territories by industry, product line, or segment. Overlays stack on primary coverage — members gain additive access.

**Hybrid:** Geographic primary coverage plus named account or overlay territories. Most enterprise orgs end up here. Requires an explicit, unique priority integer per territory type, because that integer is what decides opportunity territory assignment.

### Hierarchy Design Principles

The territory hierarchy sets parent-child relationships that control two things: how forecast data rolls up, and how the `TerritoryAndSubordinates` group is built. That group is a public group of "users in a specified territory, and users in territories subordinate to the specified territory" (Metadata API Developer Guide, `FolderShare` › `sharedTo`; the same pairing appears on territory sharing rules), and it is what propagates record access up a branch.

**Depth:** UNVERIFIED (2026-09-05): the widely repeated "3–5 levels" recommendation is not stated in the Metadata API guide, Object Reference or App Limits Cheat Sheet. What is checkable is the practice test behind it — every level must have a named person who reads the forecast at that node. Levels that fail that test are maintenance with no reader.

**Breadth:** Span of control per level should reflect the real management structure. A node with 50 direct children is not auditable and usually means a missing intermediate level.

**Independence from role hierarchy:** `Territory2.ParentTerritory2Id` is the only parenting mechanism ETM has, and it has no relationship to `UserRole`. Design the two hierarchies separately against their own purposes even where they end up similar in shape.

### Assignment Rule Design

Account assignment rules are filter-based criteria evaluated against Account field values. A rule belongs to the **model**, and its link to a territory is a separate `ruleAssociations` entry on each `Territory2` carrying an `inherited` flag — "Rule inheritance flows from the parent territory where the rule is created to the rule's descendent territories… A local rule is created within a single territory and affects that territory only." The design must therefore state, per rule, both the territories it serves and whether it is inherited.

| Design constraint | Grounded in |
|---|---|
| Max 10 rule items per rule | Metadata API, `Territory2Rule` › Usage: "A territory rule can have up to 10 rule items." |
| Operations available: `equals`, `notEqual`, `lessThan`, `greaterThan`, `lessOrEqual`, `greaterOrEqual`, `contains`, `notContain`, `startsWith`, `includes`, `excludes`, `within` (DISTANCE only) | `Territory2RuleItem` › `operation` |
| Combine items with `booleanFilter`, e.g. `(1 AND 2) OR 3`; "Numbering must start at 1 and must be contiguous" | `Territory2Rule` › `booleanFilter` |
| Rule item order is positional — "The sort order of rule items is implicitly derived from the position of the rule items in the XML" | `Territory2Rule` › Usage |
| `objectType` is `Account` (Lead assignment is a separate `Territory2Settings.supportedObjects` switch) | `Territory2Rule` › `objectType`; `Territory2SupportedObject` › `objectType` |
| An account matching several rules lands in several territories | `ObjectTerritory2Association`, one row per assignment |
| Blanket coverage: something must own the accounts no rule matches, or they appear in no territory forecast | `ObjectTerritory2Association` exists only where an assignment happened |

Date-field criteria: **UNVERIFIED (2026-09-05)** — the long-standing practitioner claim that ETM assignment rules reject Date and DateTime fields is not stated in the Metadata API guide (`Territory2RuleItem.field` is documented only as "The standard or custom object field that the rule item operates on") or the Object Reference. The operation enum does carry the comparison operators a date would need. Treat a date-based criterion as unproven until you have configured one in a sandbox, and prefer a quarter/month proxy picklist regardless, because a date predicate goes stale the moment the date passes while a rule run happens on someone's schedule.

### Access-Level Decisions

Access levels are a design decision, not a build detail: they are per territory and per object, and OWD constrains which values are legal.

| Element | Valid values | Rule from the guide |
|---|---|---|
| `accountAccessLevel` | `Read`, `Edit`, `All` | With a Public Read/Write account sharing model, only `Edit` and `All` are valid |
| `opportunityAccessLevel` | `None`, `Read`, `Edit` | Specify no value if the case/opportunity sharing model is Public Read/Write |
| `caseAccessLevel` | `None`, `Read`, `Edit` | Same omission rule as opportunity |
| `contactAccessLevel` | `None`, `Read`, `Edit` | Specify no value if the contact model is Public Read/Write or Controlled By Parent |
| `objectAccessLevels` (API 57.0+) | `accessLevel` of `Read`, `Edit`, `Transfer`, `All` plus an `objectType` | The org-level counterpart, `Territory2SupportedObject`, documents `Lead` as the only supported object type |

Omitting an element falls back to the matching `default*AccessLevel` in `Territory2Settings`. The Metadata API spellings above are not the labels the same values carry as SOQL picklists on the `Territory2` object (`Read Only` / `Read/Write` / `Owner` for accounts; `Private` / `Read Only` / `Read/Write` elsewhere) — the requirements document should carry the Metadata API spelling, because that is what deploys.

### User-to-Territory Ratio

UNVERIFIED (2026-09-05): the "approximately 3:1 territories per user" target is a field heuristic, not a documented Salesforce figure — it is absent from the App Limits Cheat Sheet, the Metadata API guide and the Object Reference. Use it as a review trigger rather than a rule:

- Ratios far above 3:1 mean many leaf territories per person: more rules to maintain, more `ObjectTerritory2Association` rows to reconcile, fragmented forecast nodes.
- Ratios below 1:1 mean coverage accountability is ambiguous — several people in one territory with no documented split.
- A user may belong to several territories; count each `UserTerritory2Association` row, and remember `IsActive` on that row can be false while the row still exists.

Test the ratio against account volume per territory, not against headcount alone.

---

## Common Patterns

### Geographic Primary Coverage Model

**When to use:** Clear geographic accountability, field reps own a region, and assignment can be determined from `BillingState` or `BillingCountry`.

**How it works:**
1. Define territory types: National → Regional → Sub-Regional, each with a unique `priority` integer.
2. Build the hierarchy with `parentTerritory` set to the parent's **developer name** — "use the developer name. Do not use the 'fully qualified' name" (`Territory2` › `parentTerritory`).
3. Create mutually exclusive rules at the leaf level: `BillingState equals CA`, `BillingState equals OR`.
4. Parent territories need no rules of their own — access flows through the `TerritoryAndSubordinates` group; an inherited rule is a separate, deliberate choice recorded in `ruleAssociations.inherited`.
5. Define a catch-all territory for accounts matching no leaf rule, including blank billing addresses.

**Why not a flat structure:** A single level of 50 nodes gives forecast rollup nothing to aggregate on, and every manager view becomes a custom report.

### Named Account Overlay Model

**When to use:** A subset of accounts belongs to strategic reps regardless of location, and those accounts are also inside geographic territories.

**How it works:**
1. Create a distinct territory type with a **higher** priority integer than the geographic type — the highest integer wins opportunity territory assignment.
2. Create one territory per named-account rep or book.
3. Assign accounts by a flag field on Account (one rule item, stable) or manually; manual lands as `AssociationCause = Territory2Manual` and `AccountShare.RowCause = Territory2AssociationManual`, rule-driven lands as `Territory2AssignmentRule` and `RowCause = Territory`. Those two values are how the audit tells them apart.
4. Both reps hold access — territory access is additive and does not change account ownership.
5. Keep the two types' priorities unique. Two territories of the *same* type on one account assign no territory to the opportunity.

**Why not a sharing rule:** A sharing rule grants access without producing an `ObjectTerritory2Association`, so the account never reaches territory forecasting. Where territory forecasting is in scope, membership is the mechanism.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Reps cover fixed geographic regions with no overlap | Geographic model with mutually exclusive `BillingState`/`BillingCountry` rules | Criteria are stable, auditable, and one rule item each |
| Enterprise reps own accounts across geographies | Named-account territory type overlaid on geographic primary coverage, with the higher priority integer | Both coverage layers keep access; the higher integer decides the opportunity |
| Industry specialists cover accounts across all regions | Overlay territory type per vertical, unique priority | Access is additive; primary and overlay coexist |
| Segmentation needs an 11th predicate on one territory | Collapse to a proxy field on Account (e.g. `Territory_Segment__c` picklist) | A rule holds at most 10 rule items (Metadata API, `Territory2Rule` › Usage) |
| Criteria combine AND and OR | One rule with a `booleanFilter` such as `(1 AND 2) OR 3` | Numbering must start at 1 and be contiguous, and item order is positional |
| Assignment criteria are date-based | Use a quarter/month proxy picklist maintained by automation | A date predicate is stale between rule runs; the field-type restriction itself is UNVERIFIED (2026-09-05) |
| Named account list changes monthly or faster | Flag field with one rule item, or manual assignment | Avoids editing rules on every list change; manual assignments are identifiable by `AssociationCause` |
| Two territories of the same type can hold one account | Split into two types with unique priorities, or make the criteria exclusive | A same-type tie assigns no territory to the opportunity (`Territory2Type` › `priority`) |
| Alignment changes every fiscal year | Plan a `Planning`-state model built alongside the active one, with a dated cutover | Archiving is one-way and only `Planning` or `Active` models can be deployed |
| Requirement reads "reps should see only their accounts" | Return it to `admin/sharing-and-visibility` as an OWD requirement | Territory access grants access to records "otherwise inaccessible" — it never removes any |

---

## Recommended Workflow

1. **Run the questionnaire in `references/worked-examples.md` §1** with sales leadership and sales ops in the room. Record answers verbatim; a dimension nobody can name an Account field for is not yet a requirement.
2. **Fill `templates/territory-design.yaml`** — territory rows with type, priority, parent, rules or an explicit `manual_assignment: true`, per-object access levels, and the realignment plan. `templates/territory-design-requirements-template.md` is the prose companion for the parts a linter cannot judge.
3. **Draft the hierarchy and the assignment-rule matrix** (`references/worked-examples.md` §2–§4). For each rule: field API name, operation from the documented enum, value, the territories it serves, and whether it is inherited. Count the rule items — the ceiling is 10 per rule.
4. **Decide the access levels per object per territory** against the org's current OWD, using the table in Core Concepts and the enum in `references/worked-examples.md` §5. Write the Metadata API spelling.
5. **Write the realignment runbook** (`references/worked-examples.md` §6): which model states the plan passes through, who runs the rules, and the fiscal date the cutover must precede.
6. **Lint the design**: `python3 scripts/check_territory_design_requirements.py --manifest-dir <design-dir>`. It fails on missing type/priority/parent, duplicate priorities, territories with neither a rule nor a manual-assignment flag, access levels outside the documented enums, two rules with identical criteria in one territory, a missing realignment plan, and any `Territory2Rule` XML in the folder whose `ruleItems` use an operation outside the enum.
7. **Attach the acceptance tests** (`references/worked-examples.md` §7) to the handoff and pass the package to `admin/enterprise-territory-management`. The tests are SOQL over `ObjectTerritory2Association` and `UserTerritory2Association`; they are the definition of "the build matches the design".

---

## Review Checklist

Run through these before marking requirements complete:

- [ ] Coverage motion is confirmed (geographic, named account, overlay, or hybrid)
- [ ] Every alignment dimension maps to a named Account field API name with a known population rate
- [ ] Every hierarchy level has a named forecast consumer; levels without one are removed
- [ ] Territory hierarchy is documented independently of the role hierarchy
- [ ] Territory types are named and each `priority` integer is unique — and the highest one is the type intended to win opportunity assignment
- [ ] No two territories of the same type can hold the same account (a tie assigns no territory)
- [ ] No rule exceeds 10 rule items; every operation is in the documented enum; `booleanFilter` numbering starts at 1 and is contiguous
- [ ] Every territory has at least one assignment rule or an explicit manual-assignment decision with an owner
- [ ] `ruleAssociations.inherited` is decided per rule, not left to the builder
- [ ] Access levels are chosen per object per territory and are legal for the current OWD, in Metadata API spelling
- [ ] Catch-all coverage exists for accounts matching no rule, including blank billing addresses
- [ ] A realignment plan names the model states, the rule runner, and the cutover date
- [ ] Acceptance tests over `ObjectTerritory2Association` / `UserTerritory2Association` are written before build starts
- [ ] Any territory-count ceiling carried in the document is marked as an assumption with an owner (see Before Starting)
- [ ] `python3 scripts/check_territory_design_requirements.py --manifest-dir <dir>` reports no ERROR findings

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems. Full form in `references/gotchas.md`.

1. **The priority integer runs the opposite way to most people's intuition** — the highest integer wins opportunity territory assignment, values must be unique per type, and a same-type tie assigns nothing at all.
2. **Ten rule items is a hard ceiling on the rule** — the eleventh predicate needs a proxy field on Account, not a second attempt at the rule.
3. **Overlapping criteria assign an account to every matching territory** — deliberate for overlays, almost never deliberate for primary coverage.
4. **A rule change assigns nothing on its own** — rules run automatically on record create and edit; a change to the rule itself needs a user-initiated run, and Metadata API cannot start one.
5. **Two flags silently stop rules from evaluating a record** — `IsExcludedFromRealign` on the record and `tm2BypassRealignAccInsert` in the org settings.
6. **Territory access can only add** — it grants access to records that are "otherwise inaccessible"; restriction is an OWD conversation.
7. **Archiving is one-way and a same-named archived model blocks the deploy** — realignment is build-alongside-then-cut-over.

---

## Output Artifacts

| Artifact | Kind | Description |
|---|---|---|
| Territory design requirements document | Markdown | Coverage model, hierarchy shape, criteria, ratio analysis, open decisions (`templates/territory-design-requirements-template.md`) |
| `territory-design.yaml` | YAML | The machine-lintable design: territories, types, priorities, parents, rules, access levels, realignment plan (`templates/territory-design.yaml`) |
| Assignment rule matrix | Table | Per rule: field, operation, value, territories served, inherited flag, rule-item count |
| Territory hierarchy table | Table | Levels, parent-child relationships, territory type, named forecast consumer per level |
| Access-level decision table | Table | Per territory per object, in Metadata API spelling, checked against current OWD |
| Realignment runbook | Markdown | Model states, rule runner, cutover date, rollback position |
| Acceptance tests | SOQL | Queries over `ObjectTerritory2Association`, `UserTerritory2Association`, `Territory2AlignmentLog` that prove the build matches the design |

---

## Reference Files

| File | Read it when |
|---|---|
| `references/worked-examples.md` | Filling in the questionnaire, the hierarchy table, the rule matrix, the access decisions, the realignment runbook or the acceptance tests — one B2B SaaS scenario carried end to end |
| `references/gotchas.md` | A design looks reasonable on paper and you want to know how it fails after activation |
| `references/examples.md` | Shaping a geographic model or a named-account overlay, and sizing the ratio |
| `references/well-architected.md` | Trading off depth, territory count and access breadth — and for the source list |
| `references/llm-anti-patterns.md` | Reviewing generated territory-design advice, especially anything asserting a priority direction or a field-type restriction |
| `templates/territory-design.yaml` | Starting the design artefact the checker lints |
| `templates/territory-design-requirements-template.md` | Writing the prose requirements document around it |

---

## Related Skills

- admin/enterprise-territory-management — the build: `Territory2*` metadata, the deploy path, activation, rule runs and verification SOQL. Read its `references/metadata-examples.md` rather than duplicating XML here
- admin/sharing-and-visibility — OWD, role hierarchy and sharing rules set the floor that territory access adds to; any "restrict to their own accounts" requirement lands here
- admin/opportunity-management — opportunity stages, forecast categories and the pipeline the territory forecast rolls up
- admin/requirements-gathering-for-sf — the general discovery practice this skill specialises; its requirements catalogue is the parent artefact a territory design plugs into
- admin/collaborative-forecasts — forecast types and quotas, once the territory forecast type is in scope
- admin/role-hierarchy-design — the structure the territory hierarchy is deliberately independent of
- data/territory-data-alignment — bulk-loading `UserTerritory2Association` and realignment data at volume
