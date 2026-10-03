# Deploy order — M2-S03

Build: `northwind-sales` · Milestone: M2 (Guidance, guardrails and who may bypass them) · Step type: `validation` · API version 62.0

This note is written by `agents/metadata-builder` Step 7 and is text for a human. Nothing in it is
executed by this agent or by any acceptance test.

Sourced from `skills/admin/validation-rules/references/metadata-examples.md` ("The type in one table",
"Where the file lives", Example 1, Example 2, "package.xml"), `skills/admin/validation-rules/references/gotchas.md`
("Rules Fire During Data Loads", "errorDisplayField Silently Relocates to Top of Page", "Rules Fire on
REST and SOAP API by Default", "A Workflow Field Update Re-Saves the Record and Validation Rules Do Not
Run Again", "ValidationRule Does Not Support the Wildcard in package.xml", "Translated Error Messages
Live in a Separate Metadata Type", Gotcha 14), `skills/admin/custom-permissions/references/gotchas.md`
#4 and `references/metadata-examples.md` § 6, `skills/admin/opportunity-management/SKILL.md` (Core
Concepts; step 5 of its workflow), `templates/admin/validation-rule-patterns.md` ("The canonical VR
shape", "Bypass contract"), and `skills/admin/change-management-and-deployment/references/metadata-examples.md`
§§ 1 and 3.

## 0. Why API version 62.0

`plan.json` carries no `api_version`, so `agents/metadata-builder/AGENT.md` ("Inputs") falls back to
`62.0`. Every step shipped so far carries the same value — `artefacts/M1-S01/package.xml`,
`artefacts/M1-S02/package.xml` and `artefacts/M2-S01/package.xml` all declare
`<version>62.0</version>`. Keeping 62.0 here means `scripts/mock_deploy.py`'s highest-version rule sees
one version across the whole build rather than a step that silently raises it.

## 1. Order inside this step

This step produces exactly one component, so there is no internal ordering to decide.

| # | Component | Because |
|---|---|---|
| 1 | `ValidationRule:Opportunity.Opportunity_Discount_Requires_Approval` | The only member in this step's `package.xml`, and the only file under `artefacts/M2-S03/`. |

## 2. Dependencies on components outside this step — all four are load-bearing

A validation rule is compiled at deploy time. Every token in `errorConditionFormula` has to resolve in
the target org *at that moment*, and the four things this formula names come from three earlier steps.
`depends_on` in `plan.json` records two of them (`M1-S01`, `M2-S01`); the layout dependency in § 3 is a
display dependency rather than a compile dependency, which is why it is not in `depends_on` and is
written out here instead.

| Must exist first | Built by | Referenced as | What happens if it is missing |
|---|---|---|---|
| `Opportunity.Discount__c` (Percent, precision 5, scale 2) | M1-S01 | `Discount__c` in the formula **and** in `errorDisplayField` | The deploy fails at formula compile: an unknown field is a compile error, not a silent false. |
| `Opportunity.Approval_Status__c` (restricted picklist Pending/Approved/Rejected) | M1-S01 | `ISPICKVAL(Approval_Status__c, "Approved")` | Same — compile error. The literal `"Approved"` must also be a value of the picklist; M1-S01's field file carries it. |
| Record types `Opportunity.Enterprise` and `Opportunity.Renewal` | M1-S01 | `RecordType.DeveloperName = "Enterprise"` / `= "Renewal"` | `RecordType.DeveloperName` is a relationship field on Opportunity and resolves regardless, but a *missing record type* makes the gate unreachable: every record has some other record type, the `OR(...)` is false, and the rule never fires. Silent, not loud. |
| `CustomPermission:Bypass_Opportunity_Sales_Validation` | M2-S01 | `NOT($Permission.Bypass_Opportunity_Sales_Validation)` | **Silently false.** See § 2.1. |

### 2.1 This is the step that proves the bypass wiring, and it proves it only in an org

`skills/admin/custom-permissions/references/gotchas.md` #4 is explicit about the failure mode: a
`$Permission.X` naming a permission that is not present evaluates to `false` with "no error, just
silent grant of access to nobody" — here, inverted by the outer `NOT()`, it means the bypass clause is
permanently `true` and **nobody can bypass the rule, including the sales-ops admin**. The deploy is
green either way. `artefacts/M2-S01/deploy-order.md` § 2 states the same thing from the other side.

Three consequences for the deployer:

1. **Deploy M2-S01 before this step, or in the same request.** Order matters in the real direction:
   the permission must be in the org when a user saves an Opportunity, not when the rule compiles.
2. **M2-S03 is the first artefact in this build that consumes the permission.** Until this step exists,
   `check_custom_permissions.py --manifest-dir artefacts` reports the permission with `Consumers 0`
   (recorded in `artefacts/M2-S01/deploy-order.md` § 2 and in M2-S01's first acceptance test). With this
   step on disk the same command over the whole tree resolves this rule as a consumer and reports
   `Consumers 1`. That is a *tree* check, not a *step* check — the same command inside `artefacts/M2-S03`
   sees no `customPermissions/` directory and checks nothing.
3. **A green checker is not a green org.** Both the custom-permissions coverage table and
   `check_validation_rules.py`'s VR-REF-02 match on the file-name stem
   `Bypass_Opportunity_Sales_Validation`. They prove the two files agree with each other. They cannot
   prove the permission is assigned to anyone — assignment is record data
   (`PermissionSetAssignment`), it ships in no manifest, and `artefacts/M2-S01/deploy-order.md` § 4
   carries the instruction. The bypass is not usable until the sales-ops admin holds
   `Sales_Ops_Validation_Bypass`.

## 3. `errorDisplayField` depends on a layout, and layouts are M1-S02's

`errorDisplayField` is `Discount__c`. The Metadata API guide's own condition, quoted in
`skills/admin/validation-rules/references/metadata-examples.md`: "If you do not specify a value **or
the field isn't visible on the page layout**, the value changes automatically to Top of Page."

Both layouts M1-S02 shipped carry `Discount__c` with `<behavior>Edit</behavior>`
(`artefacts/M1-S02/layouts/Opportunity-Opportunity Enterprise Layout.layout-meta.xml` and
`…Renewal Layout.layout-meta.xml`), so on both record types in scope the error attaches to the field
the rep has to change. Removing `Discount__c` from either layout relocates the message to the top of
the page — without a deploy, without a warning, and without touching this rule. Add
`errorDisplayField` to the change-impact list for that field.

## 4. Manifest member forms used

| Type | Member form | Source |
|---|---|---|
| `ValidationRule` | `Opportunity.Opportunity_Discount_Requires_Approval` — object, dot, rule name | `validation-rules/references/metadata-examples.md` "package.xml"; `change-management-and-deployment/references/metadata-examples.md` § 1 |

<!-- UNVERIFIED (2026-09-19): both cited references carry their own UNVERIFIED (2026-09-04) marker on
this exact point — the Metadata API Developer Guide shows no ValidationRule manifest sample, so
`Object.RuleName` is inferred from the documented CustomField / ListView `objectName.componentName`
pattern rather than quoted. It is also the form M1-S01's manifest already uses for its RecordType and
BusinessProcess members, so the build is at least internally consistent. If a deploy rejects the
member, retrieve `CustomObject:Opportunity` instead and read the form back off the result. -->

**`ValidationRule` does not accept the `*` wildcard** — stated outright in the Metadata API guide's
ValidationRule type reference and repeated in this skill's gotchas. A manifest using `*` for this type
"does not error usefully — it simply retrieves nothing, and the deploy that follows is missing every
rule while reporting success." The member above is therefore named explicitly, which is also what makes
the manifest agree with the files on disk in both directions.

Only `ValidationRule` appears in this step's `package.xml`. The custom permission and the two fields
are real deploy dependencies but they are *other steps'* members, and "Metadata API references the
components listed in the manifest, not the directories in the .zip file" — a manifest that claimed
them here would deploy nothing extra and would make two steps claim the same component.

## 5. Elements deliberately not written, and why

- **No `<errorDisplayField>` omission.** Rule 3 of the skill's Example 1 omits it on purpose when the
  error is about a transition rather than a field. Here the rep's fix is a single field — lower the
  discount or get the approval — so the field form is the right one (Q15 asked for a message that names
  the fix; the step's manual acceptance test asserts the field).
- **`active` is `true`, and that is a decision rather than a default.** The skill's standing advice is
  to ship `active=false` when existing data violates the rule, and Q16 answers that **about 6 open
  Enterprise deals already carry a discount above 20%**. Q16 also answers what to do about it: "the
  rules apply on the next save only — no clean-up in scope." Those six deals are not blocked from
  existing; they are blocked from being saved into `Closed Won` while still above the cap without an
  approval, which is precisely the rule the requester asked for. Shipping inactive would have needed a
  named cleanup owner and a second one-line deploy, and Q16 declined both.
- **No `$Setup.Integration_Bypass__c.Is_Active__c` clause.** `templates/admin/validation-rule-patterns.md`
  ("Bypass contract") asks every rule to admit a hierarchy Custom Setting *as well as* a Custom
  Permission, and calls a missing bypass a P1 finding. This rule carries the Custom Permission half
  only: Q13 answers "no integrations write Enterprise opportunities", the build's scope list rules out
  "any integration, inbound or outbound", and no `Integration_Bypass__c` custom setting exists in this
  build for the token to resolve against. Writing one would be a `$Setup` reference to a component
  nothing creates. Recorded here as a template divergence with a reason, per D3.
- **No `ISCHANGED(StageName)` and no `NOT(ISNEW())`.** This rule gates a *state*, not a *transition*: a
  deal must not sit at Closed Won above the cap without an approval, however it got there — including
  an insert straight at Closed Won, and including a later edit that leaves the stage alone and raises
  the discount. `ISCHANGED` would let both through. Both guards are the right call for M2-S04's product
  gate (`references/gotchas.md` Gotcha 15 requires them there) and the wrong call here; the two rules
  differ on this point deliberately.
- **No `PRIORVALUE`.** Nothing in this rule reads a prior value, so the `NOT(ISNEW())` guard that
  `PRIORVALUE` would require never arises.
- **No `ValidationRuleTranslation`.** Northwind is a single-language build; no clarification names a
  second language. If one is ever added, the gotcha to read first is "Translated Error Messages Live in
  a Separate Metadata Type" — the translation is a `CustomObjectTranslation` component and re-deploying
  this rule carries none of it.

## 6. What the formula does not protect against

Stated because a deployer reading a green checker should not read more into it than it says:

- **A line-item edit does not re-run this rule.** `references/gotchas.md` ("Opportunity Validation
  Rules Do Not Fire When a Line Item Changes the Opportunity") applies to every Opportunity rule. It
  does not bite *this* rule the way it bites an `Amount` rule, because `Discount__c` is a header field
  the rep types (Q12: "Line-item discounts are not used") rather than a roll-up — but if anyone ever
  converts `Discount__c` to a roll-up or formula over `OpportunityLineItem`, this rule stops being an
  invariant on the day of that change and nothing in the metadata will say so.
- **A workflow field update can still commit a violating record.** Custom validation rules are not
  re-run after a workflow field update re-saves the record. Assumption **A8** records the build's
  position — that no legacy automation writes `StageName`, `Amount`, `Discount__c` or
  `Approval_Status__c` after save — as an assumption at `risk: medium`, not as a verified fact. It is
  worth ten minutes in the target org before go-live: Setup → Workflow Rules, filtered to Opportunity.
- **The rule fires on the API too, and that is deliberate.** Assumption A7 records that both M2 rules
  are enforced everywhere — API, every layout, Flow — because they are validation rules rather than
  layout-Required settings. Q13 confirms there is no integration user to exempt.

## 7. Validate-only command for a human

`agents/metadata-builder` never runs this. It is text to copy.

This build validates against an org through the repo's own script, which assembles the selected steps'
artefacts and hands them to `sf project deploy start` with `checkOnly: true`. That behaviour is
hard-coded inside `scripts/mock_deploy.py` and there is no flag that turns it off, so nothing about it
is the operator's to pass or to forget:

```bash
python3 scripts/mock_deploy.py .sfskills/builds/northwind-sales/plan.json \
  --org-alias <your-sandbox-alias> \
  --milestone M2 \
  --mode manifest
```

**Run it at milestone scope, not step scope.** A `--step M2-S03` run deploys this rule into an org that
may not hold `Discount__c`, `Approval_Status__c` or the two record types, and it fails for the absence
of M1's metadata rather than for anything wrong here. The milestone run is also the only one that
exercises the `$Permission` token against M2-S01's permission — and even then, per § 2.1, a token that
resolves to nothing validates green. `--mode manifest` matches how M1 was validated
(`reports/MOCK-DEPLOY-M1.md`).

For a production target the sequence is different — `sf project deploy validate` returning a job id,
then `sf project deploy quick` — per `change-management-and-deployment/references/metadata-examples.md`
§ 3, which carries its own UNVERIFIED (2026-09-04) caveat on `sf` CLI flag spellings: if a flag is
rejected, run `sf project deploy validate --help` rather than guessing a synonym.

## 8. After the deploy — the two checks metadata cannot make

1. **Prove the rule landed active.** The Tooling API query in
   `validation-rules/references/metadata-examples.md` ("Verification after deploy") returns
   `ValidationName`, `Active`, `ErrorDisplayField` and `ErrorMessage` for every rule on Opportunity. A
   rule shipped `active=true` and a rule shipped `active=false` are indistinguishable in Setup at a
   glance and identical in source control apart from one word.
2. **Prove the bypass actually bypasses.** Assign `Sales_Ops_Validation_Bypass` to the sales-ops admin,
   then save a Closed Won Opportunity at 25% discount with no approval as that user. If it saves, the
   `$Permission` token resolved. If it does not, the permission is unassigned or the API name diverged —
   and nothing in this build's checkers can tell those two apart. `validation-rules/references/metadata-examples.md`
   carries the two Apex tests that make this a regression test rather than a one-off click-through; they
   are not in this build's scope (no Apex step owns them) and are named here so the gap is visible.
