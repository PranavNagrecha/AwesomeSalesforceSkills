# Gotchas — Migration From Change Sets To SFDX

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: `sf project convert mdapi` Silently Drops Unsupported Metadata Types

**What happens:** Certain metadata types (e.g., InstalledPackage, certain legacy EmailTemplate subtypes, CustomPageWebLink in some contexts) are not supported in source format. The convert command completes without error but simply omits these components from the output. Your converted source directory has fewer files than your mdapi input directory, and you do not notice until a deploy fails because a referenced component is missing.

**When it occurs:** Every migration that includes metadata types not supported in the source-format decomposition. The list of unsupported types changes with each Salesforce release.

**How to avoid:** After every conversion, compare the component count in the mdapi directory against the source directory. Use `sf project convert mdapi` with `--verbose` if available, or diff the file lists. For any dropped types, keep them in a separate mdapi deployment path alongside the source project, or file a Salesforce Known Issue if the type should be supported.

---

## Gotcha 2: Source API Version Mismatch Causes Missing Fields on Retrieved Metadata

**What happens:** If `sfdx-project.json` sets `"sourceApiVersion": "58.0"` but the org is on API version 62.0, any metadata fields or types introduced between API 58.0 and 62.0 are silently excluded from retrieval. The retrieved metadata is structurally valid but incomplete. Deploying it back to the org can overwrite newer field definitions with the older API version's schema, effectively removing new fields or settings.

**When it occurs:** Teams copy `sfdx-project.json` from a template or tutorial that hardcodes an older API version. They do not update `sourceApiVersion` before retrieving from their current org.

**How to avoid:** Always set `sourceApiVersion` to match the org's current API version. Check the org's API version with `sf org display --target-org prod` and update `sfdx-project.json` before any retrieve or convert operation.

---

## Gotcha 3: Profiles Retrieved in Full Overwrite Target Org Profiles on Deploy

**What happens:** A profile retrieved via the Metadata API contains the complete permission set for that profile across every object, field, tab, app, and record type in the org — including standard objects and managed-package components. If you convert this to source format and deploy it to another org, it replaces the entire profile in the target, removing any permissions that exist in the target but not in the retrieved snapshot.

**When it occurs:** The team includes profiles in the migration retrieval because change sets included profiles. They assume the deploy is additive (like change sets' "Add to profile" behavior) when it is actually a full overwrite.

**How to avoid:** Exclude profiles from the migration entirely. Add `**/profiles/**` to `.forceignore`. Use permission sets and permission set groups as the access-control mechanism in the source-driven workflow. If profiles must be managed, use a dedicated profile-management tool or maintain profiles as a separate, carefully reviewed deployment step.

---

## Gotcha 4: Flow Retrieval Pulls All Versions Including Inactive and Obsolete Ones

**What happens:** Retrieving FlowDefinition with `<members>*</members>` returns every version of every flow — active, inactive, draft, and obsolete. The convert step creates source files for all of them. The team ends up with dozens of flow files they do not recognize, and deploying them may activate unintended flow versions.

**When it occurs:** Any migration that uses wildcard retrieval for flows. Orgs with a long flow history may have 5-10 versions per flow.

**How to avoid:** Use specific flow names in `package.xml` instead of wildcards. Retrieve only the active version by specifying the flow's DeveloperName. After conversion, audit the `force-app/main/default/flows/` directory and remove any flow versions the team does not actively maintain. Note: in source format, only one version per flow API name is stored; the latest retrieved version is what you get. The risk is pulling flows the team did not know existed.

---

## Gotcha 5: Destructive Changes Cannot Be Expressed in Source-Format Deploys Without an Explicit Manifest

**What happens:** In the change set world, removing a field from the change set simply means not promoting it — the field stays in the target org unchanged. In source-driven development, removing a file from the source directory and running `sf project deploy start --source-dir force-app/` does not delete the component from the org. The CLI deploys what is present; it does not remove what is absent. Teams migrating from change sets assume that deleting a file equals deleting the component.

**When it occurs:** First time the team needs to remove (not just add or update) metadata after migrating to the CLI workflow.

**How to avoid:** Use `destructiveChangesPost.xml` (or `destructiveChangesPre.xml`) alongside the deployment manifest to explicitly declare components that should be deleted. Deploy with `sf project deploy start --manifest package.xml --post-destructive-changes destructiveChangesPost.xml`. Document this in the team's runbook as a key behavioral difference from change sets.
