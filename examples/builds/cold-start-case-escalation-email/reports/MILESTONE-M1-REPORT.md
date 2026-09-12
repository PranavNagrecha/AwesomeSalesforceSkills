# Milestone Acceptance Report — M1: Email the Account Owner when a Case is escalated

Build: `case-escalation-email-alert` — plan version 1 — scale: `feature` — build mode: `design-only`

**Verdict: ready-with-findings**

## Blocked steps

None. M1-S01 reached `documented` cleanly.

## Milestone and steps

| Step | Type | Agent | Status | Artefacts |
| --- | --- | --- | --- | --- |
| M1-S01 | automation | metadata-builder | documented | `flows/Case_Escalation_Notify_Account_Owner.flow-meta.xml`, `package.xml`, `deploy-order.md` |

## Reference resolution

| Reference | Found in | Resolves against | Result |
| --- | --- | --- | --- |
| `Case.IsEscalated`, `Case.AccountId`, `Case.CaseNumber`, `Case.Subject`, `Case.Id` | Flow `<start>` filters, formulas, text template | Standard Case schema | Resolved (standard field, present in every org; not shipped by this build because it does not need to be) |
| `Account.Id`, `Account.OwnerId`, `Account.Name` | `Get_Account` recordLookups filters and queried fields | Standard Account schema | Resolved (standard field) |
| `User.Id`, `User.Email` | `Get_Owner_User` recordLookups filters and queried fields | Standard User schema | Resolved (standard field) |
| `Application_Log__c.Severity__c`, `.Source__c`, `.Message__c`, `.Request_Id__c` | `Log_Skip_No_Account` and `Create_Application_Log_Error` recordCreates `inputAssignments` | **Not defined by any step in this build** | **UNRESOLVED against this build's own artefacts** — flagged, not blocking. This object is a documented external dependency: `deploy-order.md`'s pre-deploy checklist names it explicitly and states this build assumes it already exists in the target org (the same object `templates/flow/FaultPath_Template.md` and the Apex `ApplicationLogger` template write to). If it does not exist, both `recordCreates` elements fail identically and fall through to the fault chain's own (identical) failure — a safe failure mode, not a silent one, but a real pre-deploy dependency the human must confirm. |

No unclassifiable references. This is the milestone's only finding of substance.

## Deployment order

One artefact (`Flow: Case_Escalation_Notify_Account_Owner`), no ordering dependency within this milestone — the correct position for a standalone `automation` step with no upstream `depends_on`. No contradiction.

## Merged manifest

`reports/MILESTONE-M1-package.xml` — one member (`Flow: Case_Escalation_Notify_Account_Owner`), identical to M1-S01's own `package.xml` since M1 has exactly one step. No member collisions, no file reaching no `<types>` block.

## Acceptance-test results

M1-S01's 3 declared tests all passed (see `tests/M1-S01/results.json`, `"passed": true`): `xml` (2/2 parse), `manifest` (consistent both directions), and the `check_record_triggered_flow_patterns.py` checker (exit 0, "No issues found."). No milestone-level automated checker was declared.

## Manual checklist

| From | What the human does | Tick counts as |
| --- | --- | --- |
| Milestone M1's own acceptance test | Deploy the Flow (see the validate-only command below, then an actual deploy — outside this loop), escalate a test Case linked to an Account owned by a real user, and confirm the owner receives an email with the Case Number and Subject within the same interaction. Un-escalate and re-escalate the same Case and confirm a second email arrives. Escalate a Case with no Account and confirm no email sends and a log entry records the skip. Escalate a Case whose Account is owned by a Queue with no email and confirm the Support Manager placeholder address receives the email instead. | Every one of the four observations holds |

No step-level manual tests were declared on M1-S01 (`tests/M1-S01/results.json.skipped_manual` is empty).

## Optional validate-only command (human decision; not run by this agent)

```bash
sf project deploy start --manifest .sfskills/builds/case-escalation-email-alert/reports/MILESTONE-M1-package.xml \
  --dry-run --target-org <alias>
```

(Sandbox form, since this is a first deploy of a net-new Flow with no production history to protect. Use `sf project deploy validate` with the same manifest for a production target, per Salesforce's own guidance for that command.)

## Requirements this milestone closes

`REQ-001` — "Email the Account Owner (with Case Number and Subject) whenever a Case on that Account is escalated" — per `traceability.md`, status `In UAT` (the one outstanding manual test above is what moves it to `Done`).

## Why `ready-with-findings` rather than `ready-for-gate`

Every automated check passed cleanly and no plan defect was found. The one finding — `Application_Log__c` is an external dependency this build does not ship — is real, already documented in `deploy-order.md`, and does not indicate anything wrong with M1-S01's own artefacts; it is a fact the human approving the gate should see stated plainly rather than buried in a pre-deploy checklist three files away. Approving this milestone accepts that dependency as a pre-deploy responsibility, not as a defect in the build.
