# Examples — Managed Package Development

## Example 1: PostInstall Class Name Locked After First Released Upload

**Scenario:** An ISV named their PostInstall class `PackageInstaller` and uploaded the first Released version. In version 2, they wanted to rename it to `MyAppPostInstaller` for naming consistency.

**Problem:** The PostInstall class API name is locked after the first Released upload. The body can change but the registered class name in Package Settings cannot.

**Solution:**
1. Accept that `PackageInstaller` is permanent for this package
2. Update the class body in subsequent versions freely — logic can change
3. Prevention: finalize all class names before the first Released upload

---

## Example 2: Using sf CLI for 1GP Package Upload

**Scenario:** A developer tried `sf package version create --package "My Package" --installation-key test1234`. The command returned "Package not found" for the 1GP package ID.

**Problem:** `sf package version create` is a 2GP CLI command. 1GP packages are uploaded via Setup UI (Setup > Package Manager > Upload) or Tooling API — not the CLI.

**Solution:**
1. Navigate to Setup > Package Manager in the packaging org
2. Click the package name > Upload
3. Set version number, release type, and description
4. Download the installation URL after upload

---

## Example 3: Flow Cannot Be Deleted from Packaging Org After Release

**Scenario:** An ISV included a Flow in v1.0. The requirement changed and the Flow was no longer needed. The developer tried to delete it from the packaging org.

**Problem:** Flows included in a released managed package cannot be deleted from the packaging org. The platform prevents deletion of any Flow uploaded to a released or beta package.

**Solution:**
1. Deactivate the Flow in the packaging org (set Status to Inactive)
2. Release the next version with the Flow deactivated
3. Prevention: confirm all Flows are required features before including them in a managed release
