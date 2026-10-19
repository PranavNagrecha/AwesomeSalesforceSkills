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

Corpus: `sfdx_dev.txt` is the Salesforce DX Developer Guide, Summer '26 (API 67.0), fetched from resources.docs.salesforce.com/262 and converted with `pdftotext -layout`. Line numbers are `grep -n` positions.

- `sfdx_dev.txt` L9934–9950 — what a snapshot includes; static (delete and recreate to update); scratch-org-only in both directions; 200-MB data limit; not a replacement for source control or UAT sandboxes (SKILL.md Core Concepts).
- `sfdx_dev.txt` L9959–9985 — same Dev Hub required; allocation equals the edition's active scratch org allocation (3 / 40 / 100); 90-day expiry; data retention; `ActiveOrgSnapshots` / `DailyOrgSnapshots` in `sf org list limits` (gotchas 2 and 6).
- `sfdx_dev.txt` L9988–9994 — connected apps, external credentials, and named credentials aren't copied (gotcha 1).
- `sfdx_dev.txt` L10094–10145 — source org can't be snapshot-created or namespaced; late changes not reflected; `sf org create snapshot` syntax; 15-character alphanumeric names; initial `InProgress` status (gotchas 3–5, checker).
- `sfdx_dev.txt` L10150–10162 — namespaced scratch orgs from a snapshot via a `--no-namespace` source (Decision Guidance).
- `sfdx_dev.txt` L10176–10202 and L10243–10251 — definition file with `snapshot` instead of `edition`; options not to include; larger `--wait`; `--snapshot` flag (SKILL.md JSON fence, checker).
- `sfdx_dev.txt` L10255–10280 — scratch org release version follows the snapshot's when Dev Hub and snapshot differ during preview (gotcha 7).
- `sfdx_dev.txt` L10340–10370 — `sf org get snapshot` status check, `Active` before use; `sf org list snapshot` (Recommended Workflow).
- `sfdx_dev.txt` L10050–10072 — licenses and Org Snapshots object permissions for non-admin users (Recommended Workflow step 1).
- Metadata API Developer Guide (`api_meta.txt`) L114215–114240 — `DevHubSettings.enableScratchOrgSnapshotPref` (API 61.0) and sample definition (SKILL.md XML fence).
- Object Reference (`object_reference.txt`) L206582 and L206723–206735 — `OrgSnapshot` object and its `Status` values (`New`, `In Progress`, `Active`, `Error`, `Expired`) (examples.md poll query).
