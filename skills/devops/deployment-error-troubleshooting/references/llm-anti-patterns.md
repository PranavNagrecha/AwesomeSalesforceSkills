# LLM Anti-Patterns — Deployment Error Troubleshooting

Common mistakes AI coding assistants make when diagnosing or advising on Salesforce deployment errors. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Diagnosing From the Top-Level errorStatusCode Instead of componentFailures

**What the LLM generates:** Advice based on the top-level `errorStatusCode` or `errorMessage` from the DeployResult, such as: "The deployment failed with status 'Failed'. Try re-deploying with a clean package."

**Why it happens:** LLMs see the top-level error as the most prominent field in the JSON output and treat it as sufficient for diagnosis. Training data includes many forum posts where only the top-level status is shared.

**Correct pattern:**

```
Always examine the `details.componentFailures` array in the DeployResult.
Each DeployMessage contains `fullName`, `componentType`, `problem`, and
`problemType`. The `problem` field has the specific error text needed
for root cause diagnosis.

Command: sf project deploy report --json
Look at: result.details.componentFailures
```

**Detection hint:** If the advice says "re-deploy" or "try again" without referencing a specific component name or error message from componentFailures, the diagnosis is incomplete.

---

## Anti-Pattern 2: Telling the User to Fix Their Deployed Code for a "Dependent Class" Error

**What the LLM generates:** "The error says 'Dependent class is invalid'. Check your AccountService class for compilation errors and fix the syntax issue on line 42."

**Why it happens:** The LLM reads the error message and assumes the named class is the one the user is deploying. In reality, the "dependent class" in the error is a class already in the target org that depends on the deployed class — it is not the deployed class itself.

**Correct pattern:**

```
The "Dependent class is invalid" error names a class IN THE TARGET ORG that
failed to recompile when the deployed class was updated. The fix is to:
1. Open the named class in the target org (Setup > Apex Classes)
2. Attempt manual compilation
3. If it fails, fix THAT class — not the class you are deploying
4. Include the fixed dependent class in your deployment package
```

**Detection hint:** If the advice tells the user to fix the class they are deploying rather than the class named in the error message, the cause/effect is inverted.

---

## Anti-Pattern 3: Claiming rollbackOnError Defaults to True in All Orgs

**What the LLM generates:** "Don't worry about partial deploys — Salesforce rolls back all changes if any component fails."

**Why it happens:** Most documentation and tutorials describe production deployment behavior where rollbackOnError is true by default. LLMs generalize this to all org types.

**Correct pattern:**

```
rollbackOnError behavior differs by org type:
- Production: defaults to TRUE (atomic rollback on failure)
- Sandbox: defaults to FALSE (partial deploy on failure)
- Scratch org: defaults to FALSE

In sandboxes, a failed deployment leaves successfully-deployed
components in place, creating a partially-applied state.
```

**Detection hint:** If the advice assumes atomic rollback without checking the org type, it may be incorrect for sandbox or scratch org deployments.

---

## Anti-Pattern 4: Treating RunSpecifiedTests and RunLocalTests Coverage as Equivalent

**What the LLM generates:** "Your deployment needs 75% code coverage. Since your org is at 82%, you should be fine with RunSpecifiedTests."

**Why it happens:** LLMs conflate the 75% threshold across test levels. The org-wide 82% coverage is relevant for RunLocalTests, but RunSpecifiedTests evaluates each class individually at 75%.

**Correct pattern:**

```
RunSpecifiedTests: 75% coverage required PER DEPLOYED CLASS, calculated
only from the specified test classes. Org-wide coverage is irrelevant.

RunLocalTests: 75% coverage required ORG-WIDE across all local tests.
Individual classes can be below 75% if the aggregate meets the threshold.

A class at 50% coverage passes RunLocalTests (if org average is 82%)
but FAILS RunSpecifiedTests.
```

**Detection hint:** If the advice references org-wide coverage percentage as a reason RunSpecifiedTests will pass, the coverage model is wrong.

---

## Anti-Pattern 5: Suggesting --rollback-on-error Flag for sf CLI Source Deploys

**What the LLM generates:** "Run `sf project deploy start --rollback-on-error true` to ensure atomic deployment."

**Why it happens:** The `rollbackOnError` is a well-known Metadata API deploy option. LLMs assume it maps directly to a CLI flag, but `sf project deploy start` does not expose this option as a direct flag for source-format deploys.

**Correct pattern:**

```
The sf CLI does not expose --rollback-on-error for source deploys.
To force atomic behavior in a sandbox:
- Use --test-level RunLocalTests (which implicitly enforces full validation)
- Or use the Metadata API deploy() call directly with rollbackOnError=true
- Or use sf project deploy start --manifest with a SOAP-based deploy
  where the option can be set programmatically
```

**Detection hint:** Check for `--rollback-on-error` in any `sf project deploy start` command — this flag does not exist in the CLI.

---

## Anti-Pattern 6: Recommending Compile All Classes as a Definitive Fix

**What the LLM generates:** "Go to Setup > Apex Classes > Compile All Classes. This will fix the dependency error and you can re-deploy."

**Why it happens:** Compile All is a real feature and does fix some stale compilation issues. LLMs present it as a universal solution without noting that deployment-time recompilation operates differently from Setup UI compilation.

**Correct pattern:**

```
Compile All Classes in Setup is a useful diagnostic step but not a
reliable fix for deployment-time compilation errors. The deployment
engine recompiles classes in the context of the new code being deployed,
which may differ from the standalone compilation context.

If Compile All succeeds but the deployment still fails:
- The dependent class compiles against the OLD version of the deployed class
- The deployment introduces a change that breaks the dependent class
- Fix: include the dependent class in the deployment with compatible changes
```

**Detection hint:** If Compile All is presented as the final fix without a follow-up step to re-deploy and verify, the advice is incomplete.
