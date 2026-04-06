---
name: environment-specific-value-injection
description: "Use this skill when configuring, reviewing, or troubleshooting how environment-specific values — endpoint URLs, client IDs, thresholds, feature flags — are managed across Salesforce orgs without hardcoding. Triggers: 'named credential per environment', 'custom metadata for config', 'sfdx string replacement', 'CI variable substitution', 'secrets in org configuration', 'org-specific values'. NOT for sandbox refresh automation (use sandbox-refresh-and-templates), NOT for general deployment pipeline setup (use github-actions-for-salesforce or bitbucket-pipelines-for-salesforce), and NOT for per-user or per-profile configuration overrides."
category: devops
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Operational Excellence
  - Reliability
triggers:
  - "how do I store different endpoint URLs for sandbox and production without hardcoding them in Apex"
  - "my CI pipeline needs to inject org-specific values like client IDs and base URLs during deployment"
  - "Named Credential keeps pointing to the wrong environment after deploying to a new sandbox"
  - "named credential environment-specific values for CI variable substitution and org config"
  - "CI variable substitution for org-specific configuration during deployment"
  - "environment-specific org config values managed through named credentials"
tags:
  - named-credentials
  - custom-metadata
  - string-replacement
  - ci-cd
  - secrets-management
  - environment-config
  - sfdx
inputs:
  - "List of values that must differ per environment (endpoints, client IDs, thresholds, flags)"
  - "Whether values are secrets (tokens, passwords) or non-sensitive config (URLs, IDs, toggles)"
  - "CI/CD platform in use (GitHub Actions, Bitbucket Pipelines, GitLab CI, etc.) for substitution mechanics"
  - "Deployment model (source-deploy, unlocked packages, change sets) to determine what metadata can travel"
outputs:
  - "Mechanism selection decision: Named Credential vs Custom Metadata vs sfdx string replacement vs post-deploy script"
  - "Named Credential XML stubs and post-deploy population guidance for secrets"
  - "Custom Metadata record design for deployable non-secret config"
  - "sfdx-project.json replacements block for CI variable substitution"
  - "Review findings on hardcoded values, missing per-env config, or secrets in source control"
dependencies:
  - devops/github-actions-for-salesforce
  - admin/custom-metadata-types
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-06
---

# Environment-Specific Value Injection

This skill activates when a practitioner needs to keep environment-specific values — external endpoint URLs, OAuth client IDs, feature flags, numeric thresholds — consistent with each org in the pipeline without embedding them in source-controlled metadata or Apex code. It covers four mechanisms (Named Credentials, Custom Metadata Types, sfdx string replacements, and post-deploy scripts), explains when each applies, and provides a safe path so secrets never enter version control.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Value classification:** Is the value a secret (OAuth token, password, private key, client secret) or non-sensitive config (base URL, queue ID, feature flag, threshold)? Secrets must never enter source control or Custom Metadata records. Non-sensitive config can be deployed as metadata.
- **Deployment model:** Does the team deploy via `sf project deploy start`, unlocked packages, change sets, or OmniStudio DataPacks? Some mechanisms (sfdx string replacement) only work for source-deploy and scratch-org flows; others (Custom Metadata records) travel with any deployment model.
- **Most common wrong assumption:** Practitioners often assume a Named Credential record deployed from source control carries the authentication detail (password, token, endpoint) per-environment. It does not — source-deployed Named Credentials carry the endpoint stub and authentication type only. The secret credential must be populated post-deploy in each org via Setup UI or the Connect REST API.
- **Platform limits:** Custom Metadata Types have a 10 MB record limit per org and no runtime DML path. Named Credentials are org-bound and cannot be queried via SOQL — they surface only through Apex `Http.send()` callouts and merge fields.

---

## Core Concepts

### Named Credentials: Stub-Deploy, Credential-Populate

Named Credentials separate endpoint configuration from authentication credential. The metadata file (`.namedCredential`) is deployable and carries the label, callout URL, authentication type (`Anonymous`, `Named Principal`, `Per User Principal`), and protocol settings. It does not carry the password, OAuth token, or client secret — those live only in the org's credential store and must be entered or set via the Connect REST API after each deploy.

Per the Salesforce Metadata API Developer Guide, a deployed Named Credential with authentication type `Named Principal` will appear in Setup with an empty password/token field. If Apex attempts a callout using that credential before the org-specific secret is populated, the callout will succeed structurally (HTTP 200 from Salesforce's perspective) but will return an authentication error from the external service. There is no runtime error thrown by the platform itself, which makes this silent failure the most common production bug in this area.

### Custom Metadata Types: Deployable Non-Secret Config

Custom Metadata records travel with deployments, scratch-org snapshots, and managed packages. This makes them the right home for non-sensitive org-specific values: base path fragments, feature toggle states, queue names, numeric thresholds, and routing keys. Per the Salesforce Help documentation on Custom Metadata Types, records are accessible in Apex via `[MyType__mdt]` SOQL and in Flow via Get Records — with zero SOQL governor limit cost in Apex when retrieved via `getAll()`.

The key constraint: Custom Metadata records are not editable via normal DML in Apex during a transaction. They are metadata. If a value needs to change in production without a deployment, it is not a good fit for CMT — use a Custom Setting or Custom Object instead.

### sfdx String Replacement: CI Variable Substitution at Deploy Time

The Salesforce DX Developer Guide documents the `replacements` key in `sfdx-project.json` (and scratch org definition). String replacement substitutes a placeholder token in source files with a value from a CI environment variable at the moment `sf project deploy start` runs. This mechanism is ideal for values that are known at CI time (injected by the CI platform as a secret variable) but must not appear in the repository.

Example pattern: A Named Credential XML file contains `${ENV_ENDPOINT_URL}` as the callout URL. The CI pipeline has `ENV_ENDPOINT_URL` set to the org-specific URL in the pipeline's secret store. At deploy time, the CLI substitutes the placeholder before sending metadata to the org. The source file in git always contains the placeholder; no org-specific URL ever enters source control.

The substitution applies only during `sf project deploy start`, `sf project deploy validate`, and scratch-org push. It does not apply retroactively to an already-deployed org.

### Post-Deploy Scripts: Populating Credentials via Connect REST API

For values that cannot be expressed as metadata (passwords, OAuth refresh tokens, client secrets), post-deploy scripts use the Salesforce Connect REST API or Tooling API to write org-specific values directly into Named Credential or External Credential records after deployment. This pattern is used when the CI runner has access to the secret (injected as a pipeline variable) and needs to configure the org without manual intervention.

The endpoint for Named Credential population changed in API v57.0+ with the introduction of External Credentials. As of Spring '25, the preferred model is External Credential + Named Credential, where the External Credential holds the authentication configuration (including principal and credential) and the Named Credential provides the callout URL. Post-deploy scripts must target the correct API version.

---

## Common Patterns

### Pattern 1: Named Credential With sfdx String Replacement for Endpoint, Post-Deploy for Secret

**When to use:** An Apex integration calls an external REST API. The endpoint URL differs per environment. The authentication uses a password or OAuth token that must not enter source control.

**How it works:**

Step 1 — Source-controlled Named Credential XML stub (`force-app/main/default/namedCredentials/MyAPI.namedCredential`):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<NamedCredential xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>MyAPI</label>
    <name>MyAPI</name>
    <calloutUrl>${MY_API_ENDPOINT_URL}</calloutUrl>
    <allowMergeFieldsInBody>false</allowMergeFieldsInBody>
    <allowMergeFieldsInHeader>false</allowMergeFieldsInHeader>
    <generateAuthorizationHeader>true</generateAuthorizationHeader>
    <principalType>NamedUser</principalType>
    <protocol>Password</protocol>
</NamedCredential>
```

Step 2 — `sfdx-project.json` replacements block:

```json
{
  "packageDirectories": [{"path": "force-app", "default": true}],
  "name": "myproject",
  "namespace": "",
  "sfdcLoginUrl": "https://login.salesforce.com",
  "sourceApiVersion": "63.0",
  "replacements": [
    {
      "filename": "force-app/main/default/namedCredentials/MyAPI.namedCredential",
      "stringToReplace": "${MY_API_ENDPOINT_URL}",
      "replaceWithEnv": "MY_API_ENDPOINT_URL"
    }
  ]
}
```

Step 3 — CI pipeline sets `MY_API_ENDPOINT_URL` as a secret variable pointing to the sandbox or production endpoint.

Step 4 — Post-deploy script (Python, stdlib only) calls the Tooling API to set the Named Credential password for the service account.

**Why not a simpler approach:** Hardcoding `https://prod.myapi.example.com` in the Named Credential XML means every sandbox always points to production. String replacement keeps the source neutral and the CI pipeline authoritative.

### Pattern 2: Custom Metadata Records for Non-Secret Per-Env Config

**When to use:** Feature flags, numeric thresholds, queue API names, or routing keys differ between sandbox and production. The values are non-sensitive and should travel through the deployment pipeline alongside code.

**How it works:**

Create one Custom Metadata Type (e.g., `OrgSettings__mdt`) with fields for each configurable value. Create one record per environment in source control (e.g., `OrgSettings.Default`, with production values). For sandbox-specific overrides, create a separate record with a `DeveloperName` of `Sandbox` and deploy it only during sandbox promotion runs, or use a scratch org definition to override during scratch org creation.

Apex reads the record by `DeveloperName` at runtime:

```apex
OrgSettings__mdt settings = OrgSettings__mdt.getInstance('Default');
Integer maxRetries = (Integer) settings.MaxRetries__c;
```

**Why not the alternative:** A Custom Setting is org-specific data and does not deploy with the release. If a new sandbox needs the correct threshold on day one, a Custom Setting requires manual entry or a post-refresh script. A Custom Metadata record arrives with the first deployment.

### Pattern 3: External Credential + Named Credential for OAuth Per-Env

**When to use:** The external service uses OAuth 2.0 client credentials flow. The client ID and client secret differ per environment. The token endpoint URL also differs.

**How it works:**

Create an External Credential with authentication protocol `OAuth 2.0 Client Credentials`. The source-controlled External Credential XML carries the token URL placeholder (replaced via sfdx string replacement) and the scope. The client ID and client secret are populated post-deploy via the Connect REST API or entered manually in Setup under Security > Named Credentials > External Credentials.

The Named Credential references the External Credential and carries only the callout base URL. Apex uses `Http.send()` with a `HttpRequest` whose endpoint is `callout:MyAPI/path` — the platform handles token acquisition transparently using the External Credential.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Value is a password, OAuth token, or client secret | Named Credential (stub) + post-deploy script to populate credential | Secrets must never enter source control or Custom Metadata records |
| Endpoint URL differs per environment, known at CI time | sfdx string replacement (`replaceWithEnv`) in Named Credential XML | Keeps source neutral; CI pipeline is authoritative for org-specific URL |
| Non-sensitive config (flags, thresholds, queue names) must deploy with the release | Custom Metadata Type record | Records are deployable metadata; Apex reads them at zero SOQL cost via `getAll()` |
| Config must be editable in production without a deployment | Custom Setting (hierarchy) or Custom Object | Custom Metadata records are not runtime-mutable; wrong fit for ops-editable values |
| OAuth 2.0 client credentials flow, token endpoint varies per org | External Credential + Named Credential + post-deploy secret population | Platform manages token lifecycle; credentials stay out of Apex code |
| Value is a Salesforce record ID (queue, user, group) that differs per org | Post-deploy script that queries by name and writes to Custom Metadata via Metadata API | Record IDs are always org-specific and cannot be source-controlled |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. **Classify all values** — Separate each environment-specific value into: secret (never in source), non-sensitive deployable config, or operational value (changes in prod without a release). Match each to the correct mechanism from the Decision Guidance table.
2. **Scaffold Named Credential stubs** — For each integration endpoint, create or review the Named Credential XML. Replace org-specific URLs with `${ENV_VAR_NAME}` placeholders. Add a `replacements` entry in `sfdx-project.json` for each placeholder.
3. **Design Custom Metadata records** — For non-sensitive env config, define or extend a Custom Metadata Type. Create records in source control with production values. Confirm Apex and Flow access patterns use stable `DeveloperName` keys.
4. **Build post-deploy credential population** — Write a stdlib-only Python script (or equivalent) that reads credentials from CI environment variables and writes them to Named Credentials or External Credentials via the Tooling or Connect REST API. Add this step at the end of the deployment job.
5. **Set CI variables** — In the CI platform's secret store, add per-environment variables for every placeholder and every credential. Use environment-scoped secrets (GitHub Environments, Bitbucket Deployment variables, GitLab Environments) so sandbox jobs and production jobs receive different values automatically.
6. **Run the checker script** — Execute `python3 scripts/check_environment_specific_value_injection.py --manifest-dir force-app` against the source tree to catch hardcoded URLs, plaintext credentials, and missing replacements entries.
7. **Validate post-deploy** — After each deploy to a new environment, confirm Named Credential callouts return expected responses (not authentication errors) and Custom Metadata records have correct values.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] No org-specific URLs, IDs, or endpoints are hardcoded in Apex, LWC, or metadata XML files
- [ ] No passwords, tokens, or client secrets appear anywhere in source control (including `sfdx-project.json` and scratch org definition files)
- [ ] Every `${PLACEHOLDER}` in source has a corresponding `replaceWithEnv` entry in `sfdx-project.json`
- [ ] Each CI environment (sandbox, UAT, production) has the correct variable values set in the pipeline's secret store
- [ ] Named Credential stubs are deployed before any post-deploy credential-population step runs
- [ ] Post-deploy script reads credentials from environment variables, not from hardcoded values or committed config files
- [ ] Custom Metadata records for non-secret config are present in source control and deploy cleanly to a fresh scratch org
- [ ] Apex code uses stable `DeveloperName` keys (not record IDs or labels) to query Custom Metadata
- [ ] Named Credential callouts have been tested end-to-end in at least one non-production environment

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Named Credential deploy succeeds but callout silently uses no credentials** — A source-deployed Named Credential with authentication type `Named Principal` (password or OAuth) deploys with an empty credential store. Apex callouts using `callout:MyAPI` will reach the external server with no authorization header. The Salesforce platform does not throw an error; the failure appears as a 401 or 403 from the external service. Prevention: always include a post-deploy validation step that triggers a test callout and checks the response code.

2. **sfdx string replacement runs at deploy time, not at source-retrieve time** — If a developer runs `sf project retrieve start` after a replacement-based deploy, the retrieved XML contains the substituted value (the real endpoint URL), not the `${PLACEHOLDER}` token. Committing that retrieval output back to source control leaks the org-specific value. Prevention: never commit retrieved Named Credential XML without reviewing it for substituted values; consider adding `*.namedCredential` to a pre-commit check.

3. **External Credential vs Named Credential API surface changed in API v57.0** — Before Spring '23, Named Credentials held both the endpoint and the authentication credential in a single metadata type. From API v57.0, Salesforce introduced External Credentials as a separate type. Tooling API and Connect REST API scripts written for the old model will silently fail to populate credentials on orgs using API v57.0+ External Credentials. Prevention: check the `apiVersion` in `sfdx-project.json` and use the correct API surface for post-deploy scripts.

4. **Custom Metadata `getAll()` returns records from the package namespace** — In a managed package context, `MyType__mdt.getAll()` returns only records in the package namespace. If subscriber org records are in a different namespace or no namespace, they are not returned. Prevention: in ISV contexts, use `[SELECT ... FROM MyNS__MyType__mdt]` SOQL and account for subscriber customization explicitly.

5. **String replacement only applies during `sf project deploy start` and scratch-org push** — It does not apply when deploying via change sets, OmniStudio DataPacks, Metadata API direct calls, or `sf package version create`. Teams migrating from change-set-based deployments must rebuild their env-injection approach entirely; placeholder tokens in XML metadata will be deployed verbatim if the wrong deploy path is used.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Named Credential XML stubs | Source-controlled `.namedCredential` files with `${PLACEHOLDER}` tokens for org-specific URLs |
| `sfdx-project.json` replacements block | Configuration entries mapping each placeholder to a CI environment variable |
| Custom Metadata records | Source-controlled `.md` record files for non-sensitive per-env config values |
| Post-deploy credential script | stdlib-only Python script to populate Named Credential or External Credential secrets after deploy |
| CI variable inventory | Per-environment list of secret variable names to configure in the CI platform's secret store |
| Review findings | List of hardcoded values, missing replacements entries, or secrets found in source |

---

## Related Skills

- `devops/github-actions-for-salesforce` — Use for the full CI/CD pipeline setup; this skill covers only the env-injection layer within that pipeline
- `devops/bitbucket-pipelines-for-salesforce` — Same as above for Bitbucket Pipelines
- `admin/custom-metadata-types` — Use when the primary question is CMT design, Apex access patterns, or CMT vs Custom Settings — not deployment env injection
- `devops/sandbox-refresh-and-templates` — Use when the goal is automating sandbox refresh and post-refresh configuration seeding, not deployment pipeline env injection
- `devops/scratch-org-management` — Use when the env injection must work in ephemeral scratch orgs and scratch org definition files
