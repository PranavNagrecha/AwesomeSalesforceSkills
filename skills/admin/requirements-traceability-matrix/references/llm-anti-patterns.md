# LLM Anti-Patterns — Requirements Traceability Matrix

Common mistakes AI assistants make when generating or maintaining an RTM. These help the consuming agent self-check its own output.

---

## Anti-Pattern 1: Generating an RTM Without Stable IDs

**What the LLM generates:** A markdown table with columns like `Requirement | Story | Test | Status` where each cell holds a free-text description ("As a sales rep I want..." / "Validate auto-assignment"). No `req_id`, `US-XXX`, or `TC-XXX`.

**Why it happens:** The LLM optimizes for human readability and treats the description as the primary key. It mirrors the style of generic project-management blog posts that show RTM screenshots without IDs.

**Correct pattern:**

```csv
req_id,description,story_ids,test_case_ids,status
REQ-001,Sales reps see only their accounts on My Accounts list view,US-101,TC-201,Released
REQ-002,Lead conversion creates Opportunity with Stage = Prospecting,US-102,TC-202|TC-203,Released
```

**Detection hint:** If the matrix has no column matching the regex `(req|us|tc|def|bug)[-_]?\d+`, IDs are missing. Also: if the table has fewer than 8 columns, it is likely missing the canonical column set.

---

## Anti-Pattern 2: Assuming 1:1 Requirement-to-Story Cardinality

**What the LLM generates:** An RTM with one row per requirement, one cell per story, and the explanation "each requirement maps to one story." The LLM then puts a single ID in `story_ids` even when the underlying requirement clearly needs multiple stories.

**Why it happens:** The LLM treats "requirement" and "story" as synonyms. Generic agile guides do not emphasize the 1:N split that complex Salesforce requirements demand.

**Correct pattern:**

```
REQ-006,sow,Account auto-assigns to territory based on State + Industry,must,US-114|US-115|US-116,...
```
With pipe-delimited multiple story IDs when a requirement decomposes (queue setup + assignment rule + escalation, etc.).

**Detection hint:** If `story_ids` cells in the generated RTM never contain a `|` delimiter, the LLM probably forced 1:1 cardinality. For a 10+ requirement project, expect at least 20-30% of rows to have multi-valued story cells.

---

## Anti-Pattern 3: Omitting the Source Column

**What the LLM generates:** A 6-column RTM (`req_id, description, story_ids, test_case_ids, defect_ids, status`) with no column distinguishing where each requirement came from.

**Why it happens:** Generic RTM templates online often omit the source column because they target non-regulated projects. The LLM picks up the simpler shape.

**Correct pattern:** Include `source` with enum values `interview / sow / regulatory / change-request / defect-driven`. The source column is what lets Steerco answer "how much of our scope is regulatory vs elicited" and what lets auditors filter to regulatory-only rows.

**Detection hint:** Search the generated RTM headers for `source`, `origin`, or `category`. If none are present, the source column is missing.

---

## Anti-Pattern 4: Marking Everything "In Progress"

**What the LLM generates:** Sample RTM where every row's status is `In Progress` or `Active`, regardless of where the requirement actually is in the lifecycle. Released rows, deferred rows, draft rows all show the same status.

**Why it happens:** "In Progress" is a generic placeholder the LLM uses when it has no information about lifecycle state. Without the explicit enum (`Draft / In Build / In UAT / Released / Deferred / Dropped`), it defaults to a generic value.

**Correct pattern:** Always use the canonical enum. Each row's status reflects its real position in the delivery flow:

- `Draft` — requirement captured, no stories yet
- `In Build` — stories written, development underway
- `In UAT` — code complete, testing in progress
- `Released` — deployed to production
- `Deferred` — agreed to be done in a later release
- `Dropped` — agreed to not be done at all

**Detection hint:** If every row's status column has the same value, or any row's status is not in the enum, the LLM picked a placeholder.

---

## Anti-Pattern 5: Not Treating Dropped Requirements as Rows

**What the LLM generates:** When asked "show me the RTM for a project where we dropped 3 requirements," the LLM produces an RTM with the remaining requirements only and notes "3 requirements were dropped" in a separate paragraph.

**Why it happens:** The LLM treats the RTM as a "delivered scope" artifact. It does not realize that dropped requirements are first-class rows that the audit trail explicitly needs.

**Correct pattern:** Every dropped requirement keeps its row with status `Dropped` and a documented decision (owner + date + rationale) elsewhere. The RTM tells the full scope story including subtractions.

**Detection hint:** Count the rows in the generated RTM and compare to the total scope mentioned in the prompt. If the prompt says "20 requirements scoped, 3 dropped" and the RTM has 17 rows, the dropped ones are missing.

---

## Anti-Pattern 6: Hallucinating Test Case IDs That Do Not Exist

**What the LLM generates:** When the user asks for a sample RTM, the LLM invents plausible test case IDs (`TC-201`, `TC-202`, etc.) and inserts them into `test_case_ids` cells without confirming the user actually has those test cases authored.

**Why it happens:** The LLM treats sample data and real data as interchangeable for the purpose of producing a complete-looking matrix. In a real RTM, this introduces ghost test references that do not resolve in the test management tool.

**Correct pattern:** When generating a real RTM (not a sample), the LLM must either (a) ask the user for the actual test case IDs from their tool, or (b) leave `test_case_ids` blank and flag the requirement for test-case authoring. Made-up IDs are worse than blank cells because they pass surface-level coverage checks while breaking traceability.

**Detection hint:** When the LLM asserts test case IDs without the user having provided them, ask for the source. If the source is "I generated reasonable test IDs," the IDs are hallucinated.

---

## Anti-Pattern 7: Confusing Forward and Backward Traceability

**What the LLM generates:** An RTM that supports only `req → story → test` linkage and asserts that backward traceability is "the same matrix read in reverse."

**Why it happens:** Forward traceability is intuitive; backward traceability requires understanding that not every test should trace back to a requirement (regression tests are the exception) and that the matrix needs an explicit backward sample at audit time.

**Correct pattern:** Forward traceability is "every requirement has a story and a test." Backward traceability is "every test case in the test inventory either appears in some requirement row's `test_case_ids` cell or is explicitly tagged as a regression / non-functional test." The two checks have different sample populations.

**Detection hint:** If the LLM equates the two directions or claims one is a "view" of the other, the conceptual gap is present.
