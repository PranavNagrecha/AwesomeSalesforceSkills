# LLM Anti-Patterns — Configuration Workbook Authoring

Common mistakes AI coding assistants make when generating or advising on
the Configuration Workbook. Each entry shows what the LLM tends to produce,
why it happens, the correct pattern, and how to detect the mistake.

---

## Anti-Pattern 1: Generates a workbook with no row schema (prose instead of rows)

**What the LLM generates:** A free-text document organized by paragraph
("First we'll add the Account Plan object. Then we'll set up the SDR
permission set group..."). No `row_id`, no `source_req_id`, no
`recommended_agent`.

**Why it happens:** "Configuration workbook" sounds like documentation; LLMs
default to prose because their training corpus is heavy on prose-style admin
docs.

**Correct pattern:**

```markdown
| row_id | section | target_value | owner | source_req_id | source_story_id | recommended_agent | recommended_skills | status | notes |
|---|---|---|---|---|---|---|---|---|---|
| CWB-OBJ-001 | Objects+Fields | New custom object `Account_Plan__c` … | A. Singh | FG-014 | US-2031 | object-designer | admin/object-creation-and-design | proposed | |
```

**Detection hint:** No pipe characters in the section bodies and no
`row_id` token anywhere → almost certainly prose-mode output. Run
`check_workbook.py` and watch the schema check fail.

---

## Anti-Pattern 2: Omits the `recommended_agent` field

**What the LLM generates:** A clean row schema *except* for the routing
column — the LLM treats `recommended_agent` as documentation and either
omits it or fills it with "admin team" or "TBD".

**Why it happens:** The agent-routing concept is repo-specific; LLMs default
to generic project-management language.

**Correct pattern:**

```markdown
| recommended_agent |
|---|
| object-designer |
```

The value must be a single agent name from the runtime roster (see
`agents/_shared/SKILL_MAP.md`).

**Detection hint:** Grep the workbook for `recommended_agent` column values
of `TBD`, `admin team`, `team`, `varies`, or empty cells. Cross-check every
populated value against the directory listing of `agents/`.

---

## Anti-Pattern 3: Hallucinates fields that aren't in the data model

**What the LLM generates:** Workbook rows that reference fields like
`Opportunity.Estimated_Close_Confidence_Score__c` when the org has no such
field, or that re-spec a standard field with a custom name (`Account.Industry__c`
instead of the standard `Account.Industry`).

**Why it happens:** LLMs pattern-match field names from training data
without grounding in the live org. If the prompt mentions "renewal
probability," the LLM invents a plausible-sounding API name.

**Correct pattern:** Probe the org first (or have the upstream
`object-designer` agent surface existing API names). Workbook rows for
**new** fields use API names that conform to
`templates/admin/naming-conventions.md` and are flagged as new in `notes`.
Workbook rows for **existing** fields use the verified API name.

**Detection hint:** Any `target_value` containing `__c` should be
cross-referenced against a target-org probe before sprint commit. The
checker can require an explicit `new: true` or `existing: <api_name>`
annotation in `notes`.

---

## Anti-Pattern 4: Omits the Permissions/PSG section

**What the LLM generates:** A workbook with sections for Objects+Fields,
Validation, Automation, and Reports — but no Profiles+Permission Sets+PSGs
section. Every change "just works."

**Why it happens:** Permission design is invisible in feature descriptions
("the SDR sees a new field" doesn't surface the PSG work). LLMs follow the
narrative.

**Correct pattern:** Always emit all 10 canonical sections. If a release has
no PS work, the PSG section carries one row with `target_value:
not-in-scope-this-release`. An empty section is information; a missing one
is a gap.

**Detection hint:** `check_workbook.py` enforces section count = 10. Missing
section headings cause a hard fail.

---

## Anti-Pattern 5: Conflates the workbook with the RTM

**What the LLM generates:** A document that mixes requirements rows with
configuration rows — `source_req_id` *is* the row, with `target_value`
collapsed into a "what we'll build" column. The RTM and the workbook end
up the same file.

**Why it happens:** Both artifacts are tabular; LLMs collapse them when the
prompt isn't explicit about the separation.

**Correct pattern:** The workbook *consumes* the RTM via `source_req_id`,
but it is its own file with its own schema. RTM rows are
"capability-level"; workbook rows are "configurable-artifact-level." A
single RTM row often spawns multiple workbook rows across multiple
sections.

**Detection hint:** If the file's primary key is `req_id` rather than
`row_id`, it's an RTM, not a workbook.

---

## Anti-Pattern 6: Generates "epic" rows instead of atomic rows

**What the LLM generates:** A row whose `target_value` reads "Build the
renewal forecast feature" or "Set up the Tier 2 Support persona" — a
multi-paragraph description that hides three or four configurable changes.

**Why it happens:** Feature-level descriptions are how stakeholders talk;
LLMs preserve that grain in the output.

**Correct pattern:** Decompose to one row per configurable artifact (one
field, one VR, one Flow trigger, one PSG composition step). A "feature row"
is a smell — split it before committing.

**Detection hint:** Any `target_value` longer than ~200 characters or
containing the words "and", "plus", or "also" more than once is suspect.
Reviewers should split or reject.

---

## Anti-Pattern 7: Treats `status` as freeform

**What the LLM generates:** Status values like `WIP`, `Doing`, `?`, `next
sprint`, or empty cells. The schema's enum is silently broken.

**Why it happens:** LLMs pattern-match to Kanban boards, not to the
workbook's specific lifecycle.

**Correct pattern:** Status values must be from the closed enum: `proposed`,
`committed`, `in-progress`, `executed`, `verified`, `change-requested`.
Anything else is rejected.

**Detection hint:** `check_workbook.py` validates the enum and flags
`TBD`, `TODO`, `?`, `WIP`, or empty cells.
