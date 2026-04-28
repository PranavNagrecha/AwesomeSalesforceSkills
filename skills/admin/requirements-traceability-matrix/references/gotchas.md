# Gotchas — Requirements Traceability Matrix

Non-obvious delivery realities that turn an RTM from a governance artifact into a fiction.

---

## Gotcha 1: Bidirectional Drift Between Requirement and Story

**What happens:** A requirement is updated mid-flight (often via a verbal change in a refinement workshop). The story that implements it is updated to match the new behavior, but the RTM row still cites the original requirement text. Now the matrix says story `US-101` implements requirement `REQ-007 — original`, while `US-101` actually delivers `REQ-007 — refined`. At audit, the trace is wrong.

**When it occurs:** Mid-sprint scope refinements where the BA updates the agile tool but treats the RTM as a release-gate artifact, not a living document.

**How to avoid:** Treat the requirement description as a versioned field. If the requirement is materially refined, either (a) bump the description and add a `last_updated` column, or (b) close the original `REQ-007` as `Dropped` and add a new `REQ-007a` with `source: change-request`. Never silently overwrite a requirement description without an entry in the change log.

---

## Gotcha 2: Test Cases Not Tied Back to Requirements

**What happens:** UAT test cases get authored against user stories (because the QA team works from the agile tool, not the requirements doc). Tests are linked to stories, stories are linked to requirements, but the RTM only captures `req_id ↔ story_ids`, not `req_id ↔ test_case_ids`. At audit, the auditor asks "show me the test that proves REQ-007 was validated" and the team has to walk through stories to find it.

**When it occurs:** When the test management tool and the requirements tool are different systems and nobody owns the cross-reference.

**How to avoid:** Make the `test_case_ids` column mandatory before status moves to `In UAT`. The BA or QA lead populates it as cases are authored. A test case that does not trace to a requirement is either a regression test (separate column) or scope creep (escalate).

---

## Gotcha 3: IDs Reused Across Project Phases

**What happens:** Phase 1 ships REQ-001 through REQ-050. The Phase 2 BA starts a new RTM file and reuses REQ-001 for a totally different requirement. Six months later, a defect log says "regression in REQ-001" and nobody knows which one.

**When it occurs:** Multi-phase programs where each phase has a different BA or different agile tool project, and IDs are not namespaced.

**How to avoid:** Either (a) continue numbering across phases (Phase 2 starts at REQ-051), or (b) use a phase prefix (`P1-REQ-001`, `P2-REQ-001`). Never reuse a bare `REQ-XXX` ID across phases of the same program.

---

## Gotcha 4: RTM Lives in a Spreadsheet That Nobody Maintains

**What happens:** RTM is created at project kickoff in SharePoint or Google Sheets. It is populated for the first sprint, then not updated. By release, half the rows have stale story IDs, missing test references, and wrong statuses. The Steerco deck is built off the spreadsheet anyway and contains incorrect coverage numbers.

**When it occurs:** Always — this is the default failure mode for any RTM that is not in version control with a per-PR check.

**How to avoid:** Move the RTM to CSV-in-Git with a CI job that runs `check_rtm.py` on every PR. The matrix becomes a code artifact: changes are reviewed, history is auditable, drift is detectable. The markdown rendering for Steerco is generated from the CSV, never hand-edited.

---

## Gotcha 5: Missing the Deferred / Dropped Column (or Hiding Those Rows)

**What happens:** Stakeholders drop a requirement. The team deletes the row "to keep the matrix clean." Six months later, the auditor asks "you scoped 200 requirements, you delivered 150 — where are the other 50?" There is no answer.

**When it occurs:** When the team treats the RTM as a "delivered scope" artifact instead of a "scope decision" artifact.

**How to avoid:** Dropped and deferred requirements are first-class rows. Status enum includes `Deferred` and `Dropped`. Each dropped row has a documented decision (owner + date + rationale) in a sibling decision log. The Steerco rollup explicitly counts dropped rows so leadership sees the cumulative scope decisions.

---

## Gotcha 6: Backlog Churn Outpaces RTM Updates

**What happens:** Aggressive sprint teams split, merge, and rename stories weekly. The story IDs in the RTM go stale within sprints. By release, the `story_ids` column is full of dead links to tickets that were closed without delivering, while the actual delivering tickets are not in the matrix.

**When it occurs:** Programs with high backlog churn — typically Agile-mature teams that refactor stories frequently.

**How to avoid:** Update the RTM at the end of every sprint, not at release gates. Better: write a CI job that diffs the agile tool's "completed in this sprint" list against the RTM and flags any story IDs in the matrix that do not exist in the tool. Best: treat the RTM update as part of the sprint Definition of Done.

---

## Gotcha 7: Multi-Valued Cells Use the Wrong Delimiter

**What happens:** Team uses commas to separate multiple story IDs in `story_ids`. The CSV parser treats them as separate columns. The matrix loads with shifted columns and silent data corruption.

**When it occurs:** When the RTM author uses a delimiter that conflicts with the CSV format.

**How to avoid:** Standardize on the pipe `|` delimiter for multi-valued cells. Document the convention in the file header or a `README.md` next to the CSV. The `check_rtm.py` script enforces it.

---

## Gotcha 8: Defects Raised Against Stories, Not Requirements

**What happens:** QA logs defects against user stories in Jira. The defect tracker links defect to story, but never to requirement. The RTM `defect_ids` column gets populated by hand-tracing defect → story → requirement, which is error-prone and frequently skipped.

**When it occurs:** When the defect tool is configured at the story level (the agile tool default) rather than the requirement level.

**How to avoid:** Configure the defect tracker so a defect can carry both a story link and a requirement link. Where that is not possible, run a nightly job that reads the defect tracker, follows defect → story → requirement, and writes the result to the RTM `defect_ids` column. Hand-tracing does not scale past sprint 3.
