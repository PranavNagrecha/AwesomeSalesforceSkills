# Examples — Second-Generation Managed Packages

## Example 1: Version Creation Fails to Promote Due to Missing `--code-coverage` Flag

**Context:** An ISV team is building their first 2GP managed package. They run `sf package version create` repeatedly during development without the `--code-coverage` flag to keep builds fast. When the release is ready, they try to promote the latest beta version and receive an error.

**Problem:** The CLI returns an error: `The package version can't be promoted because it doesn't have code coverage data. Create a new version with the --code-coverage flag.` The team realizes they've built dozens of beta versions, none of which are promotable. There is no way to retroactively add coverage data to an existing version.

**Solution:**

```bash
# Correct command: always include --code-coverage on any version
# intended to be promoted, even during development builds
sf package version create \
  --package "Acme Billing App" \
  --target-dev-hub devhub \
  --code-coverage \
  --wait 30

# Once coverage passes, promote the resulting 04t ID
sf package version promote \
  --package 04tXXXXXXXXXXXXXXX \
  --target-dev-hub devhub
```

To avoid blocking on slow coverage runs during iterative development, teams can create two CI jobs: a fast job without `--code-coverage` for feature branches, and a gated release job that always includes `--code-coverage` for main/release branches.

**Why it works:** The `--code-coverage` flag instructs the platform to run all packaged Apex tests during version creation and record the coverage result against the package version artifact. Only versions with this recorded coverage result are eligible for promotion. Building coverage in is a one-time-per-version cost — not per deploy — so the impact on CI time is bounded.

---

## Example 2: Namespace Linked to Wrong Dev Hub Causes Package Loss

**Context:** A new ISV partner registers a namespace in a Developer Edition org and links it to that same Developer Edition org (treating it as a Dev Hub). They build a managed package, distribute a beta to a handful of test subscribers, and then the Developer Edition org expires due to inactivity. The package and all its version metadata become inaccessible.

**Problem:** Installed packages in subscriber orgs cannot receive updates because the package is associated with an expired Dev Hub. New installations of the package fail. The package ID (0Ho) is gone from the Dev Hub records. The ISV must start over with a new namespace, a new package, and re-engage all subscribers.

**Solution:**

```
Before creating any managed package:
1. Designate the Partner Business Org (PBO) as the Dev Hub.
   - Log in to PBO → Setup → Dev Hub → Enable Dev Hub.
   - Enable "Unlocked Packages and Second-Generation Managed Packages."
2. Register the namespace in a separate Developer Edition org.
3. Link the namespace to the PBO Dev Hub (not to the Developer Edition org).
   - In PBO: App Launcher → Namespace Registries → Link Namespace.
   - Log in to the Developer Edition org with the registered namespace.
4. Create all packages from the PBO Dev Hub:
   sf package create --name "Acme App" --package-type Managed \
     --path force-app --target-dev-hub pbo-devhub
```

**Why it works:** The Partner Business Org is a production org maintained by Salesforce for ISV partners. It does not expire. All packages, scratch orgs, and namespaces associated with the PBO Dev Hub persist as long as the partner relationship is active. Using a Developer Edition org as a Dev Hub is appropriate only for throwaway experimentation with disposable namespaces.

---

## Example 3: Patch Version Released Without Breaking Subscriber Upgrades

**Context:** An ISV has released version `3.2.0` of a managed package to 400 subscriber orgs. A critical bug is found in an Apex trigger that causes data corruption in a high-volume scenario. A full `3.3.0` release is weeks away and would require AppExchange re-review. The ISV needs to push a targeted fix to all subscribers immediately.

**Problem:** The team considers creating `3.3.0` immediately but realizes this would introduce all in-progress feature work, risk breaking subscribers, and likely require a full AppExchange security re-review timeline they cannot afford. Creating a patch version of `3.2.0` is the correct path but the team is unsure how to do it in 2GP.

**Solution:**

```json
// sfdx-project.json — update versionNumber to patch, set ancestor
{
  "packageDirectories": [
    {
      "path": "force-app",
      "package": "Acme Billing App",
      "versionName": "Patch — Trigger Fix",
      "versionNumber": "3.2.1.NEXT",
      "ancestorVersion": "3.2.0",
      "default": true
    }
  ],
  "namespace": "acmebill",
  "packageAliases": {
    "Acme Billing App": "0HoXXXXXXXXXXXXXXX",
    "Acme Billing App@3.2.0-1": "04tXXXXXXXXXXXXXXX"
  }
}
```

```bash
# Apply only the targeted bug fix to source, then create and promote
sf package version create \
  --package "Acme Billing App" \
  --target-dev-hub pbo-devhub \
  --code-coverage \
  --wait 30

# After validating in a scratch org:
sf package version promote \
  --package 04tYYYYYYYYYYYYYYY \
  --target-dev-hub pbo-devhub

# Push upgrade to subscribers on 3.2.0
sf package push-upgrade schedule \
  --package 04tYYYYYYYYYYYYYYY \
  --start-time "2026-04-10T02:00:00"
```

**Why it works:** Patch versions in 2GP are created with the same CLI command as any other version — there is no separate patch org required. Setting `ancestorVersion` to `3.2.0` ensures the patch branches from the correct release. Only the targeted fix is included in the patch branch's source, keeping the change surface minimal. Subscribers on `3.2.0` can receive `3.2.1` without jumping to an unvalidated `3.3.0`.

---

## Anti-Pattern: Using a Scratch Org as the Dev Hub

**What practitioners do:** A developer with no ISV experience creates a scratch org, enables Dev Hub within it (which is not actually possible — Dev Hub cannot be enabled on a scratch org itself), or conflates "create a scratch org for development" with "use this scratch org as my Dev Hub." In practice, this often means using a personal Developer Edition org as the Dev Hub.

**What goes wrong:** Developer Edition orgs expire on inactivity. When the org expires, all packages, package versions, and namespace linkages associated with it are lost. Packages already installed in subscriber orgs become unmanageable — they cannot receive updates, and new installs fail. There is no recovery path; the ISV must start over with a new package and re-engage all subscribers.

**Correct approach:** Always use the Partner Business Org (PBO) as the Dev Hub for any package intended for production distribution. Scratch orgs are ephemeral development targets created from the Dev Hub, not the Dev Hub itself. The PBO is the only org type appropriate for hosting production-grade managed 2GP packages.
