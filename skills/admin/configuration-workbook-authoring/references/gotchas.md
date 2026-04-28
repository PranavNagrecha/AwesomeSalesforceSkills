# Gotchas — Configuration Workbook Authoring

Non-obvious failure modes that turn a workbook from a delivery instrument
into a graveyard.

---

## Gotcha 1: The workbook becomes a wiki nobody maintains

**What happens:** The workbook gets authored at sprint kickoff, lives in
Notion or a Confluence page, and is never updated again. By mid-sprint the
admin team is working off Slack threads and the workbook is stale.

**When it occurs:** Whenever the workbook is treated as a *one-time*
deliverable rather than the canonical sprint instrument.

**How to avoid:** Version-lock the workbook in the repo at sprint commit
(`docs/workbooks/<release>/cwb.md`). After commit, every change is a *new*
row, not an edit-in-place. CI runs `python3 scripts/check_workbook.py` on
every PR that touches the file.

---

## Gotcha 2: Rows that span multiple sections

**What happens:** A single row reads "Add Account Plan object, give the SDR
PSG access, and trigger a notification flow on insert." That row touches
three sections (Objects+Fields, Permission Sets+PSGs, Automation) and would
need to be addressed by three different agents.

**When it occurs:** When the row author thinks in features rather than in
configurable artifacts.

**How to avoid:** Enforce **one row, one agent, one section**. If a row's
content needs more than one `recommended_agent`, split it. The split rows
share the same `source_story_id` and `source_req_id`; cross-row dependencies
go in `notes`.

---

## Gotcha 3: Missing `source_req_id` produces orphan rows

**What happens:** A row appears in the workbook with no fit-gap reference. By
the time release notes are written, nobody can explain why the field exists.

**When it occurs:** When the admin team adds "obvious" rows during build
without going back to the BA. Or when the BA forgot to open a fit-gap row.

**How to avoid:** Hard rule — every row must carry both `source_req_id` and
`source_story_id`. Reviewers reject orphan rows; `check_workbook.py` flags
them. If a real configurable change has no fit-gap row, the workflow stops
and the BA opens one before the workbook row is written.

---

## Gotcha 4: The workbook drifts from org reality (no version-lock)

**What happens:** The team re-runs the workbook generator midway through the
sprint, picking up new rows and silently losing rows that were already
deployed. The post-sprint audit finds metadata in the org with no
corresponding workbook row.

**When it occurs:** When the workbook is regenerated rather than amended, or
when authors edit existing rows in place after sprint commit.

**How to avoid:** The committed workbook is **immutable**. Mid-sprint change
requests open new rows with `status: change-requested` and reference the
superseded row in `notes`. Old rows stay; their `target_value` is preserved
as historical record. Tag the file at sprint commit so reverts are possible.

---

## Gotcha 5: The workbook is "just notes" with no schema

**What happens:** Someone authors a freeform document with prose like "We
need a few new fields on Opportunity, plus the SDR PSG, plus probably a
Flow." There are no rows, no IDs, no owners, no agents.

**When it occurs:** When a project skips the schema because it feels like
overkill for a small feature.

**How to avoid:** Even a one-row workbook uses the canonical row schema. The
overhead is trivial; the audit value is enormous. Generic templates live in
`templates/config-workbook.md` — copy and fill, never freestyle.

---

## Gotcha 6: The Integrations section is omitted

**What happens:** The team writes the first 9 sections, deploys, and then
discovers a fit-gap row required a new Named Credential and Connected App.
The integration team is angry; the workbook silently dropped their work.

**When it occurs:** When the workbook author treats Integrations as
"something the integration team owns separately."

**How to avoid:** The Integrations section is **always present**. If the
release truly has no integration work, the section carries a single row
labeled `not-in-scope-this-release` with that as `target_value` and the
release manager as owner. An empty section is information; a missing one is
a gap.

---

## Gotcha 7: Inline credentials in `target_value`

**What happens:** A row's `target_value` reads "Connect to API at
https://api.example.com with key sk_live_…". The workbook is committed to
git. Now the secret is in version control forever.

**When it occurs:** When an author copies the integration spec verbatim and
forgets to substitute Named Credential aliases for raw secrets.

**How to avoid:** Workbook rows reference Named Credentials by alias only
(e.g. `target_value: "Use Named Credential alias 'AcmeBilling_API'"`). The
checker greps for raw secret patterns; reviewers reject any row with an
inline secret regardless of how the row got committed.

---

## Gotcha 8: `recommended_agent` references an invented or deprecated agent

**What happens:** A row's `recommended_agent` says `data-loader-agent`, which
isn't a real agent in the runtime roster. The hand-off step silently fails or
gets routed to a human who doesn't know what to do.

**When it occurs:** When the author writes the agent name from memory rather
than checking `agents/_shared/SKILL_MAP.md`.

**How to avoid:** `check_workbook.py` validates every `recommended_agent`
value against the live runtime roster (read from `agents/_shared/SKILL_MAP.md`
plus the `agents/<name>/AGENT.md` directory listing). Deprecated agents (e.g.
`validation-rule-auditor` superseded by `audit-router --domain
validation_rule`) are flagged with a hint pointing to the replacement.
