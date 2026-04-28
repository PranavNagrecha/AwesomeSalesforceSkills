# Gotchas — UAT Test Case Design

Non-obvious behaviors and authoring failures that produce false-pass UAT runs in real Salesforce projects.

---

## Gotcha 1: Testing as System Administrator

**What happens:** The case runs green. The feature ships. In production, regular
users hit a P1 permission error or — worse — bypass a validation rule that was
scoped to a custom permission Sys Admin already had.

**When it occurs:** Whenever the `permission_setup` block is missing, vague
("the right permissions"), or names the System Administrator profile.

**How to avoid:** Every case must name a non-Admin profile + the explicit PSG.
The check_uat_case.py script enforces this — `permission_setup` cannot be empty
and the persona cannot be "System Administrator." For deny cases, the persona is
named WITHOUT the PSG so the deny is the test result, not the absence of setup.

---

## Gotcha 2: Missing Data Setup → Setup-Reason Failures

**What happens:** The case fails because the parent Account did not exist, the
required picklist value was retired, or the validation rule needed a Contact
that was not seeded. The team logs a feature defect when there was none.

**When it occurs:** When `data_setup` is empty or the case description assumes
"there will be records." Especially common in fresh sandboxes.

**How to avoid:** Make `data_setup` an explicit ordered list: every record,
every import file, every parent the steps depend on. For >5 records or
relationship-heavy seeds, cite `templates/apex/tests/TestDataFactory.cls` and
invoke from anonymous Apex before the run begins.

---

## Gotcha 3: UI-Coupled Steps That Break on Lightning vs Classic

**What happens:** The case steps reference "click the New button on the related
list" but the user is in Classic (or vice versa) where the action is in a
different UI region. Tester reports "step 3 unclear, blocked."

**When it occurs:** When step language assumes one UI mode without saying so.
Also bites when the persona's profile defaults to a different UI mode than the
case author assumed.

**How to avoid:** State the UI mode in `precondition` ("Lightning Experience"
explicitly). Cite UI elements by developer name or `data-id` where possible
("Quick Action `Mark_Complete`") rather than visible label, since labels can
change with translations or release upgrades.

---

## Gotcha 4: Missing Pass/Fail Evidence

**What happens:** The tester writes "Pass" with no screenshot or recording.
Three weeks later the BA cannot prove the AC was met. The auditor asks for
evidence and finds nothing.

**When it occurs:** When `evidence_url` is left blank because "the tester
remembers." Compounded when the run was on a sandbox that was later refreshed,
destroying any forensic ability to reconstruct.

**How to avoid:** `evidence_url` is required at run time. Tester attaches a
screenshot or screen-recording link (Quip, Drive, internal SharePoint) before
setting `pass_fail`. The check script enforces presence of this field for any
case marked Pass or Fail (Blocked / Not Run are exempt).

---

## Gotcha 5: Over-Testing — One Case Per Click

**What happens:** A 6-step Opportunity wizard produces 36 UAT cases. Reviewers
cannot map them to AC. The run takes 4 hours instead of 1. Negative paths get
dropped under time pressure.

**When it occurs:** When authors decompose by UI action instead of AC scenario.
Often a sign the AC block was skipped and the team is writing scripts from the
story description.

**How to avoid:** Decompose by `ac_id`. If a case has 6 steps in its `steps`
array, that's fine — one AC scenario per case is the contract, not one click
per case.

---

## Gotcha 6: Under-Testing — One Case Per Story

**What happens:** The team writes a single case per user story that walks the
whole feature in one breath. When it fails, no one knows which AC broke. The
RTM cannot close at AC granularity.

**When it occurs:** When stories are written with only narrative requirements
and no Given/When/Then AC. Or when the team is rushing and skipping the
decomposition step.

**How to avoid:** Each AC scenario in the source story produces ≥1 case. If a
story has 4 AC scenarios, the case set has ≥4 cases (more if personas split).
Reject case sets where `case_count < ac_scenario_count`.

---

## Gotcha 7: No Negative Path

**What happens:** Every case passes happy-path. Production ships. Day 2,
a user submits invalid input and the validation rule that should have blocked
the save silently passes because the team never tested the failure path.

**When it occurs:** When the case set is generated from happy-path AC only and
the negative scenarios in the AC block were ignored.

**How to avoid:** ≥1 case per story with `negative_path: true`. The check
script enforces this per-story — a story with no negative-path case fails the
gate. Negative cases come from the AC's failure scenarios; do not invent new
ones.

---

## Gotcha 8: No Traceability to AC

**What happens:** Cases lack `story_id` or `ac_id`. The RTM cannot reconcile
which AC was proven. When an auditor asks "show me the case that proved
AC-734-2," the team cannot answer.

**When it occurs:** When cases are authored as flat scripts without the
schema's mandatory ID fields, or when an "untraceable" placeholder is used
because the AC was not stable when the case was written.

**How to avoid:** `story_id` and `ac_id` are required in the schema. Cases
written before the AC stabilizes are drafts, not deliverables — block them
from execution until both IDs resolve to real artifacts.

---

## Gotcha 9: Permission Set Group Recalculation Lag

**What happens:** The case assigns a PSG, the tester immediately runs the
script, and the steps fail because the entitlement has not propagated yet.
False-fail logged.

**When it occurs:** Right after a fresh PSG assignment, especially in larger
orgs where the recalc job is queued behind other work.

**How to avoid:** Add an explicit "log out, log back in, wait 60 seconds" line
in `precondition` after PSG assignment, or schedule permission_setup as a
prior day step.
