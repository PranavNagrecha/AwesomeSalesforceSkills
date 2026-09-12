# Deploy order — M1-S01 (object model, Case field, platform event)

Build `tier2-webhook` · step `M1-S01` · type `object-model` · owner `metadata-builder`
(run under `build-step-runner`) · API version **67.0** (assumption A11) ·
`build_mode: design-only` — **nothing here has been deployed, and this agent deploys nothing.**

## 1. What this step ships

| # | Component | Type | Manifest member |
|---|---|---|---|
| 1 | `Integration_Failure__c` | CustomObject | `Integration_Failure__c` |
| 2 | Twelve custom fields on `Integration_Failure__c` | CustomField | `Integration_Failure__c.<field>` (12) |
| 3 | `Case.Tier2_Notified_At__c` | CustomField | `Case.Tier2_Notified_At__c` |
| 4 | `Tier2_Escalation__e` (with its five inline payload fields) | CustomObject | `Tier2_Escalation__e` |

## 2. Order inside this step

One `sf project deploy start` resolves all four in a single request; the order below is what
that request must not be split against.

1. **`Integration_Failure__c` before its twelve fields.** A `CustomField` member cannot deploy
   into an object that does not yet exist. The object file is also replaced *whole* — "specify
   all relevant fields when you create or update a custom object. You can't update a single
   field on the object" (`admin/object-creation-and-design/references/gotchas.md` Gotcha 10,
   api_meta.txt L41900–41901) — so never deploy a trimmed copy of it into an org that already
   holds the object.
2. **`Case.Tier2_Notified_At__c` has no intra-step predecessor.** `Case` is a standard object
   and this step deliberately ships **no** `Case.object-meta.xml`: adding one would replace the
   org's own Case definition wholesale.
3. **`Tier2_Escalation__e` is independent of both.** Its five payload fields are declared inline
   in the object file and deploy with it; they are *not* separate `CustomField` members. `EventUuid`
   and `ReplayId` are system fields on the delivered message and are deliberately not declared
   (`apex/platform-events-apex/references/code-examples.md` Artifact 1).

## 3. Order against the rest of the build

| This step | Must precede | Why |
|---|---|---|
| `Integration_Failure__c` + all 13 fields | **M1-S02** `Tier2_Webhook_Admin` permission set | "Permission sets referencing new fields fail if fields are not yet in the target" (`admin/change-management-and-deployment/references/llm-anti-patterns.md` Anti-Pattern 4, step 1 before step 5). |
| `Integration_Failure__c`, `Tier2_Escalation__e`, `Case.Tier2_Notified_At__c` | **M1-S03** Apex trigger / service / Queueable | Apex referencing an sObject or field that is not in the org fails to compile (same sequence, step 1 before step 2). |
| `Case.Tier2_Notified_At__c` | **M1-S04** scheduled health check | It queries the field. |
| — | **M1-S05** build-level `package.xml` | M1-S05 aggregates these members; it does not re-declare the files. |

**Do not deploy this step in the same request as M1-S02.** Retrieving a `CustomObject` "makes the
component appear in any Profile and PermissionSet components that are retrieved in the same
package" (Gotcha 10, api_meta.txt L41920–41921), so objects and permission sets travelling
together is how an unreviewed access change ships. Two requests, objects first.

**External dependency this step does not create:** the queue `Tier_2_Engineering` (assumption A8)
is assumed to exist in the target org. Nothing here creates or modifies it.

## 4. Decisions recorded while writing these files

| Element | Value written | Source |
|---|---|---|
| `sharingModel` | `Private` | Step input + decision **D12** / assumption **A3**; `standards/decision-trees/sharing-selection.md` Q1 ("Public Read-Only / Public Read-Write → Tighten OWD before adding anything"). |
| `deploymentStatus` | `Deployed` | Step input. `InDevelopment` is invisible to non-admin users and fails the step's own checker. |
| `enableSearch` | `true` | Step input. Search is off by default on new custom objects since API 35.0 (api_meta.txt L42062–42066). |
| `enableBulkApi` / `enableSharing` / `enableStreamingApi` | all `true` | Step input says the trio is set all-or-none; each element's guide entry requires the other two (api_meta.txt L42013–42019, L42079–42092). **See §5 item 1** — the input fixes the all-or-none rule, not the value. |
| `nameField` | `AutoNumber`, `displayFormat IF-{00000000}` | Step input. |
| `Status__c` | restricted, `required true`, New (default) / Retrying / Resent / Resolved / Abandoned | Step input (Q17). The Apex in M1-S03 must write these five strings exactly. |
| `Severity__c` (on `Integration_Failure__c`) | restricted, Error / Warning, **neither marked default** | Step input fixes the value list only; no answer names a default. `default` is required on every `CustomValue` and defaults to `true` when omitted (api_meta.txt:47513–47516), so both are written `false` rather than letting the platform pick. |
| `Resend__c` | `Checkbox`, `defaultValue false` | Step input. A Checkbox takes no `required` element; `defaultValue` is the only way to decide its unset state (`admin/custom-field-creation/references/metadata-examples.md` §4). |
| `Case__c` | `Lookup(Case)` with `deleteConstraint SetNull` | Step input's own rationale — `Case_Number__c` is denormalised "so the row stays readable after a Case delete", which is `SetNull` behaviour. `SetNull` is also the documented default; it is written explicitly because omitting it is itself a decision (`custom-field-creation` §5). |
| `publishBehavior` | `PublishAfterCommit` | Step input + decision **D10**. Omitting the element defaults to `PublishImmediately`, which fires even when the transaction rolls back (api_meta.txt L42228–42229). |
| `eventType` | `HighVolume` | Step input + assumption **A9**. `StandardVolume` is deprecated and returns an error on creation. |
| Apex/dashboard consumption of the event | Pub/Sub API subscriber, not a second callout | Decision **D9**; `standards/decision-trees/async-selection.md` Q11 — "Cross-system fan-out (subscriber is NOT Salesforce) → Yes → Platform Event + Pub/Sub API gRPC subscriber". |

## 5. UNVERIFIED and unbound — read before deploying

Five items the plan, the clarifications and the cited skills leave unstated. None is guessed here;
each is written the narrowest legal way and flagged.

1. **The trio's value.** `inputs.custom_object.optional_feature_trio` states the all-or-none rule
   but never says whether the three are `true` or absent. Both shapes clear every checker. `true`
   was written, following the worked parent object in
   `admin/object-creation-and-design/references/metadata-examples.md`, which is the only fenced
   example the cited skills carry. If the org does not want `Integration_Failure__c` classified as
   an Enterprise Application object, remove all three elements — not one of them.
2. **`externalSharingModel` is not declared.** It is a second, separate OWD governing external
   users (api_meta.txt L42132–42134) and defaults on in an org with Salesforce Experiences enabled.
   No clarification, decision or step input names it, and D12 reasons only about internal access, so
   nothing was written. **If the target org is an Experience Cloud org, decide this before deploy** —
   an omitted element leaves external access at whatever the org already had.
3. **`startingNumber` is not declared.** The platform default for a custom Auto Number field is 1.
   It "can't be retrieved… through Metadata API" (Gotcha 6, api_meta.txt L43623–43635), so a later
   retrieve/redeploy round trip will not carry it either. If this build ever seeds historical rows
   that must continue an external sequence, add the element deliberately at that deploy.
4. **Two labels were derived, not supplied.** `nameField/label` = "Integration Failure Number" and
   `Tier2_Escalation__e/pluralLabel` = "Tier 2 Escalations". Both elements appear in every cited
   fenced example, both are user-facing text only, and neither is bound by the plan. Rename freely.
   The `Case__c` lookup's `relationshipName` (`Integration_Failures`) and `relationshipLabel`
   ("Integration Failures") are derived the same way — `relationshipName` is **not** cosmetic: it is
   the subquery name (`SELECT Id, (SELECT Id FROM Integration_Failures__r) FROM Case`), so changing
   it after M1-S03 is written is a code change too.
5. **`visibleLines` on the three LongTextArea fields** (10 / 5 / 10) is a display choice copied from
   `templates/apex/custom_objects/fields/Message__c.field-meta.xml` and `Stack_Trace__c`. The element
   is required on the type; the numbers carry no requirement behind them.

## 6. A field-permission constraint M1-S02 has to absorb

`Status__c` is `required true`. "In API version 30.0 and later, permissions for required fields
can't be retrieved or deployed" (`admin/custom-field-creation/references/metadata-examples.md` §9,
api_meta.txt:95020–95021) — the platform grants access to required fields implicitly.
M1-S02's `inputs.permission_set.fieldPermissions` currently reads "Every custom field on
`Integration_Failure__c` from M1-S01 readable and editable". Taken literally that includes
`Status__c`, and a `fieldPermissions` entry for it **fails the deploy**. Eleven fields, not twelve.
This note records the constraint; it is M1-S02's to act on, and this step does not change it.

## 7. Validate-only command — for a human to run, never for an agent

This build never deploys. When a human wants an org-side check of this step, the loop's own
dry-run wrapper is the supported route (it hard-codes `checkOnly: true`):

```bash
python3 scripts/mock_deploy.py .sfskills/builds/tier2-webhook/plan.json \
  --org-alias <alias> --milestone M1
```

The raw equivalent, if the artefacts are assembled into a DX project by hand:

```bash
sf project deploy start --manifest package.xml --target-org <alias> --dry-run
```

Run the objects request before the M1-S02 permission-set request (§3).
