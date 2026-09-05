# Well-Architected Notes — Campaign Planning And Attribution

## Relevant Pillars

- **Operational Excellence** — Campaign attribution models and hierarchy designs must be explicitly documented so revenue operations teams can interpret reports consistently. Undocumented model choices (e.g., why first-touch was chosen over even-distribution) cause re-work when attribution data is questioned by stakeholders. The skill's recommended workflow includes a documentation step as a required deliverable.

- **Reliability** — The hierarchy totals are *calculated* fields (`HierarchyActualCost`, `TotalNumberofResponses` and their siblings, object_reference.txt:57273–57810) and the Object Reference publishes no refresh cadence for them. An automation that treats a change on one as an event therefore has no contract to rely on — UNVERIFIED (2026-09-05): the commonly-quoted "updates within a few hours" figure has no source in the official extracts. Source live data from the Opportunity or CampaignMember record that actually changed.

- **Scalability** — UNVERIFIED (2026-09-05): no maximum Campaign hierarchy depth is documented in the Object Reference, the Metadata API guide, or the App Limits cheat sheet, so hierarchy headroom must be treated as an unquantified constraint rather than a known budget. What *is* documented and does bound the design is row volume: `recordPreference` = `AllRecords` "creates records regardless of the revenue attribution percentage" (api_meta.txt:31920–31926), multiplying `CampaignInfluence` rows by every touched campaign including the ones credited nothing.

- **Security** — Access is gated before sharing is even considered. `Campaign` and `CampaignMemberStatus` are "defined only for those organizations that have the marketing feature enabled and valid marketing licenses… accessible only to those users that are enabled as marketing users" (object_reference.txt:57860–57863, 58672–58675), and `CampaignInfluence` requires CCI to be enabled and is closed to Customer Portal users (object_reference.txt:57909–57910). A blank attribution dashboard is a licence-and-flag question before it is a sharing-rule question.

- **Performance** — Each active model produces its own `CampaignInfluence` rows per opportunity, so row count scales with models × influencing campaigns × opportunities. `recordPreference` is the lever: `RecordsWithAttribution` "creates records only when the revenue attribution is greater than 0%" (api_meta.txt:31920–31926). Filter queries and reports on `ModelId` and a close-date range; `ModelId`, `CampaignId` and `OpportunityId` are all Filter-able (object_reference.txt:57915–57976).

## Architectural Tradeoffs

**Which model is the default**

Only one `CampaignInfluenceModel` can carry `IsDefaultModel` = true, and that one model owns three UI surfaces: the Campaign Influence related list on opportunities, the Influenced Opportunities related list on campaigns, and the Campaign Statistics section on campaigns (object_reference.txt:58055–58066). Every other model is report-and-query only. The tradeoff is therefore not "how many models can we run" — it is which single set of numbers people will quote in a meeting. Configure the rest as reports on `CampaignInfluence` grouped by `ModelId` and say so, rather than letting a deploy silently demote the model the sales team has been reading.

**`AllRecords` vs `RecordsWithAttribution`**

`recordPreference` decides whether zero-credit rows exist. `AllRecords` "creates records regardless of the revenue attribution percentage"; `RecordsWithAttribution` "creates records only when the revenue attribution is greater than 0%" (api_meta.txt:31920–31926). `AllRecords` buys a complete touch history at the cost of multiplying row count by every campaign a contact ever met, per model. Choose it only when the analysis genuinely needs uncredited touches, and expect the report and query cost that comes with it.

**Model lifecycle is a data-retention decision, not a visibility one**

"Deactivating a model deletes its campaign influence records" (api_meta.txt:31892–31895). There is no documented undo. That makes `isActive` a destructive flag in a deployable file — a valid deploy that removes data, which no validation-only run will flag. Governance belongs at the release level: name an owner, list model deactivation next to field deletions in change control, and change `isDefaultModel` when the goal is only to change what users see.

**Campaign Hierarchy depth vs. dimensional encoding**

Encoding region, product line and campaign type as hierarchy levels produces rigid structures that are expensive to reorganise, and — UNVERIFIED (2026-09-05) — spends headroom whose size is not documented anywhere in the official extracts. The sound approach is unchanged by that uncertainty: use hierarchy levels only for cost and revenue rollup (program > tactic) and encode other dimensions as Campaign custom fields, which report filters handle without restructuring anything.

**Where the rollup numbers come from**

Two independently named families of calculated fields aggregate the same hierarchy: `Hierarchy*` and `Total*` (object_reference.txt:57273–57810). Neither is wrong, but a report or dashboard that mixes them looks inconsistent for reasons no viewer can diagnose. Pick one family per artefact and state it in the description. The short-name fields (`ActualCost`, `AmountWonOpportunities`) are single-campaign values and belong only in tactic-level reporting.

## Anti-Patterns

1. **Planning a "disable Campaign Influence 1.0 first" step** — It is not a step that exists. `enableCampaignInfluence2` defaults to true and, when true, "Campaign Influence 1.0 is hidden from users and is no longer active"; the 1.0-era `enableAutoCampInfluenceDisabled` switch requires `enableCampaignInfluence2` to be false (api_meta.txt:111556–111571). `CampaignInfluence` is CCI-only (object_reference.txt:57898), so the "duplicate records from two systems" the plan budgets for cannot occur. Retrieve the settings file and read the flag instead.

2. **Automating on a calculated Campaign field** — Building Flows or Apex that fire when a hierarchy total crosses a threshold treats a calculated field with no published refresh contract as an event source. Trigger from the Opportunity or `CampaignMember` change that actually happened and walk up to the campaign.

3. **Deactivating a model to "reset" it** — Deactivation deletes the rows and reactivation does not restore them. Export first, or change the default model instead.

4. **Writing influence rows against the Primary Campaign Source model** — "Records added to the Primary Campaign Source model via the API are deleted when the model is recalculated" (object_reference.txt:57996–57999). An integration that resolves its target model as "the default one" will eventually pick it. Resolve by `DeveloperName` and assert `Model.ModelType != 1` before writing.

5. **Trusting a campaign-member load's success count** — An invalid `Status` is coerced to the campaign's default and inserts cleanly, and a member carrying both `ContactId` and `LeadId` inserts as the contact alone (object_reference.txt:58572–58577, 58553–58555). Reconcile by counts per status and per member `Type`, never by rows accepted.

## Official Sources Used

- Metadata API Developer Guide — `CampaignInfluenceModel` (api_meta.txt:31872–31966): file suffix and directory, API 38.0 availability, `isActive` / `isDefaultModel` / `isModelLocked` / `modelDescription` / `name` / `recordPreference`, both declarative sample definitions, and wildcard support. Grounds the model XML, the "deactivating deletes records" tradeoff, and the `AllRecords` vs `RecordsWithAttribution` row-volume argument. <https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf>
- Metadata API Developer Guide — `CampaignSettings` (api_meta.txt:111515–111603): `enableCampaignInfluence2` defaulting to true and hiding Campaign Influence 1.0, the `enableAutoCampInfluenceDisabled` mutual exclusion, `enableB2bmaCampaignInfluence2`, `enableAccountsAsCM`, Einstein Attribution fields, the read-only system fields, and the `Settings` manifest name. Grounds the "Before Starting" checks and the CCI-vs-1.0 tradeoff.
- Metadata API Developer Guide — `ReportType`, `RecordType`, `StandardValueSet`, Picklist samples, and StandardValueSet Names (api_meta.txt:105780–105986, 44968–45132, 130740–130828, 44744–44796, 141856–141860): the report-type join and column shape with its four-object ceiling, the record-type picklist-values shape and retrieval caveats, and the `CampaignType` / `CampaignMemberStatus` / `CampaignStatus` standard value set names. Grounds the report-type and dimension-encoding sections.
- Object Reference — `Campaign` (object_reference.txt:57086–57866): the single-campaign fields, both hierarchy field families and their `currency`-typed count fields, `ParentId` / `ParentCampaign`, the 80-character name and 40-character `Status` / `Type` limits, and the marketing-feature / marketing-user access rule. Grounds the Reliability and Security notes and the rollup-naming tradeoff. <https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf>
- Object Reference — `CampaignInfluence` and `CampaignInfluenceModel` (object_reference.txt:57894–58180): supported calls, the CCI-only scope note, the full field list including `RevenueShare`, the "don't write to Primary Campaign Source" usage rule, the six-value `ModelType` set, `IsDefaultModel`'s three UI surfaces, `IsModelLocked`, and `RecordPreference`. Grounds the Performance note on row volume and the model-governance tradeoff.
- Object Reference — `CampaignMember` and `CampaignMemberStatus` (object_reference.txt:58185–58676): `Status` controlling the read-only `HasResponded`, the text-not-Id rule, the invalid-status coercion branches, Lead-XOR-Contact, and the API 39.0 default-and-responded requirements plus the deletion restriction. Grounds the funnel-integrity argument that replaced the earlier "MCAE drops the record" claim.
- Salesforce App Limits Cheat Sheet (salesforce_app_limits_cheatsheet.txt) — searched and cited as a **negative**: `grep -i campaign` returns no rows, so no Campaign hierarchy depth or campaign-member ceiling is grounded from it. This is why the "5 levels" figure is carried as UNVERIFIED rather than stated. <https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_app_limits_cheatsheet.pdf>
- `standards/decision-trees/README.md` — the rule that a query straddling more than one technology in a tree's scope is resolved by reading the tree first; applied here when an attribution requirement turns into an automation question rather than a configuration one.
- Salesforce Well-Architected Overview — <https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html> (pillar framing for the sections above)
