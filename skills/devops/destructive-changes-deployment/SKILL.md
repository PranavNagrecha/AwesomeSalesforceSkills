---
name: destructive-changes-deployment
description: "Managing destructiveChanges.xml manifests for safe metadata deletion in Salesforce deployments. Use when deleting metadata components via Metadata API or sf CLI. Covers pre vs post destructive manifests, safe deletion sequencing, dependency handling. NOT for package.xml basics (use metadata-api-and-package-xml). NOT for basic deployment setup (use change-set-deployment)."
category: devops
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
triggers:
  - "how do I delete a custom field using Salesforce CLI"
  - "destructiveChanges.xml not working in deployment"
  - "component still referenced after deletion fails"
  - "pre vs post destructive changes manifest difference"
  - "metadata delete deployment error component in use"
tags:
  - destructive-changes
  - metadata-deletion
  - deployment
  - sfdx
  - salesforce-cli
inputs:
  - List of metadata components to delete (type and API name)
  - Target org credentials or authenticated alias
  - Understanding of component dependencies (what references the component to be deleted)
outputs:
  - Correct destructiveChanges manifest (pre or post variant) with proper XML structure
  - Validated deletion sequence accounting for dependencies
  - Deployment command with correct --pre-destructive-changes or --post-destructive-changes flags
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-05
---

# Destructive Changes Deployment

This skill activates when a practitioner or agent needs to delete metadata components from a Salesforce org using Metadata API or the sf CLI. It covers all three manifest variants, dependency sequencing, components that cannot be deleted via API, and the correct CLI flags.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm the exact API name and metadata type of every component to be deleted. Wildcards are not supported in destructiveChanges manifests — every member must be listed explicitly.
- Identify all components that reference the target component. A deletion will fail with a deployment error if any active component still holds a reference (e.g., a field referenced in a validation rule, a class referenced in a trigger, a component embedded in an active Lightning page).
- Know which components are permanently undeletable via the Metadata API: Record Types, Picklist values (field values), and active Flow versions cannot be deleted through a deployment. These require manual admin action in Setup.

---

## Core Concepts

### The Three Manifest Variants

The Metadata API supports three placements for destructive operations within a deployment, each controlled by the filename. All three files share the same XML schema as a standard `package.xml`.

**`destructiveChangesPre.xml`** — Deletions are processed before the additions and updates in the accompanying `package.xml`. Use this when the component being deleted would conflict with a new component being deployed (e.g., renaming a field by deleting the old one and creating the new one, where the old name must be cleared first).

**`destructiveChanges.xml`** (plain name) — The platform processes deletions at the same time as additions. In practice this behaves like a pre-deployment deletion. This is the legacy format from the Ant Migration Tool era and remains valid.

**`destructiveChangesPost.xml`** — Deletions are processed after all additions and updates in `package.xml` have landed. This is the required variant when the component being deleted is still referenced by another component that is itself being updated in the same deployment. The new version of the referencing component must land first (clearing the reference) before the deleted component can be removed.

All three files must be included inside the same deployment package as a `package.xml`. When using sf CLI flags, an empty `package.xml` (specifying only the API version) may be used as the companion manifest.

### Manifest XML Structure

Every destructive manifest follows the same schema as `package.xml`. The `<version>` element is omitted from destructive manifests — version lives only in `package.xml`. Each `<types>` block groups members by metadata type.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>MyObject__c.OldField__c</members>
        <name>CustomField</name>
    </types>
    <types>
        <members>OldValidationRule</members>
        <name>ValidationRule</name>
    </types>
</Package>
```

Member names must use the same format as they appear in `package.xml` — for child metadata types like `CustomField`, the format is `ParentObject.FieldName`.

### sf CLI Flags for Destructive Deployments

The `sf project deploy start` command (Salesforce CLI v2) exposes two flags:

- `--pre-destructive-changes <path>` — points to a `destructiveChangesPre.xml` file to process before deploying the `--manifest`.
- `--post-destructive-changes <path>` — points to a `destructiveChangesPost.xml` file to process after deploying the `--manifest`.

Example using pre-destructive:
```bash
sf project deploy start \
  --manifest package.xml \
  --pre-destructive-changes destructiveChangesPre.xml \
  --target-org myOrgAlias
```

The `--manifest` flag is required even when the package.xml contains no components to add; in that case use an API-version-only manifest.

### Components That Cannot Be Deleted via API

The following component types cannot be deleted through any destructive manifest and require manual removal in Setup:

- **Record Types** — must be deactivated and removed manually.
- **Picklist values** — field values on picklist/multi-select picklist fields cannot be removed via API. Use the Replace Picklist Values feature or manual field editing.
- **Active Flow versions** — an active version of an Autolaunched or Screen Flow cannot be deleted via deployment. Deactivate the flow in Setup first, then delete.

Attempting to delete these via a manifest results in a deployment error. The error message is not always obvious about the root cause.

---

## Common Patterns

### Pattern 1 — Delete a standalone component with no inbound references

**When to use:** Removing a custom object, Apex class, Lightning Web Component, or custom metadata type that has no active references in other deployed components.

**How it works:**
1. Confirm zero inbound references using Setup dependency tooling or `sf project retrieve start` to inspect local source.
2. Build `destructiveChanges.xml` listing the component.
3. Create an empty companion `package.xml` containing only the API version.
4. Deploy using `sf project deploy start --manifest package.xml --pre-destructive-changes destructiveChanges.xml --target-org alias`.

**Why not the alternative:** Deploying without an empty `package.xml` companion will cause a deployment error — the Metadata API requires a valid package manifest in the deployment container.

### Pattern 2 — Delete a component that is still referenced (use Post variant)

**When to use:** Removing a custom field or class that is still referenced by another component, where the referencing component is also being updated in the same deployment to remove the reference.

**How it works:**
1. Build the updated referencing component (e.g., updated Apex class with reference removed, updated validation rule formula, updated page layout).
2. Include the updated component in `package.xml`.
3. Place the deletion in `destructiveChangesPost.xml`.
4. Deploy: the updated component lands first (clearing the reference), then the deletion fires.

```bash
sf project deploy start \
  --manifest package.xml \
  --post-destructive-changes destructiveChangesPost.xml \
  --target-org alias
```

**Why not the alternative:** Using `destructiveChangesPre.xml` or plain `destructiveChanges.xml` in this scenario causes the deletion to fire before the reference is cleared, producing a deployment failure.

### Pattern 3 — Troubleshooting a failing destructive deployment

**When to use:** A destructive deployment is failing and the error is not immediately clear.

**How it works:**
1. Read the deployment error message carefully. Common patterns: "Component in use by...", "Cannot delete...", "Component not found".
2. "Component in use" — find the referencing component and either update it first (use post variant) or remove the reference in a prior deployment.
3. "Cannot delete" on Record Type, Picklist value, or active Flow — these are undeletable via API; handle manually.
4. "Component not found" — the API name or type is wrong in the manifest; re-check exact casing and type name.
5. Run the checker script: `python3 scripts/check_destructive.py --manifest-dir <path>`.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Deleting a component with no active references | `destructiveChanges.xml` or `--pre-destructive-changes` | Simplest case; no ordering concern |
| Deleting a component that is still referenced, and clearing the reference in the same deploy | `destructiveChangesPost.xml` via `--post-destructive-changes` | Reference must be removed before deletion fires |
| Deleting a component whose API name conflicts with a new component being added | `destructiveChangesPre.xml` via `--pre-destructive-changes` | Old component must be cleared before new one can land |
| Deleting a Record Type, Picklist value, or active Flow version | Manual Setup action | These types are undeletable via Metadata API |
| Deleting many components across multiple types | Single manifest with multiple `<types>` blocks | Metadata API processes all members in one transaction |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Inventory components to delete** — List every component by exact metadata type and API name. Confirm no wildcards are being used (they are not supported in destructive manifests).
2. **Check dependencies** — For each component, determine whether any other active component references it. Use Setup dependency tooling, org-wide metadata retrieval, or `sf project retrieve start` to inspect locally.
3. **Choose the correct manifest variant** — Use `destructiveChangesPost.xml` if the referencing component is being updated in the same deployment. Use `destructiveChangesPre.xml` or `destructiveChanges.xml` for standalone deletions. Never attempt to delete Record Types, Picklist values, or active Flow versions via manifest.
4. **Build the manifest** — Author the XML with correct `<types>` and `<members>` entries. Do not include a `<version>` element. Pair with a valid companion `package.xml` (even if empty of components, it must specify the API version).
5. **Run the checker script** — Execute `python3 scripts/check_destructive.py --manifest-dir <path>` to surface common authoring mistakes before deploying.
6. **Deploy and validate** — Run `sf project deploy start` with the appropriate flag. Check the deployment status output. If errors occur, map them to the known failure modes in Pattern 3.
7. **Verify deletion in target org** — Confirm the component no longer appears in Setup or metadata retrieval. Check that no unexpected cascading deletions occurred.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Every component in the manifest is listed by exact API name with no wildcards
- [ ] Manifest variant (pre/post/plain) matches the dependency ordering requirement
- [ ] No undeletable component types (Record Types, Picklist values, active Flows) are in the manifest
- [ ] A valid companion `package.xml` is included in the deployment container
- [ ] The correct sf CLI flag (`--pre-destructive-changes` or `--post-destructive-changes`) is used
- [ ] Checker script was run and returned no issues
- [ ] Deletion confirmed in target org after deployment

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Wildcards silently fail** — Unlike `package.xml`, wildcards (`*`) in a destructive manifest do not delete all components of a type. The wildcard is treated as a literal member name and the deployment will either fail or silently skip the deletion. List every member explicitly.
2. **Post manifest required even when both changes are in the same deploy** — Practitioners often assume that listing both the deletion and the updated referencing component in the same deployment is sufficient regardless of manifest type. The pre/plain variant fires the deletion first, before the updated component lands, causing the "still referenced" error even though the fix is in the same package.
3. **Deleted components may be re-created by a subsequent retrieve** — If a team member runs `sf project retrieve start` after the deletion without updating their local source, the deleted component re-appears in the local project and may be re-deployed in the next push, undoing the deletion in the org.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| `destructiveChangesPre.xml` | Manifest of components to delete before additions; paired with `package.xml` |
| `destructiveChangesPost.xml` | Manifest of components to delete after additions; use when deleted component is still referenced by a component being updated in the same deploy |
| `destructiveChanges.xml` | Plain (simultaneous) variant; legacy format, still valid |
| `package.xml` (companion) | Required companion manifest; may contain no members but must specify the API version |

---

## Related Skills

- `metadata-api-and-package-xml` — use for `package.xml` authoring, metadata type reference, and retrieval patterns; the destructive manifest schema mirrors this skill's package manifest structure
- `change-set-deployment` — use for UI-driven deployment workflows; change sets do not support destructive changes natively
