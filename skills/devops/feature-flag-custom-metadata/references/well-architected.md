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

Corpus: Summer '26 (API 67.0) PDFs; line numbers are `grep -n` positions in the `pdftotext -layout` text.

- Apex Developer Guide (`salesforce_apex_developer_guide.txt`) L19616–19617 — the SOQL query limit doesn't apply to custom metadata types; unlimited SOQL against them in one transaction (Performance pillar, SKILL.md Core Concepts).
- Apex Reference Guide (`salesforce_apex_reference_guide.txt`) L204514–204516 — custom metadata is exposed in the application cache and available to formula fields, validation rules, flows, Apex, and SOAP API; L204570–204571 — `getAll()` / `getInstance()` return only the first 255 characters of any field (gotcha 4, Security pillar).
- Metadata API Developer Guide (`api_meta.txt`) L41316–41320 — Apex can edit custom metadata records in memory but not upsert or delete them, and deploys them but not via DML (gotchas 5 and 7).
- Apex Developer Guide L28195 and Apex Reference Guide L174164 — `Metadata.Operations.enqueueDeployment` queues an asynchronous deployment and returns an `Id` (examples.md Example 2, gotcha 5).
- Metadata API Developer Guide L41451–41470 and L41556–41566 — `CustomMetadata` records: `.md` suffix, `customMetadata` folder, `label` / `protected` / `values`, the `xsi:type` sample (SKILL.md XML fence).
- Metadata API Developer Guide L41716–41749 — valid `xsi:type` values per field type (no multi-select; `xsd:int` for scale-0 Number, `xsd:double` otherwise) (gotcha 4, SKILL.md XML fence).
- Metadata API Developer Guide L41750–41757 — `xsi:nil` clears a value; an omitted `<values>` element leaves an updated record's field at its previous value (gotcha 6).
- Metadata API Developer Guide L41298–41402 — custom metadata types as `CustomObject` with `__mdt`, `visibility` values, sample `.object` file (metadata-examples.md).
- Apex Developer Guide L13505 and L13514–13516 — custom settings data lives in the application cache, is copied into sandboxes, and is treated as data for Apex test isolation (Operational Excellence pillar, anti-pattern 1).
- Apex Reference Guide L215454 — `FeatureManagement.checkPermission(String apiName)` (examples.md Example 2, anti-pattern 7).
