# LLM Anti-Patterns — Scratch Org Management

Common mistakes AI coding assistants make when generating or advising on Salesforce scratch org management.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Using Enterprise Edition for All Scratch Org Definitions

**What the LLM generates:** `"edition": "Enterprise"` in every scratch org definition file without considering that different editions have different feature availability, and that package development may require `Developer` edition.

**Why it happens:** Enterprise is the most common production edition, so LLMs default to it. However, scratch org edition selection affects feature availability, and some ISV development scenarios require Developer edition.

**Correct pattern:**

```json
// For internal org development (matching production features):
{ "edition": "Enterprise" }

// For unlocked package development:
{ "edition": "Developer" }

// For managed package ISV development:
{ "edition": "Developer" }

// Edition selection matters because:
// - Developer edition includes all features but lower limits
// - Enterprise edition matches most production orgs
// - Professional edition: useful for testing PE-compatible packages
// - Group edition: available but very limited features
```

**Detection hint:** Flag scratch org definitions that use Enterprise edition for package development. Check that the edition matches the development model (org vs package).

---

## Anti-Pattern 2: Not Including Required Features in the Scratch Org Definition

**What the LLM generates:** A minimal scratch org definition `{ "orgName": "dev", "edition": "Developer" }` without the features and settings that the project requires, leading to "feature not enabled" errors during source push.

**Why it happens:** LLMs generate minimal configurations. The scratch org definition file requires explicit feature flags for many capabilities that are enabled by default in production orgs (Communities, Service Cloud, Knowledge, etc.).

**Correct pattern:**

```json
{
  "orgName": "My Project Scratch Org",
  "edition": "Enterprise",
  "features": [
    "EnableSetPasswordInApi",
    "Communities",
    "ServiceCloud",
    "LightningSalesConsole",
    "LightningServiceConsole"
  ],
  "settings": {
    "lightningExperienceSettings": {
      "enableS1DesktopEnabled": true
    },
    "mobileSettings": {
      "enableS1EncryptedStorage": false
    },
    "pathAssistantSettings": {
      "pathAssistantEnabled": true
    }
  }
}
```

**Detection hint:** Flag scratch org definitions with empty or missing `features` arrays. Check for missing features that correspond to metadata types in the project source (e.g., Experience Cloud components require `Communities` feature).

---

## Anti-Pattern 3: Ignoring Active Scratch Org Limits

**What the LLM generates:** "Create a new scratch org for each feature branch" without accounting for the Dev Hub's allocation constraints — and, when it does cite numbers, conflating the *active* allocation with the *daily* allocation (e.g., claiming a Developer Edition Dev Hub allows "6 active scratch orgs", when 6 is the daily creation allowance and 3 is the active ceiling).

**Why it happens:** Scratch org creation is presented as lightweight and disposable. LLMs do not model the Dev Hub's allocation constraints, and the two allocations are frequently transposed in secondhand blog content that models train on.

**Correct pattern:**

```text
Scratch org allocations — TWO separate budgets, per Dev Hub (not per user):

Edition                        Active    Daily creations
-----------------------------  --------  ---------------
Developer Edition or trial     3         6
Enterprise Edition             40        80
Unlimited Edition              100       200
Performance Edition            100       200
Partner Business Org (active)  150       300
Partner Business Org (trial)   20        40

Active  = max scratch orgs existing at any one time.
Daily   = max successful creations initiated in a ROLLING 24-hour window.
          Deleting orgs frees Active. It does not refund Daily.

Management strategies:
1. Set short durations: --duration-days 1 for CI (default is 7, max is 30)
2. Delete unused scratch orgs: sf org delete scratch --target-org alias
3. Check real headroom against the Dev Hub, not the local CLI:
     sf org list limits --target-org <Dev Hub username or alias>
   Read the ActiveScratchOrgs and DailyScratchOrgs limits.
   (sf limits api display is a legacy alias of the same command.)
4. In CI: create scratch org, run tests, delete unconditionally (if: always())
```

Note that `sf org list --all` reports orgs the *local CLI* knows about. It is not an allocation check — it will miss orgs created by CI runners or teammates against the same Dev Hub. Only the Dev Hub knows the true remaining allocation.

**Detection hint:** Flag scratch org strategies for teams >5 developers that do not mention allocation limits or cleanup procedures. Also flag any generated text that gives a single "scratch org limit" number per edition without distinguishing active from daily, that quotes 6/3 for Developer Edition in the wrong column, or that invents allocation fields on `ScratchOrgInfo`. `ActiveScratchOrgs` and `DailyScratchOrgs` are names defined by the REST API Limits resource, not fields on `ScratchOrgInfo` — the object's field list (Object Reference) has no allocation or headroom fields, so `SELECT ActiveScratchOrgs, MaxScratchOrgs FROM ScratchOrgInfo` does not compile. Allocation headroom comes from the limits API, not SOQL.

---

## Anti-Pattern 4: Not Using Org Shape for Feature Parity with Production

**What the LLM generates:** Manually listing every feature flag and setting in the scratch org definition file instead of using Org Shape to automatically mirror the production org's configuration.

**Why it happens:** Org Shape is a newer feature with limited training data. LLMs default to manual feature configuration, which is error-prone and drifts from production over time.

**Correct pattern:**

```text
Org Shape for scratch org feature parity:

1. Create an Org Shape from your production or reference org:
   sf org create shape --target-org productionAlias

2. Reference it in the scratch org definition:
   {
     "orgName": "Feature Dev",
     "sourceOrg": "00Dxx0000001gEq"  // Production org ID
   }

3. Scratch org inherits all features and settings from the source org

Org Shape advantages:
- Automatic feature parity — no manual feature flag maintenance
- Catches features enabled in production that are forgotten in definition files
- Single source of truth for org configuration

Org Shape limitations:
- Source org must be accessible (requires Dev Hub linkage)
- Some features may not be shapeable (check Salesforce docs)
- Shape snapshot is taken at creation time — re-create shape after production changes
```

**Detection hint:** Flag scratch org definitions with >10 manually listed features that could use Org Shape instead. Check for missing `sourceOrg` when feature parity with production is the goal.

---

## Anti-Pattern 5: Committing Scratch Org Authentication Files to Source Control

**What the LLM generates:** Instructions to commit `.sfdx/` directory, `authUrl.txt`, or `server.key` files to the Git repository for team sharing.

**Why it happens:** LLMs suggest sharing auth files for convenience. The security implications of committing org credentials to source control are not always flagged.

**Correct pattern:**

```text
.gitignore for Salesforce DX projects:

# Never commit authentication artifacts:
.sfdx/
.sf/
*.key
authUrl.txt

# Each developer authenticates independently:
sf org login jwt --client-id $KEY --jwt-key-file ~/secure/server.key --username $USER

# For CI, use environment variables or encrypted secrets:
- GitHub: use GitHub Secrets
- Bitbucket: use Repository Variables (Secured)
- Jenkins: use Credentials plugin

# Share org configuration, not credentials:
- config/project-scratch-def.json (committed)
- sfdx-project.json (committed)
- server.key (NEVER committed — stored in CI secrets)
```

**Detection hint:** Flag `.sfdx/`, `.sf/`, `*.key`, or `authUrl` files not listed in `.gitignore`. Check for auth-related files in the repository.
