# Well-Architected Notes — Scratch Org Pools

## Relevant Pillars

- **Operational Excellence** — Scratch org pools automate a repetitive, time-consuming provisioning task. Scheduled replenishment, monitoring, and pruning reduce manual toil and ensure CI pipelines run predictably. This is the primary pillar.
- **Reliability** — Pool fallback logic (claim from pool, fall back to on-demand creation) ensures CI jobs do not fail when the pool is empty. Proper pruning prevents stale or expired org references from causing claim failures.
- **Scalability** — Pool sizing directly maps to Dev Hub allocation limits. As the team grows or CI concurrency increases, the pool size and replenishment cadence must scale within the Dev Hub's constraints. Upgrading the Dev Hub edition is the primary scaling lever.
- **Security** — Pool orgs must be provisioned with the same security-conscious definition files as on-demand orgs. The CumulusCI keychain stores org credentials; protect it as you would any credential store. Dev Hub authentication in CI must use JWT bearer flow, not interactive login.

## Architectural Tradeoffs

1. **Pool size vs. available allocation** — Larger pools reduce the chance of empty-pool fallbacks but consume more active org slots. Teams must balance pool size against developer org needs and other CI pipelines sharing the same Dev Hub.

2. **Org duration vs. freshness** — Shorter durations (1 day) ensure orgs use recent API versions and definition files, but increase replenishment frequency and daily create consumption. Longer durations (3-7 days) reduce replenishment cost but risk using stale org configurations.

3. **Centralized vs. distributed pool management** — A single scheduled replenishment job is simpler to maintain but creates a single point of failure. Distributing pool management across multiple workflows adds complexity but improves resilience.

4. **CumulusCI dependency** — Adopting CumulusCI for pool management introduces a new tool dependency. Teams using only the `sf` CLI must evaluate whether the pool benefits justify the added complexity. For small teams (under 5 parallel jobs), the benefit may not outweigh the cost.

## Anti-Patterns

1. **Oversized pools on limited Dev Hubs** — Creating a pool of 15 orgs on an Enterprise Dev Hub (20 active max) leaves only 5 slots for all other uses. This starves developers and causes more disruption than the provisioning time it saves. Size pools to use no more than 60% of active slots.

2. **No fallback logic in CI jobs** — CI jobs that assume the pool always has available orgs fail hard when the pool is depleted. Every pool-based CI job must include fallback-to-create logic, or the team trades slow pipelines for broken pipelines.

3. **Replenishing without pruning** — Running `cci org pool create` without first running `cci org pool prune` causes the keychain to accumulate references to expired orgs. Subsequent `pool get` commands may return an expired org reference, causing job failures.

## Official Sources Used

- CumulusCI Documentation — Manage Scratch Orgs — https://cumulusci.readthedocs.io/en/latest/scratch-orgs.html
- Salesforce DX Developer Guide — Scratch Org Editions and Allocations — https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_scratch_orgs.htm
- Salesforce CLI Reference — https://developer.salesforce.com/docs/atlas.en-us.sfdx_cli_reference.meta/sfdx_cli_reference/cli_reference.htm
