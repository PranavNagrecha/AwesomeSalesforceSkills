# Skill Factuality Report — 2026-04-17

**Org:** `sfskills-dev`
**Sample size:** 100 skill(s)
**Classified as testable (make platform claims):** 32
**Classified as guidance (skipped):** 68

**Testable skills with clean claims:** 32
**Testable skills with wrong claims:** 0

Sample seed: `42` (re-runnable). Verified via `sf sobject describe`.

## No factual errors detected in sample

## Clean testable skills

- `apex/commerce-payment-integration` — 0 claim(s) verified
- `integration/sis-integration-patterns` — 0 claim(s) verified
- `integration/streaming-api-and-pushtopic` — 1 claim(s) verified
- `apex/custom-logging-and-monitoring` — 0 claim(s) verified
- `apex/marketing-cloud-data-views` — 0 claim(s) verified
- `devops/environment-specific-value-injection` — 0 claim(s) verified
- `integration/outbound-messages-and-callbacks` — 0 claim(s) verified
- `data/patient-data-migration` — 0 claim(s) verified
- `flow/flow-governance` — 0 claim(s) verified
- `admin/gift-entry-and-processing` — 0 claim(s) verified
- `data/territory-data-alignment` — 1 claim(s) verified
- `agentforce/mcp-tool-definition-apex` — 0 claim(s) verified
- `flow/flow-bulkification` — 0 claim(s) verified
- `flow/flow-large-data-volume-patterns` — 0 claim(s) verified
- `data/data-storage-management` — 0 claim(s) verified
- `agentforce/einstein-discovery-development` — 0 claim(s) verified
- `data/batch-data-cleanup-patterns` — 0 claim(s) verified
- `integration/retry-and-backoff-patterns` — 0 claim(s) verified
- `devops/code-review-checklist-salesforce` — 0 claim(s) verified
- `apex/cpq-apex-plugins` — 0 claim(s) verified
- `data/person-accounts` — 0 claim(s) verified
- `apex/custom-iterators-and-iterables` — 0 claim(s) verified
- `omnistudio/flexcard-design-patterns` — 0 claim(s) verified
- `devops/sandbox-data-isolation-gotchas` — 0 claim(s) verified
- `data/field-history-tracking` — 0 claim(s) verified
- `apex/health-cloud-apex-extensions` — 0 claim(s) verified
- `apex/fsl-service-report-templates` — 0 claim(s) verified
- `architect/industries-data-model` — 1 claim(s) verified
- `flow/flow-error-monitoring` — 0 claim(s) verified
- `agentforce/sf-to-llm-data-pipelines` — 4 claim(s) verified
- ... and 2 more

## Methodology notes

- Skills are classified as testable when they contain 2+ markers like 'SOQL', 'describe', 'sObject', 'governor limit'.
- Field refs of the form `SObject.Field` are extracted and verified against the target org's describe output.
- Relationship traversals (e.g. `Profile.Name`) are 'unverifiable' — they can't be checked without relationship-name context.
- Custom objects and managed-package fields are not verified (the target org may not have them).
- This is a sampler, not exhaustive — 30 field refs per skill maximum.