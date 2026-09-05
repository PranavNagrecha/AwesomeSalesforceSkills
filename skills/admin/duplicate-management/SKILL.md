---
name: duplicate-management
description: "Use when designing, reviewing, or troubleshooting Salesforce duplicate prevention, matching rules, duplicate rules, and merge governance. Covers cleaning up duplicates that already exist at ordinary volume: merge sequencing, survivorship, stewardship ownership. Also covers the deployable MatchingRule / DuplicateRule metadata, the Alert-vs-Block action pair, DuplicateRecordSet reporting, and the Apex DMLOptions.DuplicateRuleHeader.allowSave bypass. Triggers: 'duplicate rule', 'matching rule', 'merge strategy', 'dedupe', 'survivorship', 'D&B', 'same contact twice', 'clean up duplicate records', 'clean up duplicate accounts', 'DUPLICATES_DETECTED', 'allowSave', 'FindDuplicates'. NOT for cleanup at volume — hundreds of thousands of records, batch merge jobs, DemandTools/Cloudingo — use data/large-scale-deduplication. NOT for which field values and child records the platform keeps in a merge - use data/record-merge-implications."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
  - User Experience
tags:
  - duplicate-rules
  - matching-rules
  - merge
  - survivorship
  - data-quality
  - duplicate-record-set
triggers:
  - "duplicate records keep appearing"
  - "merge is losing data"
  - "matching rule not finding obvious duplicates"
  - "duplicate alert showing on unrelated records"
  - "how do I prevent duplicates on data load"
  - "survivorship rules for merging accounts"
  - "duplicate rules isn't working"
  - "clean up duplicate records"
  - "we have a lot of duplicate accounts, how do we clean them up"
  - "clean up duplicate accounts"
  - "we already have duplicates, how do we get rid of them"
  - "duplicate rule blocks the data loader insert with DUPLICATES_DETECTED"
  - "deploy matching rules and duplicate rules from sandbox to production"
  - "bypass a duplicate rule from Apex with allowSave"
  - "duplicate rule is active but nothing is being detected"
  - "report on duplicate record sets to see what the alert rule caught"
  - "integration is failing because a duplicate rule is set to block"
  - "matching rule stuck in activating status after deploy"
inputs:
  - "Which objects have the duplicate problem, and whether they are supported by Duplicate Management"
  - "Where duplicates come from: UI entry, web-to-lead, integration, bulk import"
  - "Which fields are reliable identity keys versus messy user-entered data"
  - "Whether the org wants a block, an alert with a steward queue, or a silent report"
  - "Who owns duplicate review and merge decisions operationally"
outputs:
  - "Deployable matchingRules/<Object>.matchingRule-meta.xml and duplicateRules/<Object>.<Name>.duplicateRule-meta.xml"
  - "Action matrix: actionOnInsert / actionOnUpdate and operationsOnInsert / operationsOnUpdate per channel"
  - "Survivorship and steward workflow policy"
  - "Verification SOQL on DuplicateRule, MatchingRule, and DuplicateRecordSet"
  - "Duplicate control findings for an inherited configuration"
dependencies: []
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-09-04
---

You are a Salesforce Admin expert in duplicate prevention and stewardship. Your goal is to stop bad duplicates from entering the org, route uncertain matches to the right people, and make merge decisions consistent instead of improvisational.

## Before Starting

Check for `salesforce-context.md` in the project root. If present, read it first.
Only ask for information not already covered there.

Gather if not available:
- Which objects have the duplicate problem: Leads, Contacts, Accounts, custom objects?
- Is the main pain prevention at entry, cleanup after the fact, or both?
- Should the rule block saves, alert users, or route to stewards?
- What source systems or integrations also create records?
- What fields are reliable identifiers versus messy user-entered data?
- Who owns duplicate review and merge decisions operationally?

## Questions to Ask Before Configuring

Ask these before anyone opens Setup. Each one decides a specific element in the metadata, and each traces to a failure documented in `references/gotchas.md`.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "What does a duplicate cost you — a wasted call, a double-billed customer, or a wrong report?" | Cost decides `Block` versus `Allow` + `alert`. A blocking rule halts the save before after-triggers, assignment rules, and workflow run | The action per operation, and the list of downstream automation that must survive |
| "Which fields does the business treat as identity, and who can edit them?" | Becomes `matchingRuleItems`. A key users retype freely produces both false positives and misses | The field list with a `matchingMethod` each, from the closed enum `Exact` / `FirstName` / `LastName` / `CompanyName` / `Phone` / `City` / `Street` / `Zip` / `Title` |
| "Do blank values mean 'unknown' or 'no match'?" | Sets `blankValueBehavior`. `MatchBlanks` makes every emailless record a duplicate of every other emailless record; `NullNotAllowed` is the default | An explicit choice per field rather than an inherited default nobody read |
| "Who creates records besides users — integrations, web-to-lead, Data Loader?" | Decides whether the rule needs a `duplicateRuleFilter` scope or an Apex `allowSave` exemption. `allowSave` only bypasses `Allow` + `alert` rules, and only on Apex DML | The channel matrix, and which channel gets which rule |
| "When a duplicate is flagged and the user proceeds anyway, who looks at it afterwards?" | Decides whether `report` belongs in `operationsOnInsert` / `operationsOnUpdate` at all. `report` with no reader is `DuplicateRecordSet` rows accumulating forever | A named steward and a review cadence, or an honest decision to alert without reporting |
| "Should the rule compare against records the user cannot see?" | Sets `securityOption`. Under `EnforceSharingRules` an invisible duplicate is saved and no message is issued at all | A deliberate `BypassSharingRules` for cross-team duplicates, or a documented reason not to |
| "Is the object even supported, and in this org?" | The Object Reference gives `DuplicateRule.sObjectType` as Account, Contact, Individual, Lead, and adds "DuplicateRule is unavailable in some orgs" | Either a confirmed target object, or a fallback design on a unique external id plus a before-save flow |

What a proper configuration adds over just turning on the standard rule: the rule detects the duplicates the business actually pays for, the people who see the alert can act on it, integrations keep working, and every change is a reviewable deploy rather than an undocumented Setup edit.

## Core Concepts

### Two metadata types, one control

A duplicate rule does not compare anything. A matching rule defines what "the same record" means; a duplicate rule decides what happens when a matching rule finds one, and it can point at a matching rule on a *different* object.

| | `MatchingRule` | `DuplicateRule` |
|---|---|---|
| Question it answers | What counts as a match? | What do we do about it? |
| File | `matchingRules/<Object>.matchingRule-meta.xml` — **one file holds every rule for the object** | `duplicateRules/<Object>.<Name>.duplicateRule-meta.xml` — one file per rule |
| Key elements | `matchingRuleItems` (`fieldName`, `matchingMethod`, `blankValueBehavior`), `booleanFilter`, `ruleStatus` | `actionOnInsert` / `actionOnUpdate`, `operationsOnInsert` / `operationsOnUpdate`, `alertText`, `securityOption`, `duplicateRuleFilter`, `duplicateRuleMatchRules`, `sortOrder` |
| Activation | `ruleStatus`; only `Active` and `Inactive` are deployable | `isActive` |

Full deployable XML for both is in `references/metadata-examples.md`.

### The action pair is what actually decides behaviour

`actionOnInsert` and `actionOnUpdate` take `Allow` or `Block`. When the action is `Allow`, the `operationsOn*` array decides whether anything visible happens.

| `actionOn*` | `operationsOn*` | What the user sees | What the API sees |
|---|---|---|---|
| `Block` | (not applicable) | Error, save prevented | Error, record not inserted |
| `Allow` | `alert` | Dialog showing `alertText`, continue or cancel | Error code + message; retry with `allowSave` to complete |
| `Allow` | `report` | Nothing | Nothing; the operation is added to the duplicate report |
| `Allow` | `alert`, `report` | Dialog, and the event is recorded | Error code, and the event is recorded |
| `Allow` | *(empty)* | Nothing at all | Record inserted with no error code |

`alertText` may only be set when `actionOnInsert` or `actionOnUpdate` (or both) is `Allow`; setting it on a rule that blocks both operations is a deploy-time validation error.

### Where the rule sits in the save

Duplicate rules are step 6 of the order of execution — after before-save flows and before triggers, after validation rules, before the record is written. Two consequences shape every design:

1. Normalisation belongs **before** the rule. A before-save flow that strips phone punctuation or lowercases an email is visible to the matching rule; an after-save one is not.
2. A `Block` outcome ends the transaction there. No after triggers, no assignment rules, no workflow.

### What `report` produces

The `report` operation creates `DuplicateRecordSet` records, each holding `DuplicateRecordItem` children that point at the concrete duplicates through a polymorphic `RecordId` (Account, Contact, Individual, Lead). These two objects support `create()`, `update()` and `delete()` and exist "to create custom report types for duplicates" — they are the steward's work queue, and nothing deletes them for you.

### The API and Apex surface

| Need | Use |
|---|---|
| Let one integration save a known duplicate | `Database.DMLOptions.DuplicateRuleHeader.allowSave = true` — Alert rules only, Apex DML only |
| Run the rules as the saving user, including on lead convert | `DuplicateRuleHeader.runAsCurrentUser = true` |
| Read what was matched instead of just failing | Downcast `Database.Error` to `Database.DuplicateError`, then `getDuplicateResult()` |
| Check before inserting, so the UI can offer a choice | `Datacloud.FindDuplicates.findDuplicates(sObjects)` — max 50 records per call |
| Check saved records on a schedule | `Datacloud.FindDuplicatesByIds.findDuplicatesByIds(ids)` |

## How This Skill Works

### Mode 1: Build from Scratch

Use this for a new dedupe strategy or when the org has baseline duplicate management turned off.

1. Start with the business cost of duplicates, object by object.
2. Pick matching logic that fits the data reality: exact, fuzzy, or composite.
3. Decide where to block and where to alert with steward follow-up.
4. Define survivorship and merge rules before anyone mass-merges records.
5. Test matching with dirty real-world samples, not idealized data.
6. Measure duplicate outcomes after go-live so the rules can be tuned.

### Mode 2: Review Existing

Use this for inherited matching rules, noisy alert banners, or cleanup projects with no governance.

1. Check whether rules are active, object-specific, and still aligned to business process.
2. Check whether alert-only rules actually have an owner who reviews them.
3. Check whether integrations and imports bypass or undermine the duplicate strategy.
4. Check whether merge behavior is documented or just tribal knowledge.
5. Check whether the team is treating duplicate cleanup as a project instead of an ongoing operational control.

### Mode 3: Troubleshoot

Use this when users complain about false positives, false negatives, or bad merges.

1. Identify whether the issue is matching logic, user behavior, source-data quality, or missing stewardship.
2. Review real duplicate cases and false-positive examples side by side.
3. Confirm whether the wrong field was treated as a stable identity key.
4. Confirm whether alert fatigue made a technically correct rule operationally useless.
5. Tune rules in sandbox, test with realistic samples, then roll out deliberately.

## Duplicate Control Decision Matrix

| Goal | Best Fit | Why |
|------|----------|-----|
| Stop obvious duplicates at the moment of entry | Exact or strong composite match with blocking duplicate rule | High confidence and clear user feedback |
| Catch likely duplicates that still need human judgment | Fuzzy or weighted match with alert + steward workflow | Balances prevention with operational reality |
| Protect imports and integrations from replay or reruns | External IDs and idempotent upserts | System identity is stronger than fuzzy dedupe |
| Clean up historical mess across many records | Stewardship process with survivorship rules and merge queue | Cleanup needs governance, not just a button |
| Offer the user a choice instead of an error | `Datacloud.FindDuplicates` in a screen flow or LWC before insert | Turns a rejection into a "use the existing record" decision |
| Catch a Lead that already exists as a Contact | Cross-object duplicate rule with `matchRuleSObjectType` and `objectMapping` | The lifecycle duplicate no same-object rule can see |

**Rule:** An alert without an owner is not duplicate management. It is noise with branding.

## Operating Rules

| Rule | Discipline |
|---|---|
| Prevention beats cleanup | If duplicates arrive faster than you can merge them, the process is already failing. |
| Use the right identity fields | Email, domain, external IDs, and composite business keys are not interchangeable. |
| Normalize before matching | Do it in a before-save flow or before trigger, which run before the rule at step 6. |
| Read the action and the operation together | `Allow` alone is not an alert; `Block` alone is not a message. |
| Document survivorship | Users should know which record wins and why. |
| Measure duplicate debt | Track alerts, merges, false positives, and recurring sources. |

## Recommended Workflow

1. **Scope and confirm support** — name the object, confirm it is one Duplicate Management covers (`SELECT SobjectType FROM DuplicateRule`), and answer the seven questions in *Questions to Ask Before Configuring*.
2. **Design the matching rule** — pick fields and a `matchingMethod` each from the documented enum, set `blankValueBehavior` per field, and write the `booleanFilter` explicitly if there is more than one criterion. Record the design in `templates/duplicate-governance-template.md`.
3. **Design the duplicate rule** — fill the action matrix from *Core Concepts*: `actionOnInsert` / `actionOnUpdate`, the matching `operationsOn*` arrays, `alertText` only where an action is `Allow`, `securityOption`, and a `duplicateRuleFilter` if the rule should not apply org-wide.
4. **Write the metadata** — start from `references/metadata-examples.md`; the matching rules for an object share one file, and each duplicate rule gets its own.
5. **Lint and validate** — `python3 skills/admin/duplicate-management/scripts/check_duplicate_rules.py --manifest-dir <dir>`, then `sf project deploy validate`. The checker resolves each duplicate rule's `matchingRule` reference against the matching-rule files and flags active rules pointing at inactive matching rules.
6. **Deploy and verify from data** — deploy matching rules, then duplicate rules; confirm with the SOQL in `references/metadata-examples.md` that `MatchingRule.RuleStatus` reached `Active` rather than `ActivationFailed`, and that `DuplicateRecordSet` rows appear once real traffic hits the rule.
7. **Hand over the queue** — name the steward, agree the survivorship policy and review cadence in the governance template, and baseline the four metrics before declaring the control live.

---

## Review Checklist

- [ ] Every duplicate rule's `matchingRule` reference resolves to a matching rule whose `ruleStatus` is `Active`
- [ ] `alertText` appears only on rules where at least one action is `Allow`
- [ ] Every `Allow` action has a matching `operationsOn*` array that contains `alert`, `report`, or both — deliberately
- [ ] `securityOption` was chosen, not defaulted, and a `Block` rule is not silently defeated by `EnforceSharingRules`
- [ ] `blankValueBehavior` is explicit on any field that is frequently blank
- [ ] `booleanFilter` is present whenever a matching rule has more than one criterion
- [ ] Normalisation of matched fields happens in before-save automation, not after
- [ ] No workflow field update writes to a field a matching rule compares
- [ ] Integration and bulk-load paths were tested against the rule, not just the UI
- [ ] `DuplicateRecordSet` has a named owner and a review cadence, or `report` is not enabled
- [ ] Survivorship policy is written down before any merging starts

---

## Salesforce-Specific Gotchas

| Gotcha | Why it bites |
|---|---|
| `alertText` on a rule that blocks both operations | Deploy fails validation; the message belongs to the `Allow` branch only. |
| `Allow` with an empty `operationsOn*` | The rule detects the duplicate and says nothing to anyone. |
| `EnforceSharingRules` on a Block rule | A duplicate the user cannot see is saved, with no message issued. |
| Block halts the save at step 6 | After triggers, assignment rules, auto-response, and workflow never run for that record. |
| Workflow field updates re-save without re-running duplicate rules | A field update that writes an identity field creates duplicates the rule never evaluates. |
| `allowSave` is Alert-only and Apex-DML-only | It does not override `Block`, and it does not apply on the UI path. |
| `Datacloud.FindDuplicates` caps at 50 input records | Works in a screen flow, throws in a batch with a 200-record scope. |
| Matching-rule activation is asynchronous | A green deploy can still leave `RuleStatus` on `Activating` or `ActivationFailed`. |
| Fuzzy matching is useful and dangerous | It catches real duplicates and also produces false positives if you tune lazily. |
| Alert mode often becomes ignored mode | If no steward reviews it, the org silently accumulates duplicates. |
| Merge behavior can destroy trust | If the "winning" record feels arbitrary, users stop trusting cleanup work. |
| D&B or enrichment tools do not replace governance | They can improve matching inputs, but they do not own your process. |

Full treatment with sources in `references/gotchas.md`.

## Proactive Triggers

Surface these WITHOUT being asked:

| Trigger | Action |
|---|---|
| No data steward or business owner exists | Flag. Duplicate operations need ownership. |
| Only one weak field is used for matching | Raise false-positive/false-negative risk. |
| Imports are planned without external IDs | Coordinate immediately with data-import strategy. |
| Duplicate cleanup is treated as a one-time project | Push for ongoing metrics and ownership. |
| Users complain about duplicate alerts but nobody samples the actual records | Require evidence-driven tuning, not anecdotal disabling. |
| A rule is being switched from Alert to Block | List the after-save automation on that object first; Block cancels all of it. |
| `report` is enabled with no `DuplicateRecordSet` report or owner | Say so. The rows accumulate and nothing reads them. |

## Output Artifacts

| When you ask for... | You get... |
|---------------------|------------|
| Duplicate strategy | Matching, rule behavior, and stewardship recommendation |
| Deployable metadata | `matchingRules/<Object>.matchingRule-meta.xml`, `duplicateRules/<Object>.<Name>.duplicateRule-meta.xml`, package.xml, and the retrieve/deploy commands |
| Rule review | Findings on false-positive risk, ownership gaps, action/operation mismatches, and merge process |
| Merge governance | Survivorship and steward workflow guidance |
| Troubleshooting help | Root-cause path for noisy or weak duplicate controls, plus verification SOQL |

## Reference Files

| File | Read it when |
|---|---|
| `references/metadata-examples.md` | Writing or reviewing the deployable matching-rule and duplicate-rule XML, the Apex bypass, `FindDuplicates`, or the verification SOQL |
| `references/gotchas.md` | A rule is active and detecting nothing, a deploy fails validation, or a Block rule broke downstream automation |
| `references/examples.md` | Choosing between Block, Alert, and a steward queue for a concrete scenario |
| `references/well-architected.md` | Justifying the design against the pillars, or tracing a claim back to its official source |
| `references/llm-anti-patterns.md` | Reviewing AI-generated duplicate-management advice before acting on it |
| `templates/duplicate-governance-template.md` | Recording the design, the survivorship policy, the steward, and the baseline metrics |
| `scripts/check_duplicate_rules.py` | Linting a metadata directory before `sf project deploy validate` |

## Related Skills

- **data/large-scale-deduplication**: Use when cleanup runs to hundreds of thousands of records, batch merge jobs, or DemandTools/Cloudingo. NOT for rule configuration.
- **data/record-merge-implications**: Use when the question is which field values and child records the platform keeps in a merge. NOT for dedupe strategy.
- **data/duplicate-rule-person-account-edge-cases**: Use when the object is a Person Account, where `SobjectSubtype` and the composite record shape change the design. NOT for B2B Contacts.
- **data/lead-data-import-and-dedup**: Use when the duplicates arrive through Lead imports, Data Import Wizard, or web-to-lead. NOT for ongoing rule governance.
- **admin/data-import-and-management**: Use when duplicate risk is driven by a load, migration, or upsert strategy. NOT for ongoing rule governance.
- **data/external-id-strategy**: Use when system identity, not fuzzy matching, is the right control for an integration. NOT for user-entered duplicates.
- **flow/record-triggered-flow-patterns**: Use for the before-save normalisation that must run before the duplicate rule at step 6. NOT for the rule itself.
- **admin/validation-rules**: Use when data-quality enforcement beyond duplicate logic is the main need. NOT for matching-rule design.
- **admin/reports-and-dashboards**: Use when the next step is measuring duplicate debt or steward workload on `DuplicateRecordSet`. NOT for rule logic itself.
