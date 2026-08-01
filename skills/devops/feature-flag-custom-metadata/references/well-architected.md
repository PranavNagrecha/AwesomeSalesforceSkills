# Well-Architected Notes — Feature Flags via Custom Metadata

**Operational Excellence:** the flag exists to separate deploying from releasing, and a
record committed in the enabled state silently collapses that separation — the feature goes
live the moment the deployment finishes, which is the outcome the flag was added to prevent.
Committing the safe default and treating enablement as a separate, per-environment act is
what makes the mechanism worth its complexity.

**Operational Excellence, environment parity:** this is the argument for Custom Metadata
over a Custom Setting, and it is the whole argument. CMDT records are metadata, so the
flag's existence and its default travel with the source and a fresh sandbox is correct by
construction. Custom Setting records are data: they do not deploy, so every environment
accumulates a hand-made set that drifts, and production's set is eventually reproducible by
nobody. The price is that CMDT cannot be changed by ordinary DML — a real constraint, and
the cheaper one to live with.

**Performance:** the governor documentation exempts custom metadata types from the SOQL
query limit outright, which removes the usual reason to pass a flag value through call
signatures. The exemption is narrow: it covers queries, not CPU, and it does not extend to
Custom Settings. A flag evaluated per record inside a bulk loop is still a CPU cost, so the
read belongs above the loop for that reason rather than for a limit reason.

**Correctness:** a percentage rollout implemented with randomness is not a rollout. It flips
per evaluation, so a user's experience changes between page loads, in-flight work is lost,
and no defect report can be tied to a code path. A stable hash of user id plus flag name
gives an answer that is reproducible from the bug report and does not concentrate every
canary on the same unlucky cohort.

**Security:** the boundary that gets crossed by accident is flag-versus-permission. A flag
answers whether a code path is live in this org; a permission answers whether this user may
do this thing. Implementing per-user entitlement as an allow-list field on a flag puts an
access-control decision somewhere with no sharing model, no audit trail and no presence in a
permissions review — and the field will silently truncate at 255 characters when read
through the cached accessors, so the control fails open for whoever is past the cut. If the
list is expected to exist in a year, it is a permission.

## Official Sources Used

- Apex Governor Limits — the explicit SOQL exemption for custom metadata types — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_gov_limits.htm
- Custom Metadata Type Methods — `getAll()` / `getInstance()`, the application cache, and the 255-character field truncation — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_methods_system_custom_metadata_types.htm
- Retrieving and Deploying Metadata in Apex — `Metadata.Operations.enqueueDeployment()` and its asynchronous behaviour — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_metadata_retrieve_deploy.htm
- Metadata.CustomMetadata class — the `fullName`, `label` and `values` shape used to build a deployment — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_class_Metadata_CustomMetadata.htm
- Custom Metadata Types (CustomObject) in the Metadata API — how the records are represented in source — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_custommetadatatypes.htm
- Custom Metadata Allocations and Usage Calculations — the per-org limits that bound how many flags you can have — https://help.salesforce.com/s/articleView?id=platform.custommetadatatypes_limits.htm&type=5
