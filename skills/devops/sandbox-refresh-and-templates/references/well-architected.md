# Well-Architected Notes — Sandbox Refresh and Templates

## Relevant Pillars

### Reliability

Sandbox refresh reliability is foundational to release pipelines. Orgs that rely on manual post-refresh steps are one missed checklist item away from a broken test environment blocking a release.

- Automated post-refresh setup via `SandboxPostCopy` takes manual error off the critical path.
- Rescheduling the jobs each sandbox needs (scheduled jobs are not copied on refresh) keeps test cycles that depend on nightly processing from silently stalling.
- Template-driven Partial Copy sandboxes copy the same set of objects every cycle, reducing environment drift.

### Operational Excellence

Refresh cadence, ownership, and runbook quality determine how much operational overhead sandbox management consumes.

- A sandbox definition file per sandbox in source control makes the template and post-copy class part of the refresh, not something retyped in Setup.
- A pre-refresh checklist (next-available date, template, post-copy class, notifications) makes refresh a repeatable operation.
- A short manual runbook captures what the Automated Process user can't do, so the right person executes it every time.

### Security

Sandboxes that contain unmasked production personal data, or that call production systems with copied configuration, are real security and data-integrity risks.

- Masking in the post-copy class (or a Queueable it enqueues) keeps real customer data away from every sandbox user.
- Sandbox-specific Named Credentials and External Credentials keep production secrets out of sandboxes.
- Email deliverability for each sandbox is part of the runbook so test automation can't email real people.

### Performance

Template design affects refresh time and sandbox storage.

- Selecting objects the tests never read slows refresh and consumes storage.
- Omitting reference objects (catalog, configuration) produces missing data that fails tests; aim for the smallest object set that covers the suites.

## Architectural Tradeoffs

| Decision | Tradeoff |
|---|---|
| `SandboxPostCopy` vs. manual runbook | The class is faster and repeatable but runs with the Automated Process user's limited access; a runbook handles anything that user can't do |
| Partial Copy with template vs. Developer sandbox + data loading | Partial Copy gives a production-shaped data set for the selected objects; a Developer sandbox with scripted loads gives exact, repeatable records |
| Masking in `SandboxPostCopy` vs. a masking product | Apex masking is flexible and free but needs custom code per field; a product adds policy management at a licence cost |

## Anti-Patterns

1. **No post-copy class named on the sandbox** — Every refresh needs a long manual runbook, and one missed step breaks integrations or test data.
2. **Stored org IDs and URLs** — Values copied from production describe the wrong org in a sandbox; read the org ID at runtime.
3. **Partial Copy definition without a template** — `templateId` is required for Partial sandboxes; without a deliberate template the copied objects don't match the test suites.
4. **Personal data without masking** — Any sandbox that receives production data (Partial Copy, Full) needs masking before access is granted.

## Official Sources Used

Corpus: Summer '26 (API 67.0) PDFs; `sfdx_dev.txt` is the Salesforce DX Developer Guide fetched from resources.docs.salesforce.com/262 and converted with `pdftotext -layout`. Line numbers are `grep -n` positions.

- Apex Reference Guide (`salesforce_apex_reference_guide.txt`) L228876–228934 — `SandboxPostCopy` usage, the Automated Process user that isn't visible and lacks access to all objects, the run-after-activation fallback, `runApexClass(System.SandboxContext)` and the three context methods (SKILL.md Core Concepts, gotcha 4).
- Apex Reference Guide L228952–228958 — implementations must have a no-arg constructor used by the copy process (checker, Review Checklist).
- Apex Reference Guide L241140–241186 — `Test.testSandboxPostCopyScript` and the recommendation to use the `isRunAsAutoProcUser` overload (examples.md Example 1).
- Apex Developer Guide (`salesforce_apex_developer_guide.txt`) L16982–16983 — scheduled jobs from the source org aren't copied on refresh and must be rescheduled (gotcha 2, anti-pattern 4).
- `sfdx_dev.txt` L11240–11344 — sandbox definition file options: `apexClassId` / `apexClassName`, `autoActivate`, `licenseType` values, `sandboxName` (10 or fewer alphanumeric characters), one of `licenseType` / `sourceSandboxName` / `sourceId`, `templateId` required for Partial, optional for Full, not available for Developer types (gotcha 5, checker).
- `sfdx_dev.txt` L11408 and L11506–11516 — create copies metadata, plus data for Partial Copy and Full; refresh updates metadata and, for clones or template sandboxes, data; `sf org refresh sandbox --name ... --definition-file`, name can't change (Core Concepts, gotcha 7).
- Metadata API Developer Guide (`api_meta.txt`) L125434–125469 — `SandboxSettings.disableSandboxExpirationEmails`; expiration warnings for sandboxes inactive 180 days or longer (cli-refresh-runbook.md).
- Apex Reference Guide L95524–95538 — `ConnectApi.NamedCredentials.createCredential` (API 56.0) (gotcha 3).
- Salesforce Well-Architected Overview — Reliability and Operational Excellence framing: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
