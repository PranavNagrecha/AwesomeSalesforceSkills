# Gotchas — Lead Nurture Journey Design

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Programs Run on a Weekly Schedule — Not Real-Time

**What happens:** Engagement Studio programs evaluate each prospect's position in the program once per weekly run, not continuously. A prospect who clicks an email on a Monday afternoon will not be re-evaluated by the rule that follows the send until the next weekly execution window — which could be 5–7 days later. Teams that design nurture programs expecting same-day or next-day follow-up experience significant delays between prospect intent signals and program response.

**When it occurs:** Any time a practitioner configures a Wait step shorter than 7 days and expects the program to act on it within that window. Also occurs when a prospect submits a form or reaches an MQL-eligible score mid-week — the Notify User or Create Task step in the program will not fire until the next weekly run.

**How to avoid:** Design Wait periods with the weekly cadence in mind — a 3-day Wait in the UI may functionally behave as a 7-day Wait in practice. For steps that must fire within hours of a prospect action (form submission autoresponder, MQL alert to Sales), use Completion Actions on the triggering asset or a standalone Automation Rule outside the program. Document the program's actual expected cadence for stakeholders so they do not interpret delayed step execution as a configuration error.

---

## Gotcha 2: A Prospect Can Only Be Active in One Program at a Time (By Default)

**What happens:** If a prospect is already enrolled in Program A and is added to the entry list for Program B, MCAE silently ignores the Program B enrollment. The prospect remains in Program A and receives no content from Program B until they exit Program A. There is no error, no notification, and no indicator in the prospect record that the second enrollment was rejected.

**When it occurs:** Most commonly when an org runs parallel nurture programs targeting overlapping audiences — for example, a product-specific nurture program and a broad lead nurture program both targeting the same prospects. Also occurs when a re-engagement program's entry list overlaps with an active primary nurture program.

**How to avoid:** Design entry lists to be mutually exclusive where possible. Use dynamic list criteria that explicitly exclude prospects who are in an active program (use the "Is member of list" filter with an "active nurture" tracking list). Document program priority rules: which program wins when a prospect qualifies for multiple. Review the prospect's "Active Programs" tab in MCAE before assuming a new enrollment took effect.

---

## Gotcha 3: Editing a Live Program Can Strand or Skip Prospects Mid-Flow

**What happens:** When a running program is edited — steps added, removed, or reordered — prospects currently waiting between steps may be re-evaluated against the new program structure. Depending on where a prospect is in the queue, they may skip newly added steps, be evaluated against a rule that no longer corresponds to the email they received, or be placed in a step that assumes prior context that was bypassed.

**When it occurs:** Occurs any time an admin edits a program that has active prospects waiting in it. Common in early post-launch tuning (adding a missing Wait step, correcting a rule condition) or when content updates require swapping an email template in a mid-program step.

**How to avoid:** Before editing an active program, pause it. Export or document the list of prospects currently mid-program and their current step position. Make the structural changes. Verify that the prospect queue positions are still logical after the edit. Reactivate the program. For major restructuring, consider creating a new program version and migrating prospects rather than editing a live program with a large active cohort.

---

## Gotcha 4: Rule Steps Evaluate Historical Activity, Not Real-Time Intent

**What happens:** When an Engagement Studio rule checks "Did prospect click email X?", it evaluates whether the prospect has ever clicked that email within the activity history — not whether they clicked it recently. If a prospect clicked the email 45 days ago, re-entered the same program, and the rule evaluates this week, the rule fires "Yes" based on the old click. This can route a prospect to Decision-stage content based on intent signals that are weeks or months old.

**When it occurs:** Occurs when prospects re-enter a program after exiting (e.g., after a re-engagement campaign routes them back into the main nurture), when the same email is used in multiple programs, or when programs are paused and reactivated with existing prospects who have historical activity against program assets.

**How to avoid:** When precision matters, add a time window to rule conditions: "Prospect clicked email X within the last 7 days" rather than "Prospect clicked email X" with no time bound. Use unique email templates per program step rather than reusing email assets across programs, so historical activity on a shared email does not contaminate rule evaluations in a different program context.

---

## Gotcha 5: Prospects Exiting the Program Receive No Automatic Follow-On Action

**What happens:** When a prospect reaches the end of a program, is manually removed from the entry list, or exhausts all paths without meeting any branching conditions, they silently exit the program. No notification fires, no task is created, no CRM record is updated — unless those steps are explicitly configured before the exit point. Prospects who exit without meeting the MQL threshold and without a defined next action simply disappear from the nurture flow with no stakeholder awareness.

**When it occurs:** Occurs at the end of any program path that terminates without an explicit "Add to List," "Change Prospect Field," "Notify User," or "Create Task" step. Most frequently discovered during pipeline reviews when Sales asks why prospects who were in nurture for 90 days show no status in CRM.

**How to avoid:** Treat every exit point in the program as a deliberate action — not a passive end. For prospects who complete the program without reaching MQL, explicitly: add them to a "Long-term Nurture" or "Re-engagement" list, change a "Nurture Status" field to "Program Complete — No MQL," and optionally create a low-priority CRM task for Sales review. Every program path should terminate with at least one status-setting step before the prospect exits, so the record reflects what happened.
