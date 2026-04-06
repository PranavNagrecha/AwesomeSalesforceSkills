# Well-Architected Notes — Data Seeding For Testing

## Relevant Pillars

- **Reliability** — Test data seeding directly affects test reliability. Isolated, deterministic test data (via `@testSetup`) ensures tests produce the same result on every run across environments. Using `SeeAllData=true` introduces environment-dependent test behavior that undermines CI reliability.
- **Operational Excellence** — Version-controlled data seeding artifacts (plan JSON files, CumulusCI datasets) make sandbox and scratch org setup repeatable and auditable. Teams can reproduce any environment state on demand without manual steps.
- **Security** — CumulusCI dataset masking and Snowfakery synthetic generation ensure PII and sensitive production data never travels to lower environments. This supports GDPR, CCPA, and Salesforce Shield compliance requirements.

## Architectural Tradeoffs

- **Test isolation vs realism:** `@testSetup` gives perfect isolation but minimal data realism. CumulusCI datasets give production-like realism but require capture and maintenance. Choose based on the purpose of the test environment.
- **Speed vs reproducibility:** Scratch Org Snapshots reduce CI pipeline time but consume limited Dev Hub allocations and require a cleanup policy. Plan JSON imports are slower but always reproducible from source control.
- **Simplicity vs volume:** `sf data import tree` is simple to set up but capped at 200MB. CumulusCI and Bulk API handle large volumes but have more complex configuration.

## Anti-Patterns

1. **SeeAllData=true in production test classes** — Makes tests environment-dependent and breaks in scratch orgs. All test data must be explicitly created in `@testSetup` or the test method itself.
2. **Manually loading test data via UI between pipelines** — Not reproducible, not version-controlled, and gets lost on sandbox refresh. All seeded data should come from committed plan files or dataset artifacts.
3. **Committing production org data directly to source control** — Data exported from production may contain PII. Always apply masking rules before committing dataset files.

## Official Sources Used

- Salesforce DX Developer Guide — Test Data and Snapshots — https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_testing_test_data.htm
- Apex Developer Guide — Using the isTest(SeeAllData=true) Annotation — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_testing_seealldata_annotation.htm
- Salesforce CLI Reference — sf data import tree — https://developer.salesforce.com/docs/atlas.en-us.sfdx_cli_reference.meta/sfdx_cli_reference/cli_reference.htm
- Metadata API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm
