# Examples — Agent Output Formats

## Example 1: Security team wants Excel from user-access-diff

**Context:** Team runs `user-access-diff` for a quarterly access review; wants to present findings in Excel to the compliance board.

**Solution:**

```bash
# Canonical deliverable already at:
#   docs/reports/user-access-diff/2026-04-17T21-14-05Z.md
#   docs/reports/user-access-diff/2026-04-17T21-14-05Z.json

# Extract findings -> CSV with jq
jq -r '.findings | (map(keys) | add | unique) as $keys |
       ($keys | @csv), (.[] | [.[$keys[]]] | @csv)' \
    docs/reports/user-access-diff/2026-04-17T21-14-05Z.json \
    > ~/access-review-q2.csv

# Open in Excel
open ~/access-review-q2.csv
```

**Why it works:** No new deps. Excel imports CSV natively. The spreadsheet header row carries the canonical `run_id` so the audit trail is preserved.

---

## Example 2: Compliance audit wants PDF from deployment-risk-scorer

**Context:** Change Advisory Board wants PDF reports attached to every pre-prod deployment.

**Solution:**

```bash
pandoc docs/reports/deployment-risk-scorer/2026-04-17T21-14-05Z.md \
    -o ~/Desktop/deploy-risk.pdf \
    --metadata title="Deployment Risk Score"
```

**Why it works:** pandoc is system-level, not project-level. One shell command. The PDF header references the release; the body is the canonical markdown rendered to PDF.

---

## Example 3: ServiceNow integration needs ticket payload

**Context:** Every `security-scanner` P0 finding should auto-create a ServiceNow change-request ticket.

**Solution:**

```bash
jq '{
    short_description: .summary,
    description: ("Run ID: " + .run_id + "\nFull report: " + .report_path),
    priority: (if .findings | any(.severity == "P0") then "1"
               elif .findings | any(.severity == "P1") then "2"
               else "3" end)
}' docs/reports/security-scanner/2026-04-17T21-14-05Z.json
```

Pipe that JSON into the ServiceNow REST API. No new tooling in the Salesforce project; the integration lives where it should (the team's ServiceNow tooling).

---

## Example 4: Notion page for the team wiki

**Context:** Admin team keeps a running page of the latest `waf-assessor` findings.

**Solution:** Open Notion, click `/`, select `Import`, pick the markdown file. Done.

**Why it works:** Notion, Obsidian, Confluence all accept markdown imports natively. The canonical `.md` file is the source.

---

## Anti-Pattern: Regenerating instead of converting

**What practitioners do:** Re-run `user-access-diff` with a prompt like "now give me the output as Excel."

**What goes wrong:** New LLM call = new output. The "Excel" version may differ from the previous markdown in subtle ways. No `run_id` thread to trace.

**Correct approach:** Always convert from the canonical pair. The `run_id` stays consistent.

---

## Anti-Pattern: Installing exceljs/openpyxl in the project

**What practitioners do:** `npm install exceljs` to generate Excel from agent output.

**What goes wrong:** Bloats the project with a conversion tool that has nothing to do with the project's domain. Next year, `exceljs` is abandoned; the project inherits dead deps.

**Correct approach:** `open file.csv` (Excel opens it). Or install `csv2xlsx` in `~/bin/` for shell use. Conversion tools live near you, not near the project.
