# Deploy order — M1-S05 (build-level `package.xml` and the compiled M1 deploy sequence)

Build `tier2-webhook` · step `M1-S05` · type `docs` · owner `metadata-builder`
(run under `build-step-runner`) · API version **67.0** (assumption A11) ·
`build_mode: design-only` — **nothing here has been deployed, and this agent deploys nothing.**

This is the one place the whole build is addressable as a unit. `agents/apex-builder`'s Output
Contract names no manifest, so the `ApexClass` and `ApexTrigger` members M1-S03 and M1-S04 emit
exist in no `package.xml` until this step aggregates them — `standards/build-orchestration.md`
§ 5 **The Apex exception**. This step re-declares no file: every member below is backed by a
file another step already wrote, and this step writes no metadata of its own.

---

## 1. What this step ships

| File | Role |
|---|---|
| `package.xml` | the build-level manifest — 7 `<types>` blocks, **33 members**, `<version>67.0</version>`, no wildcards |
| `deploy-order.md` (this file) | the build-wide deploy sequence and the manual steps no deploy performs |

Both are declared in the step's `outputs[]`. This step emits no `-meta.xml`.

### Member roll-up — what each step contributes

| Type | Members | From |
|---|---|---|
| `CustomObject` | 2 — `Integration_Failure__c`, `Tier2_Escalation__e` | M1-S01 |
| `CustomField` | 13 — `Case.Tier2_Notified_At__c` + the twelve `Integration_Failure__c` fields | M1-S01 |
| `ExternalCredential` | 1 — `OnCall_Tool_EC` | M1-S02 |
| `NamedCredential` | 1 — `OnCall_Tool` | M1-S02 |
| `ApexClass` | **13** — ten from M1-S03, four from M1-S04, `TestDataFactory` counted **once** | M1-S03 + M1-S04 |
| `ApexTrigger` | 2 — `CaseTrigger`, `IntegrationFailureTrigger` | M1-S03 |
| `PermissionSet` | 1 — `Tier2_Webhook_Admin` | M1-S02 |

**Fields are object-qualified.** `objectName.field` is the `fullName` form the guide states
directly for `CustomField` (`admin/change-management-and-deployment/references/metadata-examples.md`
§ 1, api_meta L2265–L2287). `Case.Tier2_Notified_At__c` is a custom field on a standard object and
rides in the `CustomField` block; **no `Case` `CustomObject` member is declared**, because M1-S01
deliberately ships no `Case.object-meta.xml` and a `CustomObject` member for `Case` would replace
the org's own Case definition wholesale (M1-S01 `deploy-order.md` § 2 item 2).

**The platform event is a `CustomObject` member.** `Tier2_Escalation__e` is declared under
`CustomObject`, matching the type its own file carries (`Tier2_Escalation__e.object-meta.xml`) and
matching M1-S01's own fragment. Its five payload fields are declared **inline in the object file**
and are **not** separate `CustomField` members (M1-S01 `deploy-order.md` § 2 item 3), so the
`CustomField` count is 13 and not 18.

**`TestDataFactory` appears once — the identity is verified, not assumed.** M1-S03 and M1-S04 each
ship a copy under the template-provenance rule (`agents/apex-builder/AGENT.md` Step 6), and the two
are **identical bytes**:

```text
2f87c8c320406e1c8381f26862cdcc17130a9fe2f8a133f098ab64a271de782c  M1-S03/classes/TestDataFactory.cls
2f87c8c320406e1c8381f26862cdcc17130a9fe2f8a133f098ab64a271de782c  M1-S04/classes/TestDataFactory.cls
2f87c8c320406e1c8381f26862cdcc17130a9fe2f8a133f098ab64a271de782c  templates/apex/tests/TestDataFactory.cls

a242f6e22b472afffbd726be71165de394e417355cdf1edd81b5601278ddea32  M1-S03/classes/TestDataFactory.cls-meta.xml
a242f6e22b472afffbd726be71165de394e417355cdf1edd81b5601278ddea32  M1-S04/classes/TestDataFactory.cls-meta.xml
```

Both are also byte-identical to the template they were copied from, so there is no question of
which copy the single member refers to. This is decision **D-M1S03-06**'s open item, discharged
here: "`M1-S05` emits the `ApexClass:TestDataFactory` member exactly once when it aggregates."
`D-M1S04-06` records the same fact from M1-S04's side. A `package.xml` listing it twice would be a
manifest defect; the deploy tree itself was never at risk, because
`scripts/mock_deploy.py:copy_artefacts` rebases both onto the same assembled path.

**No wildcards anywhere.** Every member is named. The manifest and the files agree in both
directions: 33 members, 33 components, no member without a file and no artefact file in
M1-S01…M1-S04 without a member. `deploy-order.md` files and the per-step `package.xml` fragments
are notes and fragments, not components, and are correctly absent.

---

## 2. Build-wide deploy order

The reconciled order, from `admin/change-management-and-deployment/references/llm-anti-patterns.md`
Anti-Pattern 4 ("Follow dependency-driven deployment order: 1. Custom objects and fields … 2. Apex
classes and triggers … 5. Permission sets and profiles (which reference all of the above)") and
from each step's own `deploy-order.md`:

| # | Components | Step | Why here |
|---|---|---|---|
| 1 | `CustomObject` ×2, `CustomField` ×13 | M1-S01 | the data model. Nothing else compiles or resolves without it. `Integration_Failure__c` must precede its own twelve fields inside this group |
| 2 | `ExternalCredential` `OnCall_Tool_EC`, then `NamedCredential` `OnCall_Tool` | M1-S02 | the Named Credential's Authentication parameter carries `<externalCredential>OnCall_Tool_EC</externalCredential>`; a reference to a credential that does not yet exist resolves to nothing (M1-S02 `deploy-order.md` § 2 item 1). Independent of group 1 |
| 3 | `ApexClass` ×13, `ApexTrigger` ×2 | M1-S03, M1-S04 | code that references the model. Every custom symbol these classes name was grounded against M1-S01's artefacts (M1-S03 `deploy-order.md` § 9). Within the group the Metadata API resolves classes and triggers in one request; no internal ordering is required |
| 4 | `PermissionSet` `Tier2_Webhook_Admin` | M1-S02 | last, because it references all of the above: twelve `fieldPermissions` rows naming M1-S01 fields, an `objectPermissions` row on `Integration_Failure__c`, and an `externalCredentialPrincipalAccesses` grant naming the principal of the credential in group 2 |

A **single** `sf project deploy start` over this manifest resolves all four groups in one request,
which is what `scripts/mock_deploy.py --mode manifest` runs. The sequence above is what that
request must not be split against, and what a split **must** follow if one is forced.

### Two ordering facts a reader of the per-step notes will otherwise trip on

1. **The plan's `inputs.deploy_order` for this step disagrees with this table, and this table is
   the one to follow.** The step input reads "ExternalCredential, NamedCredential, PermissionSet,
   then the object and field metadata, then the Apex" — it places the permission set **before** the
   fields it grants. Deployed in that order as separate requests, `Tier2_Webhook_Admin` fails:
   "permission sets referencing new fields fail if fields are not yet in the target"
   (Anti-Pattern 4), which is exactly what M1-S01 § 3 and M1-S02 § 3 both record. In a single
   combined request the difference is invisible, and the input's own sentence says the order is for
   the staged case ("deploying in stages gives a readable failure when a reference is wrong") — so
   the staged order it gives is the one that would not work. Recorded, not silently corrected:
   `amend-step` is the writer for a step-input fix and it is refused once a step has left `pending`,
   so this is a human's to amend or to accept as superseded by this note.
2. **The per-step notes say "do not deploy M1-S01 and M1-S02 in the same request"; this manifest
   deliberately does.** Both notes cite `admin/object-creation-and-design/references/gotchas.md`
   Gotcha 10, whose own remedy carries the carve-out this build sits in: "Keep `Profile` and
   `PermissionSet` out of the same manifest as objects and tabs **unless the access change is the
   point of the deployment**." The hazard Gotcha 10 describes is a *retrieve* rewriting profile and
   permission-set files with object entries nobody reviewed ("retrieving a component of this
   metadata type … makes the component appear in any Profile and PermissionSet components that are
   retrieved in the same package", api_meta L41920–41921). Nothing here was retrieved:
   `Tier2_Webhook_Admin` is hand-authored, is new in this build, is the access change this build
   exists to make, and is reviewed line by line at the M1 gate (M1-S02 `deploy-order.md` § 6). No
   `Profile` is in this manifest at all. The combined request is safe **as long as it stays a
   deploy of authored files** — if anyone ever retrieves this manifest back out of an org, re-read
   Gotcha 10 before deploying what comes back.

### What is *not* in this manifest and must already exist

| # | Prerequisite | Assumption | If it is missing |
|---|---|---|---|
| 1 | The queue `Tier_2_Engineering` | **A8** | `CaseTriggerHandler` finds no queue, escalation becomes silently impossible and the loss reaches `System.debug` only (M1-S03 `deploy-order.md` § 4) |
| 2 | The org-wide email address `support-noreply@acme.example`, **verified**, with the scheduling user's profile in its allowed-profiles list | **A4** | the hourly job logs the unmet prerequisite at `LoggingLevel.ERROR` and sends nothing; it never falls back to the running user as the From address (M1-S04 `deploy-order.md` § 3 row 4) |
| 3 | No pre-existing `after update` trigger named `CaseTrigger` on `Case` | none — unasked in all 45 clarifications | an org that already has one cannot deploy a second with the same name (M1-S03 `deploy-order.md` § 10 item 1). Check before the first deploy; `/consolidate-triggers` is the agent for the consolidation if there is one |
| 4 | The scheduling user can read `PermissionSetAssignment` | **UNBOUND** (M1-S04 `deploy-order.md` § 4 item 1) | `resolveRecipients()` returns empty and the alert silently degrades to the Severity `Warning` gap row |

---

## 3. The manual steps — what no deploy performs, and who owns each

The deploy of this manifest does **not** make the integration work. Five steps, in order, none of
which any agent in this loop performs. Owners are named from the build's own record, not assigned
here: every clarification naming a human owner for this integration's operational surface names
Support Engineering (Q19–Q21, decision **D-M1S02-05**).

| # | Step | Owner | When |
|---|---|---|---|
| 1 | **Confirm the `X-API-Key` `AuthHeader` `parameterValue` formula** `{!$Credential.OnCall_Tool_EC.ApiKey}` | Support Engineering lead (requester) | **before** the External Credential is deployed |
| 2 | **Enter the API key in Setup** against the `OnCall_Tool_EC` principal | Support Engineering | after deploy, before the first escalation; **repeats in every org** |
| 3 | **Assign `Tier2_Webhook_Admin`** to the D14 assignee set | Support Engineering lead (the assignee set is D14's, and § 6(e) of M1-S02's note requires a named person to accept it) | after deploy, before the first escalation **and** before the first scheduled run |
| 4 | **Register the hourly scheduled job** with `System.schedule`, aborting any prior job of the same name | the user who will own the schedule (assumption **A13**) — who must also hold `Tier2_Webhook_Admin` | after deploy; **repeats after every sandbox refresh** |
| 5 | **Confirm the org-wide sender** `support-noreply@acme.example` is verified and allows the scheduling user's profile | Support Engineering (assumption **A4**) | before the first scheduled run |

### Step 1 — confirm the AuthHeader formula (read the narrowing, not the original question)

The plan's own text for this step still reads "Confirm the `X-API-Key` `AuthHeader`
`parameterValue` formula against Salesforce Help before the External Credential is deployed —
assumption A5 records that merge-field grammar as UNVERIFIED in the cited skill, which says to
confirm it or build the header in Apex instead." **That framing predates two events and overstates
what is still open.** Decision **D-M1S02-06** records this as the `PV-007` "deploy-order prose lag"
the plan-approval gate flagged in advance, and this is the note that carries the corrected reading:

- **Closed.** The parameter name and the formula are supplied by the requester
  (`steps[M1-S02].amendments[1]`, `2026-09-12T10:23:06Z`): the principal's authentication parameter
  is `ApiKey`, entered in Setup, and the formula is `{!$Credential.OnCall_Tool_EC.ApiKey}`.
  Assumption **A5** is closed by a human answer, not a build-side guess.
- **Closed.** Whether the element is required at all — the org answered it in mock-deploy run 1:
  `The parameter type "AuthHeader" requires these fields: ParameterValue.`
- **Still open, and narrower than the plan's text.** (a) that the **grammar parses on deploy** —
  settled by the next `--mode manifest` dry run; (b) that the **header arrives at the on-call tool
  carrying the key at run time** — settled only at UAT. A formula that parses and resolves to an
  empty string deploys perfectly and 401s on every callout, so a clean deploy is not evidence of
  (b). The Metadata API guide still publishes no formula grammar for this field and the
  External-Credential-scoped `$Credential.<EC>.<Param>` form appears in no guide; the cited skill's
  UNVERIFIED marker (2026-09-05) stands (M1-S02 `deploy-order.md` § 5 item 1).

**The alternative the skill offers is still open too** — build the header in Apex instead. This
build deliberately did not: M1-S03's manual test (b) asserts that no class sets an `X-API-Key` or
`Authorization` header or reads a credential value. Choosing the Apex route now is a change to
M1-S03, not a tweak here.

**Open item, for a human:** `amend-step M1-S05` to narrow this manual test's wording to "the
grammar parses on deploy (mock-deploy manifest run) and the header's run-time behaviour is
confirmed at UAT". `amend-step` is refused once a step has left `pending` and this step is now past
that, so the amendment belongs to whoever re-plans; this note is the interim carrier of the
corrected reading.

### Step 2 — enter the API key in Setup

Setup → Named Credentials → External Credentials → `OnCall_Tool_EC` → Principals →
`OnCallToolNamedPrincipal` → Edit → add an authentication parameter **named exactly `ApiKey`**
holding the key.

**The name is load-bearing.** The `AuthHeader` formula resolves by that name, so a parameter named
anything else leaves the header empty and every callout returns 401 — landing an
`Integration_Failure__c` row per attempt. The value is never in metadata, never in an export, and
**does not survive a sandbox refresh**, so this step repeats in every org (M1-S02
`deploy-order.md` § 7 step 1; decision **D-M1S02-05**).

No file in this build carries a credential value. The `parameterValue` in the External Credential
is a merge-field **reference** to where the platform reads the secret at run time — `[REDACTED]`
is not needed anywhere in these artefacts because no secret is in them.

**Also confirm the endpoint per target org.** The `Url` parameter now carries the real endpoint
`https://api.oncall.example/v1/salesforce/escalations` rather than a placeholder, but per
assumption **A7** it remains the one parameter designed to differ per org — production and sandbox
share the host and differ only in the key (M1-S02 `deploy-order.md` § 7 step 0).

### Step 3 — assign the permission set

```bash
sf org assign permset --name Tier2_Webhook_Admin --target-org <alias>
```

The assignee set is decision **D14**: every user who can escalate a Case to `Tier_2_Engineering`,
**plus** the user who will run `System.schedule` for M1-S04 (assumption **A13**). This is wider
than the three Support Engineering admins Q19 names, and assumption **A2** is why — the escalation
Queueable runs as the async context user, not as Automated Process. **A2 is `risk: high` and
self-flagged UNVERIFIED**, and no `checkOnly` validation can close it: a dry run does not execute a
Queueable. Only a real run can. If A2 is wrong the failure is loud — every escalation returns 401
and lands in an `Integration_Failure__c` row.

A principal is inert until a permission set grants it **and** that set is assigned to the running
user. Deploying the set is not assigning it, and nothing in this manifest assigns anything.

### Step 4 — register the hourly scheduled job

The active job is **data, not metadata**: this `package.xml` deploys
`Tier2ChannelHealthSchedulable`, and nothing in it creates a `CronTrigger`. The full anonymous-Apex
script — abort any live job of the same name, pre-flight the 100-scheduled-class ceiling, confirm
the alert roster is non-empty, then `System.schedule` — is in M1-S04's `deploy-order.md` § 6 and is
not repeated here. Four facts from it that change the release procedure:

- Run it **as the user who should own the schedule**: scheduled Apex runs as the scheduling user
  (**A13**), and the CRON literal is read in that user's time zone and then frozen onto
  `CronTrigger.TimeZoneSidKey`.
- A duplicate job name throws
  `System.AsyncException: The Apex job named "jobName" is already scheduled for execution`, so the
  abort step is what makes a re-release re-runnable.
- **A sandbox refresh does not copy scheduled jobs** — this step repeats after every refresh.
- **An active schedule locks this class and every class it references** — `Tier2ChannelHealthQueueable`
  and, through the test, `TestDataFactory` — against deployment until the job is aborted. Since
  `TestDataFactory` is in this manifest and is shared with M1-S03, **the abort step belongs before
  the deploy in every later release that touches any of them**, not only in releases that touch the
  health check.

### Step 5 — confirm the org-wide sender

`support-noreply@acme.example` must already exist and be verified, with the scheduling user's
profile in its allowed-profiles list (**A4**). It is a deploy prerequisite, not a build artefact —
nothing in this manifest creates it. Unmet, the job logs at `LoggingLevel.ERROR` and sends nothing.

### One thing the deploy gives you that no manual step covers

`include_logger: false` means a **healthy** hourly run leaves no durable record at all — the only
durable sink this feature has is `Integration_Failure__c`, and a healthy run has no failure to
write there. Set a debug-log trace flag on the scheduling user for the first few runs (M1-S04
`deploy-order.md` § 6).

---

## 4. Read this before go-live — losses this build accepted, carried up from the step notes

Neither is a defect in this manifest; both are consequences a reader of the build-level note should
not have to find four files down.

1. **There is no kill switch.** Remedy B dropped `templates/apex/TriggerHandler.cls` and
   `TriggerControl`, and nothing in this build ships `Trigger_Setting__mdt`. A bulk data load that
   reassigns Case ownership **will escalate every affected Case** — there is no bypass — and turning
   the feature off is a deployment (`CaseTrigger` `-meta.xml` with `<status>Inactive</status>`), not
   a checkbox. The recursion guard is not a substitute: it stops re-entry inside one transaction and
   does nothing about a bulk load. Full accounting in M1-S03 `deploy-order.md` § 4.
2. **The plan has two Apex steps and no Apex-foundations step.** That is the structural reason
   `TestDataFactory` is shipped twice and had to be de-duplicated here, and it is the same step that
   would restore the kill switch. `standards/build-orchestration.md` § 4's Apex row note describes
   it. Both M1-S03 and M1-S04 recommend it at the M1 gate; this note carries the recommendation up
   rather than re-deciding it. It is a **re-plan**, not a file change.

---

## 5. UNVERIFIED and unbound in this step

1. **`<types>` block order carries no documented deployment semantics.** The blocks above are
   ordered to match § 2 so the manifest reads as the sequence it describes, but the cited skill
   documents ordering only through manifest *naming* (`destructiveChangesPre.xml` before,
   `destructiveChangesPost.xml` after — `metadata-examples.md` § 2). Nothing in the guide section
   this skill quotes makes `<types>` order load-bearing, and nothing here relies on it.
2. **No `destructiveChanges*.xml` exists, and none is needed.** This build adds only. The checker's
   companion-manifest rule therefore never fires. If a later release retires any of these
   components, it needs its own destructive manifest **plus** a `package.xml` beside it carrying the
   version even when it lists no components (`metadata-examples.md` § 2, api_meta L4630–L4637).
3. **No `testLevel` is expressed in this artefact, by design.** A manifest carries no test level —
   it is a `DeployOptions` field set on the deploy call. The relevant fact for the human running it:
   `RunLocalTests` is "the default for production deployments that include Apex classes or
   triggers", `NoTestRun` "applies only to deployments to development environments" and is the
   default there, and the level "is enforced regardless of the types of components that are present
   in the deployment package" (`metadata-examples.md` § 3). `scripts/mock_deploy.py` makes this
   choice itself; this note does not.

---

## 6. The manual acceptance test for the M1 gate

The step's `manual` test, tickable from `artefacts/M1-S05/` alongside the other four steps:

- **(a)** This note lists the five manual steps no deploy performs — § 3, with an owner and a
  timing for each: confirming the AuthHeader formula, entering the API key against the principal,
  assigning `Tier2_Webhook_Admin` to the D14 assignee set, scheduling the hourly job, and confirming
  the org-wide sender is verified. ✅ as written.
- **(b)** The `mock_deploy.py` command is written as **text for a human to run** (§ 7), and no agent
  in this loop executes it. ✅ as written — this step ran no `sf` command and no `mock_deploy.py`.
- **(c)** Added for this run: read § 3 step 1 and accept the **narrowed** AuthHeader question
  (grammar-parses-on-deploy + UAT), rather than the pre-amendment framing the plan's own test text
  still carries. That prose lag is `PV-007` / **D-M1S02-06**; a human amends it or accepts this note
  as the carrier.

---

## 7. Validate-only command — for a human to run, never for an agent

This build never deploys. **Manifest mode is the only check that reads this merged `package.xml`**,
which makes it the run this step exists for:

```bash
python3 scripts/mock_deploy.py .sfskills/builds/tier2-webhook/plan.json \
  --org-alias <alias> --milestone M1 --mode manifest
```

It hard-codes `checkOnly: true` and has no deploy option. Run it after the milestone verifies and
before the G3 decision; its `summary.md` under `reports/mock-deploy/<ts>/` is the evidence the gate
rests on.

The raw equivalent, if the artefacts are assembled into a DX project by hand:

```bash
sf project deploy start --manifest package.xml --target-org <alias> --dry-run
```

**A clean manifest-mode run is not the end of the checks.** It proves the 33 components compile and
resolve together. It does not prove the AuthHeader formula resolves to a non-empty header (§ 3 step
1), does not execute a Queueable and so cannot close assumption **A2** (§ 3 step 3), and does not
create the scheduled job (§ 3 step 4).
