# Owner-writer map — who sets `Case.OwnerId`, when, and with what authority

Declared output of `M3-S04`. Written by `agents/metadata-builder`; it records the answer to
**Q27** ("Does anything else write `OwnerId` after save?") and the consequence `decisions.md`
**D3** hands this step: *"Two by-design post-save `OwnerId` writers remain (Omni-Channel push in
`M3-S05` and the escalation rule in `M4-S04`). Q27 already flagged this; `owner-writer-map.md` in
`M3-S04` is the artefact that has to reconcile all three."*

Nothing in this build deploys. This file is a reading for a human, not a component.

## 1. The three writers, in the order they fire

| # | Writer | Built by | When it fires | Authority | Status in this build |
|---|---|---|---|---|---|
| 1 | **`AssignmentRules:Case` → `Case_Intake_Routing`** (this step) | `M3-S04` | During the save that creates the Case, at save-order position 9 | **Sole authoritative writer at creation** (D3, Q27) | Built here, `<active>true</active>` |
| 2 | **Omni-Channel push** — `QueueRoutingConfig` `Tier_1_Push` pushing from the `Tier_1_General` queue to an available Tier 1 agent | `M3-S05` | After save, whenever an agent with capacity is available | By design, and only *after* writer 1 has landed the case in the queue | **Not built** — `M3-S05` is `blocked` on Q32–Q35 (assumptions A4–A7). Until it ships, Tier 1 works the queue's list view (`M5-S01`) and writer 1's result stands unchanged |
| 3 | **`EscalationRules:Case`** — reassign to `Tier_2_Engineering` at 8 business hours | `M4-S04` | 480 minutes of Case business hours after creation, on an untouched case | By design, and last | **Not built** — `M4-S04` is `pending`, and its plan text says it ships `<active>false</active>` (Q47) for a comparison window |

Writers 2 and 3 are **not defects and not contention**. They act on a case that writer 1 has already
placed in a queue; each is a deliberate hand-off, and each was named in Q27's answer before this step
was built. What would be a defect is a *fourth*, unnamed writer — a before-save or after-save
record-triggered Flow, an Apex trigger, or a second assignment rule — and this build contains none.

## 2. Why the first writer is a rule and not a Flow

`decisions.md` **D3**, from `standards/decision-trees/automation-selection.md` Q13, first leaf: *"The
first owner comes from an ordered criteria table of field values → Assignment Rules ·
`admin/assignment-rules`."* The tree's own note gives the mechanical reason a before-save Flow cannot
do this job: assignment rules run at **save-order position 9**, after all after triggers and before
after-save record-triggered flows at position 14, so a before-save Flow that sets `OwnerId` is simply
overwritten by the rule a few positions later.

## 3. Which creation channels actually invoke writer 1 (Q24)

`skills/admin/assignment-rules/SKILL.md` § "When Assignment Rules Run", and `references/gotchas.md`
#1 and #3. This matters because a channel that does not invoke the rule produces a case with **no**
authoritative owner *and* no acknowledgement — the auto-response rule in this step fires only when
the assignment rule fires.

| Channel | Volume (requirement) | Invokes the rule? | What has to be true |
|---|---|---|---|
| Email-to-Case (`support@`, `billing@`) | ~400/day | **Automatically** | `enableEmailToCase` is `true` — `M3-S03` |
| Web-to-Case | ~60/day | **Automatically** | `enableWebToCase` is `true` — `M3-S03` |
| Lightning UI, created by an agent | ~20/day | **Only if the agent ticks "Run assignment rules"** | Q24's answer requires the checkbox to be **defaulted on** for the Case layouts. **That default is not metadata this step writes**, and no step in this build declares it — see § 5 |
| REST / SOAP API, Data Loader, Apex | none in this phase | **No, unless the caller opts in** | `Sforce-Auto-Assign: true` (REST), `AssignmentRuleHeader` (SOAP), the rule id in Data Loader settings, or `Database.DMLOptions.assignmentRuleHeader` (Apex) — gotcha #1 |

## 4. The one-active-rule constraint, and what deploying this file does to the target org

`skills/admin/assignment-rules/SKILL.md`: **one active assignment rule per object**, platform-enforced.
Deploying `Case_Intake_Routing` with `<active>true</active>` **activates it and silently deactivates
whatever Case rule is active in the target org today** — no warning, no confirmation dialog
(gotcha #2). Acme runs case intake from a shared mailbox today and has no Service Cloud rule to
displace, so in this build the effect is nil; in any org that has been used before, record the
currently-active rule's name before deploying and confirm it reads *Inactive* afterwards.

## 5. What this map does NOT cover, stated rather than implied

1. **The "Run assignment rules" layout default (Q24).** The answer requires it; `M2-S03`'s layouts
   are already `documented` and no step declares it. It is a Setup-level layout property, not
   something this step's `outputs[]` can add. Raise it at the M3 gate or carry it as a backlog item —
   without it, ~20 cases a day are owned by their creator and get no acknowledgement.
2. **Omni-Channel's capacity model.** Writer 2's behaviour is `M3-S05`'s to specify, and it is
   blocked. Nothing here predicts how it will pick an agent.
3. **Sharing.** `M2-S05` decides who can *see* a queue-owned case. Ownership and visibility are
   different questions and this file answers only the first.
