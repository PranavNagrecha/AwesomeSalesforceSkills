# Gotchas — Managed Package Development

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

---

## Gotcha 1: PostInstall Class Name Is Locked After First Released Upload

The API name of the Apex class implementing InstallHandler is registered in Package Settings and locked after the first Released package upload. The class body (logic) can change freely in subsequent versions, but the class API name cannot. ISVs who want to rename the class must either accept the old name or create a new package with a new namespace.

**Fix:** Finalize all component API names — especially the PostInstall class name — before the first Released package upload. Treat the first Released upload as a schema-lock event for names.

---

## Gotcha 2: Flows Included in Released Packages Cannot Be Deleted from the Packaging Org

Once a Flow is included in a released or beta managed package upload, it cannot be deleted from the packaging org. The platform locks the Flow record from deletion to maintain the package component registry. You can deactivate the Flow, create new versions, and remove old versions — but the Flow entity itself is permanent in the packaging org after release.

**Fix:** Test all Flows thoroughly in a separate org before including them in a managed release. Build a pre-release review checklist that confirms each Flow is a required feature.

---

## Gotcha 3: `sf package version create` CLI Does Not Work for 1GP Packages

The `sf package version create` command in the Salesforce CLI is designed exclusively for second-generation managed packages (2GP). It uses 2GP package IDs (starting with 0Ho) and requires a Dev Hub. 1GP packages use a completely different package ID format and upload via Setup UI or Tooling API, not the CLI.

**Fix:** For 1GP package version creation, use Setup > Package Manager > Upload in the packaging org, or use the Tooling API `PackageUploadRequest` object. Never use the sf CLI for 1GP version uploads.

---

## Gotcha 4: Subscriber Org Governor Limits Apply to PostInstall Scripts

The PostInstall Apex script (`onInstall()`) executes in the subscriber org under the Automated Process user with DML, SOQL, and heap limits that apply to that org's governor limit tier. Large data seeding operations (inserting thousands of records during install) can exceed these limits and cause the install to fail with a governor limit exception — which results in the package installation failing entirely for that subscriber.

**Fix:** For large data seeding, use the PostInstall script to enqueue a Queueable Apex job rather than performing direct DML in `onInstall()`. The Queueable job runs asynchronously after install completes with its own governor limit context.

---

## Gotcha 5: Patch Orgs Are Version-Specific — One Patch Org Per Major.Minor Version

1GP patch orgs are created from a specific released package version and can only apply changes to that version's patch releases (1.0.x). A single patch org cannot be used for patches across multiple major or minor versions. If a bug affects both 1.0 and 2.0, two separate patch orgs must be created — one for each version branch.

**Fix:** Maintain a patch org registry: document which patch org corresponds to which package version. Retire patch orgs for versions that are no longer supported to avoid accidental cross-version modifications.
