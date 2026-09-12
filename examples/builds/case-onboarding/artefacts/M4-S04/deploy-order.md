# Deploy order — M4-S04 (Case escalation rules)

Written by `agents/metadata-builder` on every run, per its AGENT.md Step 7. **Nothing in this
build deploys.** The command at the end is validate-only text for a human to copy; this agent ran
no `sf` command of any kind.

**Note on declaration:** this file is *not* in `plan.json` `steps[M4-S04].outputs[]` — four paths
are declared (`escalationRules/Case.escalationRules-meta.xml`,
`escalation-activation-runbook.md`, `escalation-monitoring-note.md`, `package.xml`). It is written
anyway because the human's deploy reads it, which is the same undeclared-`deploy-order.md` pattern
`decisions.md` **O-M3S02-03** records for `M3-S01`..`M3-S04` and `artefacts/M4-S01/deploy-order.md`
records for `M4-S01`. It is reported again in this run's envelope as an undeclared artefact rather
than left for a reader to notice.

---

## 0. Rebuild record — F-36, `notifyToTemplate is required`

This step was built at `2026-09-12T07-22-10Z`, tested (3 automated, 0 failed), and then **rejected
by the org**. `reports/MOCK-DEPLOY-M4.md` run 1 — `checkOnly`, `sfskills-dev`, API 67.0 — failed
with:

```text
EscalationRules Case: notifyToTemplate is required
```

Both entries set `<notifyCaseOwner>true</notifyCaseOwner>` with no `<notifyToTemplate>`. Recorded
as **F-36**. The operator reset the step `tested → failed → pending` and re-claimed it `running`.

**The gap was closed at the skill, not worked around in the artefact.** Commit `9ae71856d`
(`admin/escalation-rules` v1.1.2) adds:

- **E10** (ERROR): `notifyCaseOwner` true or a populated `notifyTo` with no `notifyToTemplate`.
- **I4** (INFO): a `notifyToTemplate` / `assignedToTemplate` that is not folder-qualified.
- `references/gotchas.md` **#13** carrying the org's exact error text, `llm-anti-patterns.md`
  Anti-Pattern 6, and a folder-qualified `notifyToTemplate` on **every** worked example.

The checker then failed the file that had passed an hour earlier, with two E10 lines — one per
action — which is the evidence that the rule now bites:

```text
ERROR E10  [Case.escalationRules-meta.xml :: Case_SLA_Escalation :: entry 1 :: action 1]
           notifyCaseOwner is true but notifyToTemplate is empty. …
ERROR E10  [Case.escalationRules-meta.xml :: Case_SLA_Escalation :: entry 2 :: action 1]
           notifyCaseOwner is true but notifyToTemplate is empty. …
2 error(s), 1 warning(s), 4 info note(s).   EXIT=1
```

**What changed in this rebuild, and nothing else:** one `<notifyToTemplate>` element (plus its
explanatory comment) added to each of the two `escalationAction` blocks. Every other element,
value, comment and entry ordering is byte-identical to the `07-22-10Z` build. The rule still ships
`<active>false</active>`; `package.xml` is unchanged.

Note what this is **not**: the earlier build was not careless. The Metadata API guide's
`EscalationAction` table marks `notifyToTemplate` as a plain `string` with no Required marker and
no stated dependency on `notifyCaseOwner`, and every worked example in the skill at v1.1.1 wrote
`notifyCaseOwner` without it. The constraint was only discoverable against a live org. It is now
in the skill, so the next build gets it for free — and the checker catches it before a deploy does.

---

## 1. What this step produces

| Component | Type | package.xml member |
|---|---|---|
| `escalationRules/Case.escalationRules-meta.xml` | `EscalationRules` | `Case` |

One file, one member, `<version>67.0</version>` — the build API version confirmed at the M3 gate
(decision 6 on `human_gates[milestone:M3]`, finding **F-31**), matching `M3-S01`..`M4-S01`.

The file contains **one rule, `Case_SLA_Escalation`, with two entries**, shipped
`<active>false</active>` per **Q47**. One file holds every escalation rule for Case; retrieving
`EscalationRules:Case` and deploying it back overwrites the whole file
(`skills/admin/escalation-rules/references/metadata-examples.md` § "Where the file lives").

---

## 2. Order — what must already be in the org

Escalation rules deploy **last** of everything they name. The cited skill states the order
directly: *"business-hours calendars (`Settings:BusinessHours`), then queues and Classic email
templates, then the escalation rules that name them"*
(`references/metadata-examples.md` § "Retrieve, lint, deploy"), and
`skills/admin/queues-and-public-groups/references/metadata-examples.md` states the same from the
other side: *"Queues are the routing targets every assignment rule, escalation action, and
Omni-Channel routing configuration names by developer name, so they deploy first."*

| # | Component | Built by | Why it must precede this step |
|---|---|---|---|
| 1 | `Case.Severity__c` + picklist value `Severity 1` | `M1-S01` | Entry 1's `criteriaItems` filters on it. A criterion naming a field that does not exist fails on the reference |
| 2 | `Settings:BusinessHours` (`US Support`, `EMEA Support`, `Severity 1 24x7`) | `M4-S01` | Entry 2 is `businessHoursSource` `Case`, so it resolves whatever calendar `Case.BusinessHoursId` names. **Entry 1 needs none of them** |
| 3 | `Queue:Tier_2_Engineering` | `M2-S04` | Both entries' `assignedTo`. Named by **developer name**, not by the `Tier 2 Engineering` label |
| 4 | `EmailFolder:case_intake`, then `EmailTemplate:case_intake/Case_Escalated_To_Tier2` | `M3-S02` | Both entries' `assignedToTemplate`. Folder before template; template before this rule |
| 5 | `AssignmentRules:Case` (`Case_Intake_Routing`) | `M3-S04` | Not a hard deploy dependency, but the escalation only makes sense once intake places cases in a queue. It is also what determines the case owner this rule notifies — see § 5 |
| 6 | **`M4-S03`'s before-save Flow** (stamps `Case.BusinessHoursId`) | `M4-S03` — **NOT BUILT** | Not a deploy-time dependency; an **activation** dependency. See `escalation-activation-runbook.md` § 4 R1 |

Nothing in this step is a prerequisite for anything else in the build: no other step reads
`EscalationRules:Case`.

---

## 3. Elements this step could NOT ground — UNVERIFIED

Per the step's grounding rule, anything a cited skill leaves unstated is marked here rather than
guessed.

### U1 — `Case.Severity__c` inside an escalation `criteriaItems`: shape composed, not quoted

`skills/admin/escalation-rules` documents `criteriaItems/field` values only for **standard**
fields, always object-prefixed: `Case.Priority`, `Case.Status`, `Case.Type`
(`references/metadata-examples.md`, all three entries). No file in the library shows a **custom**
field inside an escalation-rule `criteriaItems`.

`Case.Severity__c` is therefore a composition of two separately grounded facts, not a quotation:
the `Case.` prefix comes from the escalation skill's own examples, and the `Object.Field__c` form
of a `criteriaItems/field` is documented in
`skills/admin/approval-processes/references/metadata-examples.md`
(`<field>Opportunity.Discount_Percent__c</field>`) and in five other admin skills. The field's own
API name is read from `artefacts/M1-S01/objects/Case/fields/Severity__c.field-meta.xml`.

**Marked UNVERIFIED, not blocked**, and this is deliberately *not* the case `decisions.md`
**D-M3S04-02** refused: that one was a **cross-object** reference
(`Account.Support_Tier__c` from a Case rule), for which every documented value is base-object.
This is base-object, which is the documented shape. Confirm the exact spelling against the target
org before the sandbox proof is signed off.

### U2 — What entry 2 does when `Case.BusinessHoursId` is null

`businessHoursSource` `Case` means *"the calendar on `Case.BusinessHoursId`"*
(`SKILL.md` § "Business Hours and the Escalation Clock"). No skill in the library states what
happens when that reference is null. `references/gotchas.md` #3 establishes only that the org's
shipped default calendar is 24/7 — if the null case falls back to it, entry 2 silently loses the
weekend pause `requirement.md` L16 promises. Verify in the sandbox; do not assume either way.
Carried as risk **R1** in `escalation-activation-runbook.md`.

### U3 — Where an `assignedToTemplate` email goes when the target queue has no `<email>` and `doesSendEmailToMembers` is `false`

`Tier_2_Engineering` has neither (`artefacts/M2-S04/queues/Tier_2_Engineering.queue-meta.xml`;
the omission is recorded as `decisions.md` **D-M2S04-02**).
`skills/admin/queues-and-public-groups` documents `email` and `doesSendEmailToMembers` as
independent switches but says nothing about an escalation handover template addressed to such a
queue. Carried as risk **R3** in the runbook.

### U4 — The engine's batching interval

`references/gotchas.md` #1 marks the commonly quoted "approximately once per hour" cadence as
UNVERIFIED in every fetchable official source. Q46 asked for headroom to be agreed against it and
no number is on file. The batched (non-immediate) behaviour is safe to design around; the interval
is not safe to quote.

### U5 — The one-active-rule ceiling

`SKILL.md` § "Before Starting" marks it UNVERIFIED: the Metadata API guide models `escalationRule`
as a repeating element with a per-rule `active` flag and does not state a ceiling. This file ships
one rule, inactive, so the question does not bite on this deploy — but step 2 of the runbook's
cutover table exists to confirm it in the target org before activation.

---

### U6 — one template serves both `notifyToTemplate` and `assignedToTemplate`

The two elements address **different recipients**: `assignedToTemplate` is *"the template for the
email sent to the new owner"* (the `Tier_2_Engineering` queue), and `notifyToTemplate` is the
template for the notification to the **outgoing** case owner that `notifyCaseOwner` true selects.
The skill's own worked example uses two distinct templates for exactly this reason — entry 1
stage 2 carries `assignedToTemplate` `unfiled$public/Sev1_Handover` alongside `notifyToTemplate`
`unfiled$public/Sev1_Escalation_Warning`.

**This build holds one escalation template, not two.** `M3-S02` is titled *"Classic
acknowledgement and escalation email templates"* and its `outputs[]` declares exactly two
templates: `case_intake/Case_Acknowledgement` (customer-facing, carries the Q64 thread token) and
`case_intake/Case_Escalated_To_Tier2`. No clarification and no line of `requirement.md` asks for a
separate owner-warning template.

So both elements name `case_intake/Case_Escalated_To_Tier2`. The alternative — inventing a second
template name such as `case_intake/Case_Escalation_Warning` — was rejected on two independent
grounds, either sufficient: it is a component no step in this build produces, so the deploy would
fail on the reference rather than on the rule; and naming a template nobody wrote is the same
class of invention `decisions.md` **D-M2S04-02** refused for the Tier 2 mailbox address.

**Consequence a human should accept or correct at the M4 gate:** the outgoing owner and the
incoming Tier 2 queue receive the same body, whose subject is *"Escalated to Tier 2: case
{!Case.CaseNumber} - {!Case.Subject}"*. That reads correctly in both directions, but it is one
template doing two jobs. If Acme wants a distinct "your case was escalated away from you" notice,
that is a new `EmailTemplate` on a `ui` step and a one-line change here.

Both values are **folder-qualified** (`case_intake/…`), so checker `I4` does not fire.

## 4. Decisions worth reading before deploy

1. **Both entries carry `minutesToEscalation` 480; the difference between them is the clock, not
   the number.** `requirement.md` L16 states one threshold ("8 business hours") and L18 says only
   that Severity 1 "never pauses" — it does not give Severity 1 a *faster* threshold. Q46 binds one
   value, 480, and the manual acceptance test asserts it for the Tier 2 entry only. Writing a
   shorter Severity 1 threshold would have been an invented SLA; writing 480 on a `None` clock is
   the requirement read literally. If Acme intends Severity 1 to escalate sooner, that is an answer
   this build does not hold and a one-line change to entry 1.

2. **Entry order is load-bearing.** A case matches **one** entry; the first match wins
   (`SKILL.md` § "Rule Structure"). Severity 1 is entry 1 *because* entry 2 would otherwise catch
   Severity 1 cases and run them on the Case's regional calendar, silently breaking the 24/7
   promise. Do not reorder, and do not "tidy" entry 2 to the top.

3. **`escalationStartTime` is `CaseCreation` and `disableEscalationWhenModified` is `false`
   (Q42), which is narrower than the word "untouched".** `requirement.md` L16 says "anything
   untouched for 8 business hours"; as built, a case an agent is actively working still escalates
   480 minutes after **creation**, because the clock measures from creation and no edit stops it.
   Q42 chose this deliberately — *"because the requirement measures from creation, not from last
   touch"* — and `references/gotchas.md` #6 gives the reason the alternative is worse here: with
   `CaseLastModified`, any automation write pushes the threshold out, and in an org with chatty
   automation a case can escalate never. `gotchas.md` #7 is the third lever
   (`disableEscalationWhenModified` `true` = "any touch ends escalation"), also declined. All three
   are explicit choices recorded per entry; none is a default. **Worth re-reading at the M4 gate**,
   because it is the one place the built behaviour and the requirement's wording diverge.

4. **Closed cases are excluded by explicit criterion, on both entries.** `gotchas.md` #12 records
   that both circulating beliefs about the engine's closed-case behaviour are ungrounded. One
   criterion makes the behaviour identical whichever is true.

5. **Entry 1 observes no holidays.** `businessHoursSource` `None` reads no calendar and therefore
   no holiday (`gotchas.md` #10). `artefacts/M4-S01/deploy-order.md` § 0 already predicted this
   exact value from the plan, and `decisions.md` **O-M4S01-01** records the consequence: the
   `Severity 1 24x7` calendar built in `M4-S01` is read by **no step in this build**, because this
   step carries the 24/7 promise through `None` rather than through a named calendar. That entry's
   remedy line still stands — a future Severity 1 *entitlement process* would point at that
   calendar, because a milestone has no `None` source.

6. **The rule ships inactive and the checker's `W1` is expected.**
   `check_escalation_rules.py` prints `WARN W1 ... no rule in this file is active` and exits 0. Q47
   requires exactly that. A future reader should not "fix" it in source; activation is a separate
   one-line deploy (`escalation-activation-runbook.md` § 2 step 5).

---

7. **`notifyToTemplate` is present on both actions because the org requires it, not because the
   guide does.** `references/gotchas.md` #13 (added at v1.1.2 from this build's own F-36) records
   the constraint as UNVERIFIED-in-the-guide but proven live. A future reader who sees the element
   on a notify-only action and thinks it redundant should read that gotcha before removing it — the
   removal deploys as valid XML and fails at org validation.

## 5. Sender identity: what this step does and does not touch

`decisions.md` **D-M3S04-01** and **D-M3S04-04** fix `support-noreply@acme.example` as the decided
sender for the auto-response rule, and **D-M3S04-03** records that the address is a **G3 deploy
prerequisite (F-28)** — `sfskills-dev` carries no `OrgWideEmailAddress` record and there is no
metadata type for one.

**`EscalationAction` has no sender element.** Its documented fields are `minutesToEscalation`,
`notifyTo`, `notifyToTemplate`, `notifyEmail`, `notifyCaseOwner`, `assignedTo`, `assignedToType`
and `assignedToTemplate` (`SKILL.md` § "Escalation Actions Are Staged Inside One Entry"); none of
them names a From address. So F-28 is **not** a prerequisite for this component, and this step
neither resolves nor re-opens `D-M3S02-04`.

What the sender-identity decisions *do* bind here is the recipient side, and it is honoured: **no
routing address appears anywhere in this file.** Neither `notifyEmail` nor `notifyTo` is written
at all, precisely because no grounded, non-routing address exists for either
(`D-M2S04-02` refused to invent Tier 2's). The notify half of Q45 is carried by `notifyCaseOwner`
and `assignedToTemplate`, both of which need no address in this file.

The F-36 rebuild adds `notifyToTemplate` to both actions and **does not change any of this**: `notifyToTemplate` names a template, not an address, and the template it names is `M3-S02`'s, whose sender identity is `M3-S02`'s question rather than this rule's. `EscalationAction` still has no sender element.

That leaves one indirect exposure, which **is** a routing address and is recorded in full as risk
**R2** in `escalation-activation-runbook.md`: `notifyCaseOwner` resolves at run time to whichever
queue owns the case, and the `Billing` queue's `<email>` is `billing@acme.example`, a live
Email-to-Case intake address. This is the check `decisions.md` **O-M3S04-02** asked the next step
to make, and the answer is that the exposure is real. It is an **activation** prerequisite — the
rule is inactive on deploy — with three remedies, none of which this agent may choose.

---

## 6. Validate-only command (text for a human; this agent ran nothing)

```bash
sf project deploy validate \
  --source-dir .sfskills/builds/case-onboarding/artefacts/M4-S04/escalationRules \
  --target-org <alias>
```

`sf project deploy validate` is documented for **production** orgs and requires Apex tests; against
a sandbox use `sf project deploy start --dry-run` instead. Deploy the § 2 prerequisites first — a
missing queue, template or picklist value fails the deploy on the reference, not on the rule.
