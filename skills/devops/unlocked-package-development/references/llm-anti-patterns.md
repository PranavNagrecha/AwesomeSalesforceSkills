# LLM Anti-Patterns — Unlocked Package Development

Common mistakes AI coding assistants make when generating or advising on Salesforce unlocked package development.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Confusing Unlocked Packages with Managed Packages

**What the LLM generates:** "Use an unlocked package to distribute your app on AppExchange" or "unlocked packages provide namespace protection and IP hiding" — confusing unlocked package capabilities with managed package features.

**Why it happens:** Both are second-generation packages created via `sf package version create`. LLMs conflate their distribution and protection models.

**Correct pattern:**

```text
Unlocked vs Managed packages:

Unlocked packages:
- Source is visible to installing org (no IP protection)
- Can be installed in any org (not AppExchange distribution)
- Metadata can be modified by the subscriber after installation
- Namespace is optional (usually namespace-less for internal use)
- Best for: internal modular development, team-owned components

Managed packages (2GP):
- Source is hidden from subscriber (IP protection)
- Distributable via AppExchange
- Metadata is locked — subscriber cannot modify managed components
- Namespace is REQUIRED
- Best for: ISV products, AppExchange listings
```

**Detection hint:** Flag unlocked package recommendations for AppExchange distribution or IP protection scenarios. Look for "unlocked package" paired with "distribute," "sell," or "AppExchange."

---

## Anti-Pattern 2: Not Promoting Package Versions Before Production Installation

**What the LLM generates:** "Install the package version in production: sf package install --package 04tXXX..." using a beta (non-promoted) version ID, which cannot be installed in production orgs.

**Why it happens:** Beta versions work fine in sandboxes and scratch orgs. LLMs do not distinguish between beta and released version states, or they skip the promotion step.

**Correct pattern:**

```text
Package version lifecycle:

1. Create beta version:
   sf package version create --package MyPkg --wait 30
   Result: 04t... (beta — installable in dev/sandbox only)

2. Test in sandbox or scratch org:
   sf package install --package 04tXXX --target-org sandbox

3. Promote to released (requires 75% code coverage):
   sf package version promote --package 04tXXX

4. Install released version in production:
   sf package install --package 04tXXX --target-org production

Beta versions CANNOT be installed in production orgs.
Promoted versions CANNOT be deleted or unpromoted.
```

**Detection hint:** Flag production installation commands where the package version has not been promoted. Check for missing `sf package version promote` step in deployment workflows.

---

## Anti-Pattern 3: Misconfiguring Package Dependencies in sfdx-project.json

**What the LLM generates:** Dependency references using package names instead of subscriber package version IDs (04t...), or omitting dependencies entirely when one package depends on another.

**Why it happens:** sfdx-project.json dependency syntax is specific and error-prone. LLMs generate approximate configurations without the exact format required.

**Correct pattern:**

```json
{
  "packageDirectories": [
    {
      "path": "force-app",
      "package": "MyPackage",
      "versionNumber": "1.2.0.NEXT",
      "default": true,
      "dependencies": [
        {
          "package": "CoreUtils",
          "versionNumber": "1.0.0.LATEST"
        }
      ]
    }
  ],
  "namespace": "",
  "packageAliases": {
    "MyPackage": "0Ho...",
    "CoreUtils": "0Ho...",
    "CoreUtils@1.0.0-1": "04t..."
  }
}

// Dependencies must use package aliases defined in packageAliases
// The alias must resolve to a subscriber package version ID (04t...)
// Use "LATEST" to auto-resolve to the latest released version
```

**Detection hint:** Flag sfdx-project.json `dependencies` that reference packages not defined in `packageAliases`, or that use raw 04t IDs instead of aliases.

---

## Anti-Pattern 4: Adding Installation Key as a Command-Line Argument in CI

**What the LLM generates:** `sf package install --package 04tXXX --installation-key "MySecretKey123"` in a CI/CD script with the key visible in plaintext in logs and version control.

**Why it happens:** LLMs generate functional commands with all parameters inline. The security practice of passing installation keys via environment variables or encrypted secrets is not consistently applied.

**Correct pattern:**

```yaml
# WRONG — key exposed in CI logs and repository:
- run: sf package install --package 04tXXX --installation-key "MySecretKey123"

# CORRECT — key from encrypted environment variable:
- run: sf package install --package 04tXXX --installation-key "${{ secrets.PKG_INSTALL_KEY }}"

# CORRECT — prompt for key interactively (local development):
- run: sf package install --package 04tXXX --installation-key "$PKG_INSTALL_KEY"

# Or create versions without installation key for internal packages:
sf package version create --package MyPkg --installation-key ""
```

**Detection hint:** Flag `--installation-key` with literal string values in CI/CD files. Regex: `--installation-key\s+["'][^$]` (starts with a non-variable character).

---

## Anti-Pattern 5: Not Understanding That Unlocked Package Metadata Can Be Modified by Subscribers

**What the LLM generates:** "Deploy the component as an unlocked package to prevent users from changing it" — implying that unlocked packages lock metadata like managed packages do.

**Why it happens:** The word "package" implies encapsulation and protection. LLMs do not consistently communicate that unlocked packages allow subscribers to modify, override, or delete the installed metadata.

**Correct pattern:**

```text
Unlocked package mutability:

After installation, subscribers CAN:
- Modify Apex classes, triggers, and LWC components
- Change Flow definitions
- Edit page layouts and record types
- Delete package components (with warnings)
- Override field-level security and sharing settings

Implications:
- Upgrades may fail if subscribers modified package components
- sf package install --upgrade-type Mixed allows subscriber changes
  to coexist with package updates
- sf package install --upgrade-type Delete removes subscriber changes
  and reinstalls the package version

For truly protected components:
- Use managed packages (2GP managed, not unlocked)
- Or document "do not modify" guidance for internal teams
```

**Detection hint:** Flag unlocked package recommendations that claim metadata protection or immutability. Look for "prevent changes" or "locked" language in unlocked package context.
