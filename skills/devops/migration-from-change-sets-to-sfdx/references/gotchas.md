# Gotchas — Migration From Change Sets To SFDX

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: `sf project convert mdapi` Silently Drops Unsupported Metadata Types

**What happens:** Certain metadata types (e.g., InstalledPackage, certain legacy EmailTemplate subtypes, CustomPageWebLink in some contexts) are not supported in source format (UNVERIFIED (2026-10-19): this type list is not in the Summer '26 DX guide, which documents only that the convert "ignores all files that start with a 'dot'" and anything matched by `.forceignore`). The convert command completes without error but simply omits these components from the output. Your converted source directory has fewer files than your mdapi input directory, and you do not notice until a deploy fails because a referenced component is missing.

**When it occurs:** Every migration that includes metadata types not supported in the source-format decomposition. The list of unsupported types changes with each Salesforce release.

**How to avoid:** After every conversion, compare the component count in the mdapi directory against the source directory. Use `sf project convert mdapi` with `--verbose` if available, or diff the file lists. For any dropped types, keep them in a separate mdapi deployment path alongside the source project, or file a Salesforce Known Issue if the type should be supported.

---

## Gotcha 2: Source API Version Mismatch Causes Missing Fields on Retrieved Metadata

**What happens:** If `sfdx-project.json` sets `"sourceApiVersion": "58.0"` but the org is on API version 62.0, any metadata fields or types introduced between API 58.0 and 62.0 are silently excluded from retrieval. The retrieved metadata is structurally valid but incomplete. Deploying it back to the org can overwrite newer field definitions with the older API version's schema, effectively removing new fields or settings.

**When it occurs:** Teams copy `sfdx-project.json` from a template or tutorial that hardcodes an older API version. They do not update `sourceApiVersion` before retrieving from their current org.

**How to avoid:** Always set `sourceApiVersion` to match the org's current API version. Check the org's API version with `sf org display --target-org prod` and update `sfdx-project.json` before any retrieve or convert operation.

---

## Gotcha 3: A Retrieved Profile Is a Partial Snapshot That Deploys as Truth

**What happens:** A retrieved `.profile` file includes "security settings for the other metadata types referenced in the retrieve request" — plus user permissions, IP address ranges, and login hours, which are always retrieved. Which settings land in the file therefore depends on the manifest, the org type, and the tracking state. Deploying that file to another org pushes whatever partial snapshot it holds: the settings it contains overwrite the target's, and settings it omits are left alone — the Metadata API guide's own example is that standard-object profile and field-level security "aren't overwritten" unless explicitly included.

**When it occurs:** The team includes profiles in the migration retrieval because change sets included profiles. They assume the file is a complete picture of the profile, when it is shaped by the retrieve manifest — so the same profile, retrieved twice with different manifests, deploys two different sets of permissions.

**How to avoid:** Exclude profiles from the migration entirely — the DX guide recommends permission sets and adding profiles to `.forceignore`. Add `**/profiles/**` to `.forceignore`. Use permission sets and permission set groups as the access-control mechanism in the source-driven workflow. If profiles must be managed, use a dedicated profile-management tool or maintain profiles as a separate, carefully reviewed deployment step.

---

## Gotcha 4: A Wildcard Flow Retrieve Pulls Flows Nobody Owns, and FlowDefinition Overrides Their Status

**What happens:** Retrieving `Flow` with `<members>*</members>` returns a file for every flow in the org — one version per flow, since API 44.0 file names carry no version number. The team ends up with flow files it does not recognize. If `FlowDefinition` files come along, "the active version numbers in the flow definitions override the status fields in the flows" on the next deploy, so a deploy can activate a version nobody chose.

**When it occurs:** Any migration that uses wildcard retrieval for flows. Orgs with a long flow history may have 5-10 versions per flow.

**How to avoid:** Use specific flow names in `package.xml` instead of wildcards. Naming a flow does not select its active version — the file holds the latest version, which may not be the active one — so record each flow's active version separately. Keep `FlowDefinition` out of the manifest. After the retrieve, audit `force-app/main/default/flows/` and remove flows the team does not maintain.

---

## Gotcha 5: Destructive Changes Cannot Be Expressed in Source-Format Deploys Without an Explicit Manifest

**What happens:** In the change set world, removing a field from the change set simply means not promoting it — the field stays in the target org unchanged. In source-driven development, removing a file from the source directory and running `sf project deploy start --source-dir force-app/` does not delete the component from the org. The CLI deploys what is present; it does not remove what is absent. Teams migrating from change sets assume that deleting a file equals deleting the component.

**When it occurs:** First time the team needs to remove (not just add or update) metadata after migrating to the CLI workflow.

**How to avoid:** Use `destructiveChangesPost.xml` (or `destructiveChangesPre.xml`) alongside the deployment manifest to explicitly declare components that should be deleted. Deploy with `sf project deploy start --manifest package.xml --post-destructive-changes destructiveChangesPost.xml` (UNVERIFIED (2026-10-19): the CLI flag name is not in the Summer '26 DX guide; check `sf project deploy start --help`). Document this in the team's runbook as a key behavioral difference from change sets.

---

## Gotcha 6: Source Tracking Exists Only Where It Has Been Turned On

**What happens:** A team expects `sf project retrieve start` with no manifest to pick up every change, the way it does in a scratch org, and gets nothing useful from a full or partial copy sandbox.

**When it occurs:** Source tracking is available in scratch orgs and in Developer and Developer Pro sandboxes once enabled — either from production for all such sandboxes, or per sandbox. Other sandbox types have no tracking.

**How to avoid:** Decide per environment: source tracking in scratch orgs and tracked Developer / Developer Pro sandboxes, manifest-based retrieve and deploy everywhere else.
