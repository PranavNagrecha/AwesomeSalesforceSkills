# Gotchas: Duplicate Management

---

## Alert Fatigue Kills Good Rules

**What happens:** Users see duplicate alerts constantly and learn to ignore them. Duplicates still enter the org, but leadership thinks there is protection because banners exist.

**When it bites you:** Contact creation, lead intake, and call-center processes with high record volume.

**How to avoid it:** Reserve alerts for cases with a clear review path, and block obvious duplicates when confidence is high.

---

## Matching on a Field Users Can Change

**What happens:** A field like email or account name is treated as the primary identity key even though users edit it freely or leave it blank.

**When it bites you:** Imports, integrations, and sales-data cleanup.

**How to avoid it:** Use stronger identifiers where possible and understand where fuzzy matching is helping versus hiding identity weakness.

---

## Merging Without Survivorship Rules

**What happens:** Different admins merge records differently. The "winner" changes based on who did the merge.

**When it bites you:** Historical cleanup projects and steward queues.

**How to avoid it:** Define record and field survivorship before bulk remediation starts.

---

## Duplicate Rules Ignore System-Created Data

**What happens:** UI entry is fairly clean, but integrations and bulk loads still create duplicate Accounts and Contacts.

**When it bites you:** Middleware retries, migration reruns, and batch imports.

**How to avoid it:** Coordinate duplicate management with integration keys, External IDs, and migration controls.

---

## `alertText` Is Rejected Unless an Action Is `Allow`

**What happens:** A `DuplicateRule` that sets `actionOnInsert` and `actionOnUpdate` to `Block` and also carries `alertText` fails to deploy. The Metadata API guide states the constraint on the `alertText` field: you can set a value for it "only when you have `actionOnInsert` or `actionOnUpdate` (or both) set to `Allow`. Otherwise, you receive a validation error when you add or update this component."

**When it bites you:** Hand-writing the XML after designing the rule in Setup, or tightening an existing alert rule to Block by editing `actionOnInsert` and forgetting to strip the message that came with it. The deployment error names a validation failure, not the field pairing, so it reads as a mystery.

**How to avoid it:** Treat `alertText` as belonging to the `Allow` branch. Block rules surface the platform's own error, not your message. If you need block behaviour *and* a custom message, block on one operation and allow-with-alert on the other, which is what the `Block` on insert / `Allow` on update example in `references/metadata-examples.md` does.

---

## `Allow` Without `alert` in `operationsOnInsert` Is a Silent No-Op

**What happens:** The rule is active, points at a good matching rule, and detects duplicates — and nobody ever sees anything. `actionOnInsert` = `Allow` only produces a dialog when `operationsOnInsert` contains `alert`. The guide spells out the other branch: "If `operationsOnInsert` isn't set to alert, the UI inserts the record without issuing an alert. The API inserts the record and doesn't return an error code."

**When it bites you:** Rules assembled from XML rather than Setup, and rules where someone removed `alert` to quieten complaints but left `report` in place. The org keeps a rule in its inventory, keeps counting it as a control, and gets nothing but `DuplicateRecordSet` rows nobody reads.

**How to avoid it:** Read `actionOn*` and `operationsOn*` as a pair, never separately. `Allow` + `alert` warns, `Allow` + `report` records silently, `Allow` + both does both, `Allow` + neither is decoration. The checker script flags the last case.

---

## `EnforceSharingRules` Lets the Invisible Duplicate Through Without a Word

**What happens:** A user creates a record that duplicates one they cannot see. Under `securityOption` = `EnforceSharingRules` the guide's behaviour is explicit: the insert or update proceeds, "the sharing rule doesn't prevent the user from creating or updating the record because the record is hidden from the user", and "No message is issued." The duplicate is created and nothing is logged to the user.

**When it bites you:** Private OWD orgs, territory-split sales teams, and Experience Cloud users — exactly the orgs whose duplicates come from two people who cannot see each other's records.

**How to avoid it:** Decide `securityOption` from the failure you are preventing, not from a security instinct. `BypassSharingRules` compares against records the user cannot see, so it actually blocks the cross-team duplicate; the guide notes that "other access restrictions apply" even then. `EnforceSharingRules` is the honest choice only when the existence of the other record is itself confidential.

---

## A Blocking Rule Cancels Everything Downstream of It

**What happens:** Duplicate rules run at step 6 of the order of execution, and the Apex Developer Guide states the consequence: if the rule "identifies the record as a duplicate and uses the block action, the record isn't saved and no further steps, such as after triggers and workflow rules, are taken." An after-insert trigger, an assignment rule, an auto-response, or a record-triggered after-save flow that the team assumes always runs simply does not.

**When it bites you:** Web-to-Lead and integration paths where the assignment rule or auto-response is the actual business function, and diagnosing "some leads never got routed" against a rule nobody connected to routing.

**How to avoid it:** Before turning an alert rule into a block rule, list the after-save automation on that object and confirm none of it is load-bearing for the blocked path. Because duplicate rules run *after* before-triggers and before-save flows (steps 3 and 4), normalisation belongs there: strip phone punctuation and lowercase the email in a before-save flow and the matching rule sees the cleaned value.

---

## A Workflow Field Update Creates Duplicates the Rule Never Sees

**What happens:** After a workflow field update the record is saved again, and the Apex Developer Guide lists what is skipped on that second pass: "Custom validation rules, flows, duplicate rules, processes built with Process Builder, and escalation rules aren't run again." If the field update writes into a field the matching rule compares, the resulting duplicate is never evaluated.

**When it bites you:** Legacy orgs with surviving workflow rules that stamp an email, a normalised company name, or a merge key — the very fields chosen as identity keys.

**How to avoid it:** Never let a workflow field update write a field a matching rule compares. Migrate those field updates to before-save record-triggered flows, which run at step 3 and are therefore visible to the duplicate rule at step 6.

---

## `allowSave` Bypasses Alerts Only, and Only From Apex DML

**What happens:** Two separate limits get conflated. First, `DMLOptions.DuplicateRuleHeader.allowSave` is documented as applying "when the Alert option is enabled" — it does not override a rule whose action is `Block`. Second, the Apex Developer Guide notes that `DMLOptions` settings "take effect only for record operations performed using Apex DML and not through the Salesforce user interface", so the same class invoked behind a Lightning action still meets the rule on the UI path.

**When it bites you:** An integration class written to "turn off duplicate checking" that keeps failing against a Block rule, and a bypass built for a batch job that stops working the moment the logic is reused by a screen flow.

**How to avoid it:** Bypass is a rule-design decision, not a code decision. To exempt a system integration, keep the rule on `Allow` + `alert` and set `allowSave` in the integration's DML, or scope the rule away from those records with a `duplicateRuleFilter`. Pair `allowSave` with `runAsCurrentUser = true`, which the guide recommends specifically for detecting duplicates during lead conversion.

---

## `Datacloud.FindDuplicates` Caps at 50 and Throws When Nothing Is Active

**What happens:** The pre-insert duplicate check that works in a screen flow fails in a batch. The Apex Reference Guide sets two hard behaviours: "the input array is limited to 50 elements", above which it raises `Configuration error: The number of records to check is greater than the permitted batch size`; and with no active rule for the object it throws `System.HandledException` with "No active duplicate rules are defined for the {ObjectName} object type."

**When it bites you:** Reusing a single-record dedupe helper inside a `Batchable.execute` with a 200-record scope, and running the same code in a sandbox where the rules were never activated after the refresh.

**How to avoid it:** Chunk input into groups of 50 and catch `System.HandledException` around the call so a deactivated rule degrades to "no duplicates found" rather than an unhandled failure. Note too that the method "doesn't return custom fields by default" and standard matching rules ignore custom fields entirely, so identity on a custom external-id field needs a custom matching rule.

---

## Standard Duplicate Rules Cover a Short, Fixed Object List

**What happens:** The Object Reference gives `DuplicateRule.sObjectType` as a restricted picklist with exactly four possible values — Account, Contact, Individual, Lead — and closes the section with "DuplicateRule is unavailable in some orgs." `DuplicateRecordItem.RecordId` refers to the same four objects. A design that assumes Opportunity or a custom object works the same way has nothing to deploy against.

**When it bites you:** Extending a dedupe programme from Contacts to a custom Application or Registration object, and writing a steward report that expects `DuplicateRecordItem` to point at anything.

**How to avoid it:** Confirm the object is supported in the target org before designing, by querying `DuplicateRule` and reading `SobjectType`. UNVERIFIED (2026-09-04): Salesforce Setup does expose custom objects for duplicate rules, but the Object Reference's restricted picklist for `sObjectType` does not list them and help.salesforce.com cannot be fetched to reconcile this — verify against the target org's `DuplicateRule` describe rather than assuming either way. For unsupported objects the fallback is a unique external-id field plus a before-save flow or trigger.

---

## Matching-Rule Activation Is Asynchronous and Can Fail

**What happens:** A deploy that sets `ruleStatus` to `Active` succeeds, and the rule is still not active. The status enum on `MatchingRule` includes `Activating`, `ActivationFailed`, `Deactivating`, and `DeactivationFailed` alongside `Active` and `Inactive` — states that only exist because activation is a background operation that builds a match index. Only `Active` and `Inactive` are declarable in a package, so the intermediate and failed states are things you observe, never things you set.

**When it bites you:** CI pipelines that deploy and immediately run a test expecting duplicate detection, and post-refresh sandbox setup where the rules look configured in Setup but never finished activating.

**How to avoid it:** After deploying, verify with `SELECT DeveloperName, RuleStatus FROM MatchingRule WHERE SobjectType = 'Contact'` rather than trusting the deploy result, and treat any value other than `Active` as a failed change. A duplicate rule pointing at a non-`Active` matching rule detects nothing; the checker script resolves that reference across files.
