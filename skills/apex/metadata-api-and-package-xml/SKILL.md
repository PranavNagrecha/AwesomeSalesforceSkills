---
name: metadata-api-and-package-xml
description: "Metadata API concepts, package.xml manifest structure, retrieve and deploy workflows, what metadata types can and cannot be retrieved, deployment order dependencies, and destructiveChanges.xml for deletions. NOT for SFDX source-format details or sf CLI command syntax (use sf-cli-and-sfdx-essentials), and NOT for CI/CD pipeline automation (use devops skills)."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Reliability
triggers:
  - "how do I write a package.xml to retrieve metadata from Salesforce"
  - "how to deploy metadata to production using the Metadata API"
  - "how to delete a component from a Salesforce org using destructiveChanges.xml"
  - "what metadata types can and cannot be retrieved with package.xml"
  - "deployment order for components with dependencies in Salesforce"
tags:
  - metadata-api
  - package-xml
  - deployment
  - retrieve
  - destructive-changes
inputs:
  - "Target metadata types and component names to retrieve or deploy"
  - "Source and destination org credentials"
  - "API version to use (check current supported range)"
outputs:
  - "Correct package.xml manifest file for the target operation"
  - "Step-by-step retrieve or deploy procedure"
  - "destructiveChanges.xml for component deletion"
  - "Review checklist for deployment readiness"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-04
---

# Metadata API and Package.xml

Use this skill when you need to retrieve metadata from a Salesforce org, deploy metadata to an org, delete components using destructiveChanges.xml, or understand what the Metadata API can and cannot move between environments. This skill covers the file-based asynchronous deploy/retrieve workflow and the package.xml manifest format.

---

## Before Starting

Gather this context before working on anything in this domain:

- **User permissions**: The deploying user needs either the "Modify Metadata Through Metadata API Functions" permission OR "Modify All Data" permission, plus "API Enabled". Without these, deploy() and retrieve() calls will fail.
- **Edition requirement**: Metadata API requires Enterprise, Unlimited, Performance, or Developer Edition. Professional Edition orgs require ISV partner API token access.
- **API version alignment**: The `<version>` tag in package.xml must match the version your CLI or client targets. Mismatches cause unexpected behavior. Current supported range: v31.0–v66.0 (Spring '26). Versions 7.0–30.0 are retired.
- **Asynchronous model**: Both deploy() and retrieve() are asynchronous. They return an AsyncResult ID immediately; you must poll checkDeployStatus() or checkRetrieveStatus() to know when they complete.

---

## Core Concepts

### Package.xml — The Manifest File

Package.xml is an XML manifest that tells the Metadata API exactly which components to retrieve or deploy. It is placed at the root of the zip file alongside the component folders.

Basic structure:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
  <types>
    <members>MyCustomObject__c</members>
    <name>CustomObject</name>
  </types>
  <types>
    <members>MyCustomObject__c.MyField__c</members>
    <name>CustomField</name>
  </types>
  <version>66.0</version>
</Package>
```

Rules:
- `<types>` — one block per metadata type
- `<name>` — the Metadata API type name (e.g., `CustomObject`, `ApexClass`, `Flow`)
- `<members>` — the component's full name. For child types: `ObjectName.ChildName`
- `<version>` — API version. Must be present. Determines which metadata types are available

**Wildcard (`*`) support**: Wildcards retrieve all components of a type but only for custom components. Standard objects (Account, Contact, etc.) do not support wildcards — each must be named explicitly. Wildcard retrieval also excludes components in managed packages.

### File-Based vs CRUD-Based Development

**File-based** (deploy/retrieve): The primary approach for CI/CD. Operates on a `.zip` file containing component files and a `package.xml` manifest. Asynchronous. Best for promoting full metadata model between environments.

**CRUD-based** (createMetadata, updateMetadata, deleteMetadata): Synchronous calls (API v30.0+) that act on individual components. Analogous to UI-based setup actions. Best for programmatic org setup scripts, not for bulk deployment pipelines.

Use file-based deploy/retrieve for DevOps workflows. Use CRUD-based calls only for programmatic setup utilities or ISV tooling.

### What Can and Cannot Be Retrieved

**Can be retrieved:**
- All custom objects and custom fields
- Apex classes, triggers, and test classes
- Lightning Web Components and Aura components
- Flows, Process Builder automations, Workflow rules
- Profiles and Permission Sets
- Assignment rules, escalation rules, auto-response rules
- Sharing rules (API v33.0+, all standard and custom objects)
- Custom settings, custom metadata types
- Page layouts, compact layouts, list views
- Standard objects — but must be named individually (no wildcard)
- Standard fields — only customizable ones (help text, history tracking, Chatter tracking). System fields (CreatedById, LastModifiedDate) are not supported.

**Cannot be retrieved:**
- Business data (records) — use Bulk API or Data Loader
- Users, Roles as live assignment data (the metadata type itself can be retrieved but not the live user records)
- Email attachments, document content (some content types have limits)
- Components locked inside managed packages cannot be retrieved as source files

**Wildcard behavior exceptions:**
- `<members>*</members>` with `CustomObject` retrieves all custom objects but NOT standard objects
- To retrieve all custom objects AND specific standard objects, list standard objects by name

### destructiveChanges.xml — Deleting Components

To delete components via deployment, include a file named `destructiveChanges.xml` in the same zip as `package.xml`. The format is identical to `package.xml` except wildcards are not supported.

The companion `package.xml` must be present but can have no components:

```xml
<!-- package.xml — empty, just version -->
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
  <version>66.0</version>
</Package>
```

```xml
<!-- destructiveChanges.xml — components to delete -->
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
  <types>
    <members>OldCustomObject__c</members>
    <name>CustomObject</name>
  </types>
</Package>
```

**Ordering deletions relative to additions:**
- Default (`destructiveChanges.xml`): deletions execute before any additions
- `destructiveChangesPre.xml`: explicitly run deletions before additions (same as default)
- `destructiveChangesPost.xml`: run deletions after additions (API v33.0+)

Use `destructiveChangesPost.xml` when a dependency must be cleared first — for example, removing the reference in an Apex class before deleting the custom object the class referenced.

**Important constraint**: You cannot use destructiveChanges.xml to delete components associated with an active Lightning App Builder page. Deactivate the page override first.

---

## Common Patterns

### Pattern 1 — Retrieve a Targeted Subset of Metadata

**When to use:** You need to pull specific components out of a production or sandbox org for version control or comparison.

**How it works:**
1. Create `package.xml` listing only the types and members you need
2. Run: `sf project retrieve start --manifest path/to/package.xml`
3. Inspect the downloaded files in the local project directory

**Example package.xml for Apex + custom object:**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
  <types>
    <members>*</members>
    <name>ApexClass</name>
  </types>
  <types>
    <members>Account</members>
    <members>*</members>
    <name>CustomObject</name>
  </types>
  <version>66.0</version>
</Package>
```

Note: this retrieves all Apex classes, all custom objects, and the Account standard object.

### Pattern 2 — Deploy to Production with Test Requirements

**When to use:** Promoting a change from sandbox to production containing Apex classes or triggers.

**How it works:**
1. Build `package.xml` with the components to deploy
2. Deploy: `sf project deploy start --manifest package.xml --test-level RunLocalTests`
3. Monitor status until the job completes. Fix any test failures before re-deploying.

**Test level options:**
- `NoTestRun` — no tests (only valid in non-production orgs)
- `RunSpecifiedTests` — run only the tests you list
- `RunLocalTests` — run all local tests except managed package tests (default for production when Apex is included)
- `RunAllTestsInOrg` — run everything including managed packages
- `RunRelevantTests` (Beta, API v58+) — auto-selects relevant tests based on payload analysis

**Code coverage requirement:** Every Apex class and trigger in the deployment must individually have at least 75% test coverage. The org-wide average does not substitute for per-component coverage.

### Pattern 3 — Delete a Component with a Dependency

**When to use:** A custom object must be removed but an Apex class still references it.

**How it works:**
1. `package.xml` — list the Apex class with the reference removed
2. `destructiveChangesPost.xml` — list the custom object to delete

Deploy once. The class update runs first; the object deletion runs after. This avoids the "component in use" error.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Retrieve specific known components | Named members in package.xml | Wildcards grab everything and slow retrieval |
| Retrieve all custom objects | `<members>*</members>` with `CustomObject` | Efficient; standard objects excluded automatically |
| Retrieve a standard object like Account | Name it explicitly: `<members>Account</members>` | Standard objects do not support wildcard retrieval |
| Delete a component with no dependencies | `destructiveChanges.xml` (default) | Simple delete-first ordering |
| Delete a component that is referenced by code | `destructiveChangesPost.xml` + updated class in `package.xml` | Clear the reference first, then delete |
| Deploy Apex to production | Set `--test-level RunLocalTests` | Required by platform; code coverage enforced per-component |
| Deploying only config (no Apex) to production | Default test level (no tests run) | Platform default skips tests when no Apex in payload |
| Bulk programmatic org setup | CRUD-based calls (createMetadata) | Synchronous, no zip/manifest overhead |

---


## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Gather context — confirm the org edition, relevant objects, and current configuration state
2. Review official sources — check the references in this skill's well-architected.md before making changes
3. Implement or advise — apply the patterns from Core Concepts and Common Patterns sections above
4. Validate — run the skill's checker script and verify against the Review Checklist below
5. Document — record any deviations from standard patterns and update the template if needed

---

## Review Checklist

Run through these before committing or deploying:

- [ ] `<version>` tag is present in package.xml and matches target API version
- [ ] All `<members>` values use the correct full name format (e.g., `Object.Field__c` for custom fields)
- [ ] Standard objects are named individually — no wildcard for standard objects
- [ ] destructiveChanges.xml does not use wildcards (not supported for deletions)
- [ ] If deleting a component referenced by Apex, destructiveChangesPost.xml is used and the referencing class is updated in the same deployment
- [ ] Components associated with active Lightning pages are not in the destructiveChanges.xml
- [ ] Test level is appropriate for target org type (production requires RunLocalTests if Apex is in payload)
- [ ] Each Apex class/trigger in the deployment has individual 75%+ test coverage
- [ ] The deploying user has "Modify Metadata Through Metadata API Functions" or "Modify All Data" plus "API Enabled"

---

## Salesforce-Specific Gotchas

1. **Wildcards silently exclude standard objects** — Using `<members>*</members>` for CustomObject returns only custom objects. Standard objects like Account, Contact, and Opportunity must each be named explicitly. Practitioners often assume wildcard means "everything" and then wonder why their standard object customizations were not retrieved.

2. **API version in package.xml overrides the client version** — The `<version>` tag in the manifest controls behavior, not the API version your CLI or code was compiled against. If you commit an old package.xml with version 40.0, you will get v40.0 metadata behavior even when deploying with a v66.0 client.

3. **75% code coverage is per-component, not org-wide** — A production deployment that includes an Apex class with 0% test coverage fails even if the org's aggregate coverage is 95%. Check per-class coverage with the Developer Console or `sf apex get coverage` before deploying.

4. **destructiveChanges.xml and active Lightning pages** — Attempting to delete a custom object that a Lightning App Builder page references will throw an error even if the object is otherwise unused. You must deactivate the override in Lightning App Builder before the deletion succeeds.

5. **Managed package components cannot be retrieved as source** — Attempting to retrieve a component in a managed package via package.xml returns empty or incomplete results. Use `packageNames` in RetrieveRequest or install the package through the normal AppExchange flow.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| package.xml | Manifest file listing types and members to retrieve or deploy |
| destructiveChanges.xml | Manifest listing components to delete (no wildcards) |
| destructiveChangesPost.xml | Deletion manifest that executes after additions in the same deployment |
| Deployment checklist | Pre-flight verification list before running deploy() |

---

## Related Skills

- sf-cli-and-sfdx-essentials — SFDX source format, sf CLI commands, and scratch org workflows; use alongside this skill for day-to-day developer operations
- soql-fundamentals — when you need to query org configuration data as a complement to metadata operations
