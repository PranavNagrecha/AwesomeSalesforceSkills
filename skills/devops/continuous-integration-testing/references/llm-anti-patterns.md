# LLM Anti-Patterns — Continuous Integration Testing

Common mistakes AI coding assistants make when generating or advising on Continuous Integration Testing.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Assuming `--code-coverage` Enforces a Threshold

**What the LLM generates:** A pipeline script that runs `sf apex run test --code-coverage` and treats a zero exit code as proof that coverage is sufficient, with no additional parsing or threshold check.

**Why it happens:** LLMs conflate "collect coverage" with "enforce coverage." The flag name `--code-coverage` sounds like it applies a gate, and training data often shows the flag without the subsequent enforcement script.

**Correct pattern:**

```bash
# --code-coverage collects data but does NOT enforce a threshold
sf apex run test --test-level RunLocalTests --code-coverage \
  --result-format json --output-dir ./results --wait 30

# You must parse and enforce the threshold yourself
python3 scripts/check_coverage.py --results-dir ./results --min-coverage 80
```

**Detection hint:** Look for `--code-coverage` without a subsequent script that parses coverage percentages and exits non-zero on failure.

---

## Anti-Pattern 2: Using `RunAllTestsInOrg` as the Default

**What the LLM generates:** Pipeline YAML with `--test-level RunAllTestsInOrg` as the standard test level for every deployment, described as "the most thorough option."

**Why it happens:** LLMs default to the most comprehensive-sounding option. "Run all tests" reads as best practice to a model that lacks context about managed package test failures and org-specific flakiness.

**Correct pattern:**

```yaml
# Use RunLocalTests to skip uncontrollable managed package tests
- run: sf project deploy start --test-level RunLocalTests --target-org prod --wait 60
```

**Detection hint:** Search for `RunAllTestsInOrg` in pipeline configuration. If present, verify there is an explicit justification (e.g., managed package compatibility check) rather than it being the default.

---

## Anti-Pattern 3: Omitting `--wait` and Not Polling

**What the LLM generates:** A pipeline step that runs `sf apex run test --test-level RunLocalTests` without `--wait`, then immediately proceeds to the next step as if tests have completed.

**Why it happens:** LLMs generate syntactically valid commands but miss that asynchronous test runs return immediately with a job ID. Without `--wait`, the pipeline continues before tests finish, and test failures are never detected.

**Correct pattern:**

```bash
# Always include --wait with a generous timeout
sf apex run test --test-level RunLocalTests \
  --wait 60 \
  --result-format junit \
  --output-dir ./test-results
```

**Detection hint:** Look for `sf apex run test` without `--wait` and without a subsequent `sf apex get test` polling loop.

---

## Anti-Pattern 4: Hardcoding org credentials in pipeline YAML

**What the LLM generates:** Pipeline configuration that includes the username, password, security token, or client secret directly in the YAML file or shell script, sometimes with a comment like "replace with your credentials."

**Why it happens:** LLMs produce self-contained examples optimized for copy-paste. Training data includes tutorials that use hardcoded values as placeholders. The model does not distinguish between "example placeholder" and "production configuration."

**Correct pattern:**

```yaml
# Store credentials as CI platform secrets, never in source
- name: Authenticate
  run: |
    echo "${{ secrets.SFDX_AUTH_URL }}" > auth.txt
    sf org login sfdx-url --sfdx-url-file auth.txt --alias target
    rm auth.txt
```

**Detection hint:** Search for `password`, `security_token`, `client_secret`, or `consumer_key` as literal strings in YAML or shell files. These should reference secret variables, not inline values.

---

## Anti-Pattern 5: Treating `RunSpecifiedTests` Coverage as Org-Wide

**What the LLM generates:** Advice that says "use RunSpecifiedTests and as long as your org has 75% coverage overall, the deployment will succeed."

**Why it happens:** LLMs generalize the 75% rule without distinguishing between test levels. Training data frequently mentions the 75% org-wide threshold without clarifying that `RunSpecifiedTests` applies it per-class and per-trigger within the deployment package.

**Correct pattern:**

```text
RunSpecifiedTests enforces 75% coverage on EACH class and trigger
in the deployment package individually.

A class with 60% coverage will block deployment even if the org
is at 95% overall. This is stricter than RunLocalTests, which
only checks the 75% threshold against the org-wide aggregate.
```

**Detection hint:** Look for advice about `RunSpecifiedTests` that references "org-wide coverage" or "75% overall" without mentioning per-class enforcement.

---

## Anti-Pattern 6: Generating Legacy `sfdx` Commands Instead of `sf`

**What the LLM generates:** Pipeline scripts using `sfdx force:apex:test:run`, `sfdx force:source:deploy`, or other legacy `sfdx` CLI v1 command syntax.

**Why it happens:** A large proportion of training data predates the `sf` CLI v2 unified command structure. The legacy `sfdx` commands were prevalent in blog posts, Stack Overflow answers, and tutorials through 2023.

**Correct pattern:**

```bash
# Current sf CLI v2 syntax
sf apex run test --test-level RunLocalTests --wait 30
sf project deploy start --source-dir force-app --test-level RunLocalTests
sf project deploy validate --source-dir force-app --test-level RunLocalTests

# NOT the legacy equivalents:
# sfdx force:apex:test:run
# sfdx force:source:deploy
# sfdx force:source:deploy --checkonly
```

**Detection hint:** Search for `sfdx force:` in any generated command. All `sfdx force:*` commands have `sf` equivalents and the legacy syntax is deprecated.

---

## Anti-Pattern 7: Missing JUnit Output Configuration

**What the LLM generates:** A pipeline that runs tests and checks the exit code but does not produce JUnit XML or any machine-readable output, making test failures visible only in raw console logs.

**Why it happens:** LLMs optimize for "does the test pass" and omit observability concerns. The minimum viable command (`sf apex run test --wait 30`) works but produces no artifacts that CI platforms can parse into test result dashboards.

**Correct pattern:**

```yaml
- name: Run tests
  run: |
    sf apex run test --test-level RunLocalTests \
      --result-format junit \
      --output-dir ./test-results \
      --wait 60

- name: Publish test results
  if: always()
  uses: actions/upload-artifact@v4
  with:
    name: apex-test-results
    path: ./test-results/
```

**Detection hint:** Look for `sf apex run test` without `--result-format junit` or `--output-dir`. Also check for missing artifact upload steps.
