# Deploy order — M3-S03 (Email-to-Case routing addresses, Web-to-Case intake, Case settings)

Written by `agents/metadata-builder` on every run, per its AGENT.md Step 7. **Nothing in this build
deploys.** The command at the end is validate-only text for a human to copy.

**Note on declaration:** this file is *not* in `plan.json` `steps[M3-S03].outputs[]` (four paths are
declared: the settings file, the two markdown notes and `package.xml`). It is written anyway because
the human's deploy reads it. The same undeclared-`deploy-order.md` gap is recorded for `M3-S01` and
`M3-S02` in `decisions.md` **O-M3S02-03**, which also explains why `amend-step` cannot close it
retroactively. Recorded here so the omission is visible from inside the step, not only from the
observation log.

## 0. Rebuild 2026-09-12 — what changed, why, and the one consequence M4 must read

This step was built, then **failed the operator's validate-only run against the org**
(`sf project deploy start --dry-run`, `checkOnly: true`, alias `sfskills-dev`; run 5 of
`reports/MOCK-DEPLOY-M3.md`). The operator proved the fix on a scratchpad copy: with the four changes
below, and no others, the file validates with **0 errors**. Nothing was deployed — by the operator or
by this rebuild — and this agent ran no `sf` command of any kind.

| # | Change | File | Why |
|---|---|---|---|
| **F-25** | `<systemUserEmail>support-noreply@acme.example</systemUserEmail>` added immediately after `<useSystemUserAsDefaultCaseUser>` | `settings/Case.settings-meta.xml` | Org error: `CaseSettings: Enter the system user's email address`. `useSystemUserAsDefaultCaseUser` `true` with no `systemUserEmail` is not deployable. Guide: "Specifies the email address used when the default case user is the system user" (api_meta L111871) |
| **F-26** | `<newEntityRecordType>Case.Support</newEntityRecordType>` on `support@`, `<newEntityRecordType>Case.Billing</newEntityRecordType>` on `billing@`, each right after `<caseOrigin>` | `settings/Case.settings-meta.xml` | `case-management-setup` gotcha 9 instructs it; the as-built run omitted it because no cited skill shows the value shape. The org showed it: bare `Support` fails (`no RecordType named Support found`), object-qualified `Case.Support` resolves |
| **F-27** | `<casePriority>Medium</casePriority>` on both addresses, right before `<createTask>` | `settings/Case.settings-meta.xml` | Org error: `EmailToCaseRoutingAddress[support@acme.example]: Missing casePriority`. Required in practice, **not** in the guide — api_meta L112039 describes it only as "the default case priority for cases created through this routing address". **UNVERIFIED-in-guide / proven-live** |
| **API** | `<version>` `62.0` → `67.0` | `package.xml` | `newEntityRecordType` is rejected at 62.0 and 63.0 (`Property 'newEntityRecordType' not valid in version 63.0`) and accepted from **64.0**. `67.0` is the org's API version and the version M4's Apex steps already target |

Everything else in both files is **byte-identical** to the as-built version. Hashes (SHA-256):

| File | Before (as-built) | After (this rebuild) |
|---|---|---|
| `settings/Case.settings-meta.xml` | `5781669c97a3db69ab8ed88fe46bd523be04ddc1d6c8003ace5127acb29c63b8` | `f43aba801741a269a5f8a6428f375b5075ca8f83d547583606319a8bb503c8f4` |
| `package.xml` | `2d5f0839b251ac31bd4110699a72d1aa8ce9ba9c1ede1b4d65244c5cca82dd41` | `c38d2ef27988d4f878cab01fadf7aba4d37d8cced36e11c02340dd84c681837e` |
| `email-to-case-routing-addresses.md` | `465ac2f4d4145bebcfdbd21494ff7d266c135a2bcd66644039a2bf56e8c4fa39` | `fe6ca9a174f5460099aee32fa58e630204f8effb95a361b4d9716e86f8c1822f` |
| `deploy-order.md` (this file) | `fefe91928fd9be1c6c1374a3abede3749577eff12427d3ff3611bc2e19039666` | see `envelopes/M3-S03/2026-09-12T04-39-20Z.json` — a file cannot carry its own hash |
| `web-to-case-form-contract.md` | `d29fd1d7abd9d8621eca564738db7b676e773dd7a98b7289f8b5d5d48740954a` | `d29fd1d7abd9d8621eca564738db7b676e773dd7a98b7289f8b5d5d48740954a` (unchanged) |

### F-25 does not pre-empt the acknowledgement-sender decision (D-M3S02-04)

`systemUserEmail` is **not a routing address and not a From address.** The guide scopes it to the
email address of the *default case user* when that user is the system user (api_meta L111871) — an
ownership/attribution field. `EmailToCaseRoutingAddress` still carries no sender element at all, and
the customer-facing sender is still `AutoResponseRules` → `ruleEntry.senderEmail`, which is M3-S04's
element and **D-M3S02-04**'s decision at the M3 gate. The value written,
`support-noreply@acme.example`, is deliberately **not** either inbound routing address, so it cannot
be mistaken for the acknowledgement sender and cannot be an inbound-loop source. It is unprovisioned
in this build: confirm the mailbox exists, or replace the value, before any org deploy.

`useSystemEmailAddress` and `isPermsetControlled` are **still omitted, for exactly the reasons in
§ 4** — the sender-axis decision belongs to D-M3S02-04 at the M3 gate, and the `isPermsetControlled`
grant lives in a metadata type (`SetupEntityAccess` / `EmailRoutingAddress`) no step declares. F-25
changes neither.

### F-27's consequence for M4-S03 — read this before building the before-save flow

**Email-originated cases now arrive with `Priority` already set to `Medium`.** `M4-S03`'s before-save
flow is specified to stamp `Case.EntitlementId`, `Case.BusinessHoursId` and `Case.Priority` "each
guarded so it writes only into a null value". **That null guard will never fire for an
email-originated case.** Either the flow derives Priority from `Severity__c` / `Support_Tier__c` and
**overwrites** the intake default — the recommended reading of Q16, "priority must be set from what
the form or email tells us" — or the plan accepts `Medium` as the email channel's intake priority and
says so. Picking one is an M3-gate decision, not something M4-S03 should discover.

**Web-to-Case has no such setting.** `WebToCaseSettings` has no priority element (three children,
api_meta L112128 ff.), so web cases still arrive with `Priority` blank and the null guard still fires
for them. The two channels no longer behave alike, and `M3-S01`'s `Priority_Required_On_Agent_Save`
plus `Bypass_Case_Intake_Validation` is now load-bearing for the **web** channel only.

## 1. This step deploys one component

| Type | Member | File |
|---|---|---|
| `Settings` | `Case` | `settings/Case.settings-meta.xml` |

Named explicitly in `package.xml`, never with `*`: the wildcard "doesn't apply to metadata types for
feature settings. The wildcard applies only when retrieving all settings, not for an individual
setting" (api_meta, `CaseSettings` → Wildcard Support in the Manifest File; both cited skills say so
independently). The file stem is `Case.settings-meta.xml` and the member is `Case` — the same
stem-equals-name discipline `case-management-setup/references/metadata-examples.md` § 2.1 records for
the decomposed object files, and the reason run 5 of `reports/MOCK-DEPLOY-M1.md` failed.

## 2. What must already be in the org before this file lands

From `case-management-setup/references/metadata-examples.md` § 5 "Deploy order", rows 2, 4 and 5,
mapped onto this build's steps. Every reference below resolves **by name at deploy time**, so a
missing prerequisite is a deploy failure, not a runtime surprise.

| # | Must be deployed first | Built by | Which element in this file needs it |
|---|---|---|---|
| 1 | `StandardValueSet:CaseOrigin` — `Email-Support`, `Email-Billing`, `Web` | **M1-S01** | `webToCase.caseOrigin` = `Web`, and `routingAddresses[].caseOrigin` = `Email-Support` / `Email-Billing`. § 5 row 2: "`webToCase.caseOrigin` … reference values that must already exist" |
| 2 | `CustomObject:Case` record types + business processes | **M1-S01** | `closeCaseThroughStatusChange` `true` only means anything if a support process exposes a closed status — both do (`Support_Process` and `Billing_Process` each carry `Closed`) |
| 3 | Queue `Tier_1_General` | **M2-S04** | `defaultCaseOwner` = `Tier_1_General` with `defaultCaseOwnerType` = `Queue`. § 5 row 4: "`defaultCaseOwner` … resolve[s] by name at deploy time" |
| 4 | **This file** (`Settings:Case`) | M3-S03 | § 5 row 5: turning the channels on *after* their origin, owner and templates exist "means no case is ever created into a half-built org" |
| 5 | `AssignmentRules:Case`, then `AutoResponseRules:Case` | **M3-S04** | nothing in this file needs them — but until they exist, live traffic through these channels has no routing and no acknowledgement (gotcha #1: "auto-response never sends"). See § 3 |

Queue `Billing` (M2-S04) is **not** a prerequisite of this file: no element here names it. It becomes
a prerequisite of M3-S04's assignment rule, which is where per-channel ownership actually lives.

The four `case*NotificationTemplate` fields are **not written** (§ 4), so the Classic email templates
at `artefacts/M3-S02/email/case_intake/` are not a prerequisite of this file either — M3-S02 is a
declared `depends_on` because the *channel* design reads its acknowledgement template, not because
this manifest references it.

## 3. The ordering hazard this file creates, and the safe sequence

`case-management-setup/references/metadata-examples.md` § 5 states it: steps 5 and 6 "are reversible
in either order **only if the channel is left off until the rules land**. The failure mode of getting
it wrong is not a deploy error — it is live traffic into an org with no active assignment rule."

This file sets `enableEmailToCase` `true`, `enableOnDemandEmailToCase` `true` and `enableWebToCase`
`true`. Once it is deployed and the mail-server forwarding is live, cases are created. If M3-S04 is
not deployed yet they are created **unrouted** — they fall to `defaultCaseOwner` (`Tier_1_General`)
and no acknowledgement is sent, because an auto-response rule only fires when an assignment rule
fires.

**Safe sequence for the first deploy to any org that will receive real mail:**

1. `StandardValueSet:CaseOrigin` and `CustomObject:Case` (M1-S01), then the queues (M2-S04).
2. `AssignmentRules:Case` and `AutoResponseRules:Case` (M3-S04) — **before** this file, not after.
3. `Settings:Case` (this file).
4. Only then point the mail-server forwarding rules at the Salesforce-generated
   `emailServicesAddress` values, and only then publish the web form.

Step 4 is the real switch. Email-to-Case cannot receive anything until forwarding is live and the
address is verified, and Web-to-Case cannot receive anything until the form is published — both of
which are outside the deploy. That is the build's actual safety margin, and it is a human action, not
a metadata one. **And it is one-way: "After Email-to-Case is enabled, it can't be disabled."**

`enableEarlyEscalationRuleTriggers` is an org-level `CaseSettings` field this file deliberately does
not set — see § 4 — which means M4-S04's escalation design may require this step to be rebuilt.

## 4. Elements deliberately not written, and what each omission costs

A `CaseSettings` field this file omits **inherits whatever the target org already has** — the skill
says so explicitly of `enableSuggestedSolutions` ("a file that omits `enableSuggestedSolutions`
inherits whatever the org had"), and there is no reason to read the others differently. So every
omission below is a decision with a consequence, not a blank.

| Omitted | Why | What it costs |
|---|---|---|
| `defaultCaseUser` (with `useSystemUserAsDefaultCaseUser` `true`) | the guide requires `defaultCaseUser` only when that flag is `false`. This build creates no `User` metadata, so a username here would have to resolve by name against a user nobody provisioned. Its companion `systemUserEmail` **is** now written (F-25) — the org requires it for the `true` branch, and unlike `defaultCaseUser` it resolves nothing by name | Case History attributes automated changes to the system user rather than a named automation user — the readability the skill recommends. Revisit when an automation user exists |
| `caseAssignNotificationTemplate`, `caseCreateNotificationTemplate`, `caseCommentNotificationTemplate`, `caseCloseNotificationTemplate` | all four take `folderName/templateName` and resolve by name at deploy time. The only Classic templates this build carries are `case_intake/Case_Acknowledgement` (the auto-response template, M3-S04's) and `case_intake/Case_Escalated_To_Tier2` (M4-S04's). Neither is a case-assignment, -creation, -comment or -close notification, and naming a template that does not exist fails the deploy | the org's existing notification templates stand. If the org has none, those notifications send the platform default. No clarification asks for them |
| `useSystemEmailAddress` | it decides whether case comment / attachment / assignment notifications appear to come from a system address or from the user updating the case — the one sender-axis lever in this file. `decisions.md` **D-M3S02-04** holds the acknowledgement-sender question open as an M3 gate decision, and this step must not pre-empt it | the org's existing value stands. Settle it in the same gate decision, not in a routing step |
| `isPermsetControlled` (per address) | API 61.0+, deny-by-default, and the grant lives in a different metadata type (`SetupEntityAccess` / `EmailRoutingAddress`) that no step declares. gotcha 13 | both addresses stay available to every agent's composer. The requirement's "replies go from support@ / billing@ from Finance" send-as restriction is therefore **not enforced** by this build |
| `authorizedSenders` (per address) | gotcha 9: on a public support address the list "turns every unknown customer into an invalid sender"; the guide says leave it blank to accept mail from any address | `unauthorizedSenderAction` `Bounce` is a recorded intent that nothing currently triggers. Set deliberately so a later population of the list cannot inherit `Discard` |
| `enableThreadIDInBody`, `enableThreadIDInSubject` | the legacy-threading pair. Assumption **A3** says Lightning Threading; gotcha 8 says the two pairs are mutually exclusive and the wrong pair is inert | if A3 is wrong, threading falls back to `useEmailHeadersForThreading` (which **is** set) and replies may open new cases when a gateway strips the token. Rebuild this step if Setup shows legacy threading |
| `enableEarlyEscalationRuleTriggers` (and the separate `escalateCaseBefore` the skill mentions) | escalation is **M4-S04**'s design (Q43: `businessHoursSource` `Case` for the 8-business-hour entry, `None` for the Severity 1 24/7 entry). Setting an escalation switch in a routing step would pre-empt it | if M4-S04's design needs early triggers, **this step must be rebuilt** — the switch lives in this file and no other step owns `Settings:Case`. Flagged for the M4 planner |
| `enableCaseFeed`, `enableDraftEmails`, `preQuoteSignature`, `enableHtmlEmail`, `enableE2CSourceTracking`, `notifyContactOnCaseComment`, `notifyOwnerOnCaseComment`, `notifyOwnerOnCaseOwnerChange`, `showEmailAttachmentsInCaseAttachmentsRL` | agent-console and notification UX that no answered clarification decides. Every one is in the cited skills' element inventory, so any of them **could** be written; none has an answer to write from | the org's existing values stand. If the agent console is designed later (M5-S01 is list views and reports only), these belong in a rebuild of this step, because they live in this file |
| ~~`casePriority` on both routing addresses~~ — **now written (F-27), see § 0** | the as-built reasoning (leave it blank so M4-S03's null-guarded stamp fires) is sound design and was overruled by the org, which refuses the file without it | email cases arrive at `Medium`; M4-S03's null guard is dead on that channel. A `priority` input on the **web form** is still not written — it is form HTML, not metadata (`web-to-case-form-contract.md` § 4) |
| ~~`newEntityRecordType` on both routing addresses~~ — **now written (F-26), see § 0** | the value shape (`Case.Support`, not `Support`) and the API ≥ 64.0 floor came from the org, not from either cited skill | **email** cases land deterministically on `Support` / `Billing`. **Web** cases still land on the handling context's default record type — `WebToCaseSettings` has no record-type element. `email-to-case-routing-addresses.md` § 9.1 |
| `fallbackQueue`, `routingFlow` (per address, API 56.0+) | named once in `email-to-case-configuration/references/well-architected.md` line 39 with no description, example or other mention | possibly a better per-channel fallback than the shared org-level `defaultCaseOwner`. Unusable from the files at hand: `email-to-case-routing-addresses.md` § 9.2 |
| `defaultResponseTemplate` (third `webToCase` child) | the guide scopes it to Self-Service portal responses, not the acknowledgement, and the portal is unavailable to new orgs | nothing — the acknowledgement is M3-S04's `AutoResponseRules` entry. `web-to-case-form-contract.md` § 4 |

## 5. Ungrounded and open — read this before deploying

Five items. None of them is a guess written into a file; each is a place where the files stop short.

1. **Element order inside `CaseSettings` — SETTLED 2026-09-12, by the org.** The order written here
   follows the guide's own sample definition **as reproduced by the two cited skills** —
   `case-management-setup` § 3's sequence, with the `emailToCase` block inserted where
   `email-to-case-configuration` puts it (after the org-level owner fields, before
   `closeCaseThroughStatusChange`) and `webToCase` last; the three new elements sit where § 0 says.
   The operator's validate-only run accepted this file with 0 errors, so the Metadata API does not
   reject this sequence. Still not established: whether order is *enforced at all* (an accepted file
   proves the order is legal, not that a different one would be rejected), and no checker in this
   build tests it.
2. **`newEntityRecordType` — CLOSED 2026-09-12 (F-26).** Written on both addresses as
   `Case.Support` / `Case.Billing`, on a value shape and an API-version floor proven against the org
   rather than read from a skill. Neither cited skill carries either fact; that is still the clearest
   deepen-a-skill signal from this step. `email-to-case-routing-addresses.md` § 9.1.
3. **`casePriority` is now `Medium` on both addresses (F-27), and this build still cannot validate
   that value.** No `CasePriority` standard value set exists anywhere under `artefacts/`, and no
   answered clarification says which priority each channel should end up with — `Medium` is the
   skill's worked-example value, and the org accepting it at validate time proves the value exists in
   *that* org's picklist and nothing more. The guide does not mark the element required (api_meta
   L112039); the org does. **UNVERIFIED-in-guide / proven-live.** The M4-S03 consequence is in § 0.
4. **`notifyDefaultCaseOwner` `true` may be inert, or may email Tier 1 against Q88.**
   `Tier_1_General.queue-meta.xml` has no `<email>` and `doesSendEmailToMembers` `false`; whether the
   notification then reaches members, the queue address, or nobody is not in the guide — the same
   open question gotcha 11 records for `notifyOwnerOnNewCaseEmail`. Written `true` on gotcha 8's
   explicit "make the fallback loud". `email-to-case-routing-addresses.md` § 9.3; tick or overturn it
   at the M3 gate.
5. **`standards/decision-trees/integration-pattern-selection.md` has no Web-to-Case branch.** The
   step declares that tree; the tree routes the middleware path (Direction 2, Q5 `< 1k rows/day →
   REST API`; Q9 `plain CRUD → Standard REST on sObject`) and cannot route the native direct-post
   path at all. Recorded rather than invented: `web-to-case-form-contract.md` § 3.

Two further UNVERIFIED facts inherited verbatim from the cited skills, both about numbers this build
must not quote: the daily Email-to-Case limit is in neither the Metadata API guide nor the App Limits
Cheat Sheet, and the Web-to-Case daily allocation and pending-request cap appear only on
help.salesforce.com, which cannot be fetched. Read both from the target org's own limits page.

## 6. One cross-step dependency that is an org action, not a deploy

Both intake channels create Cases with `Priority` blank (§ 4) and rely on
`Bypass_Case_Intake_Validation` to get past `M3-S01`'s two validation rules.
`artefacts/M3-S01/validation-bypass-note.md` records that the Custom Permission travels in the
`Case_Intake_Integration` Permission Set (M2-S01) and that "assignment is an org action, outside this
build", held by "the Email-to-Case and Web-to-Case intake identities only (Q56)".

**Confirm before the first real submission in each org:** that the identity On-Demand Email-to-Case
and Web-to-Case actually save as can hold that Permission Set. If it cannot, every intake save fails
`Origin_Must_Be_Known` or `Priority_Required_On_Agent_Save` — a rejection the submitter never sees,
because the web form still returns its `retURL` success page (`web-to-case-form-contract.md` § 8).
This is a question about the org, not about any file in this build, which is why it is a checklist
line rather than a metadata change.

## 7. Validate-only command — text for a human, never run by an agent

```bash
# Retrieve what the target org actually has FIRST. routingAddresses is a full-replacement
# list: "Removing an address from this list deletes it from the target org", and
# emailServicesAddress / isVerified cannot be restored by re-adding the element (gotcha 7).
sf project retrieve start --metadata "Settings:Case" --target-org <alias>

# Check the authored tree before deploying anything.
python3 skills/admin/case-management-setup/scripts/check_case_management_setup.py \
    --manifest-dir artefacts --verbose

# Validate without committing the change.
sf project deploy start --manifest artefacts/M3-S03/package.xml --dry-run --target-org <alias>
```

**Deploy the whole build at API ≥ 64.0.** `newEntityRecordType` is rejected below it (`Property
'newEntityRecordType' not valid in version 63.0`), and this manifest is pinned at `67.0` — the org's
own API version, and the version M4's Apex steps already target per the plan notes. The operator
validated the full `M1 + M2 + M3-S01..S03` set at **67.0** with 0 errors, so 67.0 is proven for every
artefact built so far, not only for this one. A deploy that merges manifests must not drop below
64.0.

`--dry-run` sets `checkOnly: true` and saves nothing. Use `sf project deploy validate` only against
production, per `standards/build-orchestration.md` § 5. In this build the wrapper for the whole
milestone is `python3 scripts/mock_deploy.py .sfskills/builds/case-onboarding/plan.json --org-alias
<alias> --milestone M3`, which a human runs after M3 verifies and before the G3 decision — it is
where item 1 of § 5 gets settled.
