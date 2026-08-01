# Well-Architected Notes — Scratch Org Snapshots

**Performance:** the pattern moves a fixed cost from per-build to per-night. That only pays
if the expensive part — package installs, baseline metadata — is genuinely stable between
rebuilds. Where the slow step is the team's own source, a snapshot moves the cost without
reducing it, and the added moving parts are not repaid.

**Reliability:** a snapshot is another dependency between a developer and a working org, and
it has real failure modes: 90-day expiry, an exhausted Dev Hub allocation, an overnight
rebuild that failed. A pipeline with no path except the snapshot stops completely when any of
these occur, and presents as a platform incident. Keeping the definition-file path working —
and exercising it on a schedule rather than only in an emergency — is what makes the
optimisation safe to depend on.

**Reliability, completeness:** the org that comes back is not the org that went in.
Connected apps, external credentials and named credentials are excluded, so every
integration returns unconfigured and the resulting callout-test failures are routinely
misread as flakiness. Restoring credentials as a per-org step is the design, not a
workaround — and it is also why a snapshot cannot leak one.

**Operational Excellence, capacity:** both the active count and the daily creation count are
allocated per Dev Hub and vary sharply by edition — 3 on Developer Edition against 100 on
Unlimited or Performance. A per-branch or per-commit snapshot design that works comfortably
on an Enterprise Dev Hub is impossible on a Developer Edition one, so the allocation has to
be checked before the refresh cadence is designed rather than discovered when the pilot
stops working.

**Operational Excellence, staleness as a correctness hazard:** the danger is not that a
stale snapshot is slow, it is that CI passes against a world that no longer exists — an old
managed package version, superseded baseline metadata — so green builds stop being evidence.
Rebuilding from the definition file rather than from the previous snapshot keeps the
definition itself exercised, which is what surfaces the day it stops working. The same logic
argues for minimal data: records baked into a snapshot are version-controlled nowhere and
vanish at expiry, so a test that depends on them cannot be explained later.

## Official Sources Used

- Scratch Org Snapshots — what a snapshot captures, the exclusions (connected apps, external credentials, named credentials), the per-edition allocations, and the 90-day expiry — https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_snapshots_intro.htm
- Create a Scratch Org Snapshot — `sf org create snapshot`, the 15-character name limit, and the asynchronous `InProgress` → `Active` transition — https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_snapshots_create.htm
- Create a Scratch Org Based on a Snapshot — the `snapshot` key in the definition file and the `--snapshot` flag — https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_snapshots_create_scratch_org.htm
- Create a Snapshot for Use with Namespaced Scratch Orgs — the namespace restriction on the source org — https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_snapshots_namespace_limitations.htm
- Salesforce CLI Snapshot Commands — the command surface including snapshot deletion — https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_snapshots_cli_commands.htm
- Build Your Own Scratch Org Definition File — the fallback path a snapshot pipeline must retain — https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_scratch_orgs_def_file.htm
