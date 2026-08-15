# Well-Architected Notes — Dynamic Sharing Recalculation

## Relevant Pillars

- **Reliability** — Primary pillar. Sharing recalculation is an asynchronous
  process whose completion the application cannot observe directly and whose
  duration scales with data volume, role depth, and rule count. A design that
  assumes recalculation is fast, synchronous, or automatically triggered on resume
  will produce intermittent access gaps that look like data problems. Reliability
  here means treating recalculation as a first-class scheduled operation with an
  explicit start, an observable progress signal (**Background Jobs**, **Apex
  Jobs**), a completion signal (the notification email), and an assertion-based
  exit gate — not as an implementation detail of a data load.

- **Performance** — The cost of recalculation is superlinear in the wrong
  sequence. The LDV guide's prescribed order (roles → records → groups and queues →
  sharing rules, one at a time) exists because each phase's computation depends on
  the previous phase's output; running them concurrently means recomputing the same
  rows repeatedly. Deferral converts N overlapping partial recalculations into one
  bounded rebuild, which is the single largest performance lever available.

- **Operational Excellence** — Deferral is a stateful org-level switch with no
  expiry and no alerting. Its lifecycle must be owned by a named person, recorded
  in a change record, and closed by verification rather than by elapsed time. The
  distinction between "the job finished" and "access is correct" is exactly the
  kind of gap that operational maturity closes.

- **Security** — Recalculation failures are bidirectional. Under-granting produces
  tickets; over-granting produces audit findings and is silent. A recalculation
  gate that only asserts "users can see what they should" and never asserts "users
  cannot see what they should not" has verified half the security property.

## Architectural Trade-offs

**Defer-and-rebuild vs load-in-place.** Deferral gives one clean recalculation at a
chosen time, at the cost of a window during which the org's sharing model is
frozen — group membership changes, role moves, and rule edits all stop
propagating, and the Recalculate button is disabled. For a two-week nightly
migration that freeze is acceptable and the alternative (compounding backlogs) is
not. For a two-hour load into a busy org, deferral may cost more in operational
risk than it saves in compute. Size the freeze against the org's rate of sharing
change, not just against the load duration.

**Relaxing the OWD during load vs deferring.** The LDV guide suggests "Use Public
Read/Write security during initial load to avoid sharing calculation overhead."
This is the cheapest option and the most constrained: no `__Share` row can be
inserted while the OWD is at its most permissive level, so any Apex managed sharing
must be disabled for the window; and a custom object's OWD "can't be changed from
private to public ... if Apex code uses the sharing entries associated with that
object." In practice the relaxation is available on greenfield loads and rarely
available on the mature objects where it would help most.

**Per-user shares vs group shares in the recalculation budget.** A sharing model
built on public groups recalculates group membership once and derives many rows;
one built on per-user rules recalculates per user. The group model is faster to
rebuild and slower to audit. Orgs above roughly 1,000 users should treat
recalculation duration as a design input to the sharing model, not a consequence of
it.

**Serialised sharing changes vs release-train batching.** Share locks make
concurrent sharing changes impossible on the same object family: "You can't modify
the org-wide defaults when a sharing rule recalculation for any object is in
progress." A release train that batches all sharing metadata into one deploy will
serialise anyway — badly, with partial failures. Explicitly sequencing sharing
changes into separate windows costs calendar time and buys deterministic outcomes.

**Verification instrument choice.** `UserRecordAccess` is queryable, requires no
impersonation, and is the correct probe for the sharing model. It also "doesn't
consider whether a user's access is blocked by a restriction rule," so in orgs
using restriction rules it over-reports. `System.runAs` reflects the full stack but
is test-context only. There is no single instrument that is both production-safe
and complete; say which one produced which claim in the verification report.

## Anti-Patterns

1. **Planning a migration around Defer Sharing Calculations without confirming the
   feature is enabled in production.** The Security Guide's availability is
   conditional. Discovering this on the morning of the load invalidates the plan
   with no time to replan.

2. **Treating "resume" as the end of the deferral runbook.** Resuming stops
   suppression; it does not replay suppressed work. The manual recalculation is a
   separate, mandatory, separately-signed-off step.

3. **Leaving deferral on indefinitely.** There is no expiry and no alert. Every
   subsequent group, role, rule, and ownership change stops propagating, and the
   symptom surfaces weeks later as scattered access tickets that point at
   permissions rather than at a switch nobody remembers flipping.

4. **Sizing the window to the named object.** The Account family recalculates as a
   unit (Account, Case, Contact, Opportunity), role changes cascade to every
   hierarchy-shared object, and registered Apex sharing recalculation classes run
   alongside. A single-object estimate is structurally wrong.

5. **Signing off on job completion.** A completed recalculation can still leave a
   criteria-based rule that references an expired managed-package field silently
   un-recalculated, with historical sharing preserved so the rule looks healthy.
   Gate on per-user, per-record assertions.

6. **Assuming deferral suppresses your own Apex.** The switch covers group
   membership calculation and sharing rule calculation. Application triggers that
   write `__Share` rows keep running, adding DML to an already-heavy load. Disable
   them separately and rebuild afterwards.

## Official Sources Used

- Salesforce Security Guide — Recalculate Sharing Rules Manually (deferral note, disabled Recalculate button, automatic recalculation triggers) — https://help.salesforce.com/s/articleView?id=platform.security_sharing_rule_recalculation.htm&type=5
- Salesforce Security Guide — Automatic Recalculation of Org-Wide Defaults and Sharing Rules (Account family cascade, Background Jobs subtypes, share locks, Apex recalculation rider) — https://help.salesforce.com/s/articleView?id=platform.security_sharing_auto_recalculation.htm&type=5
- Salesforce Security Guide — Defer Sharing Calculations — https://help.salesforce.com/s/articleView?id=platform.security_sharing_defer.htm&type=5
- Salesforce Security Guide — Sharing Rule Considerations (expired managed-package fields, criteria-based rule limits, 300 rules per object) — https://help.salesforce.com/s/articleView?id=platform.security_sharing_rule_considerations.htm&type=5
- Salesforce Security Guide — Organization-Wide Sharing Defaults (private-to-public restriction when Apex references share entries) — https://help.salesforce.com/s/articleView?id=platform.security_sharing_owd.htm&type=5
- Best Practices for Deployments with Large Data Volumes — Defer Sharing Calculation, and the Loading Data from the API best-practice table — https://developer.salesforce.com/docs/atlas.en-us.salesforce_large_data_volumes_bp.meta/salesforce_large_data_volumes_bp/
- Object Reference for the Salesforce Platform — UserRecordAccess (restriction-rule caveat; "Up to 200 record IDs can be queried"; "When the running user is querying a user's access to a set of records, records that the running user doesn't have read access to are filtered out of the results"; the `SELECT RecordId` + access-level-field query shapes) — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_userrecordaccess.htm
- Apex Developer Guide — Using the runAs Method ("You can use `runAs` only in test methods"; "Every call to `runAs` counts against the total number of DML statements issued in the process") — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_testing_tools_runas.htm
- Apex Developer Guide — Recalculating Apex Managed Sharing — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_bulk_sharing_recalc.htm
- Salesforce Well-Architected — Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
