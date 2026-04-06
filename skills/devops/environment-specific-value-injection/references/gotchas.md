# Gotchas — Environment-Specific Value Injection

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: `sf project retrieve start` Overwrites Placeholders With Substituted Values

**What happens:** A developer runs `sf project retrieve start` after a successful deployment to pull down any platform-side changes to the org's metadata. The Named Credential retrieved from the org contains the real substituted endpoint URL (e.g., `https://api.example.com`), not the `${EXTERNAL_API_ENDPOINT}` placeholder that was in the source file. If the developer commits this retrieved file, the real URL enters source control. Future deployments to other orgs use the hard-coded URL regardless of CI environment variables.

**When it occurs:** Any time `sf project retrieve start` is run against an org where string replacement was used during the previous deploy. The Metadata API returns the post-substitution value; it has no awareness that the value was injected from an env variable.

**How to avoid:** Add a pre-commit hook or CI lint step that scans all `.namedCredential` files for patterns matching known endpoint formats (e.g., `https://`) and fails if a substituted URL is found. Alternatively, keep Named Credential files in a separate package directory and exclude them from retrieval by listing them in `.forceignore`.

---

## Gotcha 2: Named Credential Callouts Succeed Structurally But Return 401 When Credential Is Unpopulated

**What happens:** A Named Credential stub is deployed successfully. The deployment reports zero errors. Apex code using `callout:MyAPI` executes without throwing an exception, but the external service returns HTTP 401 (Unauthorized) or 403 (Forbidden) because the credential (password, OAuth token) was never populated post-deploy. Developers often spend hours debugging Apex or firewall rules before discovering the root cause.

**When it occurs:** Any time a Named Credential with authentication type `Named Principal` (password, OAuth) is deployed from source control without a corresponding post-deploy credential population step. This is extremely common after sandbox refresh automation, where the deployment restores the Named Credential stub but no process populates the secret.

**How to avoid:** Always pair a Named Credential stub deployment with a post-deploy validation step that performs a test callout and asserts a non-4xx response. In CI, script the credential population using the Tooling API or Connect REST API before running integration tests. Document the credential population requirement in the deployment runbook.

---

## Gotcha 3: String Replacement Does Not Apply to Change Set, Package Version, or DataPack Deployments

**What happens:** A team writes `replacements` entries in `sfdx-project.json` and tests the substitution successfully using `sf project deploy start` in their CI pipeline. Later, someone deploys the same metadata using a change set (via Setup) or `sf package version create` for a second-generation package. The `${PLACEHOLDER}` tokens are deployed verbatim. The Named Credential in the target org has a callout URL of literally `${EXTERNAL_API_ENDPOINT}`, which is not a valid URL. Every callout fails with a URL parsing error.

**When it occurs:** When the team uses multiple deployment paths for the same metadata, or when an ISV packages metadata that was designed for source-deploy only. The `replacements` key in `sfdx-project.json` is a Salesforce DX feature processed by the CLI; it has no effect on metadata uploaded via the Metadata API directly or packaged into a second-generation package.

**How to avoid:** Use `replacements` only for metadata that will always be deployed via `sf project deploy start`. For metadata that travels in packages or change sets, use Custom Metadata records (deployable, no substitution needed) or document that Named Credentials must be configured manually in each target org after package installation.

---

## Gotcha 4: Custom Metadata `getAll()` Is Namespace-Aware in Managed Packages

**What happens:** A managed package ISV deploys a Custom Metadata Type `Config__mdt` and populates a default record. In the subscriber org, the record is deployed correctly, but `Config__mdt.getAll()` called from a subscriber Apex class (outside the package namespace) returns an empty map because `getAll()` resolves to the caller's namespace. The ISV's packaged records are in the ISV's namespace; the subscriber's unnamespaced call returns nothing.

**When it occurs:** In managed package scenarios where the ISV's Apex and the subscriber's Apex both try to read the same Custom Metadata records. Also occurs when a subscriber creates their own records of the packaged type and expects `getAll()` to return both ISV defaults and subscriber records.

**How to avoid:** For packaged config that must be readable from both contexts, use SOQL with the fully qualified type name (`SELECT ... FROM ISVNamespace__Config__mdt`) and handle both namespaced and unnamespaced scenarios. Document which records are ISV-owned (protected or public) and which are subscriber-extensible.

---

## Gotcha 5: External Credential API Surface Breaks Scripts Written for Pre-v57.0 Named Credentials

**What happens:** A team has a working post-deploy Python script that populates Named Credential passwords using the Tooling API endpoint `/services/data/v55.0/tooling/sobjects/NamedCredential/{id}`. After upgrading `sourceApiVersion` to `63.0` in `sfdx-project.json`, their Named Credentials are deployed as the new split model (External Credential + Named Credential, introduced in v57.0). The old Tooling API PATCH now returns an error because the password field on `NamedCredential` no longer exists — it has moved to `ExternalCredential` and `ExternalCredentialPrincipal`. Callout authentication is broken until the script is updated.

**When it occurs:** When `sourceApiVersion` is bumped to 57.0 or higher and Named Credentials in the org were previously using the legacy single-object model. The platform auto-migrates the records; scripts that were correct for the old model silently fail.

**How to avoid:** When upgrading API version, audit all post-deploy scripts that interact with Named Credentials. Test the scripts against a sandbox first. Use the Tooling API schema explorer (`/services/data/v63.0/tooling/describe`) to confirm the current fields on `NamedCredential` and `ExternalCredential` objects before writing or updating credential population scripts.
