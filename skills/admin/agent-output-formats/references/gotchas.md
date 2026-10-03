# Gotchas: Agent Output Formats

Non-obvious behaviours when converting a SfSkills agent deliverable (markdown report plus JSON envelope) into other formats. Each gotcha names its source. Claims that could not be confirmed from a fetched source carry an inline `UNVERIFIED (2026-10-03):` marker. "Deliverable Contract" means `agents/_shared/DELIVERABLE_CONTRACT.md` and "Envelope Schema" means `agents/_shared/schemas/output-envelope.schema.json` in this repository; "jq Manual" means https://jqlang.github.io/jq/manual/ (jq 1.7). The jq commands in this file were run against a schema-shaped sample envelope on 2026-10-03 with jq 1.7.1.

---

## Gotcha 1: `@csv` Rejects Objects, So The Usual "Findings To CSV" One-Liner Fails On Real Envelopes

**What happens:** The schema lets every finding carry `evidence`, which is an object. jq's `@csv` requires an array of scalars, so the generic filter `(.[] | [.[$keys[]]] | @csv)` stops with `object (...) is not valid in a csv row` (exit 5) at the first finding that has evidence. This skill's earlier Pattern 2 and Example 1 used exactly that filter.

**When it occurs:** Any envelope whose findings include `evidence`, and any array-valued field.

**How to avoid:** Name the columns and serialise nested values: `map(if type == "object" or type == "array" then tojson else . end) | @csv`. Keep the filter in a file (`findings-to-csv.jq`, Example 5 in `references/examples.md`).

**Source:** Envelope Schema, `findings.items.properties.evidence` (`"type": "object"`). jq Manual, Format strings and escaping (`@csv`: "The input must be an array"); Convert to/from JSON (`tojson`).

---

## Gotcha 2: Filters That Assume `findings` Exists Break On Deliverables-Only Agents

**What happens:** `findings` is optional; some agents emit `deliverables[]` instead. A filter such as `.findings | any(.severity == "P0")` fails with `Cannot iterate over null` on those envelopes, so a ServiceNow or Jira pipeline stops for a whole class of agents.

**When it occurs:** Shared conversion scripts run across several agents, such as builders that emit metadata XML in `deliverables[]`.

**How to avoid:** Default missing arrays with the alternative operator: `(.findings // [])`, `(.dimensions_skipped // [])`. Test each filter against one findings envelope and one deliverables envelope.

**Source:** Envelope Schema (`findings` is optional because "some agents emit pure documents via `deliverables[]` instead"; required fields list). jq Manual, Alternative operator `//` (produces the right-hand side when the left is `null` or `false`).

---

## Gotcha 3: Converting Only Findings Hides What The Run Did Not Cover

**What happens:** A spreadsheet of findings looks like a complete review. The contract makes multi-dimensional agents list every partially covered dimension in `dimensions_skipped` with a `state` of `count-only`, `partial`, or `not-run`, and caps confidence when any are present. Dropping those rows recreates the failure the contract was written to stop: a count-only dimension that looks covered.

**When it occurs:** Excel exports of `user-access-diff` and other multi-dimensional agents for compliance reviewers.

**How to avoid:** Export coverage next to findings (a coverage sheet with `dimensions_compared` and `dimensions_skipped`), and put `confidence` and `run_id` in the header of every converted artifact.

**Source:** Deliverable Contract, section on multi-dimensional agents (the stricter rule: enumeration of skipped dimensions, `state` values, confidence impact rule; "The count-only case is what burned us"). Envelope Schema, `dimensions_skipped` (required `dimension`, `reason`, `state`).

---

## Gotcha 4: CSV From Markdown Tables Loses Multi-Line Cells

**What happens:** A finding's `recommendation` or `detail` contains a line break or a list. Extracted from the rendered markdown table, the text is flattened or split across rows. RFC 4180 requires fields with line breaks, double quotes, or commas to be enclosed in double quotes, which markdown tables never carry.

**When it occurs:** Converting the `.md` report instead of the `.json` envelope.

**How to avoid:** Build CSV from the JSON envelope with jq, whose `@csv` quotes strings and doubles embedded quotes. A multi-line `detail` exported this way stayed in one cell after conversion to XLSX with LibreOffice in the 2026-10-03 test.

**Source:** RFC 4180 (https://www.rfc-editor.org/rfc/rfc4180.txt), section 2 rules 6 and 7. jq Manual, `@csv` ("rendered as CSV with double quotes for strings, and quotes escaped by repetition").

---

## Gotcha 5: Spreadsheets Change Long Numbers And Ignore Id Case

**What happens:** All-digit values longer than 15 digits lose precision in Excel ("Number precision 15 digits"), and leading zeros can be dropped from numeric-looking text. Salesforce Ids are a different problem: 15-character Ids are case-sensitive, while 18-character Ids are case-insensitive, so matching 15-character Ids in a spreadsheet needs a case-sensitive comparison such as `EXACT`. UNVERIFIED (2026-10-03): the earlier claim that an Id beginning with `005` is cast to scientific notation; Ids contain letters, so they are text, and the 15-digit limit applies to numeric values. UNVERIFIED (2026-10-03): that VLOOKUP and MATCH compare case-insensitively was not confirmed in a fetched Microsoft page.

**When it occurs:** Exports that carry numeric external Ids, phone numbers, or 15-character Salesforce Ids used as join keys.

**How to avoid:** Prefer 18-character Ids in exports. Keep numeric identifiers as quoted strings in the CSV, or import them as text columns. Use `EXACT` when comparing 15-character Ids.

**Source:** Microsoft Support, Excel specifications and limits (https://support.microsoft.com/en-us/office/excel-specifications-and-limits-1672b34d-7043-467e-8e27-269d656771c3: "Number precision 15 digits"); EXACT function (https://support.microsoft.com/en-us/office/exact-function-d3087698-fc15-4a15-9631-12575cf29926: "EXACT is case-sensitive"). Einstein Discovery REST API Developer Guide, local corpus `knowledge/imports/bi-dev-guide-rest-sdd.md`, Org and Object Identifiers (15-character Ids "case-sensitive"; 18-character "case-insensitive").

---

## Gotcha 6: Excel Truncates Long Cells And Caps Rows

**What happens:** `detail`, `recommendation`, or a deliverable's `content` (metadata XML, Apex) longer than 32,767 characters does not fit in one Excel cell, and a findings array longer than 1,048,576 rows does not fit on one sheet.

**When it occurs:** Builder agents whose `deliverables[].content` holds whole files, and very large diff runs.

**How to avoid:** Leave `content` out of spreadsheets and link to the canonical report instead. Split very large runs across sheets or deliver CSV only.

**Source:** Microsoft Support, Excel specifications and limits ("Total number of characters that a cell can contain 32,767 characters"; "1,048,576 rows by 16,384 columns"). Envelope Schema, `deliverables.items.properties.content` (`string`, no length limit).

---

## Gotcha 7: Pandoc PDF Needs A LaTeX Engine Unless You Choose Another One

**What happens:** `pandoc report.md -o report.pdf` fails on machines without LaTeX: "By default, pandoc will use LaTeX to create the PDF, which requires that a LaTeX engine be installed." (Corrected wording: it errors; it does not "silently fall back.")

**When it occurs:** Laptops and CI runners without a TeX distribution.

**How to avoid:** Use `--pdf-engine` with an engine that is installed (the manual lists ConTeXt, roff ms, and HTML-based engines), or convert to HTML (`pandoc report.md -o report.html`) and print to PDF from a browser.

**Source:** Pandoc User's Guide (https://pandoc.org/MANUAL.html), Creating a PDF and `--pdf-engine`.

---

## Gotcha 8: Shell Quoting Differs By Platform; Put jq Filters In Files

**What happens:** Multi-line jq filters with single quotes and `$` variables break in Windows PowerShell and in some CI shells.

**When it occurs:** Copying the one-liners in this skill onto Windows or into YAML pipeline steps.

**How to avoid:** Save filters as `.jq` files and run `jq -r -f findings-to-csv.jq envelope.json`.

**Source:** jq Manual, Invoking jq (`-f` / `--from-file`: "Read the filter from a file rather than from a command line").

---

## Gotcha 9: Moving Reports Out Of Version Control Must Use The Contract's Override

**What happens:** A team adds `docs/reports/` to `.gitignore`; reports work locally but CI-generated reports disappear and reviewers cannot trace a converted file back to its run. The contract says the default `docs/reports/` "IS tracked by convention" and that consumers who want reports untracked should override the output path per invocation and ignore that path instead. (Corrected: the earlier `--out ./build-reports/` flag is not part of the contract; overrides are stated in the invocation, for example "Run user-access-diff with output path ./my-reports/".)

**When it occurs:** Teams tidying their repository, and CI jobs that run agents.

**How to avoid:** Keep `docs/reports/` tracked, or use the per-invocation path override and ignore only that path. Write converted files outside the canonical folder so a clean-up never deletes the source pair.

**Source:** Deliverable Contract, "Persistence path override" and "Atomic write rule".

---

## Gotcha 10: Import Behaviour Of Notion And ServiceNow Is Not Documented Here

**What happens:** Two earlier claims in this skill could not be confirmed. UNVERIFIED (2026-10-03): that Notion's markdown importer discards YAML frontmatter, so `run_id` must be repeated in the body. UNVERIFIED (2026-10-03): that ServiceNow's description field has a size limit that a 50-finding payload exceeds.

**When it occurs:** Wiki imports and ticket integrations.

**How to avoid:** Put `**Run ID:** <run_id>` as the first line of any imported page regardless, and send a summary plus a link to the report rather than the whole envelope to ticketing systems. Test one import before automating.

**Source:** None confirmed; Notion and ServiceNow documentation were not fetched for this revision.
