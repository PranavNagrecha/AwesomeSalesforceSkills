# Gotchas — Permission Set Group Composition

Subtle traps when composing PSGs, applying mutes, sequencing recalculation, and managing assignments.

---

## 1. Mute is subtract-only — the grant-wins rule does NOT apply to mutes

**What happens:** A PSG includes `PS_A` (grants Delete on Opportunity), `MutePS_NoOpportunityDelete` (mutes Delete on Opportunity), and `PS_B` (also grants Delete on Opportunity). The admin assumes "grant-wins" — that any included PS granting Delete should beat the mute. The user still does not get Delete.

**When it occurs:** Any time someone treats Mute Permission Sets as a toggle ("I'll just re-add it via another PS"). Especially during refactors that consolidate PSes — a permission newly granted by the consolidated PS gets silently muted because the mute was never updated.

**How to avoid:** Internalise the asymmetry: between **included** PSes, grant-wins (any PS granting a permission gives it to the user). Between included PSes and a **mute** PS, mute-wins. There is no escape hatch. If the persona needs the permission, do not include the mute. If only some users in the persona need it, that is a different PSG.

---

## 2. PSG recalculation is asynchronous — assigned users see stale access until it completes

**What happens:** A `PermissionSetAssignment` row links a user to `PSG_SalesRep_Prod` immediately, but the PSG's `Status` is still `Outdated` because a referenced PS just changed. The user logs in, hits a record, and gets an FLS error on a field they "should" have. Support files a ticket; the ticket is "wait five minutes and try again."

**When it occurs:** Right after a PS edit lands and assignments fire in parallel. Common during release cuts where multiple PSes change in one deployment and several PSGs recalc concurrently.

**How to avoid:** Treat `Status = Updated` as the gate for activation. After a deployment that touches a high-fan-out PS, poll the affected PSGs (`SELECT Id, Status FROM PermissionSetGroup WHERE DeveloperName IN (...)`) and only run downstream assignment automation once every PSG reports `Updated`. For change-sets without that automation, allow a recalc window in the rollout plan.

---

## 3. Assignment vs activation — `IsActive` on the assignment is not the same as PSG status

**What happens:** An admin assumes that if `PermissionSetAssignment.IsActive = true`, the user has the PSG's effective access. It is not. The assignment row says "this user is linked to this PSG"; the PSG's `Status` says "the calculated effective access for the PSG is current." Both must be true for the user to actually get the permissions.

**When it occurs:** Anywhere automation queries assignment rows to check access. Looks fine in test sandboxes (recalc finishes in seconds because the org is empty); breaks in production where recalc takes minutes.

**How to avoid:** Verify both layers — `PermissionSetAssignment.IsActive = true` AND `PermissionSetGroup.Status = 'Updated'` before considering a user provisioned. The expiration field (`ExpirationDate`) on the assignment is independent of recalculation; it only governs when the assignment auto-expires.

---

## 4. Mute Permission Sets are separate metadata — change sets and `package.xml` retrieves miss them by default

**What happens:** A developer retrieves `PermissionSetGroup` from a sandbox via change set, deploys to prod, and the muted permissions show up as un-muted because the `MutingPermissionSet` metadata never travelled.

**When it occurs:** Any source-tracked or change-set deployment where the manifest is hand-curated and the team forgets to add `MutingPermissionSet` to `package.xml`. The PSG file references the mute by name, but if the mute itself is missing, the deploy succeeds with the reference dangling.

**How to avoid:** Always pair `PermissionSetGroup` with `MutingPermissionSet` (and `PermissionSet`) in the deployment manifest:

```xml
<types>
    <members>*</members>
    <name>PermissionSetGroup</name>
</types>
<types>
    <members>*</members>
    <name>MutingPermissionSet</name>
</types>
<types>
    <members>*</members>
    <name>PermissionSet</name>
</types>
```

Source-tracked SFDX projects do this automatically when retrieving a PSG that references a mute, but only if the mute is in the same project. Cross-project references get cut.

---

## 5. Cannot delete a permission set while any PSG still references it

**What happens:** A deployment that detaches a PS from three PSGs and deletes the PS in one shot fails — the PSGs were updated but their recalc had not released the PS reference at the moment the delete fired.

**When it occurs:** Single-transaction destructive deployments. Salesforce returns a delete error mentioning the PSG dependency.

**How to avoid:** Use the detach → wait → delete sequence:

1. Deploy the PSG updates (PS removed from `permissionSets`).
2. Poll `PermissionSetGroup.Status` for every affected PSG; wait for `Updated`.
3. Deploy the destructive change separately.

Two deployments, one wait. The wait is non-negotiable.

---

## 6. License mismatch silently reduces effective access for some assignees

**What happens:** A PSG that includes a PS scoped to "Salesforce" license is assigned to a user on the "Platform" license. The PSG accepts the assignment without error, but the Salesforce-only permissions inside are not granted to that user. The same PSG works fine for Salesforce-licensed assignees; the difference is invisible without per-user testing.

**When it occurs:** Mixed-license orgs (especially Sales Cloud + Platform Starter), or after a contract change that downgrades licenses without re-validating PSG composition.

**How to avoid:** When a PSG includes any license-restricted PS, document the licence requirement on the PSG and test assignment with at least one user per relevant license. The skill template's "License Dependency" field exists for this — fill it in.

---

## 7. PSG explosion — overlapping PSGs that should have been mutes

**What happens:** The org has 60 PSGs, most named after a manager or department, most with 80% overlap in included PSes. Every new persona request becomes a new PSG. Audit becomes archaeology.

**When it occurs:** When the team treats PSGs as cheap "snapshots" of access and never refactors back into composable PSes + targeted mutes. Often a side-effect of mass-cloning.

**How to avoid:** Run the checker — it reports PSes referenced in many PSGs (good — reuse) AND PSGs that share large subsets of PSes (sign of overlap-as-clone). When two PSGs differ by one or two permissions, they should be one PSG plus a mute, not two PSGs.

---

## 8. Setup Audit Trail captures composition changes — review it before blaming code

**What happens:** A developer chases an "intermittent" access bug that turns out to be a PSG composition change made by an admin in production. No code change, no deployment record in the dev tools — but Setup Audit Trail has the entry.

**When it occurs:** In orgs that allow direct production admin work alongside source-tracked deployments. The two control planes do not share a history view by default.

**How to avoid:** When access behaviour changes unexpectedly, check Setup Audit Trail for `PermissionSetGroup` and `PermissionSet` entries before assuming a bad deployment. The audit trail captures the assignor, timestamp, and old/new value.
