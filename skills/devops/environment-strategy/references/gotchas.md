# Gotchas — Environment Strategy

Non-obvious Salesforce platform behaviors that cause real production problems when designing environment topology.

## Gotcha 1: Scratch Org Data Is Lost on Expiry and Cannot Be Pushed to Another Org

**What happens:** All data loaded into a scratch org — via `sf data import`, Apex anonymous scripts, or manual entry — is permanently destroyed when the scratch org expires or is deleted. There is no migration path for data from a scratch org to another org. Data is not tracked by source tracking; only metadata is tracked and deployable.

**When it occurs:** Teams that use scratch orgs as shared development environments and load test data into them expecting to push that data downstream. Occurs when a developer builds a complex data scenario in a scratch org to demonstrate a feature, then tries to replicate it in UAT.

**How to avoid:** Treat scratch orgs as zero-data environments. All test data must be scripted: use Salesforce CLI data plan files (`sf data import tree`), Apex anonymous scripts, or a seeding pipeline that re-creates data on demand. Store data scripts in source control alongside metadata. Never rely on a scratch org as the source of record for test data.

---

## Gotcha 2: Sandbox Preview Opt-In Can Break CI Before Production Is Affected

**What happens:** Salesforce rolls new major releases to sandboxes in two waves. Sandboxes enrolled in the Sandbox Preview program receive the new release several weeks before production. If a sandbox or scratch org shape references features, field behavior, or API versions that behave differently between the current release and the preview release, CI pipelines can start failing on preview-enrolled environments while production is unaffected.

**When it occurs:** When a CI pipeline targets a sandbox that has been auto-enrolled in Sandbox Preview, or when scratch org shapes use `release: preview` in the definition file. Apex API version mismatches, LWC behavior changes, and Flow behavior changes are common triggers.

**How to avoid:** For sandboxes used as CI targets, explicitly opt out of Sandbox Preview from Setup > Sandboxes unless the team deliberately wants early testing of release changes. For scratch orgs, default scratch org shapes do not opt into preview — avoid adding `"release": "preview"` to `project-scratch-def.json` unless testing release readiness is the explicit goal. Monitor the Salesforce Trust release calendar to know which sandboxes are affected and when.

---

## Gotcha 3: Full Sandbox 29-Day Refresh Limit Interacts Poorly with Incident Response

**What happens:** The Full sandbox can only be refreshed once every 29 days. If a production incident requires troubleshooting in a Full sandbox and the sandbox is refreshed mid-cycle, the next planned refresh (for a quarterly release, for example) is pushed out by the full 29-day clock from the incident refresh date. Teams that use the Full sandbox for both incident investigation and pre-production regression find themselves locked out of the refresh they need.

**When it occurs:** When the same Full sandbox serves two purposes: reactive incident investigation and proactive pre-production testing. Any unplanned refresh consumes the 29-day window.

**How to avoid:** Separate Full sandbox usage by purpose. If the org has more than one Full sandbox allocation, dedicate one to production rehearsal and one to incident analysis. If only one Full sandbox is available, document a clear policy for when an unplanned refresh is authorized and communicate the downstream impact to the release schedule before acting.

---

## Gotcha 4: Source Tracking Is Not Available on Partial Copy or Full Sandboxes

**What happens:** Salesforce CLI source tracking (`sf project deploy start` with tracked metadata) only works with scratch orgs and Developer/Developer Pro sandboxes. Partial Copy and Full sandboxes do not support source tracking. Attempting to run source-tracked deployment commands against a Partial or Full sandbox results in errors or falls back to manifest-based deployment silently depending on the CLI version.

**When it occurs:** When a CI pipeline designed for source-tracked scratch org deployments is pointed at a Partial Copy sandbox for UAT validation without adjusting the deployment command. Also occurs when a team assumes that adding `--track-source` to any `sf project deploy start` command will work regardless of org type.

**How to avoid:** Use `sf project deploy start --manifest package/package.xml` (manifest-based) for all deployments targeting Partial Copy or Full sandboxes. Reserve source-tracked deployment commands exclusively for scratch orgs and Developer/Developer Pro sandboxes. Document this distinction explicitly in the CI pipeline scripts so future maintainers do not inadvertently switch approaches.

---

## Gotcha 5: Active Scratch Org Count Limit Applies Per Dev Hub, Not Per Project

**What happens:** Each Dev Hub has a maximum number of simultaneously active scratch orgs — typically 40 for standard editions, up to 200 for higher-tier plans (Salesforce DX Developer Guide). This limit is shared across all projects, teams, and CI pipelines using the same Dev Hub. A CI pipeline that creates scratch orgs per PR but never deletes them will silently hit the limit. Once the limit is reached, `sf org create scratch` fails with a capacity error, blocking all CI runs org-wide — including unrelated projects.

**When it occurs:** In multi-team programs where several projects share one Dev Hub. Also in repositories where CI creates scratch orgs on PR open but deletion is triggered only on merge — leaving long-lived PRs consuming active slots.

**How to avoid:** Every CI pipeline that creates a scratch org must also delete it. Use `sf org delete scratch --no-prompt --target-org <alias>` in a CI cleanup step that runs even on pipeline failure. Add a scheduled cleanup job that lists active scratch orgs (`sf org list`) and deletes any that are expired or orphaned. Monitor active scratch org counts in Dev Hub dashboards and set alerts before hitting the limit.
