# Well-Architected Notes — Pull Request Policy Templates

**Operational Excellence:** the recurring defect in generated policy is that it is inert
rather than wrong. Ownership paths that do not match a source-format tree, and required
check names the pipeline never emits, both produce a repository that appears governed and is
not — and neither failure announces itself, because the files exist and were reviewed. Both
are cheap to verify once, against a real tree and a completed pipeline run, and almost never
verified.

**Operational Excellence, attention as the scarce resource:** a policy that requires the
same scrutiny everywhere spends it uniformly on changes that do not need it, and reviewers
adapt by approving faster. Concentrating escalation on the metadata where a change is
irreversible or org-wide — profiles, permission sets, sharing rules, destructive changes,
field removals — puts the cost where the risk is and leaves ordinary changes cheap to merge.

**Reliability:** static analysis measures the source; deployment failures are almost always
about the destination. A required check that never contacts an org cannot see a field
reference missing from the target, a picklist value that does not exist there, or a profile
citing a permission the target lacks. A check-only validation is the only gate that consults
the org's real state, which is why it is worth its runtime even though it is the slowest
thing in the pipeline.

**Reliability, gates that block the fix:** the platform's 75% coverage requirement is
org-wide across all Apex, not a per-PR delta. Applied as a per-PR block it fails every pull
request equally once the org drifts under the line — including the one that would restore
it — which converts a quality gate into an outage. The org-wide figure belongs on the
pre-production validation; a PR should assert only what its author controls.

**Durability:** every part of the policy that names a person rather than a group has a
built-in expiry. An individual owner turns a departure into an unmergeable path, the
resolution is an administrative override, and once the override is routine the policy has
stopped constraining anything. The same reasoning applies to the template: one that exceeds
a screen is deleted by authors rather than completed, and the deployment notes and rollback
plan it existed to capture — the two things genuinely impossible to reconstruct from a diff
after a destructive change — are what get lost.

## Official Sources Used

- Metadata API `deploy()` — `checkOnly` validation and the `testLevel` values, including `RunLocalTests` as the production default and `NoTestRun` being unavailable there — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_deploy.htm
- Apex Code Coverage — the org-wide 75% requirement for deploying to production — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_code_coverage_intro.htm
- Salesforce DX Project Structure and Source File Format — the directory layout the ownership rules must match, including `objects/<Object>/fields/` — https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_source_file_format.htm
- Deleting Components from an Org — destructive changes and why reverting a commit does not undo them — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_deploy_deleting_files.htm
- Salesforce CLI project commands — `sf project deploy validate` and `sf project deploy start` — https://developer.salesforce.com/docs/platform/salesforce-cli-reference/guide/cli_reference_project_commands_unified.html
