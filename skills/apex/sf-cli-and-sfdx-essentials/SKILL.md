---
name: sf-cli-and-sfdx-essentials
description: "Use this skill when a developer needs to authenticate orgs with sf CLI, set up a Salesforce DX project, create scratch orgs, push or pull source between the local repo and a scratch org, deploy or retrieve metadata to sandboxes or production using package.xml manifests, or diagnose common sf CLI errors. Trigger keywords: sf CLI, sfdx, scratch org, source push, source pull, deploy, retrieve, package.xml, org login, sf project. NOT for full CI/CD pipeline design (use devops skills) or Metadata API SOAP programming (that is SOAP API work, not CLI)."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Security
triggers:
  - "how do I authenticate a Salesforce org with sf CLI"
  - "how to create a scratch org with sf CLI"
  - "sf project deploy start failing or not pushing any files"
  - "how do I set up sfdx project for source control"
  - "jwt auth for CI/CD pipeline to Salesforce"
  - "package.xml not retrieving all metadata types"
  - "how to deploy to sandbox or production with sf CLI"
tags:
  - sf-cli
  - sfdx
  - scratch-org
  - deployment
  - package-xml
  - source-tracking
inputs:
  - "Target org type: scratch org, sandbox, or production"
  - "Auth method preference: web flow (interactive) or JWT (CI/CD)"
  - "Deployment scope: source directory or package.xml manifest"
  - "Org alias or username"
outputs:
  - "Exact sf CLI commands with correct flags for the requested operation"
  - "package.xml manifest structure for the metadata types involved"
  - "Troubleshooting guidance for common CLI errors"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-04
---

# sf CLI and SFDX Essentials

Use this skill to authenticate Salesforce orgs, scaffold projects, manage scratch orgs, and move metadata between local development environments and Salesforce orgs using the Salesforce CLI (`sf`). Covers the complete local development loop: auth → project → scratch org → push/pull → deploy/retrieve.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Which org type is the target?** Scratch orgs use source-tracking push/pull. Sandboxes and production use deploy/retrieve with explicit manifests or directories.
- **Is this for a developer machine (interactive) or a CI/CD pipeline (non-interactive)?** This determines the auth method.
- **Is Dev Hub enabled?** Required to create scratch orgs. Without Dev Hub, scratch org commands fail with a permissions error.
- **What API version is in use?** `sfdx-project.json` has a `sourceApiVersion` that controls which metadata types are visible during retrieve.

---

## Core Concepts

### 1. Source Format vs Metadata (mdapi) Format

Salesforce CLI works with two file formats:

- **Source format** (default): files decomposed into granular folders and XML files, one component per file. Used for local development and scratch orgs. Supports source tracking.
- **Metadata (mdapi) format**: a zip-compatible directory structure with a `package.xml` manifest. Used for change sets, Metadata API SOAP calls, and `--target-metadata-dir` retrieves.

Source format is the standard for DX-based development. Metadata format is still required for some deploy/retrieve scenarios, especially when source tracking is not available (sandboxes, production).

Per the Salesforce Metadata API Developer Guide: "The `project retrieve start` command allows for source tracking. Source tracking includes information about which revision you're working on and when the last changes were made, which makes source commands more developer-friendly."

### 2. Source Tracking and Scratch Orgs

Scratch orgs use source tracking to know which metadata changed since the last push/pull. This means:
- `sf project deploy start` in a scratch org context pushes only the delta (changed files).
- `sf project retrieve start` pulls only changes made in the scratch org since the last sync.
- Source tracking does not work with sandboxes or production orgs — you must specify `--manifest`, `--source-dir`, or `--metadata` explicitly.

Scratch orgs are ephemeral: lifespan is 1–30 days (specified at creation). They are designed to be disposable. The source of truth is always the version control system, not the org.

### 3. Dev Hub and Scratch Org Lifecycle

Dev Hub is a production or Developer Edition org with "Dev Hub" enabled in Setup. It is required to create scratch orgs. Each scratch org is linked to the Dev Hub that created it. Scratch org allocation limits vary by Dev Hub edition:

| Dev Hub Edition | Daily Creates | Max Active Orgs |
|---|---|---|
| Developer Edition | 6 | 3 |
| Enterprise Edition | 40 | 20 |
| Performance Edition | 100 | 50 |
| Unlimited Edition | 100 | 50 |

Exceeding the active org limit causes `org create scratch` to fail with an allocation error — delete unused scratch orgs before creating new ones.

### 4. package.xml Manifest Structure

A `package.xml` manifest tells Metadata API which components to retrieve or deploy. Structure:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>*</members>
        <name>CustomObject</name>
    </types>
    <types>
        <members>MyClass</members>
        <name>ApexClass</name>
    </types>
    <version>62.0</version>
</Package>
```

Key rules:
- `<members>*</members>` retrieves all components of that type. Not all types support wildcard — standard objects do not.
- `<version>` is the API version. Should match or be lower than your org's current API version.
- Each `<types>` block handles one metadata type. Combine multiple types in one manifest.

---

## Common Patterns

### Pattern 1 — Authenticate a Developer Org Interactively (Web Flow)

**When to use:** Developer machine setup. A browser is available.

**Commands:**
```bash
# Authenticate production or sandbox
sf org login web --alias myorg --instance-url https://login.salesforce.com

# Authenticate a sandbox (use test.salesforce.com)
sf org login web --alias mysandbox --instance-url https://test.salesforce.com

# Set as default org for commands
sf config set target-org mysandbox
```

**Flags:**
- `--alias` (`-a`): Short name for the org. Used in subsequent commands with `--target-org`.
- `--instance-url` (`-r`): Login URL. Use `https://test.salesforce.com` for sandboxes, a custom My Domain URL for production.
- `--set-default` (`-d`): Sets this org as the default so `--target-org` is optional.

Web flow opens a browser and stores the OAuth refresh token locally. The access token is refreshed automatically on subsequent commands.

### Pattern 2 — Authenticate for CI/CD (JWT Bearer)

**When to use:** Non-interactive pipelines (GitHub Actions, Jenkins, Copado). No browser available.

**Prerequisites:**
1. A Connected App in Salesforce with OAuth enabled, using a certificate for JWT.
2. The private key file (`.key`) corresponding to the connected app's certificate.
3. The consumer key (Client ID) of the connected app.

**Command:**
```bash
sf org login jwt \
  --client-id <CONSUMER_KEY> \
  --jwt-key-file server.key \
  --username deployuser@myorg.com \
  --alias prod-ci \
  --instance-url https://login.salesforce.com
```

**Flags:**
- `--client-id`: Consumer key from the Connected App.
- `--jwt-key-file`: Path to the private key file (never commit this; use environment secrets).
- `--username`: Exact Salesforce username (must match the Connected App's permitted users policy).
- `--instance-url`: Login URL for the target org.

JWT auth does not store a refresh token. The private key signs a JWT assertion, Salesforce validates it against the Connected App certificate, and returns an access token. For CI pipelines this is the required pattern — web flow cannot run without a browser.

### Pattern 3 — Create and Use a Scratch Org

**When to use:** Feature development, automated testing, package development.

**Commands:**
```bash
# Create project first (if not already done)
sf project generate --name MyProject

# Set Dev Hub as default (first time)
sf config set target-dev-hub devhub@myorg.com

# Create scratch org (Developer edition, 7-day lifespan)
sf org create scratch \
  --edition developer \
  --duration-days 7 \
  --alias myscratch \
  --set-default

# Push local source to scratch org
sf project deploy start

# Pull changes made in scratch org back to local
sf project retrieve start

# Open scratch org in browser
sf org open --target-org myscratch

# Delete scratch org when done
sf org delete scratch --target-org myscratch --no-prompt
```

**Key facts:**
- `--edition` options: `developer`, `enterprise`, `group`, `professional`, `partner-developer`.
- `--duration-days`: 1–30. Defaults vary by edition.
- Without `--manifest` or `--source-dir`, push/pull use source tracking (delta only).
- `--set-default` and `--set-default-dev-hub` are **separate flags**. If this org should also be the Dev Hub, pass both.
- Scratch orgs start empty — no production data. Import sample data separately with `sf data import tree`.
- Add users with `sf org create user --target-org <alias>` — only the creator exists by default.

### Pattern 4 — Deploy and Retrieve with Sandboxes and Production

**When to use:** Promoting changes to sandboxes or production where source tracking is not available.

**Deploy from source directory:**
```bash
sf project deploy start \
  --source-dir force-app \
  --target-org mysandbox \
  --test-level RunLocalTests
```

**Deploy from package.xml:**
```bash
sf project deploy start \
  --manifest package.xml \
  --target-org mysandbox \
  --test-level RunLocalTests
```

**Retrieve to local source format:**
```bash
sf project retrieve start \
  --manifest package.xml \
  --target-org mysandbox
```

**Retrieve to mdapi (metadata) format:**
```bash
sf project retrieve start \
  --manifest package.xml \
  --target-org mysandbox \
  --target-metadata-dir retrieved/
```

**Preview conflicts before deploying or retrieving:**
```bash
# See what would be deployed without doing it
sf project deploy preview --target-org mysandbox

# See what would be retrieved without doing it
sf project retrieve preview --target-org mysandbox
```

**Resume a timed-out async deployment:**
```bash
sf project deploy start --manifest package.xml --target-org prod --async
# Returns a job ID immediately. Resume status check with:
sf project deploy resume --job-id <ID>
```

**Convert between formats explicitly:**
```bash
# Source format → metadata format (for inspection or legacy tooling)
sf project convert source --output-dir mdapi-out --manifest package.xml

# Metadata format → source format
sf project convert mdapi --root-dir mdapi-out --output-dir force-app
```

**Test level options for deploy:**
- `NoTestRun`: Skip tests. Only valid for sandboxes, not production.
- `RunSpecifiedTests`: Run only tests you specify with `--tests`.
- `RunLocalTests`: Run all local tests (no managed package tests). Required for production.
- `RunAllTestsInOrg`: Run everything. Slow but thorough.

**Platform limits for deploy/retrieve:**
- Maximum deploy size: **39 MB** (compressed zip). Split large deployments across multiple packages.
- Maximum retrieve component count: **10,000 items** per request. Manifests using `*` across many types can hit this limit.

Per the Salesforce Metadata API Developer Guide: "A regular deploy call executes automated Apex tests that can take a long time to complete. To skip tests for validated components and deploy components to production quickly, use the deploy recent validation option."

```bash
# Validate first (runs tests, no deployment)
sf project deploy validate --manifest package.xml --target-org prod --test-level RunLocalTests

# Then deploy the validated set without re-running tests
sf project deploy quick --job-id <ID from validate output>
```

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Developer machine, first-time org auth | `sf org login web` | Interactive, no certificate required |
| CI/CD pipeline auth | `sf org login jwt` | Non-interactive; browser not available |
| Active feature development | Scratch org + push/pull | Source tracking minimizes deploy scope |
| Deploying to sandbox or production | `sf project deploy start --manifest` | Explicit control; source tracking not available |
| Production deploy with zero downtime | Validate + Quick Deploy | Tests run once; deploy skips re-run |
| Retrieving org config for version control | `sf project retrieve start --manifest` | Gets source-format files ready for git |

---


## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Gather context — confirm the org edition, relevant objects, and current configuration state
2. Review official sources — check the references in this skill's well-architected.md before making changes
3. Implement or advise — apply the patterns from Core Concepts and Common Patterns sections above
4. Validate — run the skill's checker script and verify against the Review Checklist below
5. Document — record any deviations from standard patterns and update the template if needed

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Dev Hub is enabled and authenticated with `--set-default-dev-hub` (separate from `--set-default`)
- [ ] JWT Connected App is configured with certificate (not password) if used for CI
- [ ] JWT Connected App has the deploying user's profile pre-authorized under Manage → Edit Policies
- [ ] `sfdx-project.json` has correct `sourceApiVersion` matching target org API version
- [ ] `package.xml` version matches or is below the org's active API version
- [ ] Scratch org duration is set to match the sprint/task timeline (1–30 days)
- [ ] `--test-level RunLocalTests` or higher is used for production deploys
- [ ] Private key files (`.key`, `.pem`) are excluded from version control (`.gitignore` AND `.forceignore`)
- [ ] Deploy size is under 39 MB; retrieve scope is under 10,000 components
- [ ] `.sf/orgs/` directory is persisted in CI workspace if source tracking is needed across pipeline steps

---

## Salesforce-Specific Gotchas

1. **Scratch org push/pull does not work with sandboxes** — Source tracking is only available on scratch orgs. Running `sf project deploy start` against a sandbox without `--source-dir` or `--manifest` will either fail or behave unexpectedly. Always specify the scope explicitly for non-scratch targets.

2. **package.xml wildcard (`*`) does not work for all metadata types** — Standard objects (Account, Contact, etc.) do not support `<members>*</members>`. You must list them individually. Attempting wildcard retrieval of standard objects results in a retrieve error or silent omission.

3. **JWT auth fails if the Connected App is not pre-authorized for the user** — The Connected App must have its OAuth policies set to allow the specific user profile or permission set, and the user must be pre-authorized. Without pre-authorization, the JWT assertion is rejected even with a correct certificate.

4. **API version mismatch causes silent retrieve failures** — If `package.xml` specifies an API version higher than the org supports, the retrieve may succeed but return empty or partial results. Always match `<version>` to the org's current API version (`sf org display` shows the API version).

5. **`--target-metadata-dir` disables source tracking** — Using this flag retrieves metadata in mdapi format and breaks the source-tracking chain. Subsequent `sf project deploy start` commands (without flags) may not include these retrieved files. Use it only for one-off investigations or when you need the zip-ready directory structure.

6. **`.forceignore` is not `.gitignore`** — `.forceignore` controls what the CLI excludes from push/pull/deploy/retrieve operations. It uses `.gitignore` syntax but has no effect on git. A file ignored in `.forceignore` is still committed to version control. A file ignored in `.gitignore` is still synced by the CLI unless also in `.forceignore`.

7. **Source tracking state is lost between CI pipeline runs** — The CLI stores source tracking state in `.sf/orgs/<orgId>/` on the local filesystem. If the CI workspace is not persisted (e.g., ephemeral GitHub Actions runners), this directory is lost between runs, causing the next push to treat all local files as new changes or report false conflicts. Either persist `.sf/` in CI cache, or always use `--source-dir`/`--manifest` flags in CI to avoid dependency on tracking state.

8. **`--set-default` and `--set-default-dev-hub` are separate settings** — Setting a Dev Hub with `sf org login web --set-default-dev-hub` does not make it the default org for `deploy`/`retrieve`. You must also run `sf config set target-org <alias>` or pass `--set-default` separately. Conflating the two causes commands to target the wrong org silently.

9. **Each `-meta.xml` file carries its own `apiVersion`** — When you retrieve components from an org, each `ClassName.cls-meta.xml` file contains the API version it was authored at. This is independent of `sfdx-project.json`'s `sourceApiVersion`. Old retrieved classes may still have API version 40.0 in their metadata even if the project is on 62.0. Update these manually when a newer API version behavior is required.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| sf CLI commands | Exact commands with flags for the developer's scenario |
| package.xml manifest | Ready-to-use XML file targeting specific metadata types |
| sfdx-project.json snippet | Correct `packageDirectories` and `sourceApiVersion` for the project |

---

## Related Skills

- `integration/oauth-flows-and-connected-apps` — Deep coverage of Connected App setup and OAuth flow selection, including JWT pre-authorization
- `admin/change-management-and-deployment` — Change set and DevOps Center deployment strategy for admins
