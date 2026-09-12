# Escalation activation runbook — `Case_SLA_Escalation`

Declared output of `M4-S04`. Written by `agents/metadata-builder`. **Nothing in this build
deploys**; every command below is text for a human to run.

This file answers **Q47** ("How do we cut over without a wave of instant escalations?") —
*"Deploy the rule inactive, then activate inside a defined comparison window once the sandbox
proof is signed off."* The rule ships `<active>false</active>`, so the checker's `W1` finding
(*"no rule in this file is active"*) is the intended state of this deploy.

Procedure adapted from `skills/admin/escalation-rules/references/metadata-examples.md`
§ "Parallel run and cutover" and `SKILL.md` § "Pattern: Deploy Inactive, Then Cut Over".

---

## 0. Owner and window — OPEN

| Property | Value |
|---|---|
| Named activator | **OPEN** — no clarification in this build names an individual. Q44 names the *release manager* role; Q91 names the *Tier 2 lead* as the monitoring owner |
| Comparison window | **OPEN** — Q47 requires "a defined comparison window"; no answer fixes its length or its start |
| Sandbox proof signed off by | **OPEN** — `requirement.md` L20 requires proof in a sandbox before customers see it; no signatory is on file |

Both cells are left open deliberately rather than filled with a plausible name, on the same
grounds `decisions.md` **D-M4S01-02** records for the holiday-calendar owner. The M4 gate is
where they get answered.

---

## 1. Prerequisites that must be true in the target org before this rule deploys

Every queue, calendar and template this rule names must already exist, or the deploy fails on the
reference rather than on the rule
(`references/metadata-examples.md`, "Every queue, user, calendar, and template named here must
already exist in the target org").

| # | Prerequisite | Built by | Status |
|---|---|---|---|
| 1 | Queue `Tier_2_Engineering` exists | `M2-S04` | Built, `documented` |
| 2 | Classic email template `case_intake/Case_Escalated_To_Tier2` exists, in the `case_intake` folder | `M3-S02` | Built, `documented`. `uiType` `Aloha`, `type` `text`, `style` `none` — Classic, as both `assignedToTemplate` and `notifyToTemplate` require. **Named by both elements** — see `deploy-order.md` § 3 U6 |
| 3 | `Case.Severity__c` exists with the picklist value `Severity 1` | `M1-S01` | Built, `documented` |
| 4 | Business-hours calendars exist | `M4-S01` | Built. **Entry 2 only** — entry 1 is `businessHoursSource` `None` and reads no calendar |
| 5 | **`Case.BusinessHoursId` is populated at creation** | `M4-S03` | **NOT BUILT — see § 4 risk R1** |

---

## 2. Cutover steps

| Step | Action | What it proves |
|---|---|---|
| 1 | Deploy this file with `<active>false</active>` (as built) | The XML deploys; the queue, the template and the Severity picklist value all resolve in the target org |
| 2 | Confirm **Setup > Escalation Rules** shows no rule newly Active, and record the name of whatever rule *is* active. Q44's answer is "none — support runs from a shared mailbox today"; confirm it rather than assume it | Activation will not silently deactivate an incumbent (`gotchas.md` #2) |
| 3 | Run the clock test in `admin/business-hours-and-holidays` `references/examples.md` Example 4 against one case per entry: one with `Severity__c = Severity 1`, one without | Entry 1 fires on the wall clock; entry 2 pauses outside the Case's calendar |
| 4 | Take the escalated-case baseline (§ 3 query) immediately before switching | A wave after activation is distinguishable from normal volume |
| 5 | Deploy **only** the `<active>` flip, in a staffed window inside the agreed comparison window | The blast radius of the change is one field |
| 6 | Re-run the baseline query hourly for the first full SLA period (8 business hours) | Fired-vs-expected is confirmed, and a reactivation wave is caught early |

**Cases already older than 480 minutes at step 5 escalate on the engine's first pass after
activation.** That is expected behaviour, not a defect; step 4 exists so it can be said out loud
with a number attached.

The engine batches — it does not fire on the minute. Q46 asked for headroom to be agreed for that
latency; no number is on file, and `gotchas.md` #1 records that the commonly quoted "about every
hour" cadence is **UNVERIFIED** in any fetchable official source. Measure it in the target org
before quoting it to Acme.

---

## 3. Baseline query (run at step 4 and again hourly at step 6)

From `references/metadata-examples.md` § "Verification and monitoring":

```sql
SELECT OwnerId, COUNT(Id) escalatedOpen
FROM Case
WHERE IsEscalated = true AND IsClosed = false
GROUP BY OwnerId
ORDER BY COUNT(Id) DESC
```

`Case.IsEscalated` is a plain writable boolean, not an engine-owned lock (`gotchas.md` #11), so
treat a spike as a question rather than as proof the rule fired. Corroborate with owner-change
history on the sampled cases.

---

## 4. Risks a human must accept before flipping `<active>` to `true`

### R1 — Entry 2's clock depends on `M4-S03`, which is not built

Entry 2 is `businessHoursSource` `Case`, which reads `Case.BusinessHoursId`. The step that
populates that field from `Account.Region__c` is **`M4-S03`, and it is not built yet**
(`artefacts/M3-S04/owner-writer-map.md` § 1 and `artefacts/M4-S01/deploy-order.md` § 0 both name
it as the populating step).

What entry 2 does on a case whose `BusinessHoursId` is null is **UNVERIFIED** — no skill in the
library states the fallback, and no org was consulted. `gotchas.md` #3 establishes only that the
org's shipped default calendar is 24/7, so *if* the null case falls back to the org default, entry
2 behaves like entry 1 and the weekend pause promised by `requirement.md` L16 silently does not
happen. **Do not activate this rule before `M4-S03` is deployed and `Case.BusinessHoursId` is
confirmed populated on new cases**, or verify the null-fallback behaviour in the sandbox first.

### R2 — `notifyCaseOwner` on a Billing-queue-owned case posts into a live intake mailbox

`notifyCaseOwner` is `true` on both entries (Q45: "reassign to the Tier 2 queue **and** notify").
The case owner at escalation time is whichever queue `M3-S04`'s assignment rule placed the case
in. One of those queues, `Billing`, carries
`<email>billing@acme.example</email>` (`artefacts/M2-S04/queues/Billing.queue-meta.xml`) — and
`billing@acme.example` is also a **live Email-to-Case routing address**
(`artefacts/M3-S03/settings/Case.settings-meta.xml`). An escalation notification sent to it
becomes a new case, which itself escalates 480 minutes later and notifies it again.

This is the risk `decisions.md` **D-M2S04-04** named as latent and **O-M3S04-02** asked the next
step to check before adding a notification: *"before any future step adds an
assignment-notification template to the Billing entry, confirm it does not post into
billing@acme.example itself."* **This is that check, and the answer is that it does.**

Three remedies, none of which this step may choose on its own — each needs an answer this build
does not hold:

| Option | What it needs |
|---|---|
| a. Exclude Billing-owned cases from escalation (a third entry, or a criterion on entry 2) | An answer saying finance cases do **not** escalate to Tier 2 Engineering. `requirement.md` L16 says "anything untouched", unqualified, so this narrowing is not this agent's to invent (the `D-M3S04-02` precedent) |
| b. Drop `notifyCaseOwner` and rely on `assignedToTemplate` alone | Accepting that the notify half of Q45 may reach nobody — see R3 |
| c. Give the `Billing` queue a notification address that is not an intake address | A Finance mailbox nobody has named. `D-M2S04-02` refused to invent the equivalent address for Tier 2 |

**Because the rule ships inactive, nothing loops on deploy.** This is an activation prerequisite,
not a deployment defect.

### R3 — the `assignedToTemplate` recipient is unverified

`assignedToTemplate` is *"the template for the email sent to the new owner"*. The new owner is the
`Tier_2_Engineering` queue, which carries **no `<email>`** and
`<doesSendEmailToMembers>false</doesSendEmailToMembers>` — `decisions.md` **D-M2S04-02** omitted
the address deliberately because no clarification names a Tier 2 mailbox. Where that email is
delivered under those two settings is **UNVERIFIED**: `skills/admin/queues-and-public-groups`
documents `email` and `doesSendEmailToMembers` as independent switches but does not state what an
escalation `assignedToTemplate` does when both are off. Confirm in the sandbox at step 3, or
answer `D-M2S04-02`'s open address question first.

### R4 — the reassignment writes `OwnerId`, hours after intake

Both entries carry `assignedTo`, so both write `Case.OwnerId`
(`gotchas.md` #9). `artefacts/M3-S04/owner-writer-map.md` § 1 already registers this rule as
**writer 3 of 3** by design, after the intake assignment rule and Omni-Channel push, and records
that this is a deliberate hand-off rather than contention. No fourth, unnamed owner writer exists
in this build. Re-confirm that at the M4 gate if `M4-S03`'s before-save Flow grows an ownership
branch.

### R5 — entry 1 observes no holidays at all

`businessHoursSource` `None` reads no calendar, so it also observes **no holidays**
(`gotchas.md` #10). That is the point of the entry — `requirement.md` L18 promises Severity 1
never pauses — and it is listed here so the exception is a recorded decision rather than something
someone discovers on 25 December.

---

### R6 — `notifyToTemplate` was added after the org rejected the first build (F-36)

`reports/MOCK-DEPLOY-M4.md` run 1 failed with `EscalationRules Case: notifyToTemplate is
required`, because both actions set `notifyCaseOwner` true with no template. The element is now
present on both, naming the same template as `assignedToTemplate` — this build holds one escalation
template, not two (`deploy-order.md` § 3 U6). Two consequences for activation:

- The outgoing case owner and the incoming Tier 2 queue receive the **same body**. Correct in both
  directions, but one template doing two jobs; a distinct owner-warning notice is a new
  `EmailTemplate` on a `ui` step.
- `notifyToTemplate` sends to whoever `notifyCaseOwner` selects, which is the same recipient as
  **R2** below. Adding the template did not narrow that exposure — it made the mail that R2
  describes actually send.

## 5. Validate-only command (text for a human; this agent ran nothing)

```bash
sf project deploy validate \
  --source-dir .sfskills/builds/case-onboarding/artefacts/M4-S04/escalationRules \
  --target-org <alias>
```

`sf project deploy validate` is documented for **production** orgs; against a sandbox use
`sf project deploy start --dry-run` instead. Deploy the prerequisites in § 1 first — see
`deploy-order.md`.
