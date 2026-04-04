# Gotchas — sf CLI and SFDX Essentials

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

---

## Gotcha 1: Wildcard Retrieval Does Not Work for Standard Objects

**What happens:** A package.xml with `<members>*</members>` under `<name>CustomObject</name>` silently omits standard objects (Account, Contact, Lead, Opportunity, etc.). You get only custom objects back. No error is thrown — the retrieve succeeds with partial results.

**When it occurs:** Any retrieve using a wildcard specifier for the `CustomObject` metadata type when the goal is to include standard objects.

**How to avoid:** List standard objects explicitly by name in the `<members>` element:
```xml
<types>
    <members>Account</members>
    <members>Contact</members>
    <members>Opportunity</members>
    <members>*</members>  <!-- gets custom objects -->
    <name>CustomObject</name>
</types>
```
The wildcard retrieves only custom objects. Standard objects must be enumerated.

---

## Gotcha 2: Source Push/Pull Commands Fail Against Sandboxes and Production

**What happens:** Running `sf project deploy start` (without `--source-dir` or `--manifest`) against a sandbox or production org with `--target-org` set fails or pushes nothing. The command may complete but deploys zero components because source tracking state is empty for non-scratch orgs.

**When it occurs:** When a developer sets `sf config set target-org mysandbox` and then runs a source-tracking-dependent command assuming it behaves like a scratch org. Sandboxes do not maintain source tracking state.

**How to avoid:** Always specify the deployment scope explicitly for non-scratch orgs:
```bash
# Explicit source directory
sf project deploy start --source-dir force-app --target-org mysandbox

# Explicit manifest
sf project deploy start --manifest package.xml --target-org mysandbox
```
Reserve trackingless push/pull only for scratch orgs. Use manifest or directory flags for all sandbox and production operations.

---

## Gotcha 3: JWT Auth Fails If User Is Not Pre-Authorized on the Connected App

**What happens:** `sf org login jwt` returns a `INVALID_CLIENT: client identifier invalid` or similar error even when the client ID and private key are correct. The JWT assertion is signed correctly but Salesforce rejects it.

**When it occurs:** The Connected App's OAuth policy is set to "Admin approved users are pre-authorized" but the deploying user's profile or permission set has not been added to the Connected App's approved profiles list. This is a common oversight when rotating service accounts or creating new Connected Apps.

**How to avoid:**
1. In the Connected App settings, under **Manage** → **Manage Profiles**, add the profile (or permission set) of the deploying user.
2. Alternatively, set the Connected App's OAuth policy to "All users may self-authorize" — but this is less secure.
3. After adding the profile, there may be a brief propagation delay before JWT auth succeeds (typically seconds to minutes).

---

## Gotcha 4: `--target-metadata-dir` Retrieves Break Source Tracking Continuity

**What happens:** After running `sf project retrieve start --manifest package.xml --target-metadata-dir retrieved/`, subsequent `sf project deploy start` commands (source-tracking mode) do not include the retrieved files. The metadata landed in a separate directory, not in the tracked source tree.

**When it occurs:** Developers use `--target-metadata-dir` to inspect metadata in mdapi format, then expect the same files to be deployed via source tracking. The two directories (`force-app/` vs `retrieved/`) are separate and the CLI does not cross-reference them.

**How to avoid:** Use `--target-metadata-dir` only for inspection or one-time investigations. For changes you want to version-control and redeploy, retrieve without this flag (source format to `force-app/`), then deploy using `--source-dir force-app` or allow source tracking to pick up the changes.

---

## Gotcha 5: API Version Mismatch Causes Silent Retrieve Failures

**What happens:** A retrieve succeeds with exit code 0, but the returned components are fewer than expected or entirely empty for certain metadata types. No error is reported.

**When it occurs:** The `<version>` in `package.xml` is set to a higher API version than the org currently supports, or lower than the version at which a metadata type was introduced. Metadata API returns only what it can serve at the requested version.

**How to avoid:**
1. Match the `<version>` in `package.xml` to the org's current API version. Check with `sf org display --target-org <alias>`.
2. In `sfdx-project.json`, keep `sourceApiVersion` consistent with your target org's version.
3. When in doubt, use a slightly lower version — Metadata API is backward compatible but not forward compatible.
