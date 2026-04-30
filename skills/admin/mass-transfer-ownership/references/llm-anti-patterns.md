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

**Correct pattern:** Salesforce blocks deactivation if records remain. The required order is: transfer ownership → reassign default-owner references → deactivate.

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
