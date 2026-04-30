# Well-Architected Notes — Code Coverage Orphan Class Cleanup

## Relevant Pillars

- **Operational Excellence** — A 75% threshold met through stub tests is a maintenance liability that masks real test gaps. Removing dead code is the cleanest way to keep the threshold meaningful.
- **Reliability** — Orphan classes are uncovered by definition. They sometimes contain code paths that would crash in production if invoked. Deleting them removes a category of "lurking" failure that no test will surface.

## Architectural Tradeoffs

- **Delete vs. retain-and-test:** Both raise coverage. Delete is faster, removes maintenance burden, and reduces denominator. Retain-and-test preserves optionality but is only worth it if the class is referenced or has reactivation value.
- **Hard delete vs. `@deprecated` then delete:** Soft-delete via the deprecation annotation gives one release cycle for hidden references to surface. Cheaper than rolling back a destructive deploy.
- **Per-deploy rescue vs. quarterly tax:** Treating cleanup as a routine quarterly tech-debt sweep keeps the org healthy. Treating it as a Friday-afternoon firefight when coverage drops below 75% is the alternative — predictable, expensive.

## Anti-Patterns

1. **Stub tests for the threshold** — Tests that don't assert behavior dishonor the coverage signal. Coverage rises while real safety drops.
2. **Mass-delete without sandbox verification** — Skipping the sandbox-deploy step misses indirect references (Flow XML, validation-rule formulas referencing `$Apex.X`). Every destructive deploy must validate against a fresh test run in a non-production environment first.
3. **Treating coverage as the metric instead of a proxy** — The 75% threshold is a deploy gate, not a testing strategy. Cleanup brings the metric back in line; real test improvement comes from `apex/test-class-standards`.

## Official Sources Used

- Metadata API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm
- Salesforce CLI Reference — https://developer.salesforce.com/docs/atlas.en-us.sfdx_cli_reference.meta/sfdx_cli_reference/cli_reference.htm
- Salesforce DX Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_intro.htm
- Apex Code Coverage Tooling API — https://developer.salesforce.com/docs/atlas.en-us.api_tooling.meta/api_tooling/tooling_api_objects_apexcodecoverageaggregate.htm
- Apex Developer Guide (Test Coverage) — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_code_coverage_intro.htm
