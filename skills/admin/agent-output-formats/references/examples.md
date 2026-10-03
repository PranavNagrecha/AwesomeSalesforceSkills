# Examples — Agent Output Formats

## Example 1: Security team wants Excel from user-access-diff

**Context:** Team runs `user-access-diff` for a quarterly access review; wants to present findings in Excel to the compliance board.

**Solution:**

```bash
# Canonical deliverable already at:
#   docs/reports/user-access-diff/2026-04-17T21-14-05Z.md
#   docs/reports/user-access-diff/2026-04-17T21-14-05Z.json

# Extract findings -> CSV with jq (filter file from Example 5; the earlier inline
# filter failed with "object ... is not valid in a csv row" on findings with evidence)
jq -r -f ~/bin/agent-output/findings-to-csv.jq \
    docs/reports/user-access-diff/2026-04-17T21-14-05Z.json \
    > ~/access-review-q2.csv

# Open in Excel
open ~/access-review-q2.csv
```

**Why it works:** No new deps. Excel imports CSV natively. Every row carries the canonical `run_id` column, so the audit trail is preserved.

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
    priority: (if (.findings // []) | any(.severity == "P0") then "1"
               elif (.findings // []) | any(.severity == "P1") then "2"
               else "3" end)
}' docs/reports/security-scanner/2026-04-17T21-14-05Z.json
```

Pipe that JSON into the ServiceNow REST API. No new tooling in the Salesforce project; the integration lives where it should (the team's ServiceNow tooling).

---

## Example 4: Notion page for the team wiki

**Context:** Admin team keeps a running page of the latest `waf-assessor` findings.

**Solution:** Open Notion, click `/`, select `Import`, pick the markdown file. Put `**Run ID:** <run_id>` as the first line of the page. UNVERIFIED (2026-10-03): the Notion import steps and whether frontmatter survives were not checked against Notion documentation.

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

---

## Example 5: A Tested, Dependency-Free Conversion Kit For Any Agent Envelope

**Context:** A compliance team receives `user-access-diff`, `security-scanner`, and builder-agent envelopes and wants CSV and Excel for each, with findings and coverage, without adding anything to the Salesforce project. The kit lives outside the project, in `~/bin/agent-output/`. It was run on 2026-10-03 with jq 1.7.1 and LibreOffice against two schema-shaped envelopes: one with findings that carry `evidence` objects and a `dimensions_skipped` entry, one with `deliverables[]` and no `findings`.

`~/bin/agent-output/findings-to-csv.jq`:

```text
# One CSV row per finding, run_id in every row.
# Nested values (evidence objects, arrays) become JSON text so @csv accepts them.
.run_id as $run
| (.findings // []) as $f
| (["run_id","id","severity","title","detail","recommendation","evidence"] | @csv),
  ($f[] | [$run, .id, .severity, .title, .detail, .recommendation, .evidence]
        | map(if type == "object" or type == "array" then tojson else . end)
        | @csv)
```

`~/bin/agent-output/coverage-to-csv.jq`:

```text
# What the run covered and what it did not (Deliverable Contract, multi-dimensional rule).
.run_id as $run
| (["run_id","dimension","coverage","state","reason","confidence_impact"] | @csv),
  ((.dimensions_compared // [])[] | [$run, ., "compared", "", "", ""] | @csv),
  ((.dimensions_skipped // [])[] | [$run, .dimension, "skipped", .state, .reason, (.confidence_impact // "")] | @csv)
```

`~/bin/agent-output/convert.sh`:

```bash
#!/usr/bin/env bash
# convert.sh <envelope.json> [out-dir]
# Converts a canonical SfSkills agent envelope to CSV (and XLSX when LibreOffice is
# installed) without touching the canonical files. Requires jq; soffice is optional.
set -euo pipefail
ENV="${1:?usage: convert.sh <envelope.json> [out-dir]}"
OUT="${2:-$HOME/agent-exports}"
HERE="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$OUT"

RUN_ID="$(jq -r '.run_id' "$ENV")"
AGENT="$(jq -r '.agent' "$ENV")"
STEM="$OUT/${AGENT}_${RUN_ID}"

jq -r -f "$HERE/findings-to-csv.jq" "$ENV" > "${STEM}_findings.csv"
jq -r -f "$HERE/coverage-to-csv.jq" "$ENV" > "${STEM}_coverage.csv"

if command -v soffice >/dev/null 2>&1; then
  soffice --headless --convert-to xlsx --outdir "$OUT" "${STEM}_findings.csv" "${STEM}_coverage.csv" >/dev/null
fi

echo "run_id=${RUN_ID} confidence=$(jq -r '.confidence' "$ENV")"
ls -1 "${STEM}"_*
```

Run it:

```bash
chmod +x ~/bin/agent-output/convert.sh
~/bin/agent-output/convert.sh docs/reports/user-access-diff/2026-04-17T21-14-05Z.json
# run_id=2026-04-17T21-14-05Z confidence=MEDIUM
# ~/agent-exports/user-access-diff_2026-04-17T21-14-05Z_coverage.csv
# ~/agent-exports/user-access-diff_2026-04-17T21-14-05Z_coverage.xlsx
# ~/agent-exports/user-access-diff_2026-04-17T21-14-05Z_findings.csv
# ~/agent-exports/user-access-diff_2026-04-17T21-14-05Z_findings.xlsx
```

What the test showed: a two-line `detail` stayed in one cell in the XLSX, the `evidence` object arrived as JSON text, an 18-character Id inside it stayed text, and the deliverables-only envelope produced a header row instead of an error. `soffice --convert-to <extension> --outdir <dir>` is documented in LibreOffice Help, Starting LibreOffice Software With Parameters. This topic produces no Salesforce metadata, so there is no `package.xml` member.

**Why it works:** the filters follow the envelope schema rather than one sample (nested objects, optional arrays), the coverage sheet keeps the contract's skipped dimensions visible, every row carries `run_id`, and the kit installs nothing into the project.

