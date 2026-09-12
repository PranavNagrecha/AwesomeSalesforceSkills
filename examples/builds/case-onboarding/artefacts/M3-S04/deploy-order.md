# Deploy order — M3-S04 (Case assignment rules and auto-response rules)

Written by `agents/metadata-builder` on every run, per its AGENT.md Step 7. **Nothing in this build
deploys.** The command at the end is validate-only text for a human to copy; this agent ran no `sf`
command of any kind.

**Note on declaration:** this file is *not* in `plan.json` `steps[M3-S04].outputs[]` — four paths are
declared (the two rule files, `owner-writer-map.md` and `package.xml`). It is written anyway because
the human's deploy reads it. This is the same undeclared-`deploy-order.md` pattern `decisions.md`
**O-M3S02-03** records for `M3-S01`, `M3-S02` and `M3-S03`, and it is reported again in this run's
envelope as an undeclared artefact rather than left for a reader to notice.

## 0. The operator decision this step was built under (binding)

`plan.json` `steps[M3-S04].notes`, amended `2026-09-12T05:12:42Z` by the dry-run operator (Fable),
resolving `decisions.md` **D-M3S02-04** *for this step only*:

> `AutoResponseRules` `ruleEntry.senderEmail` = **`support-noreply@acme.example`** — a verified
> org-wide address that is **not** an Email-to-Case routing address.

`support@acme.example` and `billing@acme.example` are this org's two routing addresses
(`artefacts/M3-S03/settings/Case.settings-meta.xml`, `emailToCase/routingAddresses/emailAddress`), and
**neither appears in any `senderEmail` or `replyToEmail` in this step.** The prohibition is documented
twice and independently: `skills/admin/assignment-rules/references/gotchas.md` #6
("Auto-Response `senderEmail` Equal to the Email-to-Case Routing Address Creates a Mail Loop") and
`skills/admin/email-to-case-configuration/references/gotchas.md` #3. The written value also matches
`M3-S03`'s `systemUserEmail` (`decisions.md` **D-M3S03-01**), so the build names one unprovisioned
no-reply mailbox rather than two.

**D-M3S02-04 is not closed by this file.** The M3 gate may still affirm Q22's reading — `support@`
itself sends the acknowledgement, loop risk accepted under the Q68 sandbox loop test. If it does,
**one element changes**: `autoResponseRules/Case.autoResponseRules-meta.xml` → `ruleEntry/senderEmail`
(and, if the gate says so, `replyToEmail` with it). Nothing else in this step depends on the answer.

**Consequence a human must accept with this value:** `support-noreply@acme.example` is unprovisioned
by this build and is set as `replyToEmail` as well as `senderEmail`, following the worked example in
`skills/admin/assignment-rules/references/metadata-examples.md` § "Case auto-response rule". A
customer who hits *Reply* on the acknowledgement therefore writes to a mailbox that does not feed
Email-to-Case, and that reply does **not** thread onto the case. Customers who reply to the *original*
thread (Email-to-Case, thread token in subject and body — `M3-S03`) are unaffected. Routing the
acknowledgement's replies back into the case is exactly the trade-off D-M3S02-04 holds open, so this
file states the cost rather than resolving it.

## 1. What this step deploys

| Type | Member | File |
|---|---|---|
| `AssignmentRules` | `Case` | `assignmentRules/Case.assignmentRules-meta.xml` |
| `AutoResponseRules` | `Case` | `autoResponseRules/Case.autoResponseRules-meta.xml` |

Each type takes its own `<name>` block. Members are named explicitly rather than with `*`, although
`skills/admin/assignment-rules/references/metadata-examples.md` § "Where the files live" records that
all three rule types *do* accept the wildcard — an explicit member keeps the manifest checkable in
both directions (every member backed by a file, every file covered by a member), which is what the
step's `manifest` acceptance test asserts.

One file holds **every** rule of that type for the object. `AssignmentRules:Case` retrieves and
deploys all Case assignment rules; the singular `AssignmentRule:Case.Case_Intake_Routing` addresses
one. This build writes one rule per file, so the two forms would carry the same content today.

**`<version>` is `67.0`, not `62.0`.** `M3-S03` moved to 67.0 because `newEntityRecordType` is
rejected below 64.0 (`reports/MOCK-DEPLOY-M3.md` Run 4, probes a–c), and 67.0 is the org's own API
version and the version M4's Apex steps already target. This step follows it rather than reintroducing
the earlier floor. `decisions.md` **O-M3S03-01** records that the build now carries two `package.xml`
versions with no plan-level `api_version` field, and that the remedy is a `build-planner` backlog item
— not something this step fixes.

## 2. What must already be in the org before these two files land

Every reference below resolves **by name at deploy time**, so a missing prerequisite is a deploy
failure, not a runtime surprise (`skills/admin/queues-and-public-groups/references/metadata-examples.md`:
"Queues are the routing targets every assignment rule, escalation action, and Omni-Channel routing
configuration names by developer name, so they deploy **first**").

| # | Must be deployed first | Built by | Which element needs it |
|---|---|---|---|
| 1 | `StandardValueSet:CaseOrigin` carrying `Email-Support`, `Email-Billing`, `Web` | **M1-S01** | every `criteriaItems/value` in both files. A value not in the set matches nothing — it does not fail the deploy, which is why this row is first |
| 2 | Public groups `Support_Tier_1`, `Billing_Team` | **M2-S04** | queue membership; the queues below will not deploy without them |
| 3 | Queue `Tier_1_General` (developer name = file stem) | **M2-S04** | `assignedTo` on entries 2 and 3 |
| 4 | Queue `Billing` | **M2-S04** | `assignedTo` on entry 1. `M3-S03`'s `deploy-order.md` § 2 predicted this: "Queue `Billing` … becomes a prerequisite of M3-S04's assignment rule, which is where per-channel ownership actually lives" |
| 5 | `EmailFolder:case_intake` **and** `EmailTemplate:case_intake/Case_Acknowledgement` | **M3-S02** | `ruleEntry/template` in the auto-response file. The folder-qualified form is the deployed member name in `artefacts/M3-S02/package.xml` — **not** the `unfiled$public/` prefix the skill's worked examples carry (`workbook/99-other-configuration.md` `CWB-OTHER-020` flags that same stale prefix) |
| 6 | A verified `OrgWideEmailAddress` for `support-noreply@acme.example` | **nobody — unprovisioned** | `senderEmail` / `replyToEmail`. No step in this build creates one; `OrgWideEmailAddress` is not among any step's declared outputs. Confirm the address exists and is verified in the target org, or the acknowledgement does not send |

`Queue:Tier_2_Engineering` is **not** a prerequisite of this step: no element here names it. It becomes
a prerequisite of `M4-S04`'s escalation rule.

## 3. Order against `M3-S03` — these rules go in BEFORE the channel settings

This is the ordering hazard `M3-S03`'s own `deploy-order.md` § 3 raised, from
`skills/admin/case-management-setup/references/metadata-examples.md` § 5: steps 5 and 6 "are reversible
in either order **only if the channel is left off until the rules land**. The failure mode of getting
it wrong is not a deploy error — it is live traffic into an org with no active assignment rule."

`M3-S03` sets `enableEmailToCase`, `enableOnDemandEmailToCase` and `enableWebToCase` to `true`. Once
that file is deployed and mail forwarding is live, cases are created. If **this** step is not in the
org yet they are created unrouted: they fall to `defaultCaseOwner` (`Tier_1_General`) and **no
acknowledgement is sent**, because an auto-response rule only fires when an assignment rule fires.

**Safe sequence for the first deploy to any org that will receive real mail:**

1. `M1-S01` (`StandardValueSet:CaseOrigin`, Case record types and business processes).
2. `M2-S04` (three `Group`s, then the three `Queue`s).
3. `M3-S02` (`EmailFolder:case_intake`, then the two templates).
4. **This step** — `AssignmentRules:Case`, then `AutoResponseRules:Case`.
5. `M3-S03` (`Settings:Case`) — the channels go on **last**.

## 4. Order inside this step

| Position | Component | Why here |
|---|---|---|
| 1 | `AssignmentRules:Case` | The auto-response rule is inert without an active assignment rule (`admin/case-management-setup` gotcha #1, and the declared checker's `CMS` assignment-rule rule: "Auto-response rules depend on the assignment rule firing"). Deploying it first means the window in which the acknowledgement silently does not send is zero |
| 2 | `AutoResponseRules:Case` | Needs the template from `M3-S02` (§ 2 row 5) and, functionally, position 1 |

Entry order **inside** `Case_Intake_Routing` is load-bearing and is not alphabetical or accidental.
First match wins and evaluation stops (`skills/admin/assignment-rules/SKILL.md` § "Active Rule Limit
and Rule Entry Order"): `Email-Billing` → `Billing` must precede the catch-all, or every finance case
lands in Tier 1.

## 5. Two things a deploy of this file does that are easy to miss

1. **It deactivates whatever Case assignment rule is active in the target org**, silently — no warning
   and no confirmation (`admin/assignment-rules` gotcha #2). Record the currently-active rule's name
   before deploying and confirm it reads *Inactive* afterwards. Acme has no Service Cloud rule today,
   so the effect is nil in this build and not in an org that has been used before.
2. **`AutoResponseRules` ships `<active>true</active>`, so the acknowledgement sends the moment the
   channels are on.** Unlike `M4-S04`'s escalation rule, which ships inactive for a comparison window
   (Q47), nothing here is staged: Q16 requires the acknowledgement inside the first minute. The
   control is the Q68 sandbox loop test, run before go-live, not an inactive flag.

## 6. Elements this step could NOT ground, and did not write

Recorded per `agents/metadata-builder` AGENT.md Step 5 rule 1 — an element or value the cited skills'
inventory does not carry is a recorded gap, never a plausible guess. F-26 in this build is the precedent:
a guessed value *shape* (`Support` for `Case.Support`) deployed nowhere and cost a rebuild.

| # | Not written | Why | Who should settle it |
|---|---|---|---|
| 1 | **A rule entry keyed on the Account support tier** | Two separate blockers, either sufficient. **(a) No target.** Q25 names `Account.Support_Tier__c` as a field that is *available* at save; no answer, the requirement, or `answers-key.md` says which queue a `Premier` case should go to instead of the Origin-derived one. The requirement gives Premier a faster **SLA** (4 business hours — `M4-S02`), not a different owner. **(b) No grounded notation.** No file in either cited skill — nor anywhere under `skills/` — shows a `criteriaItems/field` on a *related* object inside a Case rule. Every documented value is base-object (`Case.Origin`, `Case.Priority`, `Lead.Country`; `Account.Customer_Tier__c` appears only in `admin/outbound-message-setup`, on an **Account** workflow rule, so it grounds nothing cross-object). Writing `Account.Support_Tier__c` or `Case.Account.Support_Tier__c` here would be a guessed value shape | **The M3 gate.** The step's title and one manual test both say "and the Account support tier", so the plan expects an entry this build cannot justify. Either an answer names the tier→queue mapping and a live org confirms the cross-object notation, or the step's title and that manual test are corrected to Origin-only |
| 2 | `<template>` on any assignment `ruleEntry` (the assignment notification to the assignee/queue) | No answer asks for one, and `M3-S02` built no assignment-notification template — only `Case_Acknowledgement` (this step's auto-response) and `Case_Escalated_To_Tier2` (`M4-S04`'s). Worth noting for whoever adds one: the `Billing` queue's `<email>` is `billing@acme.example`, **a live Email-to-Case routing address**, so an assignment notification to that queue would post mail into the intake mailbox. Q88 accepted that queue email deliberately; the interaction with a notification template did not come up | CRM admin lead, if queue notification is ever wanted |
| 3 | `team`, `overrideExistingTeams`, `notifyCcRecipients` on the Case rule entries | Documented in the cited skill, but no answer in this build asks for a case team or for the inbound Cc line to be copied onto the acknowledgement. Omitted rather than defaulted | Process owner |
| 4 | `senderType` on the auto-response entry | The declared checker reads it (`senderType` **or** `senderEmail`), but no cited skill documents its element values. `senderEmail` alone satisfies the check and is what the skill's worked example writes | — (no action needed; recorded so its absence is not read as an oversight) |

## 7. Validate-only command for a human

Text to copy. **This agent did not run it**, and this build deploys nothing.

```bash
# Queues and the email template folder must already be in the org (§ 2).
python3 skills/admin/assignment-rules/scripts/check_assignment_rules.py --manifest-dir artefacts/M3-S04
sf project deploy validate --source-dir artefacts/M3-S04 --target-org <your-sandbox>
```

`check_assignment_rules.py` is **not** a declared acceptance test on this step and exits **1** on this
artefact by design — `target 'Tier_1_General' appears in multiple rule entries` is a true reading of
Q18 plus Q26 (support@ routes to Tier 1; every unmatched case falls through to the same queue), and
the checker has no way to be told the duplication is deliberate. Read its output, do not "fix" the
rule to satisfy it. Its `AR-LOOP-01` rule is the one worth running at the **build** scope, where the
routing-address inventory is visible:

```bash
python3 skills/admin/assignment-rules/scripts/check_assignment_rules.py --manifest-dir artefacts
```
