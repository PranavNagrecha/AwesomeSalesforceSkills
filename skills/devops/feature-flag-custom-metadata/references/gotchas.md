# Gotchas — Feature Flags via Custom Metadata

## Gotcha 1: Random vs. deterministic rollout

**What happens:** Users see the feature flicker on and off between page loads; defect reports cannot be tied to a code path.

**When it occurs:** The percentage gate uses `Math.random()`, so each evaluation re-rolls.

**How to avoid:** Bucket on a hash of the user ID plus the flag name (see `examples.md`), so a user's answer is stable and two 10% flags do not select the same cohort.

---

## Gotcha 2: Dead flags

**What happens:** The codebase accumulates dozens of flags, most permanently on or off, each keeping a dead branch alive.

**When it occurs:** No lifecycle discipline — flags are added per release and never removed.

**How to avoid:** Record a removal release with every flag and audit the `customMetadata/Feature_Flag.*` files each release; a flag that has been fully on for a release is deleted together with its `else` branch.

---

## Gotcha 3: Record committed with `Is_Enabled__c = true`

**What happens:** The feature lights up in production the moment the deployment completes.

**When it occurs:** The developer commits the record with the value used locally, or retrieves it from a sandbox where it was switched on.

**How to avoid:** Commit `false`; enable per environment after deploy. The checker reports an enabled flag record as an ERROR.

---

## Gotcha 4: Lists on a flag are truncated or impossible

**What happens:** An allow-list of user IDs or profile names read through `getInstance()` silently stops at the 255th character, so users past the cut fall out of the rollout; or a design calls for a multi-select field that custom metadata values do not support.

**When it occurs:** `getAll()` and `getInstance()` return only the first 255 characters of any field; the custom metadata value types map to Checkbox, Date, Date/Time, Picklist, Text, Phone, TextArea, URL, Email, and Number/Percent — no multi-select.

**How to avoid:** Keep flags to a checkbox and a number. Use a Custom Permission for per-user access, or SOQL the field when long text is unavoidable.

---

## Gotcha 5: DML on custom metadata fails; deployment from Apex is asynchronous

**What happens:** An admin screen does `update flag;` and fails, or enqueues a deployment and immediately re-reads the old value.

**When it occurs:** Apex can edit custom metadata records in memory but not upsert or delete them, and deploys them only through `Metadata.Operations.enqueueDeployment`, which queues the deployment for asynchronous processing.

**How to avoid:** Use `enqueueDeployment` with a `Metadata.DeployCallback` and report "change requested" until the callback runs; or flip the record in Setup during an incident.

---

## Gotcha 6: Omitting a value on re-deploy keeps the org's value

**What happens:** A team removes `Is_Enabled__c` from the committed record expecting the redeploy to reset it, and production stays enabled. Or a field set to a value in Setup survives every subsequent deployment.

**When it occurs:** For an updated custom metadata record, leaving out a field's `<values>` element leaves the field at its previous value; only `<value xsi:nil="true"/>` explicitly clears it. For a newly deployed record, an omitted field is null.

**How to avoid:** Decide whether source or the org owns the live value. If source owns it, always include `Is_Enabled__c` in the record so each deploy sets it; if the org owns it, exclude flag records from routine deployments after first creation.

---

## Gotcha 7: Tests cannot insert flag records

**What happens:** A test tries to `insert new Feature_Flag__mdt(...)` to force a branch and fails to compile or run, so the team falls back to whatever records the org has.

**When it occurs:** DML is not allowed on custom metadata records; tests that rely on org flag values break when an admin flips the flag.

**How to avoid:** Give the accessor a `@TestVisible` override map (see `metadata-examples.md`) so tests set the answer in memory and never depend on deployed records.
