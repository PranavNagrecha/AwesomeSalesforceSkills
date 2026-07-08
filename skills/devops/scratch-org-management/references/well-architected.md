# Well-Architected Notes — Scratch Org Management

## Relevant Pillars

- **Reliability** — Scratch org allocation limits are hard platform constraints. CI pipelines that do not explicitly delete orgs after each run will exhaust the pool and cause test failures unrelated to the code under test. Designing reliable lifecycle management (unconditional delete steps, short `--duration-days` for CI) directly supports pipeline reliability.

- **Operational Excellence** — The definition file is the operational specification for the development environment. Keeping it accurate and version-controlled ensures every developer and CI job gets the same environment. Drifting definition files (e.g., using deprecated `orgPreferences`, missing production features) are an operational risk that causes inconsistent test results.

- **Adaptable** — Org Shape allows scratch orgs to automatically adapt to changes in the production org's feature configuration without requiring manual definition file maintenance. This is the more adaptable pattern for mature teams where production features change regularly.

## Architectural Tradeoffs

**Definition File vs. Org Shape:**
A hand-maintained definition file gives precise, portable, version-controlled control over the org shape. It is the right choice for packaging workflows where a minimal, predictable environment is required. However, it requires ongoing maintenance as production features evolve. Org Shape trades that control for automatic alignment with production — valuable for application development teams but requires the source org to remain stable and accessible.

**Short vs. Long Scratch Org Lifetime:**
Short-lived orgs (1–2 days for CI, 7 days for feature work) minimize allocation pressure and enforce a clean-state discipline. Long-lived orgs (up to 30 days) reduce setup friction for extended feature work but accumulate drift and consume allocation slots. The right default is the shortest duration that covers the expected work unit.

**Shared Dev Hub vs. Dedicated Dev Hub:**
Using a Developer Edition (or trial) as a shared Dev Hub caps the team at 3 active orgs and 6 daily creations — a hard bottleneck for teams with more than 2 developers plus CI. An Enterprise Edition Dev Hub raises that to 40 active / 80 daily, and Unlimited or Performance to 100 active / 200 daily. The architectural recommendation is to use an Enterprise or higher Dev Hub for any multi-developer team or automated CI pipeline.

Size the two allocations independently, because they constrain different things. **Active** allocation bounds concurrency: peak simultaneous orgs across developers and parallel CI jobs. **Daily** allocation bounds throughput: total creations in any rolling 24-hour window. A pipeline that creates and destroys a one-day org per pull request consumes one active slot briefly but one daily creation permanently for 24 hours — so a busy repository can exhaust the daily allocation while the active pool sits nearly empty. Deleting orgs will not rescue that situation; only time will.

**Scratch Org vs. Sandbox for Data-Dependent Testing:**
Scratch orgs carry a fixed 500 MB data / 50 MB file storage allocation that does not scale with the `edition` declared in the definition file (metadata types are excluded from the calculation). This makes scratch orgs excellent for metadata-heavy, data-light validation — unit tests, bulkification proofs, packaging — and a poor fit for tests that require production-scale record volume or large file/attachment corpora. When a test genuinely depends on data volume, the well-architected choice is a Partial Copy or Full sandbox, not a scratch org with a heroic seeding script.

## Anti-Patterns

1. **Shared mutable scratch org** — Multiple developers pushing to a single scratch org destroys source tracking integrity and creates a shared-mutable-environment anti-pattern that scratch orgs are specifically designed to avoid. Each developer and CI run should have its own isolated org.

2. **Definition file not committed to source control** — If the definition file is local-only or generated ad-hoc, there is no reproducible org shape. When a developer's org expires or a new team member joins, the org shape cannot be recreated deterministically. The definition file must live in `config/` and be committed alongside the source code it describes.

3. **CI pipeline without unconditional org deletion** — A pipeline that only deletes the scratch org on success will leak active orgs on every failed run. Over time this exhausts the daily active allocation. All CI pipelines must include a deletion step with an `if: always()` or equivalent unconditional guard.

## Official Sources Used

- Salesforce DX Developer Guide (Scratch Orgs) — https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_scratch_orgs.htm
- Salesforce DX Developer Guide (Scratch Org Definition File) — https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_scratch_orgs_def_file.htm
- Salesforce DX Developer Guide (Editions and Allocations) — https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_scratch_orgs_editions_and_allocations.htm
- ISVforce Guide (Scratch Org Allocations for Partners) — https://developer.salesforce.com/docs/atlas.en-us.pkg1_dev.meta/pkg1_dev/isv_partner_scratch_org_allocations.htm
- Salesforce DX Developer Guide (Manage Scratch Orgs from Dev Hub) — https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_scratch_orgs_view_lex.htm
- Salesforce DX Developer Guide (Create a Scratch Org Based on an Org Shape) — https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_shape_intro.htm
- Salesforce CLI Command Reference — https://developer.salesforce.com/docs/atlas.en-us.sfdx_cli_reference.meta/sfdx_cli_reference/cli_reference.htm
- Salesforce CLI Command Reference (org Commands — `sf org list limits`) — https://developer.salesforce.com/docs/atlas.en-us.sfdx_cli_reference.meta/sfdx_cli_reference/cli_reference_org_commands_unified.htm
- REST API Developer Guide (Limits resource — `ActiveScratchOrgs`, `DailyScratchOrgs`) — https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/resources_limits.htm
- Object Reference for the Salesforce Platform (ScratchOrgInfo) — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_scratchorginfo.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
