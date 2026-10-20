# Gotchas — Permission Set Deployment Ordering

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Deploying a Partial Permission Set Overwrites Its Contents

**What happens:** From API version 40.0 the guide says "when you deploy a permission set, you must include all of its metadata to avoid accidentally overwriting the permission set's contents" (api_meta 264 L97417-97418). Permissions granted in the target but absent from the deployed XML are at risk. UNVERIFIED (2026-10-20): "silently deleted, no error, no warning, no deployment failure" is the package's inference; the guide does not describe the failure signal.

**When it occurs:** Any deployment of a PermissionSet metadata type to an org where that permission set already exists with permissions configured. Most dangerous when deploying from a developer sandbox (which may have a subset of permissions) to a full/partial sandbox or production that has accumulated permissions over time.

**How to avoid:** Always retrieve the current state of the permission set from the target org before building your deployment package. Use the retrieved XML as the base file, then layer in your new changes. Never deploy a permission set constructed from scratch unless the target org has no existing version of that permission set.

---

## Gotcha 2: ConnectedApp + PermissionSet in Same Batch

**What happens:** UNVERIFIED (2026-10-20): that deploying a ConnectedApp and a PermissionSet or PermissionSetGroup that references it in one batch triggers a cross-reference id error; neither corpus describes the error.

**When it occurs:** A package with a ConnectedApp whose `permissionSetName` names a permission set in the same package (documented field, API 46.0+, api_meta 264 L37225-37226). UNVERIFIED (2026-10-20): that a PermissionSet or PSG `<applicationVisibilities>` entry can reference a connected app; the field is described for "standard and custom apps" (L97467-97471) and a PSG has no such field (L98027-98050).

**How to avoid:** Separate the ConnectedApp into its own deployment that runs before the PermissionSet deployment. Use two sequential pipeline stages rather than a single combined deploy. "Known platform limitation with no timeline for resolution" is UNVERIFIED (2026-10-20).

---

## Gotcha 3: Profile Deployment Overlays, It Does Not Replace

**What happens:** The old text of this gotcha said a Profile deploy is a full-replace that clears FLS; api_meta 264 L100265-100268 says the opposite: "We designed Profile metadata deployment to overlay the existing Profile settings in a target org. For example, if you disable permissions for a profile, the newly disabled permission information isn't exported." A permission you remove from the XML therefore stays in the target; to force a disablement, add `<value>false</value>` explicitly (L100267-100268). Login hours follow the same rule: deleting restrictions needs an explicit empty `loginHours` tag (L100743-100744). A retrieved profile also carries field-level security only for fields of objects in the same RetrieveRequest (L100261-100263), so a profile retrieved with few objects is thin, not authoritative.

**When it occurs:** Profile deployments that are meant to revoke access, and profile retrieves taken without the related objects. Contrast with PermissionSet, where the guide asks you to include all metadata (L97416-97418).

**How to avoid:** Use the `--ignore-conflicts` flag with care. The safest approach is to deploy only PermissionSets (not Profiles) for field-level security differences between orgs, and to keep Profile deployments to a minimum. When you must deploy Profiles, retrieve from the target org first. Alternatively, use wildcard retrieval to capture all field permissions before building your deploy package.

---

## Gotcha 4: PSG Muting Permission Set Creates Confusing Errors

**What happens:** A Permission Set Group can name a muting permission set in its `mutingPermissionSets` field (API 46.0+, api_meta 264 L98039-98041); settings enabled in a MutingPermissionSet "are turned off for the permission set group that it's a component of" (L92453). If the muting set is not deployed with the group, the group's effective permissions may differ from expectations in the target org.

**When it occurs:** Deploying a PSG that has a muting permission set configured, without including that MutingPermissionSet in the package. UNVERIFIED (2026-10-20): that the muting set is "system-generated" or named `Muting_<PSG_Name>`; the guide documents it as its own metadata type (L92411).

**How to avoid:** Retrieve the muting set as its own type, `sf project retrieve start --metadata "MutingPermissionSet:<name>"`, where `<name>` is the value in the group's `mutingPermissionSets` field, and include it in the same deployment as the PSG. The `--metadata <Type>:<Name>` form is the CLI's documented syntax (`sf project retrieve start --metadata ApexClass:MyFabClass`, sfdx_dev 264 L11672), and `MutingPermissionSet` is the type name (api_meta 264 L92410-92411).
