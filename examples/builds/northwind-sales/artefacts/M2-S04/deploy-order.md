# Deploy order — M2-S04

Build: `northwind-sales` · Milestone: M2 (Guidance, guardrails and who may bypass them) · Step type: `validation` · API version 62.0

This note is written by `agents/metadata-builder` Step 7 and is text for a human. Nothing in it is
executed by this agent or by any acceptance test.

Sourced from `skills/admin/validation-rules/references/metadata-examples.md` ("The type in one table",
"Where the file lives", Example 2, "package.xml"), `skills/admin/validation-rules/references/examples.md`
("At Least One Opportunity Product Before a Late Stage (Opportunity)"),
`skills/admin/validation-rules/references/gotchas.md` (Gotcha 14, Gotcha 15, "Rules Fire During Data
Loads", "Rules Fire on REST and SOAP API by Default", "errorDisplayField Silently Relocates to Top of
Page", "Opportunity Validation Rules Do Not Fire When a Line Item Changes the Opportunity", "A Workflow
Field Update Re-Saves the Record and Validation Rules Do Not Run Again", "ValidationRule Does Not
Support the Wildcard in package.xml"), `skills/admin/products-and-pricebooks/references/gotchas.md`
Gotcha 8 and its `## Questions to Ask Before Configuring` row on `HasOpportunityLineItem`,
`templates/admin/validation-rule-patterns.md` ("The canonical VR shape", "Bypass contract",
"IsChanged / IsNew patterns"),
`skills/admin/custom-permissions/references/gotchas.md` Gotcha 4, and
`skills/admin/change-management-and-deployment/references/metadata-examples.md` §§ 1 and 3.

Every source above was opened during this run. Where a claim is carried over from a sibling step's
note rather than read at its source, this note says so at the point of use.

## 0. Why API version 62.0

`plan.json` carries no `api_version`, so `agents/metadata-builder/AGENT.md` ("Inputs") falls back to
`62.0`. Every step shipped so far carries the same value — `artefacts/M1-S01/package.xml`,
`artefacts/M1-S02/package.xml`, `artefacts/M2-S01/package.xml` and `artefacts/M2-S03/package.xml` all
declare `<version>62.0</version>`. Keeping 62.0 here means `scripts/mock_deploy.py`'s
highest-version rule sees one version across the whole build rather than a step that silently raises
it.

## 1. Order inside this step

This step produces exactly one component, so there is no internal ordering to decide.

| # | Component | Because |
|---|---|---|
| 1 | `ValidationRule:Opportunity.Opportunity_Products_Required_At_Propose` | The only member in this step's `package.xml`, and the only metadata file under `artefacts/M2-S04/`. |

## 2. THE TWO CLAIMS THAT RODE WITH THIS RULE — ONE NOW ORG-VERIFIED, ONE STILL NOT

Both were carried forward verbatim from `plan.json` `steps[M2-S04].inputs.note` and from the skill that
unblocked this step. § 2.1 was settled by run 1 of the M2 mock deploy on 2026-09-19; § 2.2 was not — a
`checkOnly` deploy does not exercise it, and this agent did not resolve it either. The step's `manual`
acceptance test is ticked against this section, both claims read as of this repair.

### 2.1 ORG-VERIFIED (2026-09-19) — `HasOpportunityLineItem` is addressable inside a validation-rule formula

> RESOLVED 2026-09-19 by org contact, superseding the corpus-only UNVERIFIED (2026-09-15) marker below.
> Run 1 of the milestone M2 mock deploy (`reports/MOCK-DEPLOY-M2.md`; validate-only,
> `--org-alias sfskills-dev --mode manifest --milestone M1 --milestone M2`,
> `reports/mock-deploy/2026-09-19T14-56-10Z/`, `checkOnly: true`) compiled this rule's
> `errorConditionFormula`. A `sf project deploy start --dry-run` compiles every formula it validates
> before it checks anything else about the component, and the *only* error the org returned for
> `ValidationRule Opportunity.Opportunity_Products_Required_At_Propose` was the description-length
> rejection repaired in § 6 — no field-availability or unknown-token compile error. Per
> `reports/MOCK-DEPLOY-M2.md`: "both validation rules' formulas compile (so
> `$Permission.Bypass_Opportunity_Sales_Validation` resolves and `HasOpportunityLineItem` IS available
> in validation-rule formula context — the M2-S04 UNVERIFIED § 2.1 claim is settled by this run …)".
> The original corpus-only text is kept below for the record, superseded rather than deleted:
>
> > UNVERIFIED (2026-09-15): the corpus grounds the field's **existence, type, read-only semantics and
> > when the platform sets it**. It does not say, in so many words, that `HasOpportunityLineItem` is
> > addressable inside a validation-rule `errorConditionFormula` — no fetched source in this repo makes a
> > formula-context claim about it. The `Properties` line establishes it is filterable/groupable/sortable,
> > which is a SOQL and report property, not a formula one. Verify with `sf project deploy start
> > --dry-run` against a sandbox before shipping, exactly as Gotcha 14 was verified. This is the one
> > clause in this example that a dry run can still refute.
> > — `skills/admin/validation-rules/references/examples.md`, "At Least One Opportunity Product Before a
> > Late Stage (Opportunity)"

**What this does and does not prove.** The compile confirms `HasOpportunityLineItem` is a legal token
inside a `ValidationRule.errorConditionFormula` at API 62.0, on this org (`sfskills-dev`). It is one
org's compile pass, not an official-documentation citation — `skills/admin/validation-rules/references/examples.md`
still carries its own UNVERIFIED (2026-09-15) marker on this point and this agent does not edit skill
content; updating that skill reference from this run is recorded as a follow-up in Process Observations,
not performed here. The compile says nothing about save-time re-fire behaviour after a line-item
deletion — that is § 2.2, and it is a separate, still-open question.

### 2.2 STILL UNVERIFIED (2026-09-15, unresolved by run 1) — the official sources conflict on re-firing after a line-item deletion. **This rule is a FORWARD GATE ONLY.**

| Source | Says |
|---|---|
| Apex Developer Guide, Trigger and Order of Execution Considerations | Validation rules don't fire for an opportunity when you modify an opportunity product, even if the opportunity product changes the opportunity |
| Object Reference, Opportunity → Usage (`knowledge/imports/salesforce-channel-revenue-management.md:4299-4302`) | "On opportunities and opportunity products, the workflow rules, validation rules, and Apex triggers fire when an update to a child opportunity product or schedule causes an update to the parent record" |

> UNVERIFIED (2026-09-15): these two official sources are in direct conflict and no probe in this repo
> has settled it. Treat the rule as enforcing the **forward** gate only (you cannot move the stage
> forward without products) and do **not** promise the requester that it prevents a deal from ending up
> at `Propose` with zero products after a deletion.
> — `skills/admin/validation-rules/references/gotchas.md`, Gotcha 15

**What this rule does and does not promise, in one line each:**

- **Does:** block the transition of an Enterprise deal into `Propose`, `Negotiate` or `Closed Won`
  while the deal has no line items.
- **Does not:** prevent an Enterprise deal already at `Propose` from reaching zero products by having
  its last line item deleted. Nothing in this build catches that. If the requester needs that
  invariant, it is a record-triggered flow or trigger on `OpportunityLineItem` and a new step.

Note this conflict is **not** settled by the § 8 dry run. A `checkOnly` deploy compiles the formula; it
does not exercise a deletion. Settling it needs a live save sequence in a sandbox, or a Formula
Language / Order-of-Execution source the library does not yet carry.

## 3. Dependencies on components outside this step

A validation rule is compiled at deploy time, and every token in `errorConditionFormula` has to resolve
in the target org *at that moment*. `depends_on` in `plan.json` records `M1-S01` and `M2-S01`.

| Must exist first | Built by | Referenced as | What happens if it is missing |
|---|---|---|---|
| Record type `Opportunity.Enterprise` | M1-S01 | `RecordType.DeveloperName = "Enterprise"` | `RecordType.DeveloperName` resolves regardless, but a *missing record type* makes the gate unreachable: every record carries some other record type, the clause is false, and the rule never fires. **Silent, not loud.** |
| Stage values `Propose`, `Negotiate`, `Closed Won` on the Opportunity stage picklist | M1-S01 (`standardValueSets/OpportunityStage.standardValueSet-meta.xml`, and `businessProcesses/Enterprise_Sales_Process`) | `ISPICKVAL(StageName, "…")` ×3 | A literal that is not a value of the picklist is a compile error on some platform paths and a permanently-false clause on others. All three are present in M1-S01's value set and in the Enterprise business process; verified by reading those two files. |
| `CustomPermission:Bypass_Opportunity_Sales_Validation` | M2-S01 | `NOT($Permission.Bypass_Opportunity_Sales_Validation)` | **Silently false.** See § 3.1. |
| `HasOpportunityLineItem` on Opportunity | The platform (standard field, not built by any step) | `NOT(HasOpportunityLineItem)` | Not a build dependency — but see § 2.1, which is about whether a *formula* may read it at all. |

`Opportunity.Discount__c` and `Opportunity.Approval_Status__c` are **not** referenced by this rule. It
shares only the bypass permission with M2-S03.

### 3.1 The bypass clause is silent when it is wrong

`skills/admin/custom-permissions/references/gotchas.md:47` (Gotcha 4, "API Name Is Effectively
Immutable After Production Use") documents the mechanism, and documents it for the **rename** case:
after a rename, "Validation rules and formulas evaluate `$Permission.BetaFeature` to `false` (no error,
just silent grant of access to nobody)." A reference to a permission that was never deployed is the
same mechanism — a `$Permission` token with no matching permission — but note the source states it of a
rename rather than of an absence; that extension is this note's reading, not a quoted claim. Either
way, inverted by the outer `NOT()`, the bypass clause is permanently `true` and **nobody can bypass the
rule, including the sales-ops admin**. The deploy is green either way.

1. **Deploy M2-S01 before this step, or in the same request.** The permission must be in the org when a
   user saves an Opportunity, not when the rule compiles.
2. **This is the second consumer of that permission** (M2-S03 is the first). Run over the whole tree,
   `check_custom_permissions.py --manifest-dir artefacts` should now report
   `Bypass_Opportunity_Sales_Validation` with **`Consumers 2`**. Inside `artefacts/M2-S04` alone it sees
   no `customPermissions/` directory and checks nothing. That count is a file-to-file agreement check,
   not an org check.
3. **A green checker is not a green org.** No manifest carries `PermissionSetAssignment`. The bypass is
   unusable until the sales-ops admin actually holds `Sales_Ops_Validation_Bypass`;
   `artefacts/M2-S01/deploy-order.md` § 4 carries the assignment instruction.

## 4. `errorDisplayField` is `StageName`, and it depends on a layout M1-S02 owns

The Metadata API guide's own condition, quoted in
`skills/admin/validation-rules/references/metadata-examples.md`: "If you do not specify a value **or the
field isn't visible on the page layout**, the value changes automatically to Top of Page."

`StageName` is the field the rep just changed and the only field in scope that is on every Opportunity
layout — the worked example's reasoning, and it holds here.
`artefacts/M1-S02/layouts/Opportunity-Opportunity Enterprise Layout.layout-meta.xml` carries
`<field>StageName</field>` with `<behavior>Required</behavior>`, so on the one record type this rule
gates, the error attaches to the field the rep has to change. Removing `StageName` from that layout
relocates the message to the top of the page — without a deploy, without a warning, and without
touching this rule. The message in § 7 is written to read correctly in both places.

## 5. Manifest member forms used

| Type | Member form | Source |
|---|---|---|
| `ValidationRule` | `Opportunity.Opportunity_Products_Required_At_Propose` — object, dot, rule name | `validation-rules/references/metadata-examples.md` "package.xml"; `change-management-and-deployment/references/metadata-examples.md` § 1 |

<!-- UNVERIFIED (2026-09-19): both cited references carry their own UNVERIFIED (2026-09-04) marker on
this exact point — the Metadata API Developer Guide shows no ValidationRule manifest sample, so
`Object.RuleName` is inferred from the documented CustomField / ListView `objectName.componentName`
pattern rather than quoted. It is the form M2-S03's manifest already uses, so the build is at least
internally consistent. If a deploy rejects the member, retrieve `CustomObject:Opportunity` instead and
read the form back off the result. -->

**`ValidationRule` does not accept the `*` wildcard** — stated outright in the Metadata API guide's
ValidationRule type reference (api_meta L45447–L45449) and repeated in this skill's gotchas. The member
above is therefore named explicitly, which is also what makes the manifest agree with the files on disk
in both directions.

Only `ValidationRule` appears in this step's `package.xml`. The custom permission, the record type and
the stage value set are real deploy dependencies but they are *other steps'* members, and "Metadata API
references the components listed in the manifest, not the directories in the .zip file" — a manifest
that claimed them here would deploy nothing extra and would make two steps claim the same component.

## 6. Repair after run 1

Run 1 of the M2 mock deploy (2026-09-19T14:56:10Z, validate-only, org alias `sfskills-dev`,
`--mode manifest --milestone M1 --milestone M2`; `reports/MOCK-DEPLOY-M2.md`;
`reports/mock-deploy/2026-09-19T14-56-10Z/`) rejected this step's one component:

> **N3-F-06** `ValidationRule Opportunity.Opportunity_Products_Required_At_Propose` — "Validation rule
> description cannot be longer than 255 characters long."
> — `reports/MOCK-DEPLOY-M2.md`

**Cause.** The shipped `<description>` was 766 characters. The first build wrote both of § 2's
UNVERIFIED claims into it verbatim, in addition to the business justification and the bypass name.
`skills/admin/validation-rules` Recommended Workflow step 4 asks for "`description` (business
justification and bypass name)" — the two UNVERIFIED claims were never part of what the skill asks the
`description` element to carry; they belong in this note, where they already also lived in full in § 2.

**Repair.** `<description>` rewritten to 205 characters — business justification plus the bypass name
only, nothing else:

```
Requires at least one product before an Enterprise Opportunity advances to Propose, Negotiate or
Closed Won (Q11, Q15). Bypass: Bypass_Opportunity_Sales_Validation, granted via
Sales_Ops_Validation_Bypass.
```

No other element of
`artefacts/M2-S04/objects/Opportunity/validationRules/Opportunity_Products_Required_At_Propose.validationRule-meta.xml`
changed: `<fullName>`, `<active>`, `<errorConditionFormula>`, `<errorDisplayField>` and `<errorMessage>`
are byte-identical to what run 1 validated (and what tripped only the description-length rule, not a
formula or field-reference error — see § 2.1). The two UNVERIFIED claims are not lost; they remain in
full in § 2 above, which is where the step's `manual` acceptance test already reads them from.

**Library gap, recorded and not fixed here.** `skills/admin/validation-rules` caps `errorMessage` at 255
characters (Recommended Workflow step 4, and `check_validation_rules.py`'s CRITICAL/HIGH findings list)
but is silent on a `description` ceiling, and the checker carries no length rule for `description`
either — nothing in the step's declared checkers would have caught the 766-character value before an
org did. Queued as **VR-DESC-01** (Cursor task 18). This agent does not edit the skill or the checker;
see Process Observations.

**Status.** `plan.json` step `runs[]` already carries the org's rejection and the operator's reset
(`tested → failed → pending`, entries timestamped `2026-09-19T15:02:51Z`) from before this repair
started. This section is the step-level record of the same event, for a reader of this file alone.

## 7. Decisions inside the file, and elements deliberately not written

- **`errorMessage` is Q15's wording verbatim, and it is shorter than the skill's worked example.**
  The example ships "Add at least one product before moving this opportunity to Propose. Use the
  Products related list to add a line from the price book, then change the Stage." The step's
  `inputs.error_message` and Q15's answer both give only the first sentence, and step inputs are the
  top of `agents/metadata-builder/AGENT.md` Step 4's priority order. 66 characters, well under the
  255 cap. It names the problem and the fix; it does not name *where* to click. If the requester wants
  the second sentence, that is a one-line edit to this file plus an `amend-step` on
  `inputs.error_message` — flagged here rather than decided by this agent.
- **`active` is `true`, and the transition guard is why that is safe.** Q16 answers that about 20 open
  Enterprise deals have no products, and that "the rules apply on the next save only — no clean-up in
  scope." `ISCHANGED(StageName)` means those 20 deals are not frozen: every ordinary edit that leaves
  the stage alone still saves. They are blocked only from *advancing*, which is the gate the requester
  asked for. Shipping `active=false` would have needed a named cleanup owner and a second one-line
  deploy, and Q16 declined both.
- **`NOT(ISNEW())` is present and is load-bearing.** `HasOpportunityLineItem` cannot be true during the
  Opportunity's own insert — a line item is inserted *for* an Opportunity that already exists. An
  `ISNEW()` fire condition would make creating a deal at `Propose` **impossible** rather than gated
  (Gotcha 15). A deal created straight at `Propose` with no products therefore passes this rule until
  its next stage change. **No clarification asked for direct creation at a gated stage to be blocked**;
  if the requester wants it, Gotcha 15 is explicit that it is a separate `ISNEW()` rule with its own
  message, never an `ISNEW()` clause in this one.
- **`ISCHANGED(StageName)` rather than `ISPICKVAL(PRIORVALUE(StageName), "Discover")`.** The worked
  example offers the `PRIORVALUE` form for a sharper forward-only test. `ISCHANGED` is what the
  amendment's formula names, and it also catches a jump into `Negotiate` or `Closed Won` from any
  earlier stage rather than only from `Discover`. Q11 gates the Discover→Propose transition; the two
  later stages are in the list so the gate cannot be skipped past.
- **No `ISBLANK(`/`ISNULL(` anywhere near `StageName`.** Gotcha 14: applying either directly to a
  picklist is rejected at deploy time. `ISPICKVAL`, `ISCHANGED` and `PRIORVALUE` take a picklist
  directly; `ISBLANK` needs `TEXT()` first. The business condition here is a **checkbox**
  (`HasOpportunityLineItem`), so no blank guard arises at all. `check_validation_rules.py` prints one
  REVIEW advisory about this — see § 10.
- **`Closed Lost` is deliberately absent from the stage list.** Gotcha 15 and the worked example: a deal
  lost before a quote was ever built has no products, and blocking it teaches reps to park dead deals
  in `Negotiate`.
- **`Renewal` is deliberately absent from the record-type gate — and this disagrees with M2-S03.** See
  § 9. Recorded for the M2 gate, not resolved here.
- **No `$Setup.Integration_Bypass__c.Is_Active__c` clause.** `templates/admin/validation-rule-patterns.md`
  ("Bypass contract") asks every rule to admit a hierarchy Custom Setting *as well as* a Custom
  Permission and calls a missing bypass a P1 finding. This rule carries the Custom Permission half
  only: Q13 answers "no integrations write Enterprise opportunities", and no `Integration_Bypass__c`
  custom setting exists anywhere in this build for the token to resolve against. Writing one would be a
  `$Setup` reference to a component nothing creates. Recorded as a template divergence with a reason,
  per D3 — the same divergence M2-S03 recorded, now on two of two rules.
- **No roll-up summary, formula field or trigger.** The whole point of Gotcha 8 and Gotcha 15. Nothing
  in this step creates a second source of truth for a fact the Opportunity header already owns.
- **No `ValidationRuleTranslation`.** Northwind is a single-language build.
- **No `OpportunityLineItem` rule.** "At least one product" is a header question and this rule answers
  it. `Quantity`, `UnitPrice` and `TotalPrice` are line-item fields, and a per-line invariant belongs on
  `OpportunityLineItem`, where the rep's edit lands. No clarification asks for one.

## 8. Validate-only command for a human

`agents/metadata-builder` never runs this. It is text to copy.

This build validates against an org through the repo's own script, which assembles the selected steps'
artefacts and hands them to `sf project deploy start` with `checkOnly: true`. **That behaviour is
hard-coded inside `scripts/mock_deploy.py` and there is no flag that turns it off** — nothing about it
is the operator's to pass or to forget:

```bash
python3 scripts/mock_deploy.py .sfskills/builds/northwind-sales/plan.json \
  --org-alias <your-sandbox-alias> \
  --milestone M2 \
  --mode manifest
```

**Run it at milestone scope, not step scope.** A `--step M2-S04` run deploys this rule into an org that
may not hold the `Enterprise` record type or the eight stage values, and it fails for the absence of
M1's metadata rather than for anything wrong here. `--mode manifest` matches how M1 was validated
(`reports/MOCK-DEPLOY-M1.md`) and how M2-S03's note asks for M2.

**This run is what settles § 2.1.** Read its `summary.md` under `reports/mock-deploy/<ts>/` for the
`HasOpportunityLineItem` line specifically, and record the outcome against the skill.

For a production target the sequence is different — `sf project deploy validate` returning a job id,
then `sf project deploy quick` — per `change-management-and-deployment/references/metadata-examples.md`
§ 3, which carries its own UNVERIFIED (2026-09-04) caveat on `sf` CLI flag spellings: if a flag is
rejected, run `sf project deploy validate --help` rather than guessing a synonym.

## 9. The record-type disagreement with M2-S03 — for the M2 gate, not for this file

| | Record types gated |
|---|---|
| M2 milestone goal | "an **Enterprise or Renewal** deal above a 20% discount cannot be set to Closed Won…" (the goal's wording covers the *discount* cap) |
| `M2-S03` (discount) | `OR(RecordType.DeveloperName = "Enterprise", RecordType.DeveloperName = "Renewal")` — its builder chose both, citing the goal (open item `O-M2S03-01`) |
| `M2-S04` (this rule) | `RecordType.DeveloperName = "Enterprise"` — the amended formula names Enterprise only, and the worked example's own reasoning is "Renewals run a different process and must not be gated" |

Both are defensible and they are about two different rules, so this is not necessarily a defect —
but a reader comparing the two files will notice, and the answer should be on the record. This agent
built what the amendment says and changed neither rule. Note also that the Renewal business process
(`artefacts/M1-S01/objects/Opportunity/businessProcesses/Renewal_Sales_Process`) does not carry a
`Propose` stage at all, so extending this rule to Renewal would need its stage list rewritten to the
Renewal stages (`Renewal Review`, `Renewal Proposed`), not merely a second `RecordType` clause.
**Decide at the M2 gate.** Narrowing or widening later is one line in one file, plus a stage list.

## 10. What a green checker here does and does not prove

- `check_validation_rules.py` at **build** scope resolves this rule's `$Permission` token against
  M2-S01's custom permission and its `errorDisplayField` against the field inventory. At **step** scope
  it prints "field inventory absent at this scope, references unresolvable" as an INFO and exits 0 —
  which is why the step's declared checker test carries `"scope": "build"` and points at `artefacts`.
- The step note predicted **one REVIEW advisory**: "picklist logic has no explicit blank guard",
  because that heuristic looks for a literal `ISBLANK(` and this rule's business condition is a
  checkbox. That is not a defect and the exit code is unchanged (the test does not pass `--strict`).
  The actual run is recorded in this step's envelope.
- `check_products_and_pricebooks.py` at step scope scans a tree that contains one validation rule and
  no `Product2`, `Pricebook2` or `PricebookEntry` metadata. **It therefore has nothing in scope and its
  exit 0 asserts nothing about this step.** It is declared because the step cites the skill (§ 5
  checker-coverage WARN, `amend-step --add-checker`, 2026-09-18), and the skill earns its citation as a
  *knowledge* source — Gotcha 8 and its Questions-to-Ask row are why this rule reads the standard
  boolean instead of a roll-up — not as a source of metadata this step emits. Read its exit code as
  "nothing in scope", not as "the catalog is correct".
- **Nothing here proves the rule fires.** Setup showing "Active" does not either. The two Apex tests
  that would make this a regression test are in
  `validation-rules/references/metadata-examples.md` ("Apex tests"); no step of this build owns them,
  and that gap is named here so it is visible rather than assumed away.

## 11. After the deploy — the checks metadata cannot make

1. **Prove the rule landed active.** The Tooling API query in
   `validation-rules/references/metadata-examples.md` ("Verification after deploy") returns
   `ValidationName`, `Active`, `ErrorDisplayField` and `ErrorMessage` for every rule on Opportunity.
   A rule shipped `active=true` and one shipped `active=false` are identical in source control apart
   from one word, and indistinguishable in Setup at a glance.
2. **Prove `errorDisplayField` actually landed on `StageName`** rather than relocating to Top of Page.
   The same query returns it. This is the assertion `Database.Error.getFields()` makes in the skill's
   Apex test 1.
3. **Prove the bypass actually bypasses.** Assign `Sales_Ops_Validation_Bypass` to the sales-ops admin,
   then, as that user, move an Enterprise deal with no products from `Discover` to `Propose`. If it
   saves, the `$Permission` token resolved. If it does not, the permission is unassigned or the API
   name diverged — and nothing in this build's checkers can tell those two apart.
4. **Settle § 2.1 and record it.** Settled by run 1, § 2.1 above. The validate-only command for any
   future re-run is § 8.
