# Examples — Cloud-Specific Deployment Architecture

## Example 1: A coverage matrix that decides the pipeline before the pipeline exists

**Context:** A release spans platform metadata, Data 360 (Data Cloud) configuration, and an Agentforce agent. Three
teams each assume their components "deploy normally".

**Problem:** The assumption is untested until the production window. Metadata API support is not one property — the
Metadata Coverage report reports it per channel, and "Some metadata types may also be unsupported in source tracking,
packaging, and change sets." A type that deploys fine through the Metadata API but is invisible to source tracking
silently drops out of a source-tracked pipeline without failing anything.

**Solution:** Produce the matrix as a committed artifact, one row per component type, filled from the Metadata Coverage
report rather than from memory. Unknown is a valid value; guessed is not.

```yaml
# docs/release/coverage-matrix.yaml — checked in, reviewed, regenerated per release
release: 2026.09
components:
  - type: ApexClass
    cloud: platform
    metadata_api: supported
    source_tracking: supported
    channel: sfdx-manifest
    owner: platform-team

  - type: DataPackageKitDefinition        # top-level data kit container definition
    cloud: data-360
    metadata_api: check-report            # verify per release; kit contents move as a unit
    source_tracking: check-report
    channel: data-kit
    owner: data-team
    depends_on: [DataConnector, CustomerDataPlatformSettings]

  - type: DataConnectorS3                 # connection information specific to Amazon S3
    cloud: data-360
    metadata_api: check-report
    source_tracking: check-report
    channel: sfdx-manifest
    owner: data-team
    note: >-
      Connector config is separate metadata from the objects that consume it.
      Deploy settings, then connectors, then the kit that depends on them.

  - type: AnalyticsDashboard
    cloud: analytics
    metadata_api: supported
    source_tracking: supported
    channel: sfdx-manifest
    owner: analytics-team
    limits:
      individual_deploy: 50               # max per package zip
      daily_deploys: 100                  # org-wide, rolling 24h
    note: >-
      Counted type. Split into its own stage; do not redeploy on every merge.

manual_steps:                             # anything the report marks unsupported
  - description: <component the report marks unsupported in Metadata API>
    reason: >-
      "To make changes to these types, you must do it manually in each of your
      organizations." — Metadata API Developer Guide
    owner: <named person, not a team>
    environments: [uat, staging, prod]
```

**Why it works:** The matrix converts an assumption into a lookup with an owner attached. The `manual_steps` block is
the important half: unsupported types do not fail the deploy, they simply do not travel, so the only defence is a
runbook entry that exists before the release. The `limits` block on counted types stops a per-commit pipeline being
designed against a daily org-wide ceiling.

---

## Example 2: Ordering a mixed-cloud release inside one manifest set

**Context:** The release updates an Apex class and removes a custom field the class currently references, alongside
Data 360 configuration that must land after the org settings it depends on.

**Problem:** Teams reach for two deployments and an interval nobody tested. Within a single deployment, the platform's
default works against them: "By default, deletions are processed before component additions."

**Solution:** One manifest set, with deletion deferred and the API version pinned deliberately across every stage.

`manifest/package.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>SegmentService</members>
        <name>ApexClass</name>
    </types>
    <types>
        <members>*</members>
        <name>CustomerDataPlatformSettings</name>
    </types>
    <version>67.0</version>
</Package>
```

`manifest/destructiveChangesPost.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Account.Legacy_Segment__c</members>
        <name>CustomField</name>
    </types>
</Package>
```

```bash
sf project deploy start \
  --manifest manifest/package.xml \
  --post-destructive-changes manifest/destructiveChangesPost.xml \
  --test-level RunLocalTests \
  --target-org prod --wait 60
```

**Why it works:** The `Post` manifest defers the field deletion until after `SegmentService` no longer references it,
and "Post destructive changes are processed before running any tests" — so `RunLocalTests` executes against the
post-deletion state. The `<version>67.0</version>` matters across clouds specifically because "The API version that the
deployment uses is the API version that's specified in `package.xml`": per-cloud manifests carrying different versions
deploy the same release under different runtime semantics.

---

## Anti-Pattern: One pipeline stage, one manifest, every cloud

**What practitioners do:** Build a single stage that deploys `manifest/package.xml` containing every component type in
the release, on every merge to the integration branch.

**What goes wrong:** Three failures share this shape. Counted types (`AnalyticsDashboard`, `AnalyticsVisualization`,
`AnalyticsWorkspace`, `AIAuthoringBundle`) burn an org-wide daily allowance of 100 metadata deploys against merges that
did not touch them. Types unsupported in source tracking drop out of the payload without an error. And a single
`<version>` applied to every cloud's components removes the ability to stage an API version bump for one team at a time.

**Correct approach:** One stage per deployment channel, ordered by dependency, with counted types isolated:

```yaml
stages:
  - name: org-settings
    manifest: manifest/settings.xml            # CustomerDataPlatformSettings and friends
  - name: platform
    manifest: manifest/platform.xml            # Apex, LWC, Flow, objects
    post_destructive: manifest/destructiveChangesPost.xml
  - name: data-360-connectors
    manifest: manifest/connectors.xml          # DataConnector, DataConnectorS3, DataConnectorIngestApi
    depends_on: [org-settings]
  - name: data-360-kit
    manifest: manifest/data-kit.xml            # DataPackageKitDefinition + kit objects
    depends_on: [data-360-connectors]
  - name: counted-types                        # runs only when these components changed
    manifest: manifest/analytics.xml
    when: changed
  - name: manual
    runbook: docs/release/coverage-matrix.yaml # the unsupported types, with owners
```

Deploying deltas rather than the full manifest is what keeps the counted-type budget intact, and the `when: changed`
guard is what makes the delta real rather than aspirational.
