# LLM Anti-Patterns — Environment Strategy

Common mistakes AI coding assistants make when generating or advising on Salesforce environment strategy. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending a Full Sandbox for Unit Tests or CI Runs

**What the LLM generates:** "Create a Full sandbox to run your Apex unit tests so you have the most realistic environment possible."

**Why it happens:** LLMs associate "production parity" with "best test environment" without accounting for Salesforce's 29-day Full sandbox refresh limit, the cost of Full sandboxes, or the fact that Apex unit tests should be isolated from production data. Training data frequently contains general software engineering advice about production-like test environments that does not map to Salesforce's sandbox economics.

**Correct pattern:**

```
Unit tests and CI runs → scratch orgs (disposable, clean, parallel)
Full sandbox → performance testing and pre-production regression only
```

**Detection hint:** Flag any advice that places unit tests, CI validation, or per-PR checks in a Full or Partial Copy sandbox without explicit justification for why data volume is required.

---

## Anti-Pattern 2: Ignoring Scratch Org Active Limit and Recommending Scratch Orgs Without Deletion Steps

**What the LLM generates:** "Your CI pipeline should create a scratch org for every pull request" — without including any `sf org delete scratch` step or active-org capacity guidance.

**Why it happens:** LLMs correctly identify scratch orgs as the right environment for CI but do not model the Dev Hub capacity constraint. The create command is well-represented in training data; the deletion and capacity management steps are less prominent.

**Correct pattern:**

```bash
# Every CI pipeline that creates a scratch org must also delete it
sf org create scratch --definition-file config/project-scratch-def.json --alias ci-org
# ... run tests ...
sf org delete scratch --no-prompt --target-org ci-org
```

**Detection hint:** Any pipeline recommendation that includes `sf org create scratch` without a corresponding `sf org delete scratch` in a cleanup or finally step is missing this pattern.

---

## Anti-Pattern 3: Conflating Sandbox Type Selection with Environment Strategy

**What the LLM generates:** A recommendation that only discusses sandbox types (Developer, Partial Copy, Full) without mentioning scratch orgs, branching strategy alignment, or environment count rationale.

**Why it happens:** "Environment strategy" and "sandbox strategy" overlap heavily in training data. LLMs default to sandbox-centric advice because sandboxes are the older, more documented paradigm. The cross-type decision — when to use scratch orgs vs. which sandbox type — is the core value this skill provides, and it is frequently omitted.

**Correct pattern:**

```
Environment strategy = scratch orgs + sandboxes + branching alignment + environment count rationale
Sandbox strategy = sandbox type selection, refresh cadence, masking (see admin/sandbox-strategy)
```

**Detection hint:** If the environment strategy output only mentions sandbox types and does not address scratch orgs or branching strategy, the advice is incomplete. Ask explicitly: "Which stages use scratch orgs and which use persistent sandboxes?"

---

## Anti-Pattern 4: Recommending Source-Tracked Deployment Commands Against Full or Partial Copy Sandboxes

**What the LLM generates:**

```bash
sf project deploy start --source-dir force-app --target-org uat-sandbox
```

Applied to a Partial Copy or Full sandbox environment.

**Why it happens:** The `sf project deploy start` command works differently depending on org type, and LLMs do not consistently model the distinction. Source tracking is silently unavailable on Partial Copy and Full sandboxes. The command may fall back to manifest-based deployment or fail, depending on CLI version and sandbox configuration.

**Correct pattern:**

```bash
# For Partial Copy or Full sandbox: use manifest-based deployment
sf project deploy start --manifest package/package.xml --target-org uat-sandbox

# For scratch orgs and Developer/Developer Pro sandboxes: source-tracked deployment is valid
sf project deploy start --source-dir force-app --target-org dev-sandbox
```

**Detection hint:** Any pipeline that uses `--source-dir` deployment targeting a Partial Copy or Full sandbox should be flagged for review.

---

## Anti-Pattern 5: Designing Environment Count Based on Team Headcount Rather Than Pipeline Stages

**What the LLM generates:** "You have 10 developers, so you need 10 sandboxes."

**Why it happens:** General software engineering advice often maps environments to team members. In Salesforce, individual developer isolation is better handled by scratch orgs (disposable, created on demand) while persistent sandbox count should reflect distinct pipeline stages (integration, UAT, performance, pre-prod), not headcount. LLMs apply the general principle without accounting for Salesforce's org provisioning model.

**Correct pattern:**

```
Environment count = number of distinct pipeline stages
Individual isolation = scratch orgs per developer (not sandboxes per developer)

Example for 10-developer team:
  - Scratch orgs: one per developer or per PR (created/deleted on demand)
  - Persistent sandboxes: integration (1) + UAT (1) + pre-prod (1) = 3 sandboxes
```

**Detection hint:** If the recommendation yields one sandbox per developer, push back and ask whether scratch orgs can handle individual developer isolation, reducing persistent sandbox count to pipeline-stage-driven minimums.

---

## Anti-Pattern 6: Omitting Branching Strategy Alignment from Environment Design

**What the LLM generates:** An environment matrix that lists org types and purposes without mapping each environment to a branch tier in the team's branching strategy.

**Why it happens:** LLMs treat environment design and branching strategy as separate concerns. In practice they are tightly coupled — an environment without a corresponding branch tier has no defined promotion path, and a branching model without an environment at each tier has no validation gate.

**Correct pattern:**

```
feature/* branches     → scratch orgs (one per developer or per PR)
main / integration     → Developer Pro sandbox (shared merge target)
release/* branches     → Partial Copy sandbox (UAT)
pre-production         → Full sandbox (regression rehearsal)
production             → Production org
```

**Detection hint:** If an environment matrix does not include a "Branch" or "Branch Tier" column, it is missing branching strategy alignment. Add it before finalizing the design.
