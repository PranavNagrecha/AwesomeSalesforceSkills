# Examples — Salesforce CLI Automation

## Example 1: Deploy with JSON and explicit org

**Context:** A bash release script must deploy metadata and exit non-zero if the deployment fails, without relying on human-readable tables.

**Problem:** Parsing stderr or table output breaks when the CLI rephrases messages or enables progress UI in CI logs.

**Solution:**

```bash
#!/usr/bin/env bash
set -euo pipefail
export SF_USE_PROGRESS_BAR=false

OUT=$(sf project deploy start \
  --source-dir force-app \
  --target-org "${SF_TARGET_ORG}" \
  --test-level RunLocalTests \
  --wait 60 \
  --json)

printf '%s\n' "$OUT" | python3 -c "import json,sys; p=json.load(sys.stdin); s=p.get('status',0); ok=(s in (0,'0') or p.get('result',{}).get('success') is True); sys.exit(0 if ok else 1)"
# Tighten the success predicate against the exact JSON shape your CLI version returns.
```

**Why it works:** `--json` returns a structured document described in the Salesforce CLI Reference; `--wait` keeps the process blocked until completion; `--target-org` removes default-alias ambiguity.

---

## Example 2: Apex tests with JUnit for dashboards

**Context:** CI uploads test results to a report viewer that consumes JUnit XML.

**Problem:** Human-readable test summaries do not integrate with `junit` report collectors.

**Solution:**

```bash
sf apex run test \
  --target-org "${SF_TARGET_ORG}" \
  --test-level RunLocalTests \
  --result-format junit \
  --output-dir ./test-results \
  --wait 45
```

**Why it works:** `--result-format` and `--output-dir` produce machine files the platform can archive; `--wait` ensures the job completes before the step ends.

---

## Anti-Pattern: Interactive login inside automation

**What practitioners do:** Copy a laptop workflow `sf org login web` into a CI job so “someone can approve in the browser.”

**What goes wrong:** Headless runners cannot complete a browser login; the job hangs or fails unpredictably.

**Correct approach:** Use JWT-based non-interactive auth (`sf org login jwt`) with secrets from the CI platform, as described in the Salesforce DX Developer Guide for CI scenarios, or reuse a runner-provisioned auth file that was created out-of-band securely.
