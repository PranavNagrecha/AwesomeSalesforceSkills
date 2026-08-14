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

---

## Anti-Pattern 7: Reaching for the MFA Waiver Permission to Unblock a Deploy or a Test User

**What the LLM generates:** "Assign the Waive Multi-Factor Authentication for Exempt Users permission to your integration and automated-test users," or "your SSO users are covered by the IdP, so Salesforce MFA is not in scope for them."

**Why it happens:** Both statements were true and heavily documented for years, so the training corpus is saturated with them. Years of runbooks, org configs and forum answers encode the waiver as *the* exemption mechanism, which keeps the advice reading as verifiable long after it stopped producing the effect being claimed.

**Correct pattern:**

```
The waiver permission no longer automatically exempts anyone. Users who
hold it are prompted to enroll in and use an MFA verifier at login, and a
continuing exemption requires approval from Salesforce Support.

SSO does not exempt a user either. The IdP must pass an MFA signal to
Salesforce -- ACR (Authentication Context Class Reference) and AMR
(Authentication Methods Reference). Without those signals, the user is
prompted to enroll in Salesforce MFA.

For the deploy question specifically: the permission's API field is
removed from the PermissionSet and Profile object schema, so the fix for
a failing Profile/PermissionSet deploy is to REMOVE the reference -- never
to assign the permission somewhere else, and never to pin the API version
lower (see Gotcha 6).
```

**Detection hint:** Any advice that resolves an MFA problem or a permission-deploy failure by assigning, re-assigning, or preserving the waiver permission is asserting an exemption mechanism that no longer works. Advice that names SSO as the reason a user is out of scope is the same error one layer up.

---

## Anti-Pattern: Mapping Salesforce releases to API versions from memory (usually off by two)

**What the LLM generates:** `Summer '25 (API v62.0)`, `Spring '25 (API v61.0)`, `API version 60.0 (Spring '25)` — plausible-looking pairs that are consistently shifted by one or two releases.

**Why it happens:** The mapping is a moving offset that increments three times a year, so every training snapshot encodes a different alignment; the model has seen "Spring '25" adjacent to several different version numbers and averages them. The *relative* spacing is usually right (each release is +1), which is what makes the error survive — the example still teaches the mechanism correctly, so nothing looks broken. But version-discipline guidance is exactly the place where the absolute number is the payload, and a reader who copies "61.0 is the Spring '25 version" pins two releases too low.

**Correct version (anchor table):**

| Release | API version |
|---|---|
| Spring '24 | 60.0 |
| Summer '24 | 61.0 |
| Winter '25 | 62.0 |
| Spring '25 | 63.0 |
| Summer '25 | 64.0 |
| Winter '26 | 65.0 |
| Spring '26 | 66.0 |
| Summer '26 | 67.0 |

Note the seasons run ahead of the calendar: Winter '25 shipped in 2024. Three releases per year, +1 version each.

**Detection hint:** never assert this pair from memory — derive it from one verified anchor and count. Mechanically: parse every `<Season> '<YY>` / `vNN.0` pair in a document and check it against a single known-good anchor; a document containing two such pairs that are *internally* consistent with each other but both shifted is the common shape, so checking pairs against each other is not sufficient. In this repo, `skills/devops/api-version-management/SKILL.md` carries the anchor list; contradiction with it is the cheapest available signal.
