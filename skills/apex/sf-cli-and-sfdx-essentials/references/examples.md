# Examples — sf CLI and SFDX Essentials

---

## Example 1: Setting Up a New Developer's Machine and First Scratch Org

**Context:** A new developer joins the team. They need to authenticate the Dev Hub, clone the project repo, and create a scratch org to start working on a feature.

**Problem:** Without the right CLI setup and auth sequence, the developer cannot create scratch orgs or push source. Common errors include "No Dev Hub found", "Invalid client credentials", or "No orgs found."

**Solution:**

```bash
# 1. Authenticate Dev Hub with web flow and set as default dev hub
sf org login web \
  --alias devhub \
  --instance-url https://login.salesforce.com \
  --set-default-dev-hub

# 2. Clone project and move into it
git clone https://github.com/myorg/myproject.git
cd myproject

# 3. Create a scratch org with Developer edition, 14-day lifespan
sf org create scratch \
  --edition developer \
  --duration-days 14 \
  --alias feature-myfeature \
  --set-default

# 4. Push local source to scratch org (uses source tracking — pushes only changed files)
sf project deploy start

# 5. Open the scratch org in browser
sf org open
```

**Why it works:**
- `--set-default-dev-hub` registers the Dev Hub so subsequent `org create scratch` commands know which hub to use without additional flags.
- `--set-default` on the scratch org creation means `sf project deploy start` targets it without needing `--target-org` on every command.
- `sf project deploy start` with no additional flags uses source tracking, pushing only files that changed since the last push — the scratch org's ephemeral nature means source control is always the source of truth.

---

## Example 2: CI/CD Pipeline Auth and Deploy to Production with Quick Deploy

**Context:** A GitHub Actions workflow needs to deploy to production without a browser. The pipeline runs on merge to `main`. The team uses JWT auth with a certificate-based Connected App.

**Problem:** Web flow auth requires a browser. In CI there is no browser. Running `sf org login web` in a pipeline hangs or fails. Production deploys also require running Apex tests, which takes time when done twice (validate + deploy).

**Solution:**

```bash
# --- Authenticate (JWT, no browser required) ---
echo "$SF_JWT_KEY" > /tmp/server.key
sf org login jwt \
  --client-id "$SF_CONSUMER_KEY" \
  --jwt-key-file /tmp/server.key \
  --username "$SF_PROD_USERNAME" \
  --alias prod \
  --instance-url https://login.salesforce.com
rm /tmp/server.key

# --- Validate (runs tests, does NOT deploy) ---
sf project deploy validate \
  --manifest manifest/package.xml \
  --target-org prod \
  --test-level RunLocalTests \
  --json | tee validate-output.json

# Extract job ID for quick deploy
JOB_ID=$(cat validate-output.json | python3 -c "import sys,json; print(json.load(sys.stdin)['result']['id'])")

# --- Quick Deploy (skip re-running tests) ---
sf project deploy quick \
  --job-id "$JOB_ID" \
  --target-org prod
```

**Why it works:**
- The private key is stored as an environment secret and written to a temp file during the pipeline step only, then immediately deleted — it is never committed to the repo.
- `sf project deploy validate` runs all local Apex tests and validates the component set without deploying. If tests fail, the pipeline fails before touching production.
- `sf project deploy quick` deploys the previously validated set without re-running tests, significantly reducing production deployment time. Per Salesforce documentation, this is the recommended pattern for production deployments with long test suites.

---

## Example 3: Retrieving Configuration from a Sandbox for Version Control

**Context:** An admin made several configuration changes directly in a sandbox (new validation rules, page layout changes). The developer needs to retrieve these into the local repo for version control.

**Problem:** The sandbox has no source tracking. A plain `sf project retrieve start` without specifying scope will fail or return nothing. Standard objects do not support wildcard retrieval. The developer needs to build a targeted package.xml first.

**Solution:**

```bash
# 1. Authenticate the sandbox (test.salesforce.com for sandboxes)
sf org login web \
  --alias mysandbox \
  --instance-url https://test.salesforce.com

# 2. Create package.xml targeting the changed metadata
# Note: Standard objects (Account, Opportunity) must be listed by name — wildcards not supported
cat > package.xml << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Account</members>
        <members>Opportunity</members>
        <name>CustomObject</name>
    </types>
    <types>
        <members>*</members>
        <name>ValidationRule</name>
    </types>
    <types>
        <members>*</members>
        <name>Layout</name>
    </types>
    <version>62.0</version>
</Package>
EOF

# 3. Retrieve into source format (default — ready for git)
sf project retrieve start \
  --manifest package.xml \
  --target-org mysandbox

# 4. Review diff and commit
git diff
git add force-app/
git commit -m "feat: retrieve admin config changes from sandbox"
```

**Why it works:**
- Listing specific standard objects (`Account`, `Opportunity`) avoids the wildcard limitation — the wildcard `*` does not work for standard objects in Metadata API.
- `<members>*</members>` for `ValidationRule` and `Layout` retrieves all rules/layouts across all objects using those types.
- Retrieving into source format (default, no `--target-metadata-dir`) produces decomposed files ready for git tracking and future deploys via `sf project deploy start --source-dir`.

---

## Anti-Pattern: Using `force:source:push` (Legacy sfdx Command) in New Projects

**What practitioners do:** Copy example commands from old documentation or Stack Overflow that use the legacy `sfdx` CLI syntax: `sfdx force:source:push`, `sfdx force:org:create`, etc.

**What goes wrong:** The legacy `sfdx` namespace is deprecated. Many flags differ between the legacy and unified `sf` CLI. In some environments both CLIs exist and invoke different behavior. Mixing them in scripts causes inconsistent results and confusing errors.

**Correct approach:** Use the unified `sf` CLI commands: `sf project deploy start`, `sf org create scratch`, `sf org login web`. The `sf` CLI is the current standard. If you encounter legacy `sfdx` commands in documentation, map them to their `sf` equivalents using the official CLI reference.
