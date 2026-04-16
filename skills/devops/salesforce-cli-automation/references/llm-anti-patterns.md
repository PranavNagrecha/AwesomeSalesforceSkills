# LLM Anti-Patterns — Salesforce CLI Automation

Common mistakes AI coding assistants make when generating or advising on Salesforce CLI automation.

## Anti-Pattern 1: Emitting `sfdx force:source:deploy` in new scripts

**What the LLM generates:** `sfdx force:source:deploy -p force-app -u myorg`

**Why it happens:** Training data predates CLI v2 consolidation; older blog posts and Stack Overflow answers still show `sfdx force:*`.

**Correct pattern:**

```bash
sf project deploy start --source-dir force-app --target-org myorg --wait 30
```

**Detection hint:** Regex `\bsfdx\s+force:` in proposed shell or YAML.

---

## Anti-Pattern 2: Omitting `--wait` on `sf apex run test` in CI

**What the LLM generates:** `sf apex run test --test-level RunLocalTests --target-org ciOrg` with no `--wait` or async follow-up.

**Why it happens:** The command is treated like a synchronous local tool; the model forgets server-side test execution continues after the CLI returns.

**Correct pattern:**

```bash
sf apex run test --test-level RunLocalTests --target-org ciOrg --wait 45 \
  --result-format junit --output-dir ./results
```

**Detection hint:** Line contains `sf apex run test` and the next several lines lack `--wait`, `--synchronous`, or documented async polling.

---

## Anti-Pattern 3: Parsing human tables instead of `--json`

**What the LLM generates:** `sf project deploy start ... | grep Deployed` or instructions to “look for Succeeded in the output.”

**Why it happens:** Human summaries look definitive; models favor simple grep over JSON parsing.

**Correct pattern:**

```bash
sf project deploy start ... --json > deploy.json
# parse deploy.json with jq or python -c json.load
```

**Detection hint:** Pipelines chain `sf` to `grep`/`awk` on stdout without `--json` or `--result-format`.

---

## Anti-Pattern 4: Using `sf org login web` inside CI YAML

**What the LLM generates:** A GitHub Actions step that runs `sf org login web` and tells the user to “complete login in the browser.”

**Why it happens:** The web flow is the easiest local mental model; CI headlessness is under-specified in the prompt.

**Correct pattern:** Document `sf org login jwt` (or equivalent non-interactive flow) with secrets injected by the CI platform, per Salesforce DX Developer Guide CI guidance.

**Detection hint:** `login web` appears inside `.github/workflows`, `.gitlab-ci.yml`, `Jenkinsfile`, or `bitbucket-pipelines.yml`.

---

## Anti-Pattern 5: Ignoring `--target-org` because “developers already set the default”

**What the LLM generates:** Long scripts of `sf` commands with no `--target-org`, assuming `sf config set target-org` ran earlier.

**Why it happens:** Local developer workflows rely on defaults; shared automation inherits that shortcut.

**Correct pattern:** Pass `--target-org "$SF_TARGET_ORG"` on every mutating command, or export `SF_TARGET_ORG` only if your standardized wrapper enforces it uniformly.

**Detection hint:** Multiple `sf project` or `sf data` lines and none include `--target-org`.

---

## Anti-Pattern 6: Claiming `--code-coverage` enforces a coverage threshold

**What the LLM generates:** “Add `--code-coverage` so the build fails below 75%.”

**Why it happens:** The flag name sounds like enforcement; models conflate collection with gating.

**Correct pattern:** Collect coverage with `--code-coverage` and implement an explicit threshold check (custom script or documented CI pattern) as covered in `devops/continuous-integration-testing`.

**Detection hint:** Assertions that coverage thresholds are satisfied by the flag alone, with no follow-on validation step.
