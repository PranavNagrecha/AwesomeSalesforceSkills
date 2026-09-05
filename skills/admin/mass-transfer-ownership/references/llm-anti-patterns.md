# LLM Anti-Patterns — Mass Transfer Ownership

Common mistakes AI coding assistants make when generating or advising on mass-transfer ownership tasks.

## Anti-Pattern 1: Assuming Data Loader cascades

**What the LLM generates:** "Update Account.OwnerId via Data Loader and the child Cases will follow."

**Why it happens:** The LLM conflates the Mass Transfer Records UI (which has cascade checkboxes) with the API (which does not).

**Correct pattern:** API-driven updates leave child records on their old owner. Plan a separate Data Loader job for each child object.

**Detection hint:** Any assertion that "child records will follow" without an explicit per-child-object update step.

---

## Anti-Pattern 2: Suggesting parallel mode for large volumes

**What the LLM generates:** "Speed up the transfer by enabling parallel mode in Data Loader."

**Why it happens:** Performance heuristic generalized from other ETL tools.

**Correct pattern:** Parallel mode plus a Private OWD plus sharing recalc equals row-lock collisions on share-table rows. Use serial mode and batch size ≤200 above ~50k volume.

**Detection hint:** The phrase "use parallel mode" alongside any volume above 50k or any private-OWD object.

---

## Anti-Pattern 3: Skipping the pre-deactivation transfer

**What the LLM generates:** A user-deactivation script that calls deactivate first, then transfers records.

**Why it happens:** The LLM follows a chronological "user is leaving, deactivate them" mental model.

**Correct pattern:** The required order is transfer ownership → reassign default-owner references → strip team memberships → deactivate. The team step is the one assistants never emit, and the Object Reference is explicit that "the user interface provides options to auto-remove a user from teams, but the removal isn't supported in API" — so a scripted offboarding leaves the departing user on every account and opportunity team. (Whether deactivation is hard-*blocked* by remaining records is documented in Salesforce Help rather than the API guides; see the note in `references/gotchas.md` Gotcha 1. The ordering is correct regardless.)

**Detection hint:** Any deactivation step that precedes the OwnerId reassignment in a generated runbook.

---

## Anti-Pattern 4: Missing the AssignmentRuleHeader implication

**What the LLM generates:** A Data Loader update for Lead.OwnerId without commenting on the assignment-rule checkbox.

**Why it happens:** The header is a hidden default in the Data Loader UI; the LLM doesn't surface it.

**Correct pattern:** State explicitly whether the transfer should fire assignment rules. For Lead/Case mass transfers, you almost always want assignment rules off — otherwise the rule may immediately re-route what you just moved.

**Detection hint:** Any Lead or Case mass-transfer instruction that doesn't mention assignment rules.

---

## Anti-Pattern 5: No rollback plan

**What the LLM generates:** "Run Data Loader update on the OwnerId column. Done."

**Why it happens:** The LLM treats DML as atomic and ignores audit/recovery needs.

**Correct pattern:** Before the update, query and save `Id, OldOwnerId` to a CSV. The success.csv from Data Loader plus that pre-update snapshot is the audit trail and the rollback artifact.

**Detection hint:** Any transfer plan that has no "save current OwnerId values" step before the update.


---

## Anti-Pattern 6: Promising the new owner an email from a Bulk API or Data Loader transfer

**What the LLM generates:** A runbook that reassigns 20,000 Opportunities through Bulk API 2.0
and adds "the new owners will be notified automatically."

**Why it happens:** The assistant transfers the UI's behaviour — where changing an owner offers
a "Send Notification Email" checkbox — onto the API path, which has no such control.

**Correct pattern:** The Bulk API 2.0 *Create a Job* request body has exactly seven properties
and none of them is an email header. The Apex Reference states the consequence directly: "If you
use the API to change record ownership, or if a Lightning Experience user changes a record's
owner, no email notification is sent. To send email notifications to a record's new owner, set
the `triggerUserEmail` property to true" — and that property lives on
`Database.DMLOptions.EmailHeader`, which takes effect "only for DML operations carried out in
Apex code." If the notification is a requirement, the tool choice is Apex, not volume-driven.

**Detection hint:** Any Bulk API or Data Loader transfer plan that mentions notifying, alerting,
or emailing the new owner without switching to Apex.

---

## Anti-Pattern 7: Treating the rollback CSV as a full undo

**What the LLM generates:** "Save `Id, OldOwnerId` before the update; if anything goes wrong,
re-run it in reverse and you're back where you started."

**Why it happens:** The assistant models the transfer as a single reversible field write.

**Correct pattern:** Re-running the CSV restores `OwnerId` and, asynchronously, the `Owner` share
rows. It does not restore account team members that were dropped because they were added by a
group-access user, un-send emails, un-fire the automation that ran on each save, or repair rows
that an assignment rule re-routed to a third owner while the job was running — for those rows the
saved `Old_OwnerId` is now simply wrong. A correct plan states what rollback covers *and* what it
does not, and pairs the CSV with a team-membership snapshot.

**Detection hint:** The word "rollback" or "reversible" in a transfer plan with no accompanying
list of irreversible side effects.
