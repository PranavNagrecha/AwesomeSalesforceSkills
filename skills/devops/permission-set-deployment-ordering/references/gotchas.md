# Gotchas — Permission Set Deployment Ordering

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Full-Replace with No Warning

**What happens:** When a PermissionSet is deployed via the Metadata API (API v40+), the target org's existing permission set is completely overwritten with the deployed XML. Any permission granted in the target that is not present in the deployed XML is silently deleted. No error, no warning, no deployment failure — permissions just disappear.

**When it occurs:** Any deployment of a PermissionSet metadata type to an org where that permission set already exists with permissions configured. Most dangerous when deploying from a developer sandbox (which may have a subset of permissions) to a full/partial sandbox or production that has accumulated permissions over time.

**How to avoid:** Always retrieve the current state of the permission set from the target org before building your deployment package. Use the retrieved XML as the base file, then layer in your new changes. Never deploy a permission set constructed from scratch unless the target org has no existing version of that permission set.

---

## Gotcha 2: ConnectedApp + PermissionSet in Same Batch

**What happens:** Deploying a ConnectedApp and a PermissionSet or PermissionSetGroup that references that ConnectedApp in the same deployment batch triggers a cross-reference id error on the permission set metadata, even though both components are technically present in the batch.

**When it occurs:** Any deployment package that includes both a ConnectedApp definition and a PermissionSet or PSG that has an `<applicationVisibilities>` or similar section referencing that ConnectedApp's API name.

**How to avoid:** Separate the ConnectedApp into its own deployment that runs before the PermissionSet deployment. Use two sequential pipeline stages rather than a single combined deploy. This is a known platform limitation with no timeline for resolution.

---

## Gotcha 3: Profile Deployment Clears FLS

**What happens:** Like permission sets, deploying a Profile metadata type performs a full-replace. If you deploy a Profile that was retrieved from a sandbox with a subset of objects/fields visible, the target org's profile (which may have FLS configured for many more fields) loses all FLS grants for fields not in the deployed XML.

**When it occurs:** Profile deployments from any org that has fewer objects or fields than the target. Common in lower-environment-to-production flows where field visibility is controlled differently between environments.

**How to avoid:** Use the `--ignore-conflicts` flag with care. The safest approach is to deploy only PermissionSets (not Profiles) for field-level security differences between orgs, and to keep Profile deployments to a minimum. When you must deploy Profiles, retrieve from the target org first. Alternatively, use wildcard retrieval to capture all field permissions before building your deploy package.

---

## Gotcha 4: PSG Muting Permission Set Creates Confusing Errors

**What happens:** Permission Set Groups include a system-generated Muting Permission Set that can override permissions within the group. If this Muting PS is not included in the deployment but the PSG is updated, the group's effective permissions may differ from expectations in the target org.

**When it occurs:** Deploying a PSG that has a Muting Permission Set configured, without including the Muting PS in the package.

**How to avoid:** When retrieving a PSG for deployment, also retrieve its associated Muting Permission Set: `sf project retrieve start --metadata "PermissionSet:Muting_<PSG_Name>"`. Include the Muting PS in the same deployment as the PSG.
