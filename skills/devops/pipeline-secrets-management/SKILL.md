---
name: pipeline-secrets-management
description: "Store and inject Salesforce auth URLs, JWT keys, and API credentials into CI without leaking them. NOT for authoring the GitHub Actions workflow itself — use devops/github-actions-for-salesforce. NOT for secrets Apex reads — use apex/apex-secrets-and-protected-cmdt."
category: devops
salesforce-version: "Summer '26+"
well-architected-pillars:
  - Security
  - Operational Excellence
triggers:
  - "jwt auth ci salesforce"
  - "leak sfdx auth url"
  - "github actions salesforce secret"
  - "rotate pipeline credential"
  - "authenticate our CI pipeline to Salesforce without storing a password"
  - "set up an external client app for sf org login jwt in CI"
  - "scan the repo for a committed Salesforce auth URL or private key"
tags:
  - ci
  - secrets
  - jwt
  - sfdx-auth
inputs:
  - "CI provider (GitHub Actions / GitLab / Jenkins)"
  - "target orgs"
outputs:
  - "Secret store layout"
  - "JWT auth workflow snippet"
dependencies: []
version: 1.2.0
author: Pranav Nagrecha
updated: 2026-10-19
---

# Pipeline Secrets Management

Salesforce CI pipelines need an authenticated session for each target org (sandboxes, UAT, production). The Salesforce DX Developer Guide's CI path is the OAuth 2.0 JWT bearer flow (`sf org login jwt`): a private key held in the CI provider's secret store signs the request, and the matching certificate sits on an external client app (or, for a Dev Hub that creates scratch orgs or sandboxes, a connected app) in the org. This skill defines the app and secret layout, the login step, rotation, and leak detection.

---

## Before Starting

- List every org the pipeline authenticates to and what it does there (validate, deploy, create scratch orgs or sandboxes).
- Confirm whether any target org enforces high assurance (stepped-up) authentication — JWT and SFDX-URL headless login don't work there.
- Find out where credentials live today: CI secrets, files in the repo, runner disks, chat history.

---

## Questions to Ask Before Configuring

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| Is the target a Dev Hub that will run `sf org create scratch` or `sf org create sandbox`? | The guide says to use an external client app for JWT, except for that Dev Hub case, which needs a connected app (gotcha 4). | The right app type per org before anyone builds the wrong one. |
| Does the org enforce high assurance session security for the integration user? | Stepped-up authentication means JWT and SFDX-URL headless login can't be used (gotcha 5). | An integration user and policy that allow headless login, or a decision to use a different path. |
| Who is pre-authorized to use the app? | JWT needs "Admin approved users are pre-authorized"; an app left open lets anyone in the org authorize it (gotcha 3). | A profile or permission set that only the integration user holds. |
| Does any pipeline use an SFDX authorization URL today? | The URL contains everything needed to authorize the org, so whoever reads it has the org (gotcha 1). | A migration to JWT, or a scoped, short-lived use with the file deleted after login. |
| Which pipeline steps could print a secret? | `sf org auth show-*` commands and `SF_TEMP_SHOW_SECRETS` deliberately print credentials into logs (gotcha 2). | A rule that no CI step calls them, enforced by the checker. |
| Is any external client app OAuth settings file or connected app secret in source control? | `ExtlClntAppGlobalOauthSettings` holds consumer secrets that must not be added to source control (gotcha 6). | A `.forceignore` / repo rule and a checker gate that keeps them out. |
| When does each certificate expire, and how is it rotated without an outage? | A JWT certificate gives no warning before it stops working (gotcha 7). | A calendar entry and a rotation runbook that proves the new key before retiring the old one. |

A proper setup adds one app, one certificate, and one least-privilege integration user per environment, with no credential ever in the repository or a log, where "just pasting the auth URL into a secret" hands production to anyone who can read that secret.

---

## Core Concepts

### Authorization options for CI

| Option | Command | Use in CI |
|---|---|---|
| JWT bearer flow | `sf org login jwt --client-id <key> --jwt-key-file <file> --username <user>` | Preferred: a certificate on the app, a private key in the secret store |
| SFDX authorization URL | `sf org login sfdx-url --sfdx-url-file <file>` | Documented for CI, but the URL alone authorizes the org; treat it as a bearer credential |
| Web server flow | `sf org login web` | Interactive only |

The private key (`server.key`) is what the pipeline holds; the certificate (`server.crt`) is uploaded to the app. The guide's self-signed example certificate is valid for 365 days (`openssl x509 ... -days 365`).

### The app the pipeline authenticates through

Salesforce CLI requires an external client app (preferred) or a connected app in each authorized org. For JWT: enable OAuth, select the scopes `api`, `web`, and `refresh_token, offline_access`, enable JWT Bearer Flow, upload the certificate, and set Permitted Users to "Admin approved users are pre-authorized" with only the integration user's profile or permission set selected. A Dev Hub that creates scratch orgs or sandboxes needs a connected app instead.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- excerpt: externalClientApps/ci_prod.eca-meta.xml, the header file only (safe to commit);
     elements are a subset of the Metadata API guide's ExternalClientApplication sample -->  
<ExternalClientApplication xmlns="http://soap.sforce.com/2006/04/metadata">
    <contactEmail>platform-team@example.com</contactEmail>
    <description>CI deploys to production via JWT bearer flow</description>
    <distributionState>Local</distributionState>
    <isProtected>false</isProtected>
    <label>CI Prod</label>
</ExternalClientApplication>
```

The OAuth consumer settings for the same app (`ExtlClntAppGlobalOauthSettings`, `.ecaGlblOauth`) contain sensitive consumer information that the Metadata API guide says can't be packaged and must not be added to source control.

### Secrets the CLI will not print — unless asked

`sf org display` and `sf org list` hide access tokens, passwords, and SFDX authorization URLs. The dedicated `sf org auth show-access-token`, `show-sfdx-auth-url`, and `show-user-password` commands print them, and the guide warns that logging these is equivalent to sharing login credentials.

---

## Recommended Workflow

1. Answer the Questions table and draw the matrix: org → app type → integration user → secret names.
2. Per environment, generate a key pair, create the external client app (or connected app for a scratch/sandbox-creating Dev Hub) with JWT enabled and admin-approved pre-authorization, and record the certificate expiry.
3. Store the private key (base64) and consumer key as environment-scoped CI secrets; the username can be a plain variable.
4. Use the login step from `references/examples.md`: `umask 077`, `mktemp`, `trap 'rm -f "$KEYFILE"' EXIT`, `sf org login jwt`, and a connectivity check that prints only the username.
5. Run `python3 skills/devops/pipeline-secrets-management/scripts/check_pipeline_secrets_management.py --manifest-dir .` in CI on every pull request; it fails on committed auth URLs, private keys, consumer secrets, and `.ecaGlblOauth` files.
6. Schedule rotation well inside the certificate validity using the runbook in `references/rotation-runbook.md`.

---

## Decision Guidance

| Situation | Approach |
|---|---|
| Deploy/validate pipeline to sandbox or production | External client app + JWT, one per environment |
| Dev Hub that creates scratch orgs or sandboxes | Connected app + JWT for that Dev Hub |
| Org with high assurance sessions for the integration user | Change the user's session policy for headless login, or keep that org out of CI |
| Legacy pipeline on an SFDX auth URL | Migrate to JWT; until then, write the URL to a temp file, log in, delete it in a `trap` |
| A human needs to see a token | Locally with `sf org auth show-access-token`, never in a pipeline step |

---

## Review Checklist

- [ ] No `force://` URL, PEM private key, `<consumerSecret>`, or `.ecaGlblOauth` file in the repository (checker passes)
- [ ] One app, certificate, and integration user per environment; production secrets scoped to a protected CI environment
- [ ] App OAuth policy is admin-approved pre-authorization limited to the integration user
- [ ] Login step deletes the key file on every exit path and never uses `set -x`
- [ ] No CI step runs `sf org auth show-*` or sets `SF_TEMP_SHOW_SECRETS`
- [ ] Certificate expiry dates are tracked and rotation is scheduled
- [ ] `LoginHistory` for the integration user is reviewed (filter on the `Application` field)

---

## Salesforce-Specific Gotchas

Full list in `references/gotchas.md`. The two with the largest blast radius:

1. **An SFDX authorization URL is the org** — whoever reads it can authorize the org.
2. **`sf org auth show-*` prints real credentials** — the hiding in `sf org display` stops at those commands.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Secret store layout | Secret and variable names per environment |
| App matrix | Org → app type → integration user → certificate expiry |
| Login workflow snippet | The JWT step with key cleanup |
| Rotation runbook | Ordered steps that keep a working credential at every point |
| Checker gate | `check_pipeline_secrets_management.py` in CI |

---

## Reference Files

| File | Use it for |
|---|---|
| `references/examples.md` | Replacing an auth-URL deploy with JWT; the login step in full |
| `references/gotchas.md` | Seven credential behaviours that cause leaks or outages |
| `references/llm-anti-patterns.md` | Secret-handling mistakes AI assistants make |
| `references/well-architected.md` | Pillar framing and the guide lines behind each claim |
| `references/rotation-runbook.md` | Certificate rotation that never leaves the pipeline without a working credential |

---

## Related Skills

- `devops/github-actions-for-salesforce` — workflow structure and job design
- `devops/gitlab-ci-for-salesforce` — the same for GitLab
- `apex/apex-secrets-and-protected-cmdt` — secrets that Apex reads at runtime
