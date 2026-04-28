# Well-Architected Notes — Permission Set Group Composition

This skill maps to **Security**, **Reliability**, and **Operational Excellence** in the Salesforce Well-Architected framework. Composition tactics are where the access model meets production — a clean strategic design (`admin/permission-set-architecture`) still fails if mute semantics are misunderstood or the recalculation lifecycle is treated as instantaneous.

## Relevant Pillars

- **Security** — least-privilege depends on the asymmetry between grant and mute being respected:
  - *Trusted by construction* — Mute Permission Sets give a one-way subtractive primitive. Used correctly, they make narrow exclusions auditable and reversible without altering the underlying capability PSes that other personas depend on.
  - *No silent drift* — when a referenced PS changes, every PSG that includes it recalculates. This means a permission added to a PS propagates everywhere consistently, rather than being silently absent in some assignments.
  - *Time-boxed elevation* — `ExpirationDate` on `PermissionSetAssignment` is the platform-native primitive for temporary access. Replacing it with custom Flows weakens the audit story.

- **Reliability** — production access changes must be predictable:
  - *Recalculation is asynchronous* — treating it as instantaneous is the most common production failure. The pattern in this skill is to gate downstream automation on `PermissionSetGroup.Status = 'Updated'`, not on the assignment row alone.
  - *Deletion order is deterministic* — detach → wait → delete prevents the mid-deployment failure where a destructive change runs before the recalc has released a PS reference.
  - *Composition over cloning* — small composable PSes plus mute-driven variants reduce drift across PSG assignments. Cloned PSGs are a reliability tax that compounds at every future change.

- **Operational Excellence** — the model has to stay manageable as the org grows:
  - *Naming is policy* — `PSG_<persona>_<env>` and `MutePS_<scope>_<delta>` make PSGs and mutes searchable, reviewable, and easy to map to ownership. The checker enforces the convention.
  - *Composition surfaces ownership* — when a PSG lists 5 PSes and 1 mute, the persona's access intent is documented in the metadata itself. No external "permissions matrix" spreadsheet is required.
  - *Setup Audit Trail captures composition* — the platform records who added which PS to which PSG and when. Operational reviews use Setup Audit Trail as the single source of truth.

## Architectural Tradeoffs

- **Composability vs locality** — small composable PSes mean a permission's "home" is one file, but tracing a single user's effective access requires reading the PSG plus N PSes plus any mutes. This skill considers the trade worthwhile because the alternative (mega-PSes that each replicate similar permissions) is far worse for change management.
- **Mute clarity vs PSG count** — using mutes keeps the PSG count down at the cost of a slightly less obvious effective-access calculation (you must remember the mute exists). The Sales-Rep + Manager-Mute pattern documented in `references/examples.md` is the canonical answer to this trade.
- **Recalc cost vs change frequency** — high-fan-out PSes (referenced in 30+ PSGs) make every edit expensive because every PSG must recalculate. Splitting such PSes is a real architectural win even though it adds files.
- **Profile residue** — PSGs do not eliminate profiles. Login hours, page layout, and tab visibility still live in profiles. A PSG strategy that ignores the profile baseline will surface "I have the permission but cannot see the tab" tickets.

## Anti-Patterns

1. **PSG explosion via cloning** — building a new PSG every time a small variant is needed. Each clone is permanent technical debt; future edits to the "parent" do not propagate. Use mutes for subtractive variants and new small composable PSes for additive ones.
2. **Mute-then-re-grant inside the same PSG** — including a PS that grants a permission alongside a mute that subtracts it, expecting them to cancel out. They do not. Mute is one-way.
3. **Custom Flow replacement for `ExpirationDate`** — re-implementing time-boxed elevation as a scheduled Flow that deletes assignments. Adds a moving part with a silent failure mode where the platform primitive is reliable and audited.
4. **Single-transaction destructive deployment** — bundling PSG updates and PS deletion into one change-set. The recalc has not released the PS reference at delete time, the deployment fails, and the team has to split it anyway.
5. **Treating mute permission sets as "embedded" in the PSG file** — they are separate metadata. Forgetting them in `package.xml` causes silent drift after a change-set deployment.

## Concrete operability wins

| Before | After |
|---|---|
| 60 PSGs, mostly cloned, 80% overlap | 18 small PSes + 8 mutes + 24 PSGs |
| "Why did this user lose access?" requires reading 4 PSGs | One PSG, listed PSes and mutes obvious in metadata |
| PS deletion routinely fails mid-deploy | Detach → wait → delete is documented and rehearsed |
| Time-boxed elevation drifts past expiration | `ExpirationDate` on assignment, audited automatically |

## Official Sources Used

- **Permission Set Groups (Salesforce Help)** — <https://help.salesforce.com/s/articleView?id=sf.perm_set_groups.htm> — canonical description of PSG composition, recalculation, status values, and assignment lifecycle.
- **Muting Permission Sets in a Permission Set Group (Salesforce Help)** — <https://help.salesforce.com/s/articleView?id=sf.perm_set_groups_muting.htm> — defines mute semantics including the subtract-only behaviour and the requirement to use a Mute Permission Set rather than editing the source PS.
- **Recalculate a Permission Set Group (Salesforce Help)** — <https://help.salesforce.com/s/articleView?id=sf.perm_set_group_recalculate.htm> — the asynchronous lifecycle, status values (`Updated`, `Outdated`, `Updating`, `Failed`), and explicit recalculation entrypoints.
- **Set Expiration Dates for Permission Set Assignments (Salesforce Help)** — <https://help.salesforce.com/s/articleView?id=sf.users_permissionset_assign_expiration.htm> — `ExpirationDate` on `PermissionSetAssignment` for both PS and PSG assignments (Spring '23+).
- **MutingPermissionSet (Metadata API Developer Guide)** — <https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_mutingpermissionset.htm> — confirms `MutingPermissionSet` is its own metadata type and must be retrieved/deployed alongside `PermissionSetGroup`.
- **PermissionSetGroup (Metadata API Developer Guide)** — <https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_permissionsetgroup.htm> — the XML shape, `permissionSets`, `mutingPermissionSets`, and `hasActivationRequired` fields used by the checker.
- **Salesforce Well-Architected — Trusted: Secure** — <https://architect.salesforce.com/well-architected/trusted/secure> — frames the least-privilege and audit-trail benefits this skill underwrites.
- **Salesforce Well-Architected — Adaptable: Resilient** — <https://architect.salesforce.com/well-architected/adaptable/resilient> — frames the recalculation-aware rollout pattern as a resilience concern.
- **Companion repo skill** — `skills/admin/permission-set-architecture/SKILL.md` — strategic counterpart that decides when PSGs are the right architecture in the first place.
