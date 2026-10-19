# Gotchas — Scratch Org Snapshots

## Gotcha 1: Credentials never travel in a snapshot

**What happens:** Orgs created from the snapshot look complete, but every callout test fails.

**When it occurs:** Connected apps, external credentials, and named credentials aren't copied to a snapshot, because they risk exposing sensitive data or authentication secrets.

**How to avoid:** After every create from a snapshot, deploy the credential metadata from source and set secret values from the CI secret store.

---

## Gotcha 2: Allocations are per Dev Hub and per edition

**What happens:** A pipeline that creates a snapshot per branch or per merge starts failing within a day.

**When it occurs:** The number of snapshots you can create matches the active scratch org allocation for the Dev Hub's edition — 3 for Developer Edition, 40 for Enterprise, 100 for Unlimited and Performance — tracked as `ActiveOrgSnapshots` and `DailyOrgSnapshots` in `sf org list limits`.

**How to avoid:** Keep one or two long-lived snapshot names, rebuild on a schedule, and alert on the remaining allocation.

---

## Gotcha 3: Some orgs can't be a snapshot source

**What happens:** The "refresh the snapshot from the snapshot" job fails, or a namespaced dev org can't be snapshotted.

**When it occurs:** You can create a snapshot only if the source scratch org wasn't created from a snapshot or with a namespace.

**How to avoid:** Build the source org from the definition file each time, with `--no-namespace` for namespaced projects; orgs created from the snapshot can still have the namespace from `sfdx-project.json`.

---

## Gotcha 4: Snapshot names are short and alphanumeric

**What happens:** `sf org create snapshot --name ci-base` or `--name nightly-base-with-packages` is rejected.

**When it occurs:** A snapshot name has a maximum length of 15 characters and can contain only alphanumeric characters — no special characters or spaces, even if quoted.

**How to avoid:** Use names like `cibase` / `cibasenew` and put the detail in `--description`. The checker validates names in definition files.

---

## Gotcha 5: Creation is asynchronous, and late changes are lost

**What happens:** A CI job creates a scratch org from a snapshot that isn't ready yet; or changes made to the source org after running the command are missing from the snapshot.

**When it occurs:** The request starts as `InProgress` and becomes usable once its status is `Active`. If you keep modifying the source scratch org after running the snapshot command, not all modifications are reflected.

**How to avoid:** Finish configuring the source org first, then create the snapshot, then poll `OrgSnapshot.Status` (or `sf org get snapshot`) until `Active` before switching consumers.

---

## Gotcha 6: Snapshots expire after 90 days

**What happens:** CI stops being able to create orgs on an ordinary morning.

**When it occurs:** Snapshots expire after 90 days; when a snapshot expires or is deleted, its license becomes available again and its data is deleted later.

**How to avoid:** Rebuild well inside 90 days, and keep the definition-file fallback in CI and exercised on a schedule.

---

## Gotcha 7: During preview, the snapshot's release wins

**What happens:** Tests run on the preview release (or stay on the current release) unexpectedly during the Salesforce release transition.

**When it occurs:** A scratch org is normally created on the Dev Hub's release, but when the Dev Hub and snapshot release versions differ, the scratch org is created on the snapshot's release version.

**How to avoid:** Rebuild the snapshot on the release the tests should target when a preview window opens or closes, and record the release in `--description`.
