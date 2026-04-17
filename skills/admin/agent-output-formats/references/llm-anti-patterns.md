# LLM Anti-Patterns — Agent Output Formats

Common mistakes AI coding assistants make when generating or advising on Agent Output Formats.

## Anti-Pattern 1: Regenerating instead of converting

**What the LLM generates:** "Let me re-run the agent with the output format as Excel."

**Why it happens:** LLMs treat different output formats as different prompts.

**Correct pattern:** Always convert from the canonical pair (`docs/reports/<id>/<run_id>.{md,json}`). The `run_id` stays consistent; the LLM output doesn't drift.

---

## Anti-Pattern 2: Installing conversion libraries into the project

**What the LLM generates:** `npm install exceljs` or `pip install openpyxl` inside the user's project.

**Why it happens:** LLMs default to "install what you need where you're working."

**Correct pattern:** Conversion tools live in `~/bin/` or as system-level installs. They don't belong in the project that consumes the agent.

---

## Anti-Pattern 3: Stripping run_id during conversion

**What the LLM generates:** Excel export that just has the findings table, no header referencing the run.

**Why it happens:** LLMs focus on the "content" and drop metadata.

**Correct pattern:** Every converted artifact references the canonical `run_id` somewhere — header row, filename, sheet title.

---

## Anti-Pattern 4: Adding output formats to the AGENT.md

**What the LLM generates:** Edits the agent spec to add "also supports Excel output" as a native format.

**Why it happens:** LLMs solve "user asked for Excel" by changing the agent.

**Correct pattern:** Agent natively emits markdown + JSON. Anything else is downstream conversion. The AGENT.md stays stable.

---

## Anti-Pattern 5: Hallucinating jq filters

**What the LLM generates:** Complex jq filters that reference fields not in the envelope.

**Why it happens:** LLMs pattern-match on jq syntax without checking the actual envelope schema.

**Correct pattern:** Before writing a jq filter, read `output-envelope.schema.json` (or the actual JSON file) to confirm field names.

---

## Anti-Pattern 6: Bulk-converting and deleting canonical files

**What the LLM generates:** Converts all reports to PDFs and removes the markdown originals.

**Why it happens:** LLMs treat conversion as replacement.

**Correct pattern:** Always preserve the canonical markdown + JSON pair. Converted artifacts are additive.

---

## Anti-Pattern 7: One Excel sheet per field

**What the LLM generates:** An Excel workbook with 20 sheets, one per envelope field, making it unreadable.

**Why it happens:** LLMs flatten structured JSON mechanically.

**Correct pattern:** Flatten only the `findings[]` array to a sheet; keep metadata (run_id, confidence, summary) as a header block on the same sheet. One sheet unless there's a strong structural reason for more.
