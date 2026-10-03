# Decisions log

Append-only. Written by the build doc keeper.

Entry shape follows `skills/devops/development-documentation-standards` § "Org-level design
standards" — one central location, and an entry that records the date, the step, the agent that
made the call, **the alternative it rejected** and **the source it was grounded in**, rather than a
sentence asserting the outcome. Append-only: an earlier entry is never rewritten, and a reversal is
a new entry naming the one it supersedes.

`D-` entries are decisions per `agents/build-doc-keeper/AGENT.md` Step 3 (technology choice / design
trade-off / skill gap / deviation). `O-` entries are open items and ambiguities the build carries
forward for a human to close — not decisions in Step 3's sense, but recorded in the same append-only
log because that is the one central location this skill names.

---

## D-M1S01-01 — No stage carries `<default>true</default>` on the OpportunityStage value set

- **Date:** 2026-09-15
- **Step:** `M1-S01` (`object-model`)
- **Agent:** `metadata-builder` (run `2026-09-15T19-21-43Z`)
- **Kind:** design trade-off
- **What was recorded:** None of the eight shipped stages carries `<default>true</default>`; all
  eight are explicitly `false`. The per-motion default lives on the business process instead
  (`Qualify` for Enterprise, `Renewal Review` for Renewal).
- **Alternative rejected:** marking one of the eight new stages as the value-set-level default.
  Rejected because the org's existing default stage must survive the §0 retrieve-and-merge
  untouched — moving the org-wide default would disturb the SMB record type, which
  `requirement.md` item 6 says must not break.
- **Grounded in:** `requirement.md` item 6, plus `admin/picklist-and-value-sets`
  `references/metadata-examples.md` § 1 (exactly one `<default>true</default>` per value-set file)
  and `admin/opportunity-management` `references/metadata-examples.md` § 2 (a `BusinessProcess`'s
  `<values>` carry their own default independent of the value set).
- **Evidence:** `artefacts/M1-S01/standardValueSets/OpportunityStage.standardValueSet-meta.xml`
  (8× `<default>false</default>`); `artefacts/M1-S01/objects/Opportunity/businessProcesses/*.xml`
  (1× `<default>true</default>` each); `envelopes/M1-S01/2026-09-15T19-21-43Z.json` →
  `extensions.decision_record[4]`.

## D-M1S01-02 — No `<picklistValues>` block on either record type; Q40 defaults to A5

- **Date:** 2026-09-15
- **Step:** `M1-S01` (`object-model`)
- **Agent:** `metadata-builder` (run `2026-09-15T19-21-43Z`)
- **Kind:** design trade-off, recorded by the owning agent as a default standing in for an open
  clarification
- **What was recorded:** Neither `Enterprise.recordType-meta.xml` nor `Renewal.recordType-meta.xml`
  carries a `<picklistValues>` block. `StageName` is the only picklist that differs between the two
  processes, and it is governed entirely by each record type's `<businessProcess>` reference rather
  than by a per-record-type picklist override; `Approval_Status__c` needs no block either, because a
  brand-new record type receives all current master values by default.
- **Alternative rejected:** writing an explicit `<picklistValues>` block for `Approval_Status__c` (or
  for any other field) on one or both record types. Rejected because clarification **Q40** ("which
  picklist values differ between these processes, field by field, beyond `StageName`") is still
  **open** — the plan's `defaults_applied` maps it to assumption **A5**, which states no other field
  needs a per-record-type block, and inventing one would assert an answer nobody gave.
- **Grounded in:** documented default — assumption A5 standing in for open clarification Q40 — plus
  `admin/picklist-and-value-sets` `references/gotchas.md` Gotcha 5 (a brand-new record type receives
  all current master values by default, which is what makes "no block" the correct reading of A5
  rather than an omission).
- **Open item this decision creates:** confirm at the M1 gate that `StageName` is genuinely the only
  picklist differing between the two record types — carried below as **O-M1S01-02** is a different
  open item (Q39); this one is tracked directly against Q40 in `traceability.md`'s `source` column
  on the two `RecordType` rows.
- **Evidence:** `artefacts/M1-S01/objects/Opportunity/recordTypes/*.recordType-meta.xml` (no
  `<picklistValues>` element in either file); `plan.json` → `steps[M1-S01].inputs.defaults_applied`
  (`{"Q40": "A5"}`); `envelopes/M1-S01/2026-09-15T19-21-43Z.json` → `extensions.decision_record[7]`.

## D-M1S01-03 — `Approval_Status__c` ships with no default value

- **Date:** 2026-09-15
- **Step:** `M1-S01` (`object-model`)
- **Agent:** `metadata-builder` (run `2026-09-15T19-21-43Z`)
- **Kind:** design trade-off
- **What was recorded:** All three legal values (`Pending`, `Approved`, `Rejected`) carry
  `<default>false</default>`. The field is left blank on a new Opportunity.
- **Alternative rejected:** defaulting the field to `Pending`. Rejected because Q22's answer lists
  blank as a legal fourth state ("Pending, Approved, Rejected, blank") set by the approval process
  itself — defaulting to `Pending` would put every new Opportunity into a status nobody had actually
  submitted for approval, which is a state the approval process (M3) never produces on its own.
- **Grounded in:** clarification Q22.
- **Evidence:** `artefacts/M1-S01/objects/Opportunity/fields/Approval_Status__c.field-meta.xml`
  (`<valueSetDefinition>`, three `<value>` blocks, each `<default>false</default>`);
  `envelopes/M1-S01/2026-09-15T19-21-43Z.json` → `extensions.decision_record[13]`.

## D-M1S01-04 — `Discount__c` and `Approval_Status__c` ship with field history tracking explicitly off

- **Date:** 2026-09-15
- **Step:** `M1-S01` (`object-model`)
- **Agent:** `metadata-builder` (run `2026-09-15T19-21-43Z`)
- **Kind:** design trade-off
- **What was recorded:** Both new fields carry `<trackHistory>false</trackHistory>` and
  `<trackFeedHistory>false</trackFeedHistory>` explicitly, written rather than left to an object-level
  flag this build does not set.
- **Alternative rejected:** leaving the tracking elements unset and relying on
  `OpportunitySettings.enableOpportunityFieldHistoryTracking`'s platform default. Rejected because no
  field-level history was requested for either field by any clarification, and no
  `OpportunitySettings` file ships in this build (assumption A4) — an unset element would make the
  fields' history behaviour depend silently on an object setting nothing here confirms.
- **Grounded in:** assumption A4, plus clarification Q39 (open — see **O-M1S01-02** below, which
  tracks the object-level tracking question this field-level decision does not resolve).
- **Evidence:** `artefacts/M1-S01/objects/Opportunity/fields/Discount__c.field-meta.xml` and
  `Approval_Status__c.field-meta.xml` (`<trackHistory>false</trackHistory>`,
  `<trackFeedHistory>false</trackFeedHistory>` on both); `envelopes/M1-S01/2026-09-15T19-21-43Z.json`
  → `extensions.decision_record[10]`.

---

## O-M1S01-01 — BLOCKING: the shipped `OpportunityStage` value set must be retrieved-and-merged before deploy

- **Date:** 2026-09-15 · **Recorded by:** `build-doc-keeper`, from the builder's envelope and
  `artefacts/M1-S01/deploy-order.md` § 0
- `standardValueSets/OpportunityStage.standardValueSet-meta.xml` as shipped contains **only the
  eight new Northwind stages**. It is a fragment. Deploying it as-is deactivates every stage it does
  not mention — including every stage the SMB team's generic pipeline runs on today — because for a
  value set, omission is the deactivate instruction, not "no opinion" (decision **D1**;
  `admin/picklist-and-value-sets` `references/gotchas.md` Gotcha 10).
- **Why this build cannot close it itself:** `plan.json.build_mode` is `design-only`; there is no org
  connection to run the retrieve. Assumption **A24** carries the gap at risk `high`.
- **What must happen before deploy:** `sf project retrieve start --metadata
  "StandardValueSet:OpportunityStage" --target-org <alias>`, then merge the retrieved active values
  into the shipped file, keeping the org's existing `<default>true</default>` stage untouched (see
  D-M1S01-01) and retiring any value with `<isActive>false</isActive>` rather than deleting the
  element.
- **Which requirement this decides:** `requirement.md` item 6 ("nothing should break the existing
  generic process for the SMB team") is decided entirely by whether this merge happens.
- **Evidence:** `artefacts/M1-S01/deploy-order.md` § 0;
  `envelopes/M1-S01/2026-09-15T19-21-43Z.json` → `extensions.open_items_for_the_human[0]` and
  `process_observations` (concerning/medium, domain `deploy-order`).

## O-M1S01-02 — Q39 is unanswered; Opportunity field history tracking rests on an unconfirmed platform default

- **Date:** 2026-09-15 · **Recorded by:** `build-doc-keeper`, from the builder's envelope and
  `artefacts/M1-S01/deploy-order.md` § 3 item 3
- Clarification **Q39** ("how will Enterprise/Renewal stage movement be measured six months from
  now?") is still `open`. Assumption **A4** relies on
  `OpportunitySettings.enableOpportunityFieldHistoryTracking` defaulting to `true` — no
  `OpportunitySettings` file ships anywhere in this build to guarantee it.
- **Why it matters more than a normal open question:** Opportunity field history cannot be
  backfilled. If the platform default is off, or is turned off before go-live, no measurement is
  possible after the fact.
- **Remedy:** confirm the setting is on in the target org before go-live, and get the Sales
  Operations lead to answer Q39 — not a fix this step or any later metadata step can make on its
  own, since it is an org setting, not a deployable component.
- **Evidence:** `plan.json` → `clarifications[Q39]` (`status: open`); `artefacts/M1-S01/objects/
  Opportunity/fields/Discount__c.field-meta.xml` and `Approval_Status__c.field-meta.xml`
  (`<trackHistory>false</trackHistory>` on both — see D-M1S01-04, a field-level decision that does
  not resolve this object-level question); `envelopes/M1-S01/2026-09-15T19-21-43Z.json` →
  `extensions.open_items_for_the_human[1]`.

## O-M1S01-03 — The Enterprise and Renewal record types deploy in this step but are not yet selectable

- **Date:** 2026-09-15 · **Recorded by:** `build-doc-keeper`, from `artefacts/M1-S01/deploy-order.md`
  § 2
- A permission set can grant record-type **visibility** only; the **default** record type and the
  page-layout assignment exist solely on `Profile`
  (`admin/record-types-and-page-layouts/references/metadata-examples.md`, "Making the record type
  visible and assigning the page"). That step is **M2-S02**, and it is human-gated.
- **Until M2-S02 ships:** `RecordType:Opportunity.Enterprise` and `RecordType:Opportunity.Renewal`
  are deployed metadata that no user can pick from the Opportunity's "New" record-type picker.
- **Not a defect in this step** — the dependency is named and ordered correctly in
  `artefacts/M1-S01/deploy-order.md` § 2 — but it is the reason the M1 milestone gate should not be
  read as "reps can start working Enterprise deals."
- **Evidence:** `artefacts/M1-S01/deploy-order.md` § 2, row 2 ("Profile layout assignments and
  recordTypeVisibilities … Until that ships, these two record types are deployed but nobody can
  select them."); `plan.json` → `steps[M2-S02]`.

---

## D-M1S02-01 — No layout item on either Opportunity layout carries `behavior=Required`

- **Date:** 2026-09-15
- **Step:** `M1-S02` (`ui`)
- **Agent:** `metadata-builder` (run `2026-09-15T19-58-38Z`)
- **Kind:** design trade-off
- **What was recorded:** every `layoutItems` element on both `Layout` files is `Edit` or
  `Readonly`; none is `Required` — including `Amount` and `Discount__c`, two of the fields Q11
  names as must-fill before a rep can advance a stage.
- **Alternative rejected:** marking `Amount`, `Discount__c`, or any of Q11's other must-fill fields
  `Required` directly on the layout. Rejected because Layout `Required` binds to that one layout
  only — the API, Flow, and every other layout ignore it
  (`admin/record-types-and-page-layouts` `references/gotchas.md` Gotcha #11) — so using it here
  would look like enforcement and enforce nothing; Q11's must-fill rules are a validation-rule
  backlog for `M2-S03`/`M2-S04` instead, not a layout backlog.
- **Grounded in:** clarification Q11; `admin/record-types-and-page-layouts`
  `references/gotchas.md` Gotcha #11.
- **Evidence:** `artefacts/M1-S02/layouts/*.layout-meta.xml` (ten `layoutItems` total across both
  files, every one `Edit` or `Readonly`); `envelopes/M1-S02/2026-09-15T19-58-38Z.json` →
  `extensions.decision_record[0]`.

## D-M1S02-02 — Q20's five standard fields ship present but not `Required`; the platform's own required set is carried as assumption A25

- **Date:** 2026-09-15
- **Step:** `M1-S02` (`ui`)
- **Agent:** `metadata-builder` (run `2026-09-15T19-58-38Z`)
- **Kind:** design trade-off
- **What was recorded:** `Name`, `AccountId`, `StageName`, `CloseDate` and `Amount` are on both
  layouts per Q20, but none carries `behavior=Required`.
- **Alternative rejected:** extrapolating the platform's own Opportunity-layout-required field set
  from the Case set this library has verified (`ContactId`, `Description`, `SuppliedEmail`
  present, `Status` Required). Rejected because `admin/record-types-and-page-layouts`
  `references/metadata-examples.md` states in bold that the membership does not generalise, and
  `references/gotchas.md` Gotcha #13 names this exact temptation ("Do not generalise `Status` to
  `StageName` on Opportunity … without a dry run against the target org"). Carried as assumption
  **A25**, risk medium, with the iterate-the-dry-run discovery procedure in `deploy-order.md` § 3
  item 2.
- **Grounded in:** clarification Q20; `admin/record-types-and-page-layouts`
  `references/metadata-examples.md` and `references/gotchas.md` Gotcha #13; assumption A25.
- **Evidence:** both layout files (five `layoutItems` in the "Opportunity Information" section,
  all `Edit`); `artefacts/M1-S02/deploy-order.md` § 3 item 2;
  `envelopes/M1-S02/2026-09-15T19-58-38Z.json` → `extensions.decision_record[1]`.

## D-M1S02-03 — Neither layout ships a `relatedLists` block; Opportunity Products is deferred to a live-org retrieve

- **Date:** 2026-09-15
- **Step:** `M1-S02` (`ui`)
- **Agent:** `metadata-builder` (run `2026-09-15T19-58-38Z`)
- **Kind:** design trade-off / deviation from requirement item 2's expectation that reps see
  products on the layout
- **What was recorded:** neither file carries a `<relatedLists>` element, so a deployed layout
  shows no Opportunity Products related list.
- **Alternative rejected:** hand-authoring a `relatedLists` block naming the Opportunity Products
  related list. Rejected because the related-list API name appears in no skill in this library — a
  grep across `skills/` and `templates/` returns `RelatedOpportunityTeamList`,
  `RelatedNoteList` and `RelatedActivityList` and nothing else —
  `admin/opportunity-management` `references/metadata-examples.md` § 4 marks the one related-list
  example `UNVERIFIED (2026-09-04)` and instructs retrieving it from an org instead, and
  `admin/record-types-and-page-layouts` `references/metadata-examples.md` documents that
  related-list `fields` for standard fields are retrieval aliases, not API names (Fax/Mobile/Home
  Phone return as `Phone2`/`Phone3`/`Phone4`) — a hand-written name can round-trip wrong even when
  it deploys. Carried as assumption **A26**, risk medium, because this design-only build has no
  org connection to run the retrieve.
- **Grounded in:** clarification Q14 ("the products related list is on both"); `admin/opportunity-management`
  `references/metadata-examples.md` § 4; `admin/record-types-and-page-layouts`
  `references/metadata-examples.md`; assumption A26.
- **Evidence:** both layout files (no `relatedLists` element); `artefacts/M1-S02/deploy-order.md`
  § 0; `envelopes/M1-S02/2026-09-15T19-58-38Z.json` → `extensions.decision_record[2]`;
  **O-M1S02-01** below (the BLOCKING open item this decision creates).

## D-M1S02-04 — `Approval_Status__c` is `Readonly` on both layouts

- **Date:** 2026-09-15
- **Step:** `M1-S02` (`ui`)
- **Agent:** `metadata-builder` (run `2026-09-15T19-58-38Z`)
- **Kind:** design trade-off
- **What was recorded:** the "Discount Approval" section's `Approval_Status__c` `layoutItems`
  carries `behavior=Readonly` on both files.
- **Alternative rejected:** `Edit`. Rejected because the field is set by the M3 approval process,
  not typed by a rep — the field's own definition (`M1-S01`) reads "Set by the discount approval
  process. Blank means nothing has been submitted for this deal yet," and Q22 confirms nothing is
  rolled up from line items. A field update from a flow or approval action sets the value
  regardless of the layout item's behavior, so `Readonly` costs the approval process nothing while
  stopping a rep from typing "Approved" directly.
- **Grounded in:** clarification Q22; `artefacts/M1-S01/objects/Opportunity/fields/Approval_Status__c.field-meta.xml`;
  `decisions.md` D-M1S01-03.
- **Evidence:** both layout files ("Discount Approval" section, `layoutItems`
  `behavior=Readonly` `field=Approval_Status__c`); `envelopes/M1-S02/2026-09-15T19-58-38Z.json`
  → `extensions.decision_record[3]`.

## D-M1S02-05 — Neither layout carries `showEmailCheckbox`, `showRunAssignmentRulesCheckbox` or `showKnowledgeComponent`

- **Date:** 2026-09-15
- **Step:** `M1-S02` (`ui`)
- **Agent:** `metadata-builder` (run `2026-09-15T19-58-38Z`)
- **Kind:** design trade-off
- **What was recorded:** none of the three Case-oriented layout switches from the skill's worked
  example appear on either file.
- **Alternative rejected:** copying the three switches from the skill's Case worked example
  verbatim. Rejected because the object here is Opportunity, not Case, and
  `admin/record-types-and-page-layouts` `references/metadata-examples.md` states each switch is
  allowed only on specific objects and "deploying one on the wrong object fails."
- **Grounded in:** `requirement.md` (the object is Opportunity);
  `artefacts/M1-S01/objects/Opportunity/recordTypes/` (the record types this layout serves);
  `admin/record-types-and-page-layouts` `references/metadata-examples.md`.
- **Evidence:** both layout files (absence of all three elements);
  `envelopes/M1-S02/2026-09-15T19-58-38Z.json` → `extensions.decision_record[5]`.

## D-M1S02-06 — Two `TwoColumnsTopToBottom` sections, copied from the skill's Case worked example

- **Date:** 2026-09-15
- **Step:** `M1-S02` (`ui`)
- **Agent:** `metadata-builder` (run `2026-09-15T19-58-38Z`)
- **Kind:** design trade-off
- **What was recorded:** both layouts use the same two-section, two-column structure
  ("Opportunity Information", "Discount Approval"), `customLabel` true on both sections, one
  `emptySpace` in "Opportunity Information" to keep the columns aligned.
- **Alternative rejected:** none named as such — no Questions-to-Ask row governs section layout,
  so the shape (the style enum, the `emptySpace` cell, the columns-must-match-the-style rule) was
  taken directly from the skill's own worked example rather than invented.
- **Grounded in:** `admin/record-types-and-page-layouts` `references/metadata-examples.md` (the
  Case worked example's section/column/style shape).
- **Evidence:** both layout files (`layoutSections` ×2, `style` `TwoColumnsTopToBottom`,
  `layoutColumns` ×2 per section, one `emptySpace`); `envelopes/M1-S02/2026-09-15T19-58-38Z.json`
  → `extensions.decision_record[6]`.

---

## O-M1S02-01 — BLOCKING: the Opportunity Products related list must be retrieved-and-copied into both layouts before deploy

- **Date:** 2026-09-15 · **Recorded by:** `build-doc-keeper`, from the builder's envelope and
  `artefacts/M1-S02/deploy-order.md` § 0
- Neither layout file carries a `relatedLists` block, so a rep who opens either page as deployed
  cannot add a product line — `requirement.md` item 2 ("reps add products from our price book to
  every Enterprise opportunity") is **not satisfied** by these two files alone.
- **Why this build cannot close it itself:** `plan.json.build_mode` is `design-only`; the
  related-list API name is a retrieval alias absent from every skill in this library (see
  D-M1S02-03).
- **What must happen before deploy:** `sf project retrieve start --metadata
  "Layout:Opportunity-Opportunity Layout" --target-org <alias>`, then paste the Opportunity
  Products `<relatedLists>` element verbatim into both files.
- **Which requirement this decides:** `requirement.md` item 2 (the product-line-entry half) —
  `traceability.md` **REQ-010**, status `In Build` until this happens.
- **Evidence:** `artefacts/M1-S02/deploy-order.md` § 0;
  `envelopes/M1-S02/2026-09-15T19-58-38Z.json` → `extensions.open_items_for_the_human[0]`;
  `decisions.md` D-M1S02-03.

## O-M1S02-02 — The platform's own Opportunity layout-required-field set remains unverified

- **Date:** 2026-09-15 · **Recorded by:** `build-doc-keeper`, from the builder's envelope and
  `artefacts/M1-S02/deploy-order.md` § 3 item 2
- Assumption **A25**, risk medium: no field on either layout carries `behavior=Required`, and
  `admin/record-types-and-page-layouts` `references/metadata-examples.md` forbids extrapolating
  the verified Case set onto Opportunity.
- **Remedy:** iterate `python3 scripts/mock_deploy.py .sfskills/builds/northwind-sales/plan.json
  --org-alias <alias> --step M1-S02`, one missing field per run, applying every resulting fix to
  both files. `deploy-order.md` § 3 item 2 also corrects a plan-text mismatch: assumption A25 and
  the step's own manual acceptance test both name a `--dry-run` flag on `mock_deploy.py` that does
  not exist — the script's `--dry-run` behaviour needs no flag, per its own `--help`.
- **Evidence:** `artefacts/M1-S02/deploy-order.md` § 3 item 2;
  `envelopes/M1-S02/2026-09-15T19-58-38Z.json` → `extensions.decision_record[1]` and
  `process_observations` (ambiguous/medium, domain `checker-pass`); `decisions.md` D-M1S02-02.

## O-M1S02-03 — Design question for the M1 gate: the Enterprise and Renewal layouts are byte-identical

- **Date:** 2026-09-15 · **Recorded by:** `build-doc-keeper`, from the builder's envelope and
  `artefacts/M1-S02/deploy-order.md` § 3 item 4
- Both layout files are byte-for-byte identical; they differ only in file name. Nothing in the
  step's inputs, in Q14, or in Q20 gives the Renewal motion a field the Enterprise motion does not
  also carry — the second file exists because decision **D2** produced two record types, not
  because anyone asked for a different page.
- `admin/record-types-and-page-layouts` lists "record type with an identical page layout to
  another record type" as a merge candidate to surface proactively (SKILL.md Proactive Triggers;
  `references/llm-anti-patterns.md` Anti-Pattern 3).
- **This is not resolved here.** It is an open question for a human to decide at the M1 gate: keep
  both layouts as independently deployed files (defensible — it leaves room for the two motions to
  diverge later without a record-type change) or merge them into one shared layout referenced by
  both record types. Recorded as a question, not a decision, because inventing a Renewal-specific
  field or collapsing the pair would each assert an answer nobody gave.
- **Evidence:** `artefacts/M1-S02/layouts/*.layout-meta.xml` (byte-for-byte diff is empty except
  file name); `artefacts/M1-S02/deploy-order.md` § 3 item 4;
  `envelopes/M1-S02/2026-09-15T19-58-38Z.json` → `process_observations` (concerning/medium, domain
  `element-grounding`) and `extensions.open_items_for_the_human[2]`; `decisions.md` D2.

---

## D-M1S01-05 — Repair: no `BusinessProcess` value on Opportunity may carry `<default>true</default>`; supersedes D-M1S01-01's per-motion-default design

- **Date:** 2026-09-18
- **Step:** `M1-S01` (`object-model`)
- **Agent:** `metadata-builder` (run `2026-09-18T13-40-27Z`), re-tested by `step-tester` (run
  `2026-09-18T13-47-29Z`)
- **Kind:** deviation — the step was repaired after an org finding, for a reason that did not exist
  when D-M1S01-01 was made
- **Why the repair happened:** `reports/MOCK-DEPLOY-M1.md` run 1 (`mode manifest`, milestone M1)
  finding **N3-F-01 (HIGH)**: the org rejected both `BusinessProcess` components — *"Cannot specify a
  default on: Opportunity"* — because each shipped `<default>true</default>` on its opening stage
  (`Qualify` for `Enterprise_Sales_Process`, `Renewal Review` for `Renewal_Sales_Process`), exactly
  the shape D-M1S01-01 put there.
- **What changed** — two lines across two files, and nothing else: `<default>true</default>` removed
  from the `Qualify` `<values>` block in `Enterprise_Sales_Process.businessProcess-meta.xml` and from
  the `Renewal Review` `<values>` block in `Renewal_Sales_Process.businessProcess-meta.xml`. The other
  five `<values>` blocks in each file keep `<default>false</default>` unchanged; no other file among
  the step's nine outputs changed; `package.xml` was not touched (the repair edits a child element's
  value, not a member's existence).
- **Alternative rejected:** none — this is a repair forced by the org's own rejection (a HIGH
  mock-deploy finding), not a design choice between two live options. Run 2 confirms the narrower
  reading: the remaining `<default>false</default>` elements on the other stages were accepted, so
  the platform rejects a *true* default on this object's `BusinessProcess`, not the `<default>`
  element as such.
- **What it supersedes:** **D-M1S01-01**'s reasoning that "the per-motion default lives on the
  business process instead" (`Qualify` for Enterprise, `Renewal Review` for Renewal). That mechanism
  does not exist for Opportunity — the org refuses it outright. D-M1S01-01's other holding — that
  none of the eight `OpportunityStage` value-set stages may carry `<default>true</default>`, so the
  org's existing global default survives the §0 retrieve-and-merge untouched — is unaffected and
  stands. D-M1S01-01 is not rewritten; this entry names it, per the append-only rule.
- **Filed for the library:** `admin/opportunity-management` `references/metadata-examples.md` § 2's
  "New Business" sales-process sample — the authority D-M1S01-01 cited — ships
  `<default>true</default>` on the opening stage of an Opportunity `BusinessProcess`, the exact shape
  the org just rejected. This is a real deploy-time failure this build surfaced, not a misreading of
  the example; the skill needs either a gotcha or a per-object caveat before another build copies it
  onto Opportunity again. A second, independent occurrence of the same shape lives in
  `admin/path-and-guidance` `references/metadata-examples.md` § 1 (`Enterprise_New_Business_Process`),
  which this step does not cite and this repair did not touch.
- **Open item this repair creates:** with no value on either process now carrying
  `<default>true</default>`, no cited skill states what stage a new Enterprise or Renewal Opportunity
  opens on. Filed below as **O-M1S01-04**.
- **Grounded in:** `reports/MOCK-DEPLOY-M1.md` runs 1 and 2; `artefacts/M1-S01/deploy-order.md` § 6;
  `admin/opportunity-management` `references/metadata-examples.md` § 2 (the contradicted example);
  `admin/sales-process-mapping` `references/worked-examples.md` § 5 (the only documented `<default>`
  mechanism for `OpportunityStage`, unaffected by this repair).
- **Evidence:**
  `artefacts/M1-S01/objects/Opportunity/businessProcesses/Enterprise_Sales_Process.businessProcess-meta.xml`
  and `Renewal_Sales_Process.businessProcess-meta.xml` (both now 0× `<default>true</default>`, five
  `<default>false</default>` each, unchanged); `envelopes/M1-S01/2026-09-18T13-40-27Z.json` → the diff
  and Confidence sections; `envelopes/M1-S01/2026-09-18T13-47-29Z.json` → re-run checker results;
  `tests/M1-S01/results.json` (`"passed": true`, 5 ran, 0 failed, 2 manual, fresh `artefact_hashes`).

## O-M1S01-04 — UNVERIFIED: which stage a new Enterprise or Renewal Opportunity opens on, now that neither `BusinessProcess` carries a default

- **Date:** 2026-09-18 · **Recorded by:** `build-doc-keeper`, from `artefacts/M1-S01/deploy-order.md`
  § 6 and D-M1S01-05
- After D-M1S01-05 removed `<default>true</default>` from both processes' opening stage, none of this
  step's five cited skills (`admin/picklist-and-value-sets`, `admin/opportunity-management`,
  `admin/record-types-and-page-layouts`, `admin/object-creation-and-design`,
  `admin/sales-process-mapping`) documents a per-`BusinessProcess` or per-`RecordType` default-stage
  mechanism for Opportunity. The only `<default>` mechanism these skills document for
  `OpportunityStage` at all is the global `StandardValueSet`'s own element — the same one § 0 of
  `deploy-order.md` already preserves at the org's existing value during the retrieve-and-merge
  (D-M1S01-01, O-M1S01-01).
- **Recorded as `UNVERIFIED (2026-09-18)`, not as a grounded claim:** the likely mechanism is that a
  new Enterprise or Renewal Opportunity's Stage field takes whatever stage carries
  `<default>true</default>` on the global value set, with no per-process override — but no cited skill
  states this for Opportunity specifically, and if the org's existing global default is not one of
  the eight stages this step ships, or not a member of the Enterprise or Renewal stage subset, which
  stage a new record opens on is unresolved by anything in this step's `skills[]`.
- **Why this build cannot close it itself:** `plan.json.build_mode` is `design-only`; there is no org
  connection to run the verification query.
- **Close condition:** the § 4 post-deploy verification SOQL in `artefacts/M1-S01/deploy-order.md`
  (`SELECT ApiName, MasterLabel, SortOrder, DefaultProbability, ForecastCategoryName, IsActive,
  IsClosed, IsWon FROM OpportunityStage ORDER BY SortOrder`, cross-checked against
  `OpportunityStage.IsActive`/default membership for each process's stage subset) — not assumed from
  the UI, per the same section's instruction not to trust what "Qualify" or "Renewal Review" show as
  selected by default without running it.
- **Evidence:** `artefacts/M1-S01/deploy-order.md` § 6 ("Where the default stage now comes from") and
  § 4 (the verification SOQL); `envelopes/M1-S01/2026-09-18T13-40-27Z.json` → Confidence item 3 and
  Process Observations (concerning, medium); `decisions.md` D-M1S01-05.

---

## D-M1S02-07 — Repair: four `layoutItems` on both Opportunity layouts now carry `behavior=Required`, every one a platform requirement the org named or accepted; supersedes D-M1S02-02's "present but not `Required`" holding and narrows D-M1S02-01

- **Date:** 2026-09-18
- **Step:** `M1-S02` (`ui`)
- **Agent:** `metadata-builder` (runs `2026-09-18T13-39-55Z`, `2026-09-18T13-50-03Z`,
  `2026-09-18T13-54-29Z`), re-tested by `step-tester` (run `2026-09-18T14-00-27Z`)
- **Kind:** deviation — three repairs forced by three org findings, for reasons that did not exist
  when D-M1S02-01 and D-M1S02-02 were recorded on 2026-09-15
- **Why the repairs happened:** `reports/MOCK-DEPLOY-M1.md` runs 1–3 returned one HIGH finding per
  run against both layout files — exactly the one-field-at-a-time behaviour
  `admin/record-types-and-page-layouts` `references/gotchas.md` #12 predicts, which is why three
  rounds were needed rather than one:
  - **N3-F-02** (run 1, 2026-09-18T13:34Z) — *"Layout must contain an item for required layout
    field: Probability."* `Probability` was on neither file. This is the missing-item failure shape.
  - **N3-F-03** (run 2, 13:43Z) — *"Field:Name must be Required."* `Name` was present at
    `behavior=Edit`. This is the wrong-behavior failure shape, not a missing field.
  - **N3-F-04** (run 3, 13:52Z) — *"Field:StageName must be Required."* Same shape as N3-F-03.
- **What changed** — four `layoutItems` entries in each of the two files, and nothing else: a new
  `Probability` item (`Required`) added to the second `layoutColumns` of the "Opportunity
  Information" section immediately after `Amount`; `Name`, `StageName` and `CloseDate` changed
  `Edit` → `Required`. `AccountId` and `Amount` stay `Edit`, `Discount__c` stays `Edit`,
  `Approval_Status__c` stays `Readonly`; no section, column, `style` or `relatedLists` content
  changed. `artefacts/M1-S02/package.xml` was not touched — a `behavior` value is a child element,
  not a manifest member — and `tests/M1-S02/results.json` `artefact_hashes` confirms it: both layout
  hashes changed across these repairs while `package.xml`'s did not.
- **Alternative rejected:** writing `Edit` for each newly-named field, which is the least the first
  deploy message strictly asks for (the skill's layout-required-fields table says a platform-required
  field needs an *item*, at "any behavior"). Rejected per `gotchas.md` #13: a field the platform
  requires on the layout is a deploy precondition rather than the analyst's `Edit`/`Required` choice
  — the same shape as `Status` on Case — and runs 2 and 3 then proved the point twice by rejecting
  `Edit` on `Name` and `StageName` outright. The narrow bet paid: setting `Probability` to `Required`
  on run 1's evidence pre-empted a fourth round.
- **What it supersedes:** **D-M1S02-02**'s holding that Q20's five standard fields "ship present but
  not `Required`". Three of those five (`Name`, `StageName`, `CloseDate`) now carry `Required`, and a
  sixth field (`Probability`) the requester never named is on both layouts because the platform
  demands it. D-M1S02-02's *reasoning* — that the Opportunity layout-required set must not be
  extrapolated from Case and must be discovered by dry run — is not superseded; it is what produced
  these three findings. **D-M1S02-01** ("no layout item carries `behavior=Required`") is narrowed,
  not reversed: its subject was the *design-chosen* must-fill fields of Q11, and those —
  `Amount` and `Discount__c` — are still `Edit`, with enforcement still a validation-rule backlog for
  `M2-S03`/`M2-S04`. Neither earlier entry is rewritten; this one names them, per the append-only
  rule.
- **What the org proved, and what it did not.** `reports/MOCK-DEPLOY-M1.md` run 4 (13:57Z,
  `checkOnly`) reports **Succeeded, 9/9 components**, both `Layout` members ok — so the four-item
  configuration as shipped is *sufficient* to validate against the org, and assumption **A25** is
  discharged for these two files as they now stand. It does not follow that each of the four is
  individually *necessary*: `Probability`, `Name` and `StageName` were each named by the org in a
  message of its own, but `CloseDate` never was — it was set in the same pass as `StageName`, one
  round ahead of any finding, so run 4's silence is consistent both with `CloseDate` being
  platform-required and with `Required` merely being accepted on a field that did not need it. That
  residue is filed as **O-M1S02-04** rather than rounded up to "org-confirmed".
- **Filed for the library:** all four org facts are already routed to `admin/record-types-and-page-
  layouts` as Cursor task 18 (`reports/MOCK-DEPLOY-M1.md` runs 1–4 closing note) — `Probability`
  present on an Opportunity layout, and `Name`/`StageName`/`CloseDate` `Required`. Nothing in this
  build's cited skills held any of them before the dry run: `gotchas.md` #13 names the *pattern*
  (a platform-required field is a deploy precondition) and forbids generalising Case's set, but no
  skill carries Opportunity's own membership list.
- **Grounded in:** `reports/MOCK-DEPLOY-M1.md` runs 1–4; `artefacts/M1-S02/deploy-order.md` § 6 and
  its two subsections; `admin/record-types-and-page-layouts` `references/gotchas.md` #12 (one field
  per run) and #13 (platform-required behavior); the same skill's `references/metadata-examples.md`
  `behavior` table.
- **Evidence:** both files under `artefacts/M1-S02/layouts/` (each now 7 `layoutItems` plus one
  `emptySpace`; 4 × `Required`, 2 × `Edit`, 1 × `Readonly`);
  `envelopes/M1-S02/2026-09-18T13-39-55Z.json`, `…T13-50-03Z.json` and `…T13-54-29Z.json` →
  `extensions.decision_record`; `envelopes/M1-S02/2026-09-18T14-00-27Z.json` → checker results
  (exit 0, 1 REVIEW + 1 INFO); `tests/M1-S02/results.json` (`"passed": true`, 3 ran, 0 failed, 2
  manual, fresh `artefact_hashes`); `reports/mock-deploy/2026-09-18T13-57-17Z/summary.md`.

## O-M1S02-04 — UNVERIFIED: whether `CloseDate` is platform-required on an Opportunity layout, and two texts that still describe the required-field question as open

- **Date:** 2026-09-18 · **Recorded by:** `build-doc-keeper`, from `reports/MOCK-DEPLOY-M1.md` run 4,
  `artefacts/M1-S02/deploy-order.md` § 6 "Third discovery" and `plan.json` step `M1-S02`
  `acceptance_tests[4]`
- **The open fact.** `CloseDate` carries `behavior=Required` on both layouts on the strength of an
  inference (Opportunity's three `nillable=false` standard fields are `Name`, `StageName`,
  `CloseDate`), not of a deploy message naming it. Run 4 validated the pair 9/9 with `CloseDate`
  already `Required`, which proves the shipped configuration **deploys**; it cannot distinguish
  "the platform requires `CloseDate` on the layout" from "`Required` is merely accepted there". The
  only run that could have named `CloseDate` was run 3, and `gotchas.md` #12's one-field-per-run
  behaviour means its silence then proves nothing either. Recorded as `UNVERIFIED (2026-09-18)`.
- **Why this matters beyond this build:** the fact is on its way into the library as Cursor task 18.
  A skill rule that states `CloseDate` is layout-required on Opportunity would be asserting more than
  this build's evidence carries; a rule that states the four-item set validates is exactly what was
  observed.
- **Close condition:** one further `scripts/mock_deploy.py` round against a copy of either layout
  with `CloseDate` back at `behavior=Edit` and everything else unchanged — if the org answers
  *"Field:CloseDate must be Required"*, the claim is confirmed; if that run succeeds, `CloseDate`
  was never required and the entry is closed the other way. Cheap, decisive, and not run here: this
  agent does not build, edit or copy artefacts, and nothing in a documentation pass may touch an org.
- **Two texts still point at the older state, and neither is this agent's to edit.**
  1. `artefacts/M1-S02/deploy-order.md` § 6 "Third discovery (run 3)" carries the inline marker
     **`CloseDate` — UNVERIFIED (2026-09-18)** and instructs a later pass to "replace
     `UNVERIFIED (2026-09-18)` with a confirmed citation to that run" if run 4 is silent on it.
     `reports/MOCK-DEPLOY-M1.md` run 4 goes further and says the marker "resolves to confirmed at the
     next doc-keeper pass" — **it has not been resolved, on two grounds**: the doc keeper does not
     write inside `artefacts/` (`agents/build-doc-keeper/AGENT.md`, What This Agent Does NOT Do), and
     on the evidence above run 4 confirms sufficiency, not necessity. The marker is correct as it
     stands. Whoever clears it does so through a `documented` → `running` rebuild of `M1-S02` owned by
     `metadata-builder`, after the close condition above, not by hand.
  2. `plan.json` step `M1-S02` `acceptance_tests[4]` (the A25 manual test) still reads "…records that
     the platform's layout-required set for Opportunity is unverified and is discovered by iterating
     `scripts/mock_deploy.py --dry-run`, one field per run". The observable it names is still true
     and the test is still tickable, but a human reading only that line at the M1 gate would not learn
     that three fields are now org-confirmed and a fourth is shipped ahead of confirmation. Prose
     only — the test's `type`, `expected` and `scope` are unchanged — so the writer is
     `build_plan.py amend-step --prose-only`, the planner's call, not this agent's:
     `python3 scripts/build_plan.py amend-step .sfskills/builds/northwind-sales/plan.json M1-S02
     --prose-only --file <amendment.json> --by "<who>" --reason "A25 discharged for these two layouts
     by MOCK-DEPLOY-M1 runs 1-4; manual-test wording still says unverified"`. The same line also
     carries the older `--dry-run` flag error `O-M1S02-02` already recorded, so one amendment can
     close both.
- **Evidence:** `artefacts/M1-S02/deploy-order.md` § 6 "Third discovery (run 3) — StageName
  confirmed, CloseDate inferred"; `reports/MOCK-DEPLOY-M1.md` runs 3 and 4;
  `reports/mock-deploy/2026-09-18T13-57-17Z/summary.md` (Succeeded, 9 total, 0 errors);
  `envelopes/M1-S02/2026-09-18T13-54-29Z.json` → `extensions.decision_record[1]`;
  `envelopes/M1-S02/2026-09-18T14-00-27Z.json` → `process_observations` (concerning/low, domain
  `plan-documentation-drift`); `decisions.md` D-M1S02-02, D-M1S02-07, O-M1S02-02.

---

## O-M2S01-01 — Nothing in this build assigns `Sales_Ops_Validation_Bypass`; "only the sales-ops admin" is a design claim until the org confirms it

- **Date:** 2026-09-18 · **Recorded by:** `build-doc-keeper`, from the builder's envelope
  (`envelopes/M2-S01/2026-09-18T15-16-34Z.md` § 9, `O-M2S01-01`) and
  `artefacts/M2-S01/deploy-order.md` § 4
- `PermissionSetAssignment` is record data, not metadata
  (`admin/permission-set-architecture/references/metadata-examples.md` § 4); no manifest in this
  build assigns anything, and `plan.json` schedules no step that does. The M2 goal that "the
  sales-ops admin is the only person who can save past the discount-cap rule" is true of the
  *design* and unproven of any org.
- **Why this build cannot close it itself:** `plan.json.build_mode` is `design-only`; assignment is
  record data created against a live org, after deploy.
- **What must happen before go-live:** assign `Sales_Ops_Validation_Bypass` to the sales-ops admin
  and to nobody else (Q13), then run the `SetupEntityAccess` → `PermissionSetAssignment` query in
  `artefacts/M2-S01/deploy-order.md` § 4 and read `PermissionSet.IsOwnedByProfile` on the result —
  `true` means the grant arrived through a profile rather than through this set (the separate gap
  **O-M2S01-04** tracks that reading specifically).
- **Which requirement this decides:** `traceability.md` **REQ-012** — the row stays `In UAT`, never
  `Released`, until this query runs against the target org.
- **Evidence:** `artefacts/M2-S01/deploy-order.md` § 4 ("Post-deploy steps the deploy does not
  perform"); `envelopes/M2-S01/2026-09-18T15-16-34Z.json` →
  `extensions.open_items_for_the_human[0]`.

## O-M2S01-02 — CLOSED: `acceptance_tests[0]`'s stale fixture narration, closed by a prose-only amendment

- **Date recorded:** 2026-09-18 · **Recorded by:** `build-doc-keeper`, from the builder's and
  tester's envelopes and `plan.json` `steps[M2-S01].amendments[0]`
- **The open item, as first recorded:** `acceptance_tests[0].description` (the `custom-permissions`
  checker test) narrated a planning-stage fixture run — step scope "1 info", build scope "Consumers
  1" — that the step as actually built did not reproduce (0 info at both scopes, because the
  shipped description is 197 characters, under `CP-DESC-02`'s 200-character threshold, exactly as
  `inputs.note` asked; Consumers 0 at both scopes, because `M2-S03`, the validation rule that would
  reference this permission, does not exist yet). The narrated fixture also contradicted
  `inputs.note`'s own "keep it under 200 characters" instruction. Both the builder
  (`envelopes/M2-S01/2026-09-18T15-16-34Z.md` § 5) and the tester
  (`envelopes/M2-S01/2026-09-18T15-29-25Z.md`, "Concerning") recorded the drift independently and
  judged the test by its declared `expected: exit 0` and its declared command, not by the narrated
  numbers.
- **Closed by:** `plan.json` → `steps[M2-S01].amendments[0]`, written `--prose-only` at
  2026-09-18T15:32:48Z by "dry-run operator (Fable; design-only, nothing deploys)". The amendment
  replaced only the `description` field of all five `acceptance_tests[]` entries (every other
  structural field — `type`, `command`, `scope`, `expected` — unchanged index-for-index); the first
  entry's new text states the recorded runs ("Summary: 0 error(s), 0 warning(s), 0 info." at both
  scopes; Consumers 0 today; Consumers 1 once `M2-S03` ships) instead of the stale fixture numbers.
  `amendments[0].prose_only: true` confirms no structural field changed.
- **Not reopened:** the fix is to the plan's prose, not to an artefact or to a test's pass
  condition, and both runs that observed the drift had already judged the test by its declared
  `expected` value — no further test run is needed to confirm the close.
- **Evidence:** `plan.json` → `steps[M2-S01].amendments[0]` (`prose_only: true`, `reason` naming
  `O-M2S01-02` verbatim); `envelopes/M2-S01/2026-09-18T15-16-34Z.md` § 5; `tests/M2-S01/results.json`
  → `test_detail[2].divergence_from_plan_description`.

## O-M2S01-03 — No expiry answer on file; the grant ships as a permanent standing capability

- **Date:** 2026-09-18 · **Recorded by:** `build-doc-keeper`, from the builder's envelope § 9
  (`O-M2S01-03`) and `artefacts/M2-S01/deploy-order.md` § 4
- Neither cited skill's Questions-to-Ask row on expiry ("Is the grant permanent, or should it
  expire?") was answered by any clarification. `PermissionSetAssignment.ExpirationDate` (API 52.0+,
  `admin/permission-set-architecture/references/metadata-examples.md` § 4) is the platform's
  time-boxing mechanism, and it is unset by design here — the grant is treated as a standing
  capability of the sales-ops-admin role, not a migration window.
- **Why this is filed rather than left silent:** an unexpiring assignment made later is a decision
  worth seeing, not an oversight only once it is visible.
- **Remedy:** if the grant is ever handed to a person for a one-off data fix rather than to the
  standing role, use an expiring `PermissionSetAssignment` instead of a standing one. No
  `plan.json` clarification currently asks this question, so closing it is a clarification-and-answer,
  not a metadata change.
- **Evidence:** `artefacts/M2-S01/deploy-order.md` § 4 ("Expiry was considered and not applied");
  `envelopes/M2-S01/2026-09-18T15-16-34Z.json` → `extensions.open_items_for_the_human[2]` and
  `extensions.decision_record[6]` ("Is the grant permanent, or should it expire?").

## O-M2S01-04 — No live-org baseline for a pre-existing profile-borne grant

- **Date:** 2026-09-18 · **Recorded by:** `build-doc-keeper`, from the builder's envelope § 9
  (`O-M2S01-04`) and `artefacts/M2-S01/deploy-order.md` § 4
- `admin/custom-permissions` gotcha 1: a custom permission can already reach a user through a
  profile, invisibly to any permission-set-level review. This build has no org connection
  (`build_mode: design-only`) to query whether `Bypass_Opportunity_Sales_Validation` is already held
  by anyone through `System Administrator` or any other profile.
- **Why it matters alongside O-M2S01-01:** even after the permission set is assigned to the
  sales-ops admin alone, the same bypass could already be reachable by someone else through a
  profile a metadata retrieve never surfaces — only enabled grants are ever retrieved (gotcha 8),
  and a metadata diff can never prove a revocation.
- **Remedy:** run the `SetupEntityAccess` → `PermissionSetAssignment` query in
  `artefacts/M2-S01/deploy-order.md` § 4 against the target org before go-live, and read
  `PermissionSet.IsOwnedByProfile` on every result naming this permission.
- **Evidence:** `artefacts/M2-S01/deploy-order.md` § 4 ("Evidence is a query, not a diff");
  `envelopes/M2-S01/2026-09-18T15-16-34Z.json` → `extensions.open_items_for_the_human[3]` and
  `extensions.decision_record[5]` ("Does anything already hold this through a profile?").

---

## D-M2S02-01 — `Enterprise_Sales_Record_Types` grants record-type visibility only; field-level security is deliberately not carried here

- **Date:** 2026-09-19
- **Step:** `M2-S02` (`access`)
- **Agent:** `metadata-builder` (run `2026-09-19T14-25-55Z`)
- **Kind:** design trade-off
- **What was recorded:** `PermissionSet:Enterprise_Sales_Record_Types` carries exactly two
  `recordTypeVisibilities` entries (`Opportunity.Enterprise`, `Opportunity.Renewal`) and nothing
  else — no `objectPermissions`, `fieldPermissions`, `tabSettings`, `userPermissions` or
  `customPermissions` element.
- **Alternative rejected:** granting object or field access (including FLS on
  `Discount__c`/`Approval_Status__c`) inside this same set. Rejected because Q19 names the
  persona's access source as the org's pre-existing Sales Cloud permission set outside this build,
  the step's own `inputs{}` bind no field, and `check_access_model.py`'s `PSVP-FLS-01` rule — which
  fires on a permission set that grants object CRUD with zero field permissions — has nothing to
  attach to because this set grants no object permissions at all.
- **Grounded in:** clarification Q19; `artefacts/M2-S02/deploy-order.md` § 0;
  `skills/admin/permission-sets-vs-profiles/scripts/check_access_model.py` check 7 (`PSVP-FLS-01`).
- **Evidence:** `artefacts/M2-S02/permissionsets/Enterprise_Sales_Record_Types.permissionset-meta.xml`
  (no `objectPermissions`/`fieldPermissions` element); `envelopes/M2-S02/2026-09-19T14-25-55Z.json`
  → `extensions.decision_record[0]`, `[8]`, `[10]`; `artefacts/M2-S02/deploy-order.md` § 0. **Open
  item this decision creates:** **O-M2S02-01** below.

---

## O-M2S02-01 — HIGH: field-level security for `Discount__c` and `Approval_Status__c` is granted by no file across any access step in this build

- **Date:** 2026-09-19 · **Recorded by:** `build-doc-keeper`, from the builder's envelope
  (`process_observations`, concerning/high, domain `fls`) and `artefacts/M2-S02/deploy-order.md` § 0
- Three access files exist across `M2-S01` and `M2-S02` (`Sales_Ops_Validation_Bypass`,
  `Enterprise_Sales_Record_Types`, the `Sales User` profile overlay) and none carries a
  `fieldPermissions` block. `reports/MILESTONE-M1-REPORT.md` records the same zero from the M1 side
  and points at "M2-S01 / M2-S02". On deploy day, `Opportunity.Discount__c` and
  `Opportunity.Approval_Status__c` — both placed on the `M1-S02` layouts, both read or written by
  `M2-S03`'s validation rule and `M3-S02`'s approval process — are FLS-invisible to the 14 Sales
  User holders and to the deploying admin.
- **Why this build cannot close it itself:** `D-M2S02-01` above records that this step's `inputs{}`
  bind no field, and no other step in this build declares a field-grant output.
- **What must happen before deploy — a human's call, per `deploy-order.md` § 0:** either add the two
  `fieldPermissions` blocks to the org's existing Sales Cloud permission set as an `M4-S04`
  cutover-runbook item, or `amend-step` this step to declare a field-grant output and rebuild it
  (which reopens this step's `step:M2-S02` gate).
- **Which requirement this decides:** `traceability.md` **REQ-013**, **REQ-014** (this step's two
  rows) and **REQ-006**/**REQ-007** (the fields themselves) — none reaches `Released` until FLS
  exists somewhere in the build or the cutover runbook.
- **Evidence:** `envelopes/M2-S02/2026-09-19T14-25-55Z.json` → `process_observations`
  (concerning/high, domain `fls`); `artefacts/M2-S02/deploy-order.md` § 0;
  `reports/MILESTONE-M1-REPORT.md`.

## O-M2S02-02 — Accepted by design: `PSVP-FLS-02` WARN on the `Sales User` overlay

- **Date:** 2026-09-19 · **Recorded by:** `build-doc-keeper`, from the builder's envelope
  (`process_observations`, ambiguous/low, domain `access-model`) and
  `tests/M2-S02/check_access_model.stdout.txt`
- `check_access_model.py`'s step-scope run reports one WARN, `PSVP-FLS-02`: the profile overlay
  carries zero `objectPermissions`/`fieldPermissions` and no `PermissionSetGroup` exists anywhere in
  the scanned tree. The checker's own docstring calls the rule deliberately simplified — it asserts
  only that some group exists to be the claimed access source.
- **Why accepted rather than fixed:** this build designs no PSG at all; the access source is the
  org's pre-existing Sales Cloud permission set, outside this build's tree (`D-M2S02-01`). Inventing
  a `PermissionSetGroup` to silence the WARN would deploy a component nobody asked for.
- **Status:** accepted by design at this pass, not reopened, unless a human decides otherwise at the
  M2 gate.
- **Evidence:** `tests/M2-S02/check_access_model.stdout.txt` (score 97, 1 WARN finding
  `PSVP-FLS-02`); `envelopes/M2-S02/2026-09-19T14-25-55Z.json` → `process_observations`
  (ambiguous/low, domain `access-model`).

## O-M2S02-03 — UNVERIFIED (2026-09-19): the profile's exact `Name` in the target org

- **Date:** 2026-09-19 · **Recorded by:** `build-doc-keeper`, from the builder's envelope
  (`process_observations`, ambiguous/low, domain `naming`) and the inline marker in
  `artefacts/M2-S02/deploy-order.md`
- The `Profile` member and file stem are written `Sales User`, with its space, on the strength of
  Q19's phrase "the standard Sales User profile" alone — no cited skill file shows a space-carrying
  profile member as a worked example, so the form follows the stem-equals-member naming rule rather
  than a verified precedent. Marked `UNVERIFIED (2026-09-19)` inline in `deploy-order.md`.
- **Why it matters:** a mismatch between the shipped file stem/member and the org's actual profile
  `Name` is an `INVALID_CROSS_REFERENCE_KEY` on the profile half of this step only — the
  `PermissionSet` half does not depend on it.
- **Remedy:** confirm the exact profile `Name` in the target org before deploy (Setup → Profiles, or
  a metadata list retrieve).
- **Evidence:** `artefacts/M2-S02/deploy-order.md` (inline `UNVERIFIED (2026-09-19)` marker, "Where
  the files live" discussion); `envelopes/M2-S02/2026-09-19T14-25-55Z.json` →
  `process_observations` (ambiguous/low, domain `naming`).

## O-M2S02-04 — Prose drift: `acceptance_tests[1]`'s description narrates a stale fixture count

- **Date:** 2026-09-19 · **Recorded by:** `build-doc-keeper`, from the builder's and tester's
  envelopes and `plan.json` `steps[M2-S02].acceptance_tests[1].description`
- `acceptance_tests[1]` (`check_record_type_layouts.py`, build scope) narrates a planning-stage
  fixture run of "0 finding(s) detected"; the step as tested reproduces 1 finding instead — REVIEW
  `RTL-MERGE-01`, the pre-existing M1 identical-layouts item already adjudicated at the M1 gate as
  **O-M1S02-03**, resurfacing here only because this checker runs at build scope over the whole
  `artefacts/` tree. Both the builder and the tester recorded the drift independently
  (`envelopes/M2-S02/2026-09-19T14-25-55Z.json` and `…T14-39-24Z.json`, both concerning/low) and
  judged the test by its declared `expected: exit 0` and its declared command, not by the narrated
  numbers — the exit code is unaffected because the checker is lenient without `--strict`.
- **Not a test failure:** `tests/M2-S02/results.json` (`"passed": true`) stands as tested.
- **Remedy:** a prose-only amendment to `acceptance_tests[1].description` —
  `build_plan.py amend-step … --prose-only`, the planner's call, the same pattern **O-M2S01-02**
  already closed.
- **Evidence:** `plan.json` → `steps[M2-S02].acceptance_tests[1].description`;
  `tests/M2-S02/check_record_type_layouts.stdout.txt` (1 REVIEW finding);
  `envelopes/M2-S02/2026-09-19T14-25-55Z.json` and `…T14-39-24Z.json` → `process_observations`
  (concerning/low, domain `plan-documentation-drift`).

---

## D-M2S03-01 — The discount cap's relevance gate matches both Enterprise and Renewal record types, not Enterprise alone

- **Date:** 2026-09-19
- **Step:** `M2-S03` (`validation`)
- **Agent:** `metadata-builder` (run `2026-09-19T14-31-57Z`)
- **Kind:** design trade-off, and the source of an open item
- **What was recorded:** `Opportunity_Discount_Requires_Approval`'s relevance gate is
  `OR(RecordType.DeveloperName = "Enterprise", RecordType.DeveloperName = "Renewal")` — the rule
  gates both motions.
- **Alternative rejected:** gating `Enterprise` alone, the reading `requirement.md` item 2 supports
  in context. Rejected because `plan.json`'s `milestones[M2].goal` reads "an Enterprise or Renewal
  deal above a 20% discount", and `M3-S02` (pending) already declares its `entry_criteria_formula`
  as the identical `OR(RecordType.DeveloperName = "Enterprise", RecordType.DeveloperName =
  "Renewal")` — matching it keeps the validation rule and its own escape hatch, the approval
  process, gating the same population. An Enterprise-only rule would leave a Renewal deal blocked
  with no approval process able to accept the submission the rule demands.
- **Grounded in:** `plan.json` → `milestones[M2].goal`; `plan.json` →
  `steps[M3-S02].inputs.entry_criteria_formula` (sibling step record).
- **Open item this decision creates:** **O-M2S03-01** below — `requirement.md` item 2 and the
  milestone goal/`M3-S02` disagree on scope, and only a human can resolve which one is right.
- **Evidence:** `artefacts/M2-S03/objects/Opportunity/validationRules/Opportunity_Discount_Requires_Approval.validationRule-meta.xml`
  (`errorConditionFormula`); `envelopes/M2-S03/2026-09-19T14-31-57Z.json` →
  `extensions.decision_record[8]`, `extensions.open_items_for_the_human[0]`.

---

## O-M2S03-01 — Open scope question for the M2 gate: does the discount cap apply to Renewal deals?

- **Date:** 2026-09-19 · **Recorded by:** `build-doc-keeper`, from the builder's envelope
  (`open_items_for_the_human[0]`, id `O-M2S03-01`)
- `requirement.md` item 2, read in context, is Enterprise-only; the M2 milestone goal and
  `M3-S02`'s planned entry criteria both read Enterprise **or** Renewal. `D-M2S03-01` above records
  that the rule was written to match the milestone goal and `M3-S02`, not `requirement.md`'s
  narrower reading.
- **Remedy:** confirm the intended scope at the M2 gate. Narrowing the rule to Enterprise-only
  afterward is a one-line change to the `errorConditionFormula` in this file and, symmetrically, to
  `M3-S02`'s `entry_criteria_formula` once that step is built.
- **Evidence:** `requirement.md` item 2; `plan.json` → `milestones[M2].goal`,
  `steps[M3-S02].inputs.entry_criteria_formula`; `envelopes/M2-S03/2026-09-19T14-31-57Z.json` →
  `extensions.open_items_for_the_human[0]`; `decisions.md` **D-M2S03-01**.

## O-M2S03-02 — UNVERIFIED: assumption A8, that no legacy automation re-saves the record after a workflow field update

- **Date:** 2026-09-19 · **Recorded by:** `build-doc-keeper`, from the builder's envelope
  (`open_items_for_the_human[1]`) and `artefacts/M2-S03/deploy-order.md` § 6
- Custom validation rules do not re-run after a workflow field update re-saves a record. Assumption
  **A8** (risk medium) assumes no legacy automation writes `StageName`, `Amount`, `Discount__c` or
  `Approval_Status__c` after save; this cannot be checked offline in a `design-only` build.
- **Remedy:** before go-live, check Setup → Workflow Rules filtered to Opportunity in the target
  org.
- **Evidence:** `artefacts/M2-S03/deploy-order.md` § 6 ("What the formula does not protect
  against"); `envelopes/M2-S03/2026-09-19T14-31-57Z.json` → `extensions.open_items_for_the_human[1]`,
  `extensions.decision_record[7]`.

## O-M2S03-03 — Deploy-sequencing risk: the rule is active with no approval process yet built

- **Date:** 2026-09-19 · **Recorded by:** `build-doc-keeper`, from the builder's envelope
  (`open_items_for_the_human[2]`) and `artefacts/M2-S03/deploy-order.md` § 5
- The rule ships `active=true` (a deliberate choice — Q16 declines a clean-up window for the
  roughly six existing above-cap Enterprise deals) while `M3`'s approval process, the only
  non-bypass path to satisfy the rule, is still `pending`. Between an `M2`-only deploy and `M3`'s,
  any of those existing deals that reaches `Closed Won` is blocked with no submit path except the
  sales-ops-admin bypass.
- **Remedy — a human's call:** deploy `M2` and `M3` together, or accept the window explicitly and
  communicate it to the sales-ops admin before `M2` goes live alone.
- **Evidence:** `artefacts/M2-S03/deploy-order.md` § 5 ("`active` is `true`, and that is a decision
  rather than a default"); `envelopes/M2-S03/2026-09-19T14-31-57Z.json` →
  `extensions.open_items_for_the_human[2]`, `extensions.decision_record[4]`.

## O-M2S03-04 — Nothing proves the bypass bypasses until someone holds it

- **Date:** 2026-09-19 · **Recorded by:** `build-doc-keeper`, from the builder's envelope
  (`open_items_for_the_human[3]`) and `artefacts/M2-S03/deploy-order.md` § 8
- `check_custom_permissions.py` and `check_validation_rules.py` match the `$Permission` token's
  spelling against the `CustomPermission` file's name, not against a live grant —
  `PermissionSetAssignment` ships in no manifest in this build (same gap as **O-M2S01-01**/
  **O-M2S01-04**). Nothing in this build's checkers can distinguish "the permission is unassigned"
  from "the API name diverged" if the bypass is ever exercised and fails.
- **Remedy:** assign `Sales_Ops_Validation_Bypass` to the sales-ops admin, then save a Closed Won
  Opportunity at 25% discount with no approval as that user, per the procedure in
  `deploy-order.md` § 8. The two Apex tests that would make this a regression test rather than a
  one-off click-through are named in `admin/validation-rules/references/metadata-examples.md` but
  are in no step of this build.
- **Evidence:** `artefacts/M2-S03/deploy-order.md` § 8 ("After the deploy — the two checks metadata
  cannot make"); `envelopes/M2-S03/2026-09-19T14-31-57Z.json` →
  `extensions.open_items_for_the_human[3]`; `decisions.md` **O-M2S01-01**, **O-M2S01-04**.

---

## O-M2S05-01 — Checker-coverage gap: `check_sales_process_mapping.py` at step scope asserts nothing

- **Date:** 2026-09-19 · **Recorded by:** `build-doc-keeper`, from the builder's and tester's
  envelopes and `artefacts/M2-S05/deploy-order.md` § 7
- `check_sales_process_mapping.py --manifest-dir artefacts/M2-S05` exits 0 but its own stdout reads
  "Scanned 0 file(s) — nothing asserted; check --manifest-dir". The checker was added by
  `amend-step --add-checker` on 2026-09-18 to close a § 5 coverage warning (the step cites
  `admin/sales-process-mapping` in `skills[]`), but this step's artefacts are `PathAssistant`/
  `Settings` XML, not the `*.yaml`/`*.yml`/`*.csv` sales-process maps or retrieved
  `OpportunityStage` value set that checker inspects.
- **Remedy — a human's call, per `deploy-order.md` § 7:** re-declare the test at `scope: "build"`
  with `--manifest-dir artefacts` (where the same command does read `M1-S01`'s value set and prints
  "No issues found"), move it to an `M2` milestone acceptance test, or drop the citation and record
  that the skill was used only for its Questions-to-Ask table (Q2's source).
- **Evidence:** `tests/M2-S05/check_sales_process_mapping.out`; `artefacts/M2-S05/deploy-order.md`
  § 7; `envelopes/M2-S05/2026-09-19T14-26-26Z.json` and `…T14-45-08Z.json` →
  `process_observations` (concerning/low, domain `checker-coverage`).

## O-M2S05-02 — Prose drift: the step's `inputs.note` still calls `M2-S04` blocked

- **Date:** 2026-09-19 · **Recorded by:** `build-doc-keeper`, from the builder's envelope
  (`open_items_for_the_human[1]`)
- `plan.json` `steps[M2-S05].inputs.note` states "M2-S04 is blocked and words are what is left"
  (referring to the Discover-step info text carrying the product gate in prose because the
  enforcing rule did not exist). `M2-S04`'s own `inputs.note` records it was unblocked 2026-09-15,
  and `plan.json`'s step status for `M2-S04` is not `blocked`. The prose in `M2-S05`'s note is
  stale.
- **Remedy:** a prose-only amendment, the planner's call — `build_plan.py amend-step M2-S05
  --prose-only`, correcting the note's characterisation of `M2-S04`.
- **Evidence:** `plan.json` → `steps[M2-S05].inputs.note`, `steps[M2-S04].inputs.note`;
  `envelopes/M2-S05/2026-09-19T14-26-26Z.json` → `extensions.open_items_for_the_human[1]`.

## O-M2S05-03 — The Closed Won handoff to Finance and Customer Success (Q3) is carried by no path step

- **Date:** 2026-09-19 · **Recorded by:** `build-doc-keeper`, from the builder's envelope
  (`open_items_for_the_human[2]`) and `plan.json` `steps[M2-S05].inputs.key_fields_by_stage`
- Q3's answer (Finance needs amount/products/discount/close date; Customer Success needs
  account/products/contract start at Closed Won) names a handoff at Closed Won.
  `key_fields_by_stage` carries no `Closed Won` row, and neither path's `pathAssistantSteps`
  addresses it — by the plan's explicit instruction that Closed Won and Closed Lost carry no step
  (a missing step means unconfigured, not absent; the chevron still renders). No step anywhere in
  this build's `plan.json` builds this handoff.
- **Remedy:** a decision for the VP at the M2 gate — whether the handoff needs a Path step's info
  text, a Flow notification, or is out of this build's scope entirely.
- **Evidence:** clarification Q3; `plan.json` → `steps[M2-S05].inputs.key_fields_by_stage` (no
  `Closed Won` key); `envelopes/M2-S05/2026-09-19T14-26-26Z.json` → `extensions.decision_record`
  (the Q3 row) and `extensions.open_items_for_the_human[2]`.

## O-M2S05-04 — Cross-step dependency: `Renewal_Opportunity_Path` may have no Lightning record page carrying the Path component

- **Date:** 2026-09-19 · **Recorded by:** `build-doc-keeper`, from the builder's envelope
  (`open_items_for_the_human[3]`) and `artefacts/M2-S05/deploy-order.md` § 3
- `M3-S05` (pending) rebuilds the Enterprise Lightning record page only — its own step note records
  the decision explicitly ("Only the Enterprise page is built... the Renewal record type falls
  through to the org's existing Opportunity page"). `Renewal_Opportunity_Path` therefore renders
  only if Northwind's **current** Opportunity record page already carries the
  `runtime_sales_pathassistant:pathAssistant` component. Nothing in this build asserts that it
  does, and `check_path_and_guidance.py`'s FlexiPage check stays silent by construction when no
  FlexiPage is in the manifest at all (this step's case, and the whole of M2).
- **Remedy:** before the M2 gate, run the retrieve-and-grep `deploy-order.md` § 3 gives:
  `sf project retrieve start --metadata "FlexiPage" --target-org <alias>` then
  `grep -rl "runtime_sales_pathassistant:pathAssistant" force-app/main/default/flexipages/`.
- **Evidence:** `artefacts/M2-S05/deploy-order.md` § 3 ("And M3-S05 covers only the Enterprise
  record type"); `plan.json` → `steps[M3-S05]`; `envelopes/M2-S05/2026-09-19T14-26-26Z.json` →
  `extensions.open_items_for_the_human[3]`.

## O-M2S05-05 — No metadata element exists for stage-advance celebration; it is a manual Setup step if wanted

- **Date:** 2026-09-19 · **Recorded by:** `build-doc-keeper`, from the builder's envelope
  (`open_items_for_the_human[4]`)
- Path celebration ("confetti" on reaching a milestone stage) has no representation in
  `PathAssistant` metadata. If it is wanted on Closed Won, it is a manual Setup action in
  production and in every sandbox refreshed afterward.
- **Remedy:** add it to the `M4-S04` cutover runbook if the VP wants it; not actionable by any
  metadata step.
- **Evidence:** `envelopes/M2-S05/2026-09-19T14-26-26Z.json` →
  `extensions.open_items_for_the_human[4]`, `extensions.decision_record` (the "who advances the
  stage" row).

## O-M2S05-06 — UNVERIFIED: whether the 20% discount-approval rule is meant to apply to Renewal opportunities

- **Date:** 2026-09-19 · **Recorded by:** `build-doc-keeper`, from the builder's envelope
  (`open_items_for_the_human[5]`)
- The Renewal Proposed step's info text names the discount-approval rule by inference from
  `D-M2S03-01`'s both-record-types reading, not from a direct answer — clarification **Q58**
  ("does the discount policy apply to renewals the same way") is still open.
- **Remedy:** if Renewal is ultimately exempted at the M2 gate (see **O-M2S03-01**), strike the
  sentence naming it from the Renewal Proposed step's info text — a rebuild of this step, not a
  prose-only amendment, because it is metadata content rather than plan prose.
- **Evidence:** `artefacts/M2-S05/pathAssistants/Renewal_Opportunity_Path.pathAssistant-meta.xml`
  (Renewal Proposed step info text); `envelopes/M2-S05/2026-09-19T14-26-26Z.json` →
  `extensions.open_items_for_the_human[5]`; `decisions.md` **O-M2S03-01**.

---

## D-M2S04-01 — The product-gate's record-type scope is Enterprise only, diverging from `M2-S03`'s Enterprise-and-Renewal scope

- **Date:** 2026-09-19
- **Step:** `M2-S04` (`validation`)
- **Agent:** `metadata-builder` (run `2026-09-19T14-41-29Z`)
- **Kind:** design trade-off
- **What was recorded:** `Opportunity_Products_Required_At_Propose`'s `errorConditionFormula` gates
  `RecordType.DeveloperName = "Enterprise"` only — no clause reaching `Renewal`, unlike `M2-S03`'s
  discount-cap rule.
- **Alternative rejected:** matching `M2-S03`'s Enterprise-**and**-Renewal scope. Rejected on the
  2026-09-15 amendment's own terms (step inputs) and on the cited worked example's stated reasoning
  that "Renewals run a different process and must not be gated" — and, as a practical matter,
  `Renewal_Sales_Process` carries no `Propose` stage at all, so widening this rule to Renewal would
  need Renewal's own stage names (`Renewal Review`, `Renewal Proposed`) substituted into the rule's
  `OR`, not merely a second `RecordType` clause.
- **Grounded in:** `plan.json` → `steps[M2-S04].amendments[0]` (the 2026-09-15 unblock);
  `skills/admin/validation-rules/references/examples.md` ("At Least One Opportunity Product Before a
  Late Stage (Opportunity)"); `artefacts/M1-S01/objects/Opportunity/businessProcesses/Renewal_Sales_Process.businessProcess-meta.xml`
  (no `Propose` stage).
- **Open item this decision creates:** **O-M2S04-01** below — the scope disagreement with `M2-S03`,
  for the M2 gate to resolve.
- **Evidence:**
  `artefacts/M2-S04/objects/Opportunity/validationRules/Opportunity_Products_Required_At_Propose.validationRule-meta.xml`
  (`errorConditionFormula`); `envelopes/M2-S04/2026-09-19T14-41-29Z.json` →
  `extensions.decision_record[10]`, `extensions.open_items_for_the_human[0]`;
  `artefacts/M2-S04/deploy-order.md` § 9 ("The record-type disagreement with M2-S03").

## D-M2S04-02 — Repair: `<description>` rewritten from 766 to 205 characters after org rejection N3-F-06; `deploy-order.md` § 2.1 moves from UNVERIFIED to ORG-VERIFIED on the same run

- **Date:** 2026-09-19
- **Step:** `M2-S04` (`validation`)
- **Agent:** `metadata-builder` (run `2026-09-19T15-08-49Z`), re-tested by `step-tester` (run
  `2026-09-19T15-15-42Z`)
- **Kind:** deviation — a repair forced by an org rejection, for a reason that did not exist when the
  step was first built
- **Why the repair happened:** `reports/MOCK-DEPLOY-M2.md` run 1 (`mode manifest`, milestones M1+M2,
  `reports/mock-deploy/2026-09-19T14-56-10Z/`) finding **N3-F-06**: *"Validation rule description
  cannot be longer than 255 characters long."* The shipped `<description>` was 766 characters — the
  first build wrote both of § 2's UNVERIFIED claims into it, on top of the business justification and
  bypass name `skills/admin/validation-rules` Recommended Workflow step 4 asks the element to carry.
- **What changed** — one element, and nothing else: `<description>` rewritten to 205 characters
  (business justification and bypass name only). `<fullName>`, `<active>`, `<errorConditionFormula>`,
  `<errorDisplayField>` and `<errorMessage>` are byte-identical to what run 1 validated, confirmed by
  reconstructing the pre-repair file from the prior envelope and diffing it against the repaired file
  on disk; `package.xml` is unchanged (a description is not a manifest member) —
  `tests/M2-S04/results.json` `artefact_hashes` records the rule file and `deploy-order.md` as
  changed and `package.xml` as unchanged.
- **A fact settled by the same run, not itself part of the repair:** `deploy-order.md` § 2.1
  (whether `HasOpportunityLineItem` is addressable inside a validation-rule formula, carried as
  `UNVERIFIED (2026-09-15)` since the step was unblocked) is now **ORG-VERIFIED (2026-09-19)** — run
  1's `checkOnly` compile of this rule's formula returned no field-availability or unknown-token
  error, and the *only* error it returned for this component was the description-length rejection
  repaired here. § 2.2 (whether the rule re-fires after a line-item deletion) is unaffected and
  **stays UNVERIFIED** — a `checkOnly` deploy exercises no deletion.
- **Alternative rejected:** none — this is a repair forced by the org's own rejection, not a design
  choice between two live options.
- **Filed for the library:** `skills/admin/validation-rules` caps `errorMessage` at 255 characters
  but is silent on a `description` ceiling, and `check_validation_rules.py` carries no length rule
  for `description` — nothing in this step's declared checkers would have caught the 766-character
  value before an org did. Queued as **VR-DESC-01** (Cursor task 18), the same filing
  `reports/MOCK-DEPLOY-M2.md` records for this finding.
- **Grounded in:** `reports/MOCK-DEPLOY-M2.md` run 1; `artefacts/M2-S04/deploy-order.md` §§ 2.1, 6;
  `skills/admin/validation-rules` Recommended Workflow step 4.
- **Evidence:**
  `artefacts/M2-S04/objects/Opportunity/validationRules/Opportunity_Products_Required_At_Propose.validationRule-meta.xml`
  (`<description>` now 205 characters); `envelopes/M2-S04/2026-09-19T15-08-49Z.json` → the diff
  section; `tests/M2-S04/results.json` (`"passed": true`, `artefact_hashes`);
  `reports/mock-deploy/2026-09-19T15-26-20Z/` (run 3, Succeeded 18/18, the gate evidence this repair
  contributes to).

---

## O-M2S04-01 — Open scope question for the M2 gate: does the product gate at Propose apply to Renewal deals too?

- **Date:** 2026-09-19 · **Recorded by:** `build-doc-keeper`, from the builder's envelope
  (`envelopes/M2-S04/2026-09-19T14-41-29Z.md` § 10, id `O-M2S04-01`) and `artefacts/M2-S04/deploy-order.md` § 9
- `M2-S03` gates its discount cap on **Enterprise and Renewal**, citing the M2 milestone goal; this
  step's amended formula gates **Enterprise only**, citing the worked example's own reasoning that
  Renewals run a different process. Both are defensible and the two rules serve different business
  conditions, so this is not necessarily a defect — but a reader comparing the two files will notice.
- **Remedy:** decide Enterprise-only vs Enterprise-and-Renewal at the M2 gate. Widening this rule to
  Renewal also needs the Renewal stage list rewritten into the `OR` (`Renewal Review`,
  `Renewal Proposed`) — `Renewal_Sales_Process` has no `Propose` stage at all, so a second
  `RecordType` clause alone would not work.
- **Evidence:** `artefacts/M2-S04/deploy-order.md` § 9 ("The record-type disagreement with M2-S03 —
  for the M2 gate, not for this file"); `envelopes/M2-S04/2026-09-19T14-41-29Z.json` →
  `extensions.open_items_for_the_human[0]`; `decisions.md` **D-M2S04-01**, **D-M2S03-01**,
  **O-M2S03-01**.

## O-M2S04-02 — Q42 is still open; assumption A7 stood in for it

- **Date:** 2026-09-19 · **Recorded by:** `build-doc-keeper`, from the builder's envelope
  (`envelopes/M2-S04/2026-09-19T14-41-29Z.md` § 10, id `O-M2S04-02`)
- Q42 ("enforced everywhere, or standard UI only?") is still `open` in `plan.json`. Assumption **A7**
  (risk low) stood in for it, and it is the only Questions-to-Ask row this step answered with a
  default rather than a recorded answer — the reason `question-coverage` is `partial` in
  `dimensions_skipped` and confidence is capped at MEDIUM on both builder runs.
- **Remedy:** have the Sales Operations lead answer Q42.
- **Evidence:** `plan.json` → `clarifications[Q42]` (`status: open`), `steps[M2-S04].inputs.defaults_applied`
  (`{"Q42": "A7"}`); `envelopes/M2-S04/2026-09-19T14-41-29Z.json` →
  `extensions.open_items_for_the_human[1]`, `dimensions_skipped[0]`.

## O-M2S04-03 — Milestone M2's own acceptance tests still narrate this step as blocked

- **Date:** 2026-09-19 · **Recorded by:** `build-doc-keeper`, from the builder's envelope
  (`envelopes/M2-S04/2026-09-19T14-41-29Z.md` § 10, id `O-M2S04-03`)
- `plan.json` → `milestones[M2].acceptance_tests[3]` and `[4]` still read this rule as absent from any
  manifest and this step as blocked. The 2026-09-15 amendment made both statements false, and this
  build now makes them visibly false. No `build_plan.py` writer can correct a **milestone**
  acceptance test's prose while the build is `building` — `amend-step --prose-only` writes a step,
  not a milestone, and `set-plan` is refused while the build is `building` (`PLAN_FROZEN_STATUSES`).
- **Remedy:** raise it at the M2 gate; correcting milestone-level test prose needs either a scoped
  writer this layer does not yet have, or a re-plan the build's current status forbids.
- **Evidence:** `plan.json` → `milestones[M2].acceptance_tests[3].description`, `[4].description`;
  `envelopes/M2-S04/2026-09-19T14-41-29Z.json` → `extensions.open_items_for_the_human[2]`,
  Process Observations (concerning).

## O-M2S04-04 — Creation directly at a gated stage is not blocked, by design

- **Date:** 2026-09-19 · **Recorded by:** `build-doc-keeper`, from the builder's envelope
  (`envelopes/M2-S04/2026-09-19T14-41-29Z.md` § 10, id `O-M2S04-04`)
- `NOT(ISNEW())` means an Enterprise deal created directly at `Propose` with zero products **saves**
  — it is caught only at its next stage change (`ISCHANGED(StageName)`). No clarification asked for
  creation itself to be blocked.
- **Remedy:** if the requester wants creation blocked too, `admin/validation-rules/references/gotchas.md`
  Gotcha 15 is explicit that this needs a **separate** `ISNEW()` rule with its own message, never a
  clause folded into this one.
- **Evidence:** `artefacts/M2-S04/objects/Opportunity/validationRules/Opportunity_Products_Required_At_Propose.validationRule-meta.xml`
  (`NOT(ISNEW())`, `ISCHANGED(StageName)`); `envelopes/M2-S04/2026-09-19T14-41-29Z.json` →
  `extensions.open_items_for_the_human[3]`.

## O-M2S04-05 — Nothing in this build proves the rule actually fires

- **Date:** 2026-09-19 · **Recorded by:** `build-doc-keeper`, from the builder's envelope
  (`envelopes/M2-S04/2026-09-19T14-41-29Z.md` § 10, id `O-M2S04-05`)
- The two Apex tests that would turn this into a regression test rather than a one-off click-through
  are named in `admin/validation-rules/references/metadata-examples.md`; no step of this build owns
  them. `artefacts/M2-S04/deploy-order.md` § 11 carries the manual equivalents (save at Propose with
  no products as a rep and as the bypass holder).
- **Remedy:** before go-live, run the manual equivalents in `deploy-order.md` § 11, or add a step
  that owns the two Apex tests.
- **Evidence:** `artefacts/M2-S04/deploy-order.md` § 11 ("After the deploy — the checks metadata
  cannot make"); `envelopes/M2-S04/2026-09-19T14-41-29Z.json` →
  `extensions.open_items_for_the_human[4]`.

## O-M2S04-06 — A build-scoped test's recorded evidence went stale while this step was being written, and no guard can see it

- **Date:** 2026-09-19 · **Recorded by:** `build-doc-keeper`, from the builder's envelope
  (`envelopes/M2-S04/2026-09-19T14-41-29Z.md` § 10, id `O-M2S04-06`, and its Process Observations)
- `tests/M2-S03/check_validation_rules.stdout.txt` was written at 14:37:47Z, 88 seconds before this
  step wrote the second `ValidationRule` into the shared `artefacts/` tree at 14:39:15Z. `M2-S03` is
  recorded `tested` on that now-stale evidence: the same build-scoped command, re-run today, reports
  2 rules and 1 REVIEW finding rather than 1 rule and 0 findings — still exit 0, so the pass itself
  still holds, but the stored output describes a tree that no longer exists. The
  `artefact_hashes` stale-pass guard cannot catch this because it hashes each step's own artefacts,
  and `M2-S03`'s did not change.
- **Remedy:** re-run `M2-S03`'s build-scoped checker before the M2 gate to refresh its stored
  evidence, or accept that a build-scoped test's evidence is only as current as the last step written
  into `artefacts/` — a scope-hash over the tree the command actually reads (rather than only the
  step's own artefacts) would close this generally, and is filed as a library gap alongside
  `VR-DESC-01`.
- **Evidence:** file mtimes, `tests/M2-S03/check_validation_rules.stdout.txt` vs
  `artefacts/M2-S04/objects/Opportunity/validationRules/Opportunity_Products_Required_At_Propose.validationRule-meta.xml`;
  `envelopes/M2-S04/2026-09-19T14-41-29Z.json` → `extensions.open_items_for_the_human[5]`, Process
  Observations (concerning).

---

## D-M2S02-02 — Repair: the `Sales User` profile overlay's `recordTypeVisibilities` block is dropped entirely after org rejection N3-F-05; record-type visibility is now carried solely by the permission set

- **Date:** 2026-09-19
- **Step:** `M2-S02` (`access`)
- **Agent:** `metadata-builder` (run `2026-09-19T15-22-09Z`), re-tested by `step-tester` (run
  `2026-09-19T15-29-15Z`)
- **Kind:** deviation — a repair forced by an org rejection
- **Why the repair happened:** `reports/MOCK-DEPLOY-M2.md` run 1 finding **N3-F-05**: *"No default
  record type specified for recordTypeVisibility: Opportunity. To make the '--master--' record type
  the default, set visible on all record types to false."* The profile as first built carried two
  `recordTypeVisibilities` entries (`Opportunity.Enterprise`, `Opportunity.Renewal`), both
  `visible=true`, `default=false`, naming no default — the platform requires a profile's *stated*
  record-type block for an object to name a default, or to mark every listed type invisible.
- **What changed:** both `recordTypeVisibilities` blocks removed from `Sales User.profile-meta.xml`;
  its two `layoutAssignments` blocks are byte-identical to before. Visibility for
  `Opportunity.Enterprise`/`Opportunity.Renewal` is now carried solely by
  `Enterprise_Sales_Record_Types` (which has no `default` field to move), and the profile's silence
  leaves the org's existing default Opportunity record type untouched — the same overlay mechanism
  the step's original design already rested on (`admin/permission-sets-vs-profiles`).
- **Alternative rejected:** naming a default among the two new record types (would move the SMB
  team's default, violating Q4) or marking every listed type invisible (would undo the step's
  purpose). The repair is neither — the block is dropped entirely.
- **Filed for the library:** no cited skill or checker states the profile
  default-or-invisible-all rule the org just enforced; recorded as **PSVP-RT-DEFAULT-01**, filed
  alongside N3-F-05's own filing (Cursor task 18).
- **Grounded in:** `reports/MOCK-DEPLOY-M2.md` run 1; `artefacts/M2-S02/deploy-order.md` § 6
  ("Repair after run 1"); `skills/admin/permission-sets-vs-profiles/references/metadata-examples.md`
  (overlay-silence rule).
- **Evidence:** `artefacts/M2-S02/profiles/Sales User.profile-meta.xml` (0 `recordTypeVisibilities`
  elements); `envelopes/M2-S02/2026-09-19T15-22-09Z.json` → the diff section; `tests/M2-S02/results.json`
  → `artefact_hashes` (profile file changed, `package.xml` unchanged); `reports/mock-deploy/2026-09-19T15-26-20Z/`
  (run 3, Succeeded 18/18, the gate evidence this repair contributes to). This repair is also what
  made the step's manual test 1 (Q4/Q9) stale as first worded — corrected by the prose-only
  amendment at `plan.json` → `steps[M2-S02].amendments[1]` (2026-09-19T15:33:50Z), reflected in
  `traceability.md` REQ-014 in this pass.

## D-M2S02-03 — Repair, by requester decision: `Enterprise_Sales_Record_Types` gains `fieldPermissions` for `Discount__c` (edit) and `Approval_Status__c` (read), narrowing D-M2S02-01's "field-level security is deliberately not carried here" holding and closing HIGH open item O-M2S02-01

- **Date:** 2026-09-19
- **Step:** `M2-S02` (`access`)
- **Agent:** `metadata-builder` (run `2026-09-19T15-22-09Z`), re-tested by `step-tester` (run
  `2026-09-19T15-29-15Z`)
- **Kind:** deviation — a requester decision taken at the repair pass, distinct from D-M2S02-02's
  org-forced repair above
- **What was recorded:** two `fieldPermissions` blocks added to
  `Enterprise_Sales_Record_Types.permissionset-meta.xml` — `Opportunity.Discount__c`
  (`readable=true`, `editable=true`) and `Opportunity.Approval_Status__c` (`readable=true`,
  `editable=false` — the M3 approval process is the intended writer, matching the field's own
  definition from `M1-S01`, "Set by the discount approval process"). No `objectPermissions` were
  added; Q19's existing org Sales Cloud permission set is untouched. The set's `description` was
  revised to state the widened scope (195 characters, under both `check_permission_set_architecture.py`
  length thresholds).
- **What it supersedes:** **D-M2S02-01**'s "field-level security is deliberately not carried here"
  holding, made when this step's `inputs{}` bound no field. D-M2S02-01's other holding — that this
  permission set grants no object-level, tab or system permission — is unaffected and stands.
  D-M2S02-01 is not rewritten; this entry names it, per the append-only rule.
- **Alternative rejected:** adding the FLS to the org's existing Sales Cloud permission set as an
  `M4-S04` cutover-runbook item instead — the other remedy **O-M2S02-01** originally named. Rejected
  by requester decision at this repair, in favour of granting it inside this build's own permission
  set.
- **Grounded in:** requester decision at the repair pass (2026-09-19); `decisions.md` D-M2S02-01,
  O-M2S02-01 (the HIGH gap this closes); `skills/admin/permission-set-architecture/references/metadata-examples.md`
  (`fieldPermissions` element shape).
- **Evidence:** `artefacts/M2-S02/permissionsets/Enterprise_Sales_Record_Types.permissionset-meta.xml`
  (2 `fieldPermissions` blocks); `envelopes/M2-S02/2026-09-19T15-22-09Z.json` → the diff section;
  `tests/M2-S02/check_access_model.stdout.txt` (`PSVP-FLS-01` stays silent — no `objectPermissions`
  element exists for it to fire on); `reports/mock-deploy/2026-09-19T15-26-20Z/` (run 3, Succeeded
  18/18 — both new `fieldPermissions` grants deploy clean).

## O-M2S02-01 — CLOSED: field-level security for `Discount__c` and `Approval_Status__c` is now granted by `Enterprise_Sales_Record_Types`

- **Date closed:** 2026-09-19 · **Recorded by:** `build-doc-keeper`, from the repair envelope and the
  re-test
- **The open item, as first recorded** (above, HIGH): three access files across `M2-S01` and
  `M2-S02` carried no `fieldPermissions` block, leaving `Opportunity.Discount__c` and
  `Opportunity.Approval_Status__c` FLS-invisible to the 14 Sales User holders and to the deploying
  admin.
- **Closed by:** **D-M2S02-03** above — the repair pass (`metadata-builder`, run
  `2026-09-19T15-22-09Z`) added the two `fieldPermissions` blocks to `Enterprise_Sales_Record_Types`,
  by requester decision, in preference to the cutover-runbook remedy this item originally named.
  `check_access_model.py`'s re-run confirms `PSVP-FLS-01` stays silent (no `objectPermissions`
  element exists for it to fire on) and `check_permission_set_architecture.py` exits 0 with the two
  new grants in place. `reports/MOCK-DEPLOY-M2.md` run 3 (Succeeded, 18/18, 2026-09-19T15:26:20Z) is
  the org evidence that both grants deploy clean.
- **Not reopened:** the gap this item named — no file in the build granting FLS for these two
  fields — no longer exists; `traceability.md` **REQ-013** is updated in this pass to reflect it.
- **Evidence:** `envelopes/M2-S02/2026-09-19T15-22-09Z.json` (diff + Confidence sections);
  `envelopes/M2-S02/2026-09-19T15-29-15Z.md` (re-test, all three checkers exit 0);
  `reports/mock-deploy/2026-09-19T15-26-20Z/summary.md`; `decisions.md` **D-M2S02-03**.

## D-M3S01-01 — The approval emails are sent as the current user, not from an org-wide address

- **Date:** 2026-09-19 · **Recorded by:** dry-run operator (Fable), from the builder's envelope
  (`envelopes/M3-S01/2026-09-19T16-17-00Z.md` § 4) and the requester's decision at this pass
- The cited skill's first question — who does the email come from — was never asked on this build, and no
  `OrgWideEmailAddress` is known to exist in any target org. Decision: M3-S02's two workflow alerts use
  `senderType CurrentUser` (internal audience, nothing to provision); the approval process's own submit
  email needs no alert. This is the shape that avoids case-onboarding's F-28 (a sender-address failure at
  deploy). A shared mailbox, if ever wanted, becomes an M3 gate prerequisite. Recorded in
  `artefacts/M3-S01/deploy-order.md` § 4 as UNVERIFIED (2026-09-19) pending an org where the address question is answered.

## O-M3S01-01 — M3-S02 must set `showApprovalHistory` true, or the rejection email points at nothing

- **Date:** 2026-09-19 · **Recorded by:** dry-run operator (Fable), from the builder's envelope
- `Discount_Rejected.email` delivers Q33's "with the comments" clause by pointing the rep at the approval
  history related list (A27: no documented merge field carries approval comments). Close condition: M3-S02's
  `ApprovalProcess` carries `<showApprovalHistory>true</showApprovalHistory>` and the M3 verifier checks it.

## O-M3S01-02 — A27's premise is one word too absolute

- **Date:** 2026-09-19 · **Recorded by:** dry-run operator (Fable), from the builder's envelope
- A27 says no `{!ApprovalRequest.*}` merge field is documented anywhere in the library; two incidental mentions
  exist (`skills/admin/quote-to-cash-process/references/gotchas.md`, `skills/flow/pause-elements-and-wait-events/SKILL.md`),
  neither a comments merge field nor in a cited skill. A27's conclusion stands; its wording should say "in no cited
  skill's example". Close condition: planner rewords A27 (prose) or the M3 gate accepts as written.

## O-M3S01-03 — Two rendering facts only a send can settle

- **Date:** 2026-09-19 · **Recorded by:** dry-run operator (Fable), from the builder's envelope
- (a) Whether `{!Opportunity.Approval_Status__c}` in the approved/rejected bodies reads the post-update value —
  Q33 puts the field update and the alert in the same approval action block and no cited skill fixes their order;
  both bodies word it so a stale merge reads as redundant, not contradictory; if stale, delete that one line.
  (b) How a Percent field renders in a Classic merge — the `%` sign is left off the bodies. UNVERIFIED (2026-09-19);
  close at the M3 mock deploy or UAT by sending each template once.

## D-M3S02-01 — Entry criteria exclude Closed Won and Closed Lost

- **Date:** 2026-09-19 · **Recorded by:** dry-run operator (Fable), requester decision at the step's reset
  (`plan.json` steps[M3-S02].amendments[], first build envelope `envelopes/M3-S02/2026-09-19T16-38-52Z.md`)
- The plan's entry criteria carried no stage filter. A submit-then-recall on a closed record would fire
  `Clear_Approval_Status`, and a workflow field update re-saves without re-running validation rules —
  committing a Closed Won record above 20% with a blank status, the state M2-S03 exists to prevent. The
  criteria now add `NOT(ISPICKVAL(StageName, "Closed Won"))` and `NOT(ISPICKVAL(StageName, "Closed Lost"))`,
  matching the cited skill's worked example. Rebuilt 16:46Z; one line differs. Org-validated by
  `reports/MOCK-DEPLOY-M3.md` run 1 (30/30).

## D-M3S02-02 — The email-templates checker declared on this step was withdrawn

- **Date:** 2026-09-19 · **Recorded by:** dry-run operator (Fable)
- `amend-step --add-checker` had declared `check_email_templates.py` at step scope on a step that holds no
  template artefact by design (M3-S01 owns them); the checker can only exit 1 there. Withdrawn by amendment;
  M3-S01's own declared run covers the templates. The remaining § 5 WARN (validation-rules cited, no checker)
  is accepted as advisory for the same reason — driver's log friction (52).

## O-M3S02-01 — A manager-owned deal routes to the manager's own manager; a blank Manager fails at submit time

- **Date:** 2026-09-19 · **Recorded by:** dry-run operator (Fable), from the first build's envelope
- With `useApproverFieldOfRecordOwner` true the hierarchy field is read on the record owner. The requirement
  names 12 reps and 2 managers and says nothing about whether managers own deals or whether every user has
  a Manager set; a blank one is a run-time submission failure no deploy catches. Close condition: the org's
  user data confirms every Enterprise/Renewal owner has a Manager, or a pre-submission validation rule /
  fallback approver is added as a step (candidate for M4 planning). Not settled by the dry run.

## D-M3S03-01 — API 62.0 on the four authored classes, 67.0 on the template copy

- **Date:** 2026-09-19 · **Recorded by:** dry-run operator (Fable), from the builder's envelope
  (`envelopes/M3-S03/2026-09-19T17-14-42Z.md`) and `plan.json` steps[M3-S03].inputs.api_version
- The plan pins 62.0 in `inputs.api_version`, in the step note (a deliberate split, not a slip) and in
  manual test 6, which ticks only if the four authored classes carry 62.0 while `TestDataFactory.cls`
  carries the template's 67.0. The operator's brief said 67.0 from memory of other scenarios; the builder
  followed the plan, which is the only shared state. Consequence recorded: at 62.0 the explicit
  `WITH USER_MODE` on the service's SOQL is the enforcement, not a statement of intent. Raising it is an
  `amend-step` on `inputs.api_version` and manual test 6, then `documented -> running`.

## D-M3S03-02 — A batch submit exists beside the single submit the requirement asks for

- **Date:** 2026-09-19 · **Recorded by:** dry-run operator (Fable), builder's flagged deviation accepted
- `@InvocableMethod` is a list-in/list-out contract and Flow hands the action a whole batch; looping the
  single submit would have put one SOQL and one `Approval.process` per input inside a loop, a defect no
  declared checker catches (IM005 matches literal SOQL and DML, not a service call that performs them).
  `submitOne` remains the requirement's capability and the only thing the controller calls.

## O-M3S03-01 — The process name must stay a string literal inside the submit call

- **Date:** 2026-09-19 · **Recorded by:** dry-run operator (Fable), from the builder's envelope
- `check_approval_process_apex_patterns.py` resolves the process name only from a literal inside
  `setProcessDefinitionNameOrId(...)`; a `private static final` constant hid it and the declared test exited 0
  having checked nothing. The literal is inline with a comment saying why. Library backlog: the checker
  should follow constants. Close condition: the checker change lands, or the M3 gate accepts the constraint.

## O-M3S03-02 — apex-security-patterns is cited but undeclared, and would fail on the deliberate class split

- **Date:** 2026-09-19 · **Recorded by:** dry-run operator (Fable), from the builder's envelope
- Run by hand: exit 1, two HIGH "entry point lacks read-access enforcement" (a per-file heuristic meeting
  D6's three-class split; the read-access enforcement lives in the service the entry points call) and one
  MEDIUM against `TestDataFactory.cls`, the canonical template shipped verbatim, which carries no sharing
  keyword. Close condition: the template gains an explicit sharing keyword (library), and the checker's rule
  learns to follow a call into a same-package service, or the M3 gate accepts the two HIGHs as design.

## O-M3S03-03 — Compile not run: no offline Apex compiler and no org contact at build time

- **Date:** 2026-09-19 · **Recorded by:** dry-run operator (Fable)
- The M3 dry run at RunSpecifiedTests is the first compile and the first coverage measurement (every class
  in the package needs 75%). Close condition: `reports/MOCK-DEPLOY-M3.md` run 2.

## D-M3S04-01 — The panel reads the record through the platform, not through a second Apex read

- **Date:** 2026-09-19 · **Recorded by:** dry-run operator (Fable), from the builder's envelope
  (`envelopes/M3-S04/2026-09-19T17-41-20Z.md`)
- `lightning-record-view-form` renders Discount__c and Approval_Status__c with the platform's labels, Percent
  formatting and per-field FLS; `@wire(getRecord)` provisions the same two fields for the button rule. The click
  calls `OpportunityApprovalController.submitForApproval({ opportunityId })` — signature copied from M3-S03 — and
  handles both refusal shapes (returned success=false with a message; a thrown error). Success notifies the record
  UI (`notifyRecordUpdateAvailable`), not `refreshApex`. Threshold is an App Builder design attribute (default 20),
  coerced with `Number()` because Integer properties arrive as strings. API 62.0, resolved from the build itself
  because the step's inputs carry no version.

## O-M3S04-01 — The Jest suite is reviewed evidence, not passing evidence

- **Date:** 2026-09-19 · **Recorded by:** dry-run operator (Fable), from the builder's envelope (finding M3S04-F-02)
- No Node harness exists at or above the repo root and installing one is outside the agent's scope, so the 16
  Jest cases never ran; `node --check` fails open on an ESM module with decorators and is not a parse check.
  Close condition: run `sfdx-lwc-jest` in a project that has the harness, or accept the suite as reviewed at the
  M3 gate with the deploy (which compiles the bundle) as the first real check.

## O-M3S04-02 — The percent comparison assumes the UI API returns 20, not 0.20

- **Date:** 2026-09-19 · **Recorded by:** dry-run operator (Fable), from the builder's envelope
- A35's UI API half is unconfirmed: the component compares the Percent field against 20 while the validation
  rule and the approval entry criteria compare 0.20 in formula context. UNVERIFIED (2026-09-19) inline; the Jest
  suite fails first if a retrieved record disagrees. Close condition: one record read in the org.

## O-M3S04-03 — `next`'s checker advice would block a correct step on two of its three suggestions

- **Date:** 2026-09-19 · **Recorded by:** dry-run operator (Fable), from the builder's envelope
- `check_wire_service_patterns.py` exits 0 (worth declaring); `check_lwc_jest_testing_with_accessibility.py`
  exits 1 only on "no package.json / jest.config.js at project root" (the build directory is not an SFDX project);
  `check_invocable_methods.py` finds no Apex here and asserts nothing. Same shape as driver's log friction (39)/(52):
  the tool advises declarations without checking the step's outputs against the checker's file patterns.

## O-M3S04-04 — The canonical LWC skeleton still uses legacy `if:true`

- **Date:** 2026-09-19 · **Recorded by:** dry-run operator (Fable), from the builder's envelope
- `templates/lwc/component-skeleton/componentSkeleton.html` uses `if:true` in three places, which the lwc-builder
  playbook and `skills/lwc/lwc-conditional-rendering` forbid in new bundles — copying the canonical shell
  faithfully produces a template the skill rejects. Library backlog (template owner). The bundle here uses
  `lwc:if`.

## D-M3S05-01 — Org-default activation by ActionOverride on the object, not by profile

- **Date:** 2026-09-19 · **Recorded by:** dry-run operator (Fable), from the builder's envelope
  (`envelopes/M3-S05/2026-09-19T17-57-44Z.md`)
- The Enterprise record page is activated as the org default through two `actionOverrides` (View / Flexipage,
  Large and Small) on `Opportunity.object-meta.xml`; there is no profile or permission-set rung below that, so
  the operator's brief pointing at the M2-S02 profile overlay as precedent was wrong and the plan won. The org
  default has no record-type dimension: it becomes the page for Renewal too unless an app-level assignment
  (Rung 1 or 2, `CustomApplication` metadata this build does not carry — A38 open) outranks it.

## O-M3S05-01 — Two shapes only the org can settle

- **Date:** 2026-09-19 · **Recorded by:** dry-run operator (Fable), from the builder's envelope
- (a) Whether `flexipage:recordHomeWithSubheaderTemplateDesktop` defines a region named `sidebar` (the skill's
  fence for this template shows `subheader` and `main` only); (b) the `c:` prefix on a custom LWC
  `componentName` (one occurrence in the whole library, in a skill this step does not cite). Both marked
  UNVERIFIED (2026-09-19) inline. Close condition: `reports/MOCK-DEPLOY-M3.md` run 2.

## O-M3S05-02 — A38: which Lightning apps expose Opportunity is still unknown

- **Date:** 2026-09-19 · **Recorded by:** dry-run operator (Fable), from the builder's envelope
- An app with its own Opportunity record page outranks the org default written here and must be re-pointed in
  Setup; `deploy-order.md` § 3.1 carries the retrieve commands and the delete-or-re-point decision. Close
  condition: the org's `CustomApplication` metadata is retrieved and read before the M3 deploy.

## O-M3S05-03 — The Renewal path's page is still unconfirmed, and the green path checker does not close it

- **Date:** 2026-09-19 · **Recorded by:** dry-run operator (Fable), from the builder's envelope
- O-M2S05-04 stays open. `check_path_and_guidance.py`'s Check 6c indexes FlexiPage components by object, not
  by record type, so the one Enterprise page silences the note for both paths. Close condition unchanged:
  retrieve the org's existing Opportunity page and grep for the Path component.

## O-M3S05-04 — No org-validated FlexiPage exists anywhere in the library

- **Date:** 2026-09-19 · **Recorded by:** dry-run operator (Fable), from the builder's envelope
- Every Lightning-page shape the repo ships is fence-grounded; `examples/builds/` holds no
  `*.flexipage-meta.xml`. Run 2 of the M3 dry run is the first. Library gap: the cited skill also ships no
  `## Questions to Ask Before Configuring` section (its `## Before Starting` block stands in) and disagrees with
  its own examples on `actionOverride` enum casing.

## O-M3S05-01 — UNVERIFIED (2026-09-19): that flexipage:recordHomeWithSubheaderTemplateDesktop provides a region named 'sideba

- **Date:** 2026-09-19 · **Recorded by:** dry-run operator (Fable), from the builder's envelope (`envelopes/M3-S05/2026-09-19T17-57-44Z.json`)
- UNVERIFIED (2026-09-19): that flexipage:recordHomeWithSubheaderTemplateDesktop provides a region named 'sidebar'. Settled by opening the template in Lightning App Builder or retrieving any page built on it. If the name differs, one <name> element changes. A region name the template does not define is a deploy-time failure the checker cannot see.


## O-M3S05-02 — UNVERIFIED (2026-09-19): the c: namespace prefix on a custom LWC componentName. Grounded only in admin/service

- **Date:** 2026-09-19 · **Recorded by:** dry-run operator (Fable), from the builder's envelope (`envelopes/M3-S05/2026-09-19T17-57-44Z.json`)
- UNVERIFIED (2026-09-19): the c: namespace prefix on a custom LWC componentName. Grounded only in admin/service-console-configuration, which this step does not cite. Settled by the dry run in deploy-order.md section 6.


## O-M3S05-03 — A38 is open, medium risk: nobody has enumerated which Lightning apps expose Opportunity at Northwind. Rungs 1

- **Date:** 2026-09-19 · **Recorded by:** dry-run operator (Fable), from the builder's envelope (`envelopes/M3-S05/2026-09-19T17-57-44Z.json`)
- A38 is open, medium risk: nobody has enumerated which Lightning apps expose Opportunity at Northwind. Rungs 1 and 2 both outrank the org default this step writes, and both live in CustomApplication metadata this build does not contain. deploy-order.md section 3.1 carries the retrieve commands. Do this before the M3 gate, not after.


## O-M3S05-04 — O-M2S05-04 stays open: nothing in this build asserts that the page a Renewal Opportunity resolves to carries r

- **Date:** 2026-09-19 · **Recorded by:** dry-run operator (Fable), from the builder's envelope (`envelopes/M3-S05/2026-09-19T17-57-44Z.json`)
- O-M2S05-04 stays open: nothing in this build asserts that the page a Renewal Opportunity resolves to carries runtime_sales_pathassistant:pathAssistant. Note also that the org default written here is not record-type-scoped - ActionOverride on CustomObject has no recordType field - so it makes the Enterprise page the default for Renewal too unless a higher rung says otherwise.


## O-M3S05-05 — Two cited checkers are undeclared on this step: check_path_and_guidance.py and check_lwc_base_component_recipe

- **Date:** 2026-09-19 · **Recorded by:** dry-run operator (Fable), from the builder's envelope (`envelopes/M3-S05/2026-09-19T17-57-44Z.json`)
- Two cited checkers are undeclared on this step: check_path_and_guidance.py and check_lwc_base_component_recipes.py. build_plan.py next prints the amend-step --add-checker command for both. Before declaring them, read the advisory results above: at step scope both are vacuous passes, and only check_path_and_guidance.py at scope build asserts anything (and its Check 6c is keyed by sobjectType, not record type).


## O-M3S05-06 — admin/lightning-record-page-configuration ships no '## Questions to Ask Before Configuring' section. Its '## B

- **Date:** 2026-09-19 · **Recorded by:** dry-run operator (Fable), from the builder's envelope (`envelopes/M3-S05/2026-09-19T17-57-44Z.json`)
- admin/lightning-record-page-configuration ships no '## Questions to Ask Before Configuring' section. Its '## Before Starting' block is the equivalent and was bound as such. A library follow-up, not a build blocker.


## O-M3S05-07 — The step's two manual acceptance tests are for the M3 milestone gate. Both were written to be tickable from th

- **Date:** 2026-09-19 · **Recorded by:** dry-run operator (Fable), from the builder's envelope (`envelopes/M3-S05/2026-09-19T17-57-44Z.json`)
- The step's two manual acceptance tests are for the M3 milestone gate. Both were written to be tickable from the files as they stand: two actionOverrides blocks and nothing else in the object file plus the app-default sentence in deploy-order.md (test 3), and the Path in subheader with hideUpdateButton false, the panel in sidebar with discountThreshold 20, and every identifier under 120 characters (test 4).

## D-M3S03-03 — The test seeds its own Opportunity object grant (N3-F-08)

- **Date:** 2026-10-02 · **Recorded by:** dry-run operator (Fable), requester decision at the repair
  (`envelopes/M3-S03/2026-09-19T18-17-01Z.md`; `reports/MOCK-DEPLOY-M3.md` runs 4–5)
- Run 4 showed all six test methods throwing `System.QueryException: sObject type 'Opportunity' is not supported`
  at the service's `WITH USER_MODE` SOQL under `System.runAs(<persona>)`: the persona held record types and two
  field grants and no object permission, because the Sales Cloud set Q19 relies on is neither in the build nor in
  the validating org. The test now seeds a test-scoped `PermissionSet` with `ObjectPermissions` on Opportunity
  (read/create/edit) inside its mixed-DML fence and assigns it to both users; the build's metadata is unchanged.
  Run 5: 6/6 passed, coverage 95.6%. Library backlog: test-class-standards needs the object-level twin of Gotcha 15.

## O-M3S03-04 — Static checkers cannot see a runtime permission gap

- **Date:** 2026-10-02 · **Recorded by:** dry-run operator (Fable), from the re-tester's envelope
- All three declared checkers were green before and after the repair; only the org run saw the six exceptions.
  `tested` on an Apex step says the declared static checks pass, not that the tests pass — the org run is the
  evidence. Close condition: the loop records an org test run as a declared acceptance test for Apex steps.

## D-M4S01-01 — Column codes are confirmed by a split deploy, not by a dry run

- **Date:** 2026-10-02 · **Recorded by:** dry-run operator (Fable), from the builder's envelope
  (`envelopes/M4-S01/2026-10-02T17-23-14Z.md`)
- The report type is new and two of its six columns are new M1-S01 fields, so no report in any org today
  carries the codes M4-S02 must write. The runbook's Phase B therefore deploys the ReportType first, builds one
  throwaway report on it, retrieves it and compares codes — a split of the M4 deploy the plan left implicit.
  Decision for the M4 gate: accept the split (ReportType in a first deploy, Report and Dashboard after
  confirmation) or accept the six UNVERIFIED (2026-10-02) codes as the risk of a single deploy.

## O-M4S01-01 — M4 gate: decide whether to split the M4 deploy (M1-S01 fields + M4-S02 ReportType first) so that Phase B can c

- **Date:** 2026-10-02 · **Recorded by:** dry-run operator (Fable), from the builder's envelope (`envelopes/M4-S01/2026-10-02T17-23-14Z.json`)
- M4 gate: decide whether to split the M4 deploy (M1-S01 fields + M4-S02 ReportType first) so that Phase B can confirm the six codes. Otherwise accept the F-51 fallback for any code that cannot be harvested.


## O-M4S01-02 — Run Phase A (section 2) against the target org before M4-S02 deploys, and record SMB's report type (closes U2,

- **Date:** 2026-10-02 · **Recorded by:** dry-run operator (Fable), from the builder's envelope (`envelopes/M4-S01/2026-10-02T17-23-14Z.json`)
- Run Phase A (section 2) against the target org before M4-S02 deploys, and record SMB's report type (closes U2, and U3 if standard).


## O-M4S01-03 — Fill section 4's confirmed-code column. Any replaced code goes into M4-S02 through a rebuild, not a hand edit

- **Date:** 2026-10-02 · **Recorded by:** dry-run operator (Fable), from the builder's envelope (`envelopes/M4-S01/2026-10-02T17-23-14Z.json`)
- Fill section 4's confirmed-code column. Any replaced code goes into M4-S02 through a rebuild, not a hand edit.


## O-M4S01-04 — U4: the first mock_deploy run over M4-S02 shows whether a same-request dry run rejects a wrong column code on

- **Date:** 2026-10-02 · **Recorded by:** dry-run operator (Fable), from the builder's envelope (`envelopes/M4-S01/2026-10-02T17-23-14Z.json`)
- U4: the first mock_deploy run over M4-S02 shows whether a same-request dry run rejects a wrong column code on a new custom report type. Feed the answer back into admin/reports-and-dashboards gotchas.

## D-M4S02-01 — One report serves both views: Close Date became a grouping, and a record-type filter was added

- **Date:** 2026-10-02 · **Recorded by:** dry-run operator (Fable), from the builder's envelope
  (`envelopes/M4-S02/2026-10-02T17-51-49Z.md`)
- The plan declares one report for the managers' by-stage view and the VP's by-month tile. A field cannot be
  both a grouping and a column (RPT-GRP-01), so Close Date groups by month rather than appearing as a column
  per row as A43 listed. A record-type filter (`RecordTypeId = Enterprise`) was added: without it the
  "Enterprise" report and tile would total SMB and Renewal deals too (Q8, Q9). A public group
  `Enterprise_Managers` was built, not a role — plan.json and Q25 say group; the operator's brief said role
  and the plan won. The group ships empty (membership is data, A32).

## O-M4S02-01 — Manager visibility may not narrow to their own reps

- **Date:** 2026-10-02 · **Recorded by:** dry-run operator (Fable), from the builder's envelope
- Q4 implies a public Opportunity org-wide default and forbids tightening it; the report carries no scope
  element (D7). Each manager may see the whole Enterprise pipeline, not only their reps' deals (U12).
  Close condition: `access-path-explainer` against the org's OWD and role hierarchy, or the requester accepts.

## O-M4S02-02 — The dashboard's running user is not on file

- **Date:** 2026-10-02 · **Recorded by:** dry-run operator (Fable), from the builder's envelope
- `SpecifiedUser` with no `runningUser` (A29; the checker's MEDIUM). Insert the VP's username in the deploy
  copy, or choose a service user as the skill recommends (U14). Gate decision.

## O-M4S02-03 — The deploy must be split so the column codes can be confirmed between the halves

- **Date:** 2026-10-02 · **Recorded by:** dry-run operator (Fable), from M4-S01 § 7 and this step's § 0
- ReportType first; throwaway report; retrieve; compare; then Report and Dashboard. Carries D-M4S01-01.
  The record-type filter code (U8) is the one that must not ship absent.

## O-M4S02-04 — Skill depth: four mismatches between the cited skill and the Summer '26 Metadata API guide

- **Date:** 2026-10-02 · **Recorded by:** dry-run operator (Fable), from the builder's envelope
- F-49 says the guide does not state the 255-character description limit (it now does); `summaryAxisRange`
  required in the guide, absent from the skill's chart example; `chartAxisRange` casing; `isAutoSelectFromReport`
  vs `autoselectColumnsFromReport`. Library backlog for `admin/reports-and-dashboards`; the report checker also
  does not scan dashboard column codes.

## D-M4S02-02 — Repair after org run 1: record-type column form and dashboard sortBy

- **Date:** 2026-10-02 · **Recorded by:** dry-run operator (Fable), from `reports/MOCK-DEPLOY-M4.md`
- N4-F-01: the report type named its record-type column by the field API name and the org refused it; the
  repair uses the guide's column form for a lookup and stays UNVERIFIED until run 2. N4-F-03: a chart dashboard
  component requires `<sortBy>`; the skill's example never carried one — rule RPT-DASH-SORT-01 queued.

## D-M4S02-03 — Repair 2 settled the column form; the report itself needs the split deploy

- **Date:** 2026-10-02 · **Recorded by:** dry-run operator (Fable), from `reports/MOCK-DEPLOY-M4.md` runs 2–3
- Run 3 accepted the report type with `<field>RecordType</field>` (org-verified: the lookup's relationship
  name alone, after `RecordTypeId` and `RecordType.Name` were refused) and the dashboard with `chartAxisRange`
  (`Auto`). The report still reads "invalid report type" because its type does not exist until deployed
  (N4-F-06): the ReportType must deploy first, then the Report and Dashboard. The validate-only loop cannot
  show the second half green; the M4 gate accepts it on the checker, the manual tests and the type's validation.

## O-M4S02-05 — M4 gate: split the M4 deploy (B4: Group, ReportType, folders and M1-S01 fields first) so that Phase B can conf

- **Date:** 2026-10-02 · **Recorded by:** dry-run operator (Fable), from the builder's envelope (`envelopes/M4-S02/2026-10-02T18-03-39Z.json`)
- M4 gate: split the M4 deploy (B4: Group, ReportType, folders and M1-S01 fields first) so that Phase B can confirm the codes. The record-type criterion (U8) cannot ship absent; for any other code that cannot be harvested, the F-51 fallback applies.


## O-M4S02-06 — B3/U12: confirm the Opportunity OWD. If it is public, Q4 and Q24 conflict for the managers' report and a human

- **Date:** 2026-10-02 · **Recorded by:** dry-run operator (Fable), from the builder's envelope (`envelopes/M4-S02/2026-10-02T18-03-39Z.json`)
- B3/U12: confirm the Opportunity OWD. If it is public, Q4 and Q24 conflict for the managers' report and a human must rank them (deploy-order section 8).


## O-M4S02-07 — B2/U14: obtain the VP's username per target org and substitute runningUser in the deploy copy, or decide on a

- **Date:** 2026-10-02 · **Recorded by:** dry-run operator (Fable), from the builder's envelope (`envelopes/M4-S02/2026-10-02T18-03-39Z.json`)
- B2/U14: obtain the VP's username per target org and substitute runningUser in the deploy copy, or decide on a service user (deploy-order section 6).


## O-M4S02-08 — O-3: Q23's 'see the gap' could be met by a HasOpportunityLineItem yes/no column (amend-step and rebuild). Corr

- **Date:** 2026-10-02 · **Recorded by:** dry-run operator (Fable), from the builder's envelope (`envelopes/M4-S02/2026-10-02T18-03-39Z.json`)
- O-3: Q23's 'see the gap' could be met by a HasOpportunityLineItem yes/no column (amend-step and rebuild). Correct the stale 'M2-S04 block' prose in inputs.note and manual test 3 with amend-step --prose-only.


## O-M4S02-09 — O-4: the checker-test description predicts six RPT-COL-01 lines and seven findings; the built step gives five

- **Date:** 2026-10-02 · **Recorded by:** dry-run operator (Fable), from the builder's envelope (`envelopes/M4-S02/2026-10-02T18-03-39Z.json`)
- O-4: the checker-test description predicts six RPT-COL-01 lines and seven findings; the built step gives five and six (amend-step --prose-only).


## O-M4S02-10 — O-5: declare check_queues.py on M4-S02 (amend-step --add-checker admin/queues-and-public-groups). Self-check e

- **Date:** 2026-10-02 · **Recorded by:** dry-run operator (Fable), from the builder's envelope (`envelopes/M4-S02/2026-10-02T18-03-39Z.json`)
- O-5: declare check_queues.py on M4-S02 (amend-step --add-checker admin/queues-and-public-groups). Self-check exit 0.


## O-M4S02-11 — Post-deploy: the sales-ops admin adds the two Enterprise managers and the VP to the Enterprise Managers group

- **Date:** 2026-10-02 · **Recorded by:** dry-run operator (Fable), from the builder's envelope (`envelopes/M4-S02/2026-10-02T18-03-39Z.json`)
- Post-deploy: the sales-ops admin adds the two Enterprise managers and the VP to the Enterprise Managers group (A32).


## O-M4S02-12 — Run MOCK-DEPLOY-M4 run 2; record the accepted record-type column name in deploy-order.md section 13 and close

- **Date:** 2026-10-02 · **Recorded by:** dry-run operator (Fable), from the builder's envelope (`envelopes/M4-S02/2026-10-02T18-03-39Z.json`)
- Run MOCK-DEPLOY-M4 run 2; record the accepted record-type column name in deploy-order.md section 13 and close U7 and U8.


## O-M4S02-13 — Run MOCK-DEPLOY-M4 run 3; record the accepted record-type column name in deploy-order.md section 14 and close

- **Date:** 2026-10-02 · **Recorded by:** dry-run operator (Fable), from the builder's envelope (`envelopes/M4-S02/2026-10-02T18-03-39Z.json`)
- Run MOCK-DEPLOY-M4 run 3; record the accepted record-type column name in deploy-order.md section 14 and close U7 and U8.

## D-M4S03-01 — The compile fixed the plan, not the pack

- **Date:** 2026-10-02 · **Recorded by:** dry-run operator (Fable), from the compile envelopes
  (`envelopes/M4-S03/2026-10-02T18-48-03Z.md`, `…19-15-35Z.md`)
- The first compile failed two of its own checkers on gaps in the build's record — no negative test for
  REQ-004/016/017/018 anywhere, and REQ-010 untested since M1 — and said so rather than inventing cases. The
  requester added the missing tests to M4-S04 (four negative cases, one runbook check for the related list),
  reworded three tests that still assumed a blocked M2-S04 (one would have dropped a shipped rule from the
  manifest), then split two compound tests and moved the negative cases to post-deploy UAT. The pack is
  re-compiled incrementally after M4-S04 builds so it carries the final test set.

## O-M4S03-01 — Four workbook sections carry no rows

- **Date:** 2026-10-02 · **Recorded by:** dry-run operator (Fable), from the compile envelope
- Sections 4 (sharing), 7, 9 and 10 have no slice rows: the build designs no sharing change (D7, Q4), no
  integration, no data migration. The compiled workbook says so per section. Close: accepted at the M4 gate.

## O-M4S03-02 — `check_rtm.py` reads a prose artefact cell as a real artefact

- **Date:** 2026-10-02 · **Recorded by:** dry-run operator (Fable), from the compile envelope
- REQ-010's cell `none — deliberately absent from both layouts` is not matched by the checker's empty-marker
  list (exactly `none`), so the row passes on its test id alone. Library backlog for the RTM checker.

## D-M4S04-01 — Two deploy requests, four edits in the deploy copy, never in the artefacts

- **Date:** 2026-10-02 · **Recorded by:** dry-run operator (Fable), from the builder's envelope
  (`envelopes/M4-S04/2026-10-02T19-41-27Z.md`)
- Request 1 carries 36 members; between the requests the report column codes are confirmed and the
  dashboard's running user inserted; request 2 carries the report and the dashboard (N4-F-06). Four edits are
  made in the deploy copy only: the OpportunityStage merge (O-M1S01-01), the related-list copy (A26/REQ-010),
  the Opportunity object-file merge (new, below) and the runningUser. The manifest includes M2-S04's rule
  exactly once; the step's own inputs still called that step blocked — the fourth stale description — and
  the builder followed the amended test, correctly.

## O-M4S04-01 — HIGH: a partial Opportunity object file may replace the whole object definition

- **Date:** 2026-10-02 · **Recorded by:** dry-run operator (Fable), from the builder's envelope
- M3-S05 ships a two-element `Opportunity.object-meta.xml` (the two actionOverrides). The object skill's
  Gotcha 10 says a partial object file replaces the object definition on deploy; the dry runs proved only that
  it deploys. The runbook makes the retrieve-and-merge of the org's Opportunity object file blocking (E3, A-5).
  UNVERIFIED (2026-10-02); requester decision: blocking pre-deploy step, owner sales-ops admin.

## O-M4S04-02 — HIGH: the 140-deal reassignment needs a stage mapping Q8 said it would not

- **Date:** 2026-10-02 · **Recorded by:** dry-run operator (Fable), from the builder's envelope
- None of the generic pipeline's open stages exists in Enterprise_Sales_Process; values missing from the new
  record type are cleared on the switch (record-types skill Gotcha 1). Mapping them fires M2-S04's product gate
  on about twenty product-less deals unless the bypass holder runs the update, which then meets Q17's Chatter
  rule. Requester decision: the VP and the Sales Operations lead settle the mapping before P-8; the runbook
  carries the SOQL to count the affected deals.

## O-M4S04-03 — MEDIUM: SMB users will land on the Enterprise page unless an app assignment outranks it

- **Date:** 2026-10-02 · **Recorded by:** dry-run operator (Fable), from the builder's envelope
- The org-default record page has no record-type dimension (D-M3S05-01); the discount panel has no record-type
  check. Requirement item 6 (leave SMB alone) needs a VP decision at A-8: an app-level assignment scoped to
  the Enterprise record type, or accept.

## O-M4S04-04 — The runbook offers read-only retrieves and SOQL; test 4 says mock_deploy.py is the only org command

- **Date:** 2026-10-02 · **Recorded by:** dry-run operator (Fable)
- Tests 7 and 11 require retrieve-and-grep checks, so the runbook treats read-only retrieves and queries as
  allowed and says so in its header. Requester decision at the gate: read-only org commands are permitted in
  a runbook; the deny-list is about deploys.

## O-M4S04-05 — BLOCKING before request 1: retrieve CustomObject:Opportunity alone and merge M3-S05's two View actionOverrides

- **Date:** 2026-10-02 · **Recorded by:** dry-run operator (Fable), from the builder's envelope (`envelopes/M4-S04/2026-10-02T19-41-27Z.json`)
- BLOCKING before request 1: retrieve CustomObject:Opportunity alone and merge M3-S05's two View actionOverrides into it (deploy-copy edit E3). admin/object-creation-and-design Gotcha 10 says a partial object file replaces the whole definition; M3-S05's header says it changes nothing else. No validate-only run can settle which; deploy-order.md section 2, A-5.


## O-M4S04-06 — Decision before P-8: Q8 says the 140-deal reassignment needs no field mapping, but the Enterprise process offe

- **Date:** 2026-10-02 · **Recorded by:** dry-run operator (Fable), from the builder's envelope (`envelopes/M4-S04/2026-10-02T19-41-27Z.json`)
- Decision before P-8: Q8 says the 140-deal reassignment needs no field mapping, but the Enterprise process offers none of the generic open stages and admin/record-types-and-page-layouts Gotcha 1 says absent values are cleared on a record-type change. The VP and the Sales Operations lead map the stages; a stage change then fires M2-S04's product rule (about 20 deals have no products, Q16) unless the bypass holder runs it, which brings in Q17's Chatter post. deploy-order.md section 6, P-8.


## O-M4S04-07 — Decision for the VP (requirement.md item 6): the org-default record page M3-S05 activates has no record-type d

- **Date:** 2026-10-02 · **Recorded by:** dry-run operator (Fable), from the builder's envelope (`envelopes/M4-S04/2026-10-02T19-41-27Z.json`)
- Decision for the VP (requirement.md item 6): the org-default record page M3-S05 activates has no record-type dimension, so SMB records also open Opportunity_Enterprise_Record_Page, with the discount panel (no record-type gate) unless an app-level assignment outranks it. Accept, or plan an app-level assignment. deploy-order.md section 5, A-8.


## O-M4S04-08 — M4 gate: the deploy is two requests (N4-F-06). Request 1 = package.xml minus Report Enterprise_Sales/Open_Ente

- **Date:** 2026-10-02 · **Recorded by:** dry-run operator (Fable), from the builder's envelope (`envelopes/M4-S04/2026-10-02T19-41-27Z.json`)
- M4 gate: the deploy is two requests (N4-F-06). Request 1 = package.xml minus Report Enterprise_Sales/Open_Enterprise_Pipeline_By_Stage and Dashboard Enterprise_Sales/Enterprise_Pipeline (36 members); request 2 = those two, after B-1 (column codes) and B-2 (runningUser). deploy-order.md section 4.


## O-M4S04-09 — Name a person against each role before the window: release owner, sales-ops admin, Sales Operations lead (only

- **Date:** 2026-10-02 · **Recorded by:** dry-run operator (Fable), from the builder's envelope (`envelopes/M4-S04/2026-10-02T19-41-27Z.json`)
- Name a person against each role before the window: release owner, sales-ops admin, Sales Operations lead (only the VP is named on file). deploy-order.md section 0.


## O-M4S04-10 — Plan prose: steps[M4-S04].inputs.aggregates and inputs.note still call M2-S04 excluded/blocked, contradicting

- **Date:** 2026-10-02 · **Recorded by:** dry-run operator (Fable), from the builder's envelope (`envelopes/M4-S04/2026-10-02T19-41-27Z.json`)
- Plan prose: steps[M4-S04].inputs.aggregates and inputs.note still call M2-S04 excluded/blocked, contradicting the amended acceptance test 5 and the step's documented status; depends_on omits M2-S04 and M4-S01 whose artefacts this step reads. amend-step --prose-only can fix the note (not the depends_on, which is set-plan's).


## O-M4S04-11 — Do not declare check_opportunity_management.py or check_approval_design.py on M4-S04 as next advises: at step

- **Date:** 2026-10-02 · **Recorded by:** dry-run operator (Fable), from the builder's envelope (`envelopes/M4-S04/2026-10-02T19-41-27Z.json`)
- Do not declare check_opportunity_management.py or check_approval_design.py on M4-S04 as next advises: at step scope the first asserts nothing (exit 0, nothing in scope) and the second exits 1 on a tree with no approval file; at build scope the first still finds nothing and the second only re-checks M3-S02.


## O-M4S04-12 — Rehearsal tooling: scripts/mock_deploy.py copies every non-.md file, so a --milestone M4 run puts M4-S03's uat

- **Date:** 2026-10-02 · **Recorded by:** dry-run operator (Fable), from the builder's envelope (`envelopes/M4-S04/2026-10-02T19-41-27Z.json`)
- Rehearsal tooling: scripts/mock_deploy.py copies every non-.md file, so a --milestone M4 run puts M4-S03's uat-test-cases.yaml in the assembled tree (untested); and --without Dashboard is still refused (friction 64), so M4-S02 deploy-order.md section 10's probe form will not run. Fallback selector in deploy-order.md section 10.
