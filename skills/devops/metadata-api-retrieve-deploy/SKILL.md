---
name: metadata-api-retrieve-deploy
description: "Metadata API retrieve/deploy via sf CLI and package.xml: manifest authoring, destructiveChanges, deploy options (checkOnly, testLevel, rollbackOnError), CI scripting. NOT for DX source format conversions (use salesforce-dx-source-tracking). NOT for unlocked packages (use unlocked-packages)."
category: devops
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Security
tags:
  - metadata-api
  - sf-cli
  - package-xml
  - deploy
  - destructive-changes
triggers:
  - "salesforce metadata api retrieve package.xml manifest"
  - "sf project deploy start checkonly testlevel"
  - "destructivechanges pre vs post for metadata removal"
  - "rollbackonerror false partial deploy risk"
  - "metadata api ci pipeline authentication"
  - "package.xml wildcards vs explicit members"
inputs:
  - Source org auth alias
  - Target org auth alias
  - Metadata scope (component types, names)
  - Deployment policy (check-only, test level)
outputs:
  - package.xml manifest
  - destructiveChanges manifest (if removing)
  - sf CLI retrieve and deploy commands
  - CI pipeline stanza
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-21
---

# Metadata API Retrieve / Deploy

Activate when retrieving or deploying Salesforce metadata via `sf` CLI (Metadata API or Source Format). This skill covers manifest authoring (`package.xml`), destructive-change handling, deploy options (`checkOnly`, `testLevel`, `rollbackOnError`), and CI pipeline wiring. Missteps corrupt orgs: partial deploys with `rollbackOnError=false` leave production half-configured; wildcards in `package.xml` pull thousands of unrelated components.

## Before Starting

- **Decide manifest scope.** Explicit members (safer for CI) vs wildcards (broad retrieve for initial capture).
- **Choose test level.** Production deploys require `RunLocalTests` or `RunSpecifiedTests`.
- **Decide rollback policy.** `rollbackOnError=true` is the safe default; `false` creates partial-state risk.
- **Pre or post destructive?** Pre runs deletions before adds (safe for rename); post runs deletions after (safe when new metadata depends on old).

## Core Concepts

### package.xml manifest

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Account.Industry__c</members>
        <members>Account.Region__c</members>
        <name>CustomField</name>
    </types>
    <types>
        <members>AccountTrigger</members>
        <name>ApexTrigger</name>
    </types>
    <version>60.0</version>
</Package>
```

Use explicit members for CI; wildcards (`<members>*</members>`) for one-off retrieves.

### Retrieve

```
sf project retrieve start \
  --target-org source-sandbox \
  --manifest manifest/package.xml \
  --output-dir force-app
```

### Deploy

```
sf project deploy start \
  --target-org prod \
  --manifest manifest/package.xml \
  --test-level RunSpecifiedTests \
  --tests AccountTriggerTest \
  --wait 60
```

Use `--dry-run` (or `--check-only` equivalent) to validate without committing.

### destructiveChanges

```
destructiveChangesPre.xml  → deletions BEFORE deploy
destructiveChanges.xml     → deletions AFTER deploy (default)
destructiveChangesPost.xml → alias for post
```

Pair with an empty `package.xml` that references only the API version.

### Test levels

| Level | Behavior |
|---|---|
| NoTestRun | Sandbox only; prod rejects |
| RunSpecifiedTests | Provide `--tests` list |
| RunLocalTests | All tests except managed packages (required for prod) |
| RunAllTestsInOrg | All tests including managed |

### rollbackOnError

Default `true`. Setting `false` is dangerous — a failed component leaves orphaned partial metadata. Rarely useful outside scripted cleanup.

## Common Patterns

### Pattern: CI deploy gate

```bash
sf project deploy validate \
  --target-org prod \
  --manifest manifest/package.xml \
  --test-level RunLocalTests \
  --wait 120
# Later in the pipeline, after approval:
sf project deploy quick --job-id <ID> --target-org prod
```

`validate` runs tests and produces a job ID reusable by `quick` within 10 days.

### Pattern: Rename a field (pre-destructive)

```xml
<!-- destructiveChangesPre.xml -->
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types><members>Account.OldName__c</members><name>CustomField</name></types>
    <version>60.0</version>
</Package>
<!-- package.xml adds Account.NewName__c -->
```

### Pattern: Authenticated CI login

```
sf org login jwt \
  --username ci@example.com \
  --jwt-key-file server.key \
  --client-id $CONSUMER_KEY \
  --instance-url https://login.salesforce.com \
  --alias prod
```

## Decision Guidance

| Scenario | Approach |
|---|---|
| Production deploy | validate → quick; `RunLocalTests`; `rollbackOnError=true` |
| Sandbox refresh | `sf project deploy start` with `NoTestRun` |
| Field rename | destructiveChangesPre + package.xml add |
| Component removal | destructiveChanges (post) |
| One-off manual retrieve | wildcard manifest |
| CI retrieve | explicit manifest under version control |

## Recommended Workflow

1. Author `package.xml` with explicit members matching the change scope.
2. If removing metadata, add `destructiveChangesPre.xml` or `destructiveChanges.xml`.
3. Retrieve from source org; commit metadata diff.
4. Run `sf project deploy validate` against target; capture job ID.
5. Review test results and coverage.
6. On approval, run `sf project deploy quick --job-id <ID>`.
7. Tag the deploy in git; archive manifest + job ID for rollback trace.

## Review Checklist

- [ ] Manifest uses explicit members (no unintentional wildcards)
- [ ] `rollbackOnError=true` (default) on production deploys
- [ ] Test level is `RunLocalTests` or `RunSpecifiedTests` for prod
- [ ] Destructive changes paired with empty package.xml
- [ ] validate → quick pattern used for high-risk deploys
- [ ] JWT auth used in CI (never username/password)
- [ ] Deploy job ID archived for traceability

## Salesforce-Specific Gotchas

1. **Quick-deploy job IDs expire after 10 days** — re-validate if the window passes.
2. **`<members>*</members>` for `CustomObject` includes standard objects' field overrides** — unexpectedly large diff.
3. **Profiles and Permission Sets retrieve only fields/objects referenced in the manifest.** To get full profile content, the package.xml must also include the referenced metadata.

## Output Artifacts

| Artifact | Description |
|---|---|
| `manifest/package.xml` | Explicit member list |
| `manifest/destructiveChanges.xml` | Pre/post destructive manifest |
| CI pipeline stanza | validate + quick-deploy steps |
| JWT auth bootstrap | `sf org login jwt` command + server.key generation |

## Related Skills

- `devops/salesforce-dx-source-tracking` — source-format projects and track commands
- `devops/unlocked-packages` — modular packaged metadata
- `devops/apex-test-coverage-strategy` — test level tuning
