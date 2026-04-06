# Gotchas — Destructive Changes Deployment

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: No `<version>` Element in Destructive Manifests

**What happens:** A deployment fails with a schema validation error or the version element is silently ignored, but practitioners writing their first destructive manifest often copy the full structure from `package.xml` including the `<version>` tag. Depending on the API version being used, this either throws a parse error or the API treats the manifest as malformed.

**When it occurs:** When a developer copies `package.xml` as a starting point for a destructive manifest and forgets to remove the `<version>` element. The `<version>` element belongs only in `package.xml`, not in any of the three destructive manifest files.

**How to avoid:** Author destructive manifests without a `<version>` element. The version is declared in the companion `package.xml` only. The checker script flags this pattern.

---

## Gotcha 2: The `destructiveChanges.xml` Plain Variant Behaves Like Pre, Not Simultaneous

**What happens:** Practitioners assume that the plain `destructiveChanges.xml` (as opposed to the Pre and Post variants) processes deletions at exactly the same instant as additions — atomically, side-by-side. In practice, Salesforce processes plain `destructiveChanges.xml` before the additions in `package.xml`, making it functionally equivalent to `destructiveChangesPre.xml`. If you need deletions to fire after additions, only `destructiveChangesPost.xml` guarantees that ordering.

**When it occurs:** When a team uses `destructiveChanges.xml` thinking it will handle a "delete-then-re-create-with-same-name" scenario without the Pre naming, and then encounters a "still referenced" error that only the Post variant would have avoided.

**How to avoid:** Treat `destructiveChanges.xml` and `destructiveChangesPre.xml` as equivalent. When post-deployment ordering is needed, use `destructiveChangesPost.xml` explicitly.

---

## Gotcha 3: Deleted Component Re-Appears After Next Team Retrieve

**What happens:** After a successful destructive deployment removes a component from production, a teammate running `sf project retrieve start` without scoping their retrieve will pull the current org state. If the retrieve includes all metadata, the deleted component is simply absent from the result. However, if the teammate has the old component file locally and does not refresh their local source before the next deploy, they will inadvertently re-deploy the deleted component, un-deleting it in the org.

**When it occurs:** On teams where developers maintain long-lived local project directories without regularly syncing to the source org, and where CI/CD pipelines do not enforce retrieve-before-deploy. Particularly problematic when deletions are done out-of-band (e.g., directly in a sandbox then promoted).

**How to avoid:** After a destructive deployment, immediately remove the corresponding local source file from the project. Document the deletion in the branch/PR so teammates know to delete the file from their local branches. CI pipelines should retrieve before deploying or use source tracking.

---

## Gotcha 4: Active Flow Versions Cannot Be Deleted via Metadata API

**What happens:** Attempting to include an active Flow version in a destructive manifest produces a deployment error. Salesforce does not allow deletion of any Flow that has an active version through the Metadata API. The error message may reference the flow by internal ID rather than the friendly name, making it hard to correlate.

**When it occurs:** When a developer retrieves a Flow metadata file, includes it in a destructive manifest, and the flow currently has an active version in the target org — even if the local file corresponds to an older version.

**How to avoid:** Before deploying a Flow deletion, navigate to Setup > Flows, open the flow, and deactivate all active versions. Once deactivated, the deletion can be performed via a subsequent destructive deployment or manually from Setup.

---

## Gotcha 5: Record Types and Picklist Values Are Permanently Undeletable via API

**What happens:** Deployments that include Record Types or Picklist field values in a destructive manifest fail unconditionally. The Metadata API does not support deletion of Record Types or individual Picklist values (including Global Value Set members). The only supported action for these types via the API is deactivation, not removal.

**When it occurs:** When a data model cleanup effort includes retiring a Record Type or removing obsolete picklist values, and the team assumes the destructive manifest handles all metadata deletion uniformly.

**How to avoid:** Remove Record Types manually via Setup > Object Manager > Record Types. Remove Picklist values via Setup > Object Manager > [Object] > Fields > [Field] > Edit. For Global Value Sets, use Setup > Picklist Value Sets. Document these manual steps in the deployment runbook so they are not missed during a release.
