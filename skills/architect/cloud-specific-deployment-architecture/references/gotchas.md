# Gotchas — Cloud-Specific Deployment Architecture

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Coverage is a lookup, never a recollection — and "unsupported" means manual, forever

**What happens:** Every cloud-specific pipeline design starts with an implicit claim: "this component type ships
through the Metadata API." That claim is checkable and frequently wrong, and it changes every release. The Metadata API
Developer Guide names the authority: "Launch the Metadata Coverage report to determine supported metadata components.
The Metadata Coverage report is the ultimate source of truth for metadata coverage across several channels. These
channels include Metadata API, scratch org source tracking, unlocked packages, second-generation managed packages,
classic managed packages, and more." It also states the cost of guessing wrong: "Some Salesforce features have metadata
types that aren't available in Metadata API. These metadata types can't be retrieved or deployed with Metadata API. To
make changes to these types, you must do it manually in each of your organizations."

**When it occurs:** At the end of a multi-cloud release, when the component that has to be clicked in every environment
is discovered during the production window rather than during design.

**How to avoid:** Make the coverage check a design artifact, not a conversation. For every component type in scope,
record the four columns the report gives you — Metadata API, source tracking, unlocked package, managed package — and
mark the manual ones as runbook steps with a named owner before the pipeline is built. The report needs no org login,
so there is no reason to defer the check. Note the second sentence too: "Some metadata types may also be unsupported in
source tracking, packaging, and change sets" — Metadata API support does not imply the other three.

---

## Gotcha 2: Data Cloud is `Data 360` in the metadata, and its unit of deployment is a data kit

**What happens:** The Metadata API Developer Guide carries a dedicated chapter — *Data 360 Metadata Types* — and the
types there are not shaped like platform metadata. The connector, the activation target, and the object templates are
each their own type: `DataConnector` ("the white-labeled metadata configuration for an external connector in Data
360"), `DataConnectorS3` ("the connection information specific to Amazon S3"), `DataConnectorIngestApi`,
`ActivationPlatform` ("the ActivationPlatform configuration, such as platform name, delivery schedule, output format,
and destination folder"), `ActvPfrmDataConnectorS3`, and `CustomerDataPlatformSettings` ("an org's Data 360 settings").

The packaging unit is the data kit: `DataPackageKitDefinition` is "the top-level data kit container definition",
`DataKitObjectTemplate` and `DataPackageKitObject` are the objects inside it, and `DataKitObjectDependency` "represents
the dependency between two data kit objects".

**When it occurs:** When a pipeline is designed around "deploy the DMOs" and discovers that the object templates travel
in a kit, the connector is separate metadata, and the org-level settings are a third thing that a sandbox refresh does
not carry.

**How to avoid:** Model Data 360 as three separate deployables with an explicit order — org settings, then connectors,
then the data kit that depends on them — and search the guide for `Data 360`, not `Data Cloud`, when checking whether a
type exists. Searching the old product name is how teams conclude a supported type is unsupported.

---

## Gotcha 3: Certain metadata types carry per-deploy and per-day counts

**What happens:** "Certain metadata types have deploy and retrieve limits. Limits apply to each individual deploy or
retrieve transaction, and there are daily limits for specific metadata types. The individual deploy and retrieve limits
represent the maximum count that a metadata type may be deployed or retrieved in a single package zip. Daily deploy and
retrieve limits apply to individual org usage within a 24-hour period." The published numbers are Individual Metadata
Deploy 50, Daily Metadata Deploys 100, Individual Metadata Retrieve 100, Daily Metadata Retrievals 200, and they apply
to a named list that includes `AIAuthoringBundle`, `AnalyticsDashboard`, `AnalyticsVisualization`, and
`AnalyticsWorkspace`.

**When it occurs:** In analytics-heavy and Agentforce-heavy orgs where a single logical release contains dozens of
bundles, and in pipelines that redeploy the full manifest per merge. The daily ceiling is org-wide across a rolling
24-hour window, so several teams sharing an org share the budget — and the team that exhausts it is rarely the team
that needs the next deploy.

**How to avoid:** Split affected types into their own pipeline stage, deploy deltas rather than the whole manifest, and
check the counted-type list before designing any per-commit redeploy. In a shared org, publish the daily budget
alongside the release calendar so the constraint is visible to every team drawing on it.

---

## Gotcha 4: Deletion order and API version are set by the manifest, not the cloud

**What happens:** Cross-cloud releases fail on ordering more often than on content. Two platform defaults do the
damage: "By default, deletions are processed before component additions" — so a component still referenced by
something being updated in the same payload cannot be removed unless you move it to `destructiveChangesPost.xml`
(available since API version 33.0) — and "The API version that the deployment uses is the API version that's specified
in `package.xml`", regardless of the CLI or the org's release.

**When it occurs:** In pipelines assembled per cloud with separate manifests, where each manifest carries its own
`<version>` and nobody reconciles them. Two stages of the same release then deploy under different API semantics.

**How to avoid:** Reconcile `<version>` across every manifest in a release and treat it as a release-level decision.
Choose `destructiveChangesPre.xml` or `destructiveChangesPost.xml` per deletion rather than defaulting, and note that
"Post destructive changes are processed before running any tests", which determines the state your tests will see.

## Official Sources Used

- Metadata API Developer Guide, Version 67.0 (Summer '26) — *Metadata Types*: the Metadata Coverage report is "the
  ultimate source of truth for metadata coverage across several channels", and the channel list it covers.
  https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_types_list.htm (verified 2026-08-14)
- Metadata API Developer Guide, Version 67.0 — *Unsupported Metadata Types*: the manual-in-every-org consequence, and
  "Some metadata types may also be unsupported in source tracking, packaging, and change sets."
  https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_unsupported_types.htm (verified 2026-08-14)
- Metadata API Developer Guide, Version 67.0 — *Data 360 Metadata Types*: `DataConnector`, `DataConnectorS3`,
  `DataConnectorIngestApi`, `ActivationPlatform`, `ActvPfrmDataConnectorS3`, `CustomerDataPlatformSettings`,
  `DataPackageKitDefinition`, `DataKitObjectTemplate`, `DataPackageKitObject`, `DataKitObjectDependency`, and the
  current product naming.
  https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_data_cloud_types.htm (verified 2026-08-14)
- Metadata API Developer Guide, Version 67.0 — *Metadata Type Limits*: Individual Metadata Deploy 50, Daily Metadata
  Deploys 100, Individual Metadata Retrieve 100, Daily Metadata Retrievals 200, applied to `AIAuthoringBundle`,
  `AnalyticsDashboard`, `AnalyticsVisualization`, and `AnalyticsWorkspace`.
  https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_metadata_type_limits.htm (verified 2026-08-14)
- Metadata API Developer Guide, Version 67.0 — *Deleting Components from an Organization*: default deletion ordering,
  the `Pre`/`Post` manifests (API version 33.0 and later), and that the deployment's API version comes from
  `package.xml`.
  https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_deploy_deleting_files.htm (verified 2026-08-14)
- Metadata Coverage report — the tool the guide designates as authoritative, linked from the guide as *Metadata
  Coverage*; not fetched directly for this note.
