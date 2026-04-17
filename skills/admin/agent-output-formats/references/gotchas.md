# Gotchas — Agent Output Formats

Non-obvious behaviors when converting agent deliverables across formats.

## Gotcha 1: CSV breaks on embedded newlines in markdown tables

Markdown tables converted to CSV via pandoc preserve multi-line cells poorly. A finding's `recommendation` field containing a bulleted list becomes garbled. Fix: use `jq` against the JSON envelope (structured data) instead of pandoc against the markdown.

---

## Gotcha 2: Excel mangles long numeric IDs

A Salesforce 18-char ID starting with digits (e.g. `005...`) gets cast to scientific notation by Excel on CSV import. Fix: prefix the ID with an apostrophe in the CSV, or generate `.xlsx` directly with typed string columns.

---

## Gotcha 3: Pandoc PDF requires LaTeX on some systems

`pandoc foo.md -o foo.pdf` silently falls back to an error on systems without a LaTeX engine. Fix: `pandoc foo.md -o foo.html` is dependency-free; open the HTML in a browser and Save-as-PDF from there.

---

## Gotcha 4: Notion import strips frontmatter

If the markdown report has YAML frontmatter (run_id, date), Notion's importer throws it away. Fix: duplicate critical metadata (run_id at minimum) into the document body as the first line: `**Run ID:** <id>`.

---

## Gotcha 5: ServiceNow payload size limits

Large findings arrays (50+ items) can exceed ServiceNow's description field limit. Fix: include a link to the full report file and a summary in the description; don't dump the whole JSON.

---

## Gotcha 6: Windows path issues in jq one-liners

Backticks, single quotes, and shell escaping differ on Windows PowerShell. Fix: save the jq filter to a `.jq` file and reference it: `jq -f filter.jq report.json`.

---

## Gotcha 7: docs/reports/ gitignore shadowing

If a team adds `docs/reports/` to `.gitignore`, their bundle exports work locally but CI-generated reports disappear. Fix: commit `.gitkeep` files per agent, or use a dedicated output dir override (`--out ./build-reports/`) that IS committed.
