# Mock deploy — milestone M3 in progress (validation only, nothing deployed)

## Run 1 — 2026-09-12, source mode, M1 + M2 + M3-S01 + M3-S02 as built

`python3 scripts/mock_deploy.py plan.json --org-alias sfskills-dev --step M1-S01 --step M1-S02 --step M2-S01 --step M2-S02 --step M2-S03 --step M2-S04 --step M2-S05 --step M3-S01 --step M3-S02`

**Tool failure, not a build failure — `status: Unknown`, 0 components.** `result.json` carried
`ExpectedSourceFilesError: …/email/case_intake/Case_Acknowledgement.email-meta.xml: Expected source files for type
'EmailTemplate'`. Only the `.email-meta.xml` files reached the assembled tree; the `.email` bodies beside them did not.

**F-24 (HIGH, tooling, closed).** `scripts/mock_deploy.py` copied `*.xml` only, so every source-format type with a
non-XML body (EmailTemplate `.email`, ApexClass `.cls`, ApexTrigger `.trigger`, LWC `.js/.html/.css`, StaticResource
`.resource`, Aura) would have failed the same way from M3 onward. Fixed in 85f701ed5: the tool now copies every file
under `artefacts/<step>/` preserving paths, excluding only `package.xml` (merged), `*.md` (build notes) and dotfiles;
`summary.md` reports copied/skipped counts; four regression tests added (40 pass). The M3-S02 artefacts were not touched.

## Run 2 — 2026-09-12, source mode, same nine steps after the tool fix

**Succeeded — 37 components, 0 errors, `checkOnly: true`.** 38 files copied, 23 skipped (package.xml/notes). The M3-S01
validation rules (`Case.Origin_Must_Be_Known`, `Case.Priority_Required_On_Agent_Save`) and the M3-S02 email folder and
two templates (`case_intake/Case_Acknowledgement`, `case_intake/Case_Escalated_To_Tier2`) validate alongside every M1
and M2 artefact, unmodified. Output: `reports/mock-deploy/2026-09-12T04-14-39Z/`.

## Run 3 — 2026-09-12, source mode, M1 + M2 + M3-S01..M3-S03 as built (API 62.0)

`python3 scripts/mock_deploy.py plan.json --org-alias sfskills-dev --step M1-S01 … --step M3-S03`

**Failed — 38 components, 38 ok, 1 error.** `CaseSettings Case: Enter the system user's email address.`

**F-25 (HIGH, build + skill).** `settings/Case.settings-meta.xml` sets `useSystemUserAsDefaultCaseUser` `true` with no
`systemUserEmail`. The guide documents the field (api_meta L111871, "the email address used when the default case user
is the system user") but only states the requirement in the other direction (`false` → `defaultCaseUser`, L111880), and
`admin/case-management-setup`'s checker enforces only that direction. Remedy: checker rule + gotcha + example in the
skill; rebuild adds `systemUserEmail` = `support-noreply@acme.example` (not a routing address, so D-M3S02-04 is not
pre-empted). Step reset `built → failed → pending` with the run recorded on `runs[]` (agent `mock-deploy`).

## Run 4 — 2026-09-12, operator probes on a scratchpad copy of the build (nothing in the build changed)

Purpose: settle the runner's ungrounded item 2 — `EmailToCaseRoutingAddress.newEntityRecordType` value format — and
find the API-version gate, before asking for a rebuild. Copy = build dir minus `reports/`, `envelopes/`, `skills`.

| Probe | package.xml version | Injected | Result |
|---|---|---|---|
| a | 62.0 | `newEntityRecordType` = `Support` / `Billing` | `Property 'newEntityRecordType' not valid in version 62.0` |
| b | 63.0 | same + `systemUserEmail` | `Property 'newEntityRecordType' not valid in version 63.0` |
| c | 64.0, 65.0, 66.0 | same | `In field: newEntityRecordType - no RecordType named Support found` |
| d | 64.0 and 67.0 | `Case.Support` / `Case.Billing` + `systemUserEmail` | `EmailToCaseRoutingAddress[support@acme.example]: Missing casePriority` |
| e | 67.0 | d + `casePriority` `Medium` on both addresses | **Succeeded — 38 components, 0 errors** |

**F-26 (HIGH, build + skill).** `newEntityRecordType` is version-gated: rejected at 62.0/63.0, accepted from 64.0 — the
v62 guide (api_meta L112078) carries no version note (UNVERIFIED in guide, proven live). The value must be
object-qualified (`Case.Support`); the bare developer name never resolves. `admin/case-management-setup` gotcha 9
instructs writing the element but states neither fact; `admin/email-to-case-configuration` owns the element.
Remedy: gotchas + example + checker rules (bare form → ERROR; manifest version < 64.0 → ERROR); rebuild stamps both
addresses and pins `package.xml` at 67.0 (the org's version, which the M4 Apex steps already target).

**F-27 (HIGH, build + skill).** The org requires `casePriority` on every routing address; the guide only says
"Specifies the default case priority" (api_meta L112039) with no Required marker (UNVERIFIED in guide, proven live).
The runner omitted it deliberately so M4-S03's null-guarded flow could stamp priority. Remedy: checker rule + gotcha
in `admin/email-to-case-configuration`; rebuild sets `Medium` on both addresses and records for the M4-S03 builder
that email cases now arrive with Priority set, so the flow must derive priority from `Severity__c` /
`Support_Tier__c` and overwrite the default rather than fill a null.

**Tooling (closed alongside).** `scripts/mock_deploy.py` pinned the source API version to the FIRST selected step's
`package.xml` (62.0 from M1-S01), so a later step could never raise it; changed to the highest version across the
selected steps, with `--api-version` override and the choice printed in `summary.md`.

## Run 5 — 2026-09-12, source mode, M1 + M2 + M3-S01..M3-S03 after the F-25/F-26/F-27 rebuild

`python3 scripts/mock_deploy.py plan.json --org-alias sfskills-dev --step M1-S01 … --step M3-S03`

**Succeeded — 38 components, 0 errors, `checkOnly: true`**, deployed at API 67.0 (highest across the selected steps;
M3-S03 alone declares it, the nine earlier steps still say 62.0). 39 files copied, 27 skipped. The rebuilt
`settings/Case.settings-meta.xml` (four changes, hashes in the step's `deploy-order.md` § 0) validates alongside every
M1, M2, M3-S01 and M3-S02 artefact unmodified. F-25, F-26 and F-27 closed in the build; the skill-side rules are in
`admin/case-management-setup` and `admin/email-to-case-configuration` (see the commit that follows this run).
Output: `reports/mock-deploy/2026-09-12T04-49-27Z/`.

## Run 6 — 2026-09-12, source mode, M1 + M2 + M3-S01..M3-S04 as built (API 67.0)

`python3 scripts/mock_deploy.py plan.json --org-alias sfskills-dev --step M1-S01 … --step M3-S04`

**Failed — 42 components, 42 ok, 1 error.** `AutoResponseRule Case.Case_Acknowledgement: support-noreply@acme.example
is an invalid From email address.: Email Address`. The assignment rule (`Case_Intake_Routing`, three entries) validated.

**F-28 (MEDIUM, org prerequisite + skill).** The org validates an auto-response rule's `senderEmail` against its
verified `OrgWideEmailAddress` records at deploy time, not only at send time. `sfskills-dev` has none
(`SELECT Address FROM OrgWideEmailAddress` → 0 rows), there is no metadata type for them
(`admin/email-templates-and-alerts` § "Org-wide email address (the sender)" already says Setup-only + verified), so a
design-only build cannot make this rule validate here. Not a metadata defect: the value is the one the operator
decided ahead of the M3 gate (M3-S04 `notes`, D-M3S02-04) and M3-S04's `deploy-order.md` already flags that the
address is "named by two steps and provisioned by neither". Remedy: (1) `admin/assignment-rules` gains a gotcha and
an advisory checker line that `senderEmail` / `replyToEmail` are deploy-time prerequisites — provision and verify the
org-wide address BEFORE deploying the rule, or the deploy fails; (2) the M3 milestone report lists the address as a
G3 prerequisite; (3) no rebuild. Until a human provisions the address in the dev org, M3 validation is run without
M3-S04's auto-response rule (the assignment rule alone validates — run 6's per-component table).

Still to validate for M3: M3-S04 auto-response rule once the org-wide address exists; M3-S05 (blocked on Q32–Q35).
