# Gotchas — Dynamic Sharing Recalculation

Non-obvious platform behaviours around sharing recalculation. Sourced from the
Salesforce Security Guide and *Best Practices for Deployments with Large Data
Volumes* (Summer '26, API 67.0).

## Gotcha 1: Defer Sharing Calculations Is Not Enabled by Default and Is Not Self-Service

**What happens:** The migration plan says "enable Defer Sharing Calculations
before the load." On the morning of the load, the admin searches Setup for
"Defer" and finds nothing. There is no permission to grant, no feature to toggle,
and no documentation path that turns it on from inside the org.

**When it occurs:** On the first large migration in any org that has never used
it. The Security Guide phrases the availability as conditional — "**If enabled in
your org**, you can temporarily defer sharing rule calculations" — which reads like
a licensing note and is easy to skim past during planning.

**How to avoid:** Verify the **Setup → Defer Sharing Calculations** page renders
in *production* (not just in a sandbox, and not just from your own admin profile)
at project kickoff, and record the screenshot in the migration plan. If it is
absent, raise the request with Salesforce Support immediately and treat the
enablement date as a hard dependency on the migration schedule. A plan built on an
unavailable feature is not a plan.

---

## Gotcha 2: Resume Does Not Recalculate — You Must Trigger It Manually

**What happens:** The team suspends sharing calculations, runs the load, resumes
calculations, and reopens the org. Access is wrong for a subset of users and
nobody can say why. Background Jobs is empty, so the natural conclusion is that
recalculation completed successfully.

It never ran. Resuming the process only stops *suppressing* future computations —
it does not replay the ones that were suppressed.

> "After this work is completed, you must resume sharing rule calculations and
> manually initiate a full sharing rule recalculation to prevent errors."
> — Salesforce Security Guide, *Recalculate Sharing Rules Manually*

**When it occurs:** Every time the runbook treats "resume" as the last step.

**How to avoid:** Make the sequence explicit and non-collapsible in the runbook:

```text
1. Resume group membership calculation
2. Resume sharing rule calculation
3. Setup → Sharing Settings → [object] → Sharing Rules → Recalculate
4. Setup → Background Jobs — wait for empty
5. Wait for the completion email
6. Run the access verification probe
7. Only now: close the change record
```

Steps 3 and 4 are separate from step 2 and must be signed off separately.

---

## Gotcha 3: The Recalculate Button Is Disabled While Calculations Are Deferred

**What happens:** An operator working the runbook at 03:00 tries to recalculate,
finds the button greyed out, and assumes a permission problem. They spend the
window checking `Manage Sharing` on their own profile.

> "The Recalculate button is disabled when group membership or sharing rule
> calculations are deferred."
> — Salesforce Security Guide

**When it occurs:** Any runbook that lists "recalculate" before "resume," which is
the intuitive order if you think of the deferral as a queue that you flush.

**How to avoid:** Resume first, recalculate second. Put the reason in the runbook
next to the step so the 03:00 operator does not have to reconstruct it: *the button
is disabled while deferral is active; if it is greyed out, deferral is still on.*
That one line converts a 40-minute detour into a 10-second check.

---

## Gotcha 4: Recalculating Accounts Recalculates Three Other Objects

**What happens:** A change scoped in the change record as "recalculate Account
sharing rules — 20 minutes" runs for hours and touches Cases, Contacts, and
Opportunities. The blast radius in the change record was wrong by a factor of four.

> "If sharing rules are recalculated for accounts, cases, contacts, or
> opportunities, sharing rules are also recalculated for the other three objects.
> This behavior occurs because cases, contacts, and opportunities are child objects
> of accounts."
> — Salesforce Security Guide, *Automatic Recalculation of Org-Wide Defaults and
> Sharing Rules*

**When it occurs:** On the four most heavily populated standard objects in most
orgs — that is, the worst possible place for an unplanned four-way cascade.

**How to avoid:** Size the window against the row count of all four objects, not
the one you named. Conversely, use the cascade deliberately: you only need to
trigger recalculation on one of the four to cover all of them. On the Background
Jobs page these appear as the subtypes `Account — Parent Access Grant` and
`Account — Extra Parent Access Removal`; a deleted sharing rule appears as
`Object — Access Cleanup`.

---

## Gotcha 5: Share Locks Block Unrelated-Looking Changes Mid-Recalculation

**What happens:** During a long recalculation, an admin tries to fix an unrelated
org-wide default and the save is rejected. It looks like a bug or a permissions
issue.

> "You can't modify the org-wide defaults when a sharing rule recalculation for any
> object is in progress. Similarly, you can't modify sharing rules when
> recalculation for an org-wide default update is in progress."
> — Salesforce Security Guide, *Share Locks*

There is a second, narrower lock on the Account family:

> "To maintain implicit sharing between accounts and child records, updating the
> org-wide default on an account or its child objects disables further org-wide
> default and sharing rule updates on them. For example, when you update an
> opportunity sharing rule and recalculation is in progress, you can't update the
> org-wide default or sharing rules for accounts, contacts, opportunities, and
> cases."

**When it occurs:** Whenever two sharing changes are scheduled into the same
window, which is exactly what a release train encourages.

**How to avoid:** Serialise sharing changes. One sharing change per window, and
treat "Background Jobs is empty" as the gate between them. Note the one degree of
freedom the guide grants: "You can make changes to the org-wide defaults and
sharing rules for other objects" — so unrelated objects are still workable, and a
release plan can sequence around the Account family specifically.

---

## Gotcha 6: Criteria-Based Rules Referencing Expired Package Fields Are Silently Skipped

**What happens:** A recalculation completes cleanly, the email arrives, Background
Jobs is empty — and one group of users still cannot see their records. The rule
exists, is active, and looks correct in Setup.

> "If a criteria-based sharing rule references a field from a licensed managed
> package whose license has expired, (expired) is appended to the label of the
> field ... Criteria-based sharing rules that reference expired fields aren't
> recalculated, and new records aren't shared based on those rules. But the sharing
> of existing records before the package's expiration is preserved."
> — Salesforce Security Guide, *Sharing Rule Considerations*

The preserved historical sharing is what makes this so hard to spot: old records
are still visible, so the rule looks alive. Only records created after the license
expired are missing.

**When it occurs:** After an AppExchange package license lapses — often months
after anyone remembers installing it, and never in the same change window as the
symptom.

**How to avoid:** Include managed-package license expiry in the pre-recalculation
checklist. Scan criteria-based sharing rule definitions for field labels ending in
`(expired)`. As a detective control, the "new records missing, old records fine"
signature is diagnostic — when it appears, check package licenses before checking
anything else.

---

## Gotcha 7: Apex Sharing Recalculation Rides Along With Platform Recalculation

**What happens:** A team plans a recalculation window sized for platform sharing
only, and the window runs long because every registered Apex sharing recalculation
class also executes.

> "When sharing is recalculated, Salesforce also runs all Apex sharing
> recalculations."
> — Salesforce Security Guide

And from the Apex Developer Guide: "Every time a custom object's organization-wide
sharing default access level is updated, any Apex recalculation classes defined for
associated custom object are also executed."

**When it occurs:** In orgs that have Apex managed sharing on custom objects,
which the sharing team frequently does not know about because it was built by a
different squad.

**How to avoid:** Before the window, inventory Apex sharing recalculation classes
(**Object Manager → [object] → Apex Sharing Recalculation** on every custom object
with a `__Share`) and add their batch runtime to the window estimate. Monitor them
separately under **Setup → Apex Jobs** — they do not appear on the Background Jobs
page with the platform recalculation subtypes. See
`security/apex-managed-sharing-patterns`.

---

## Gotcha 8: Deferring Sharing Does Not Stop Your Own Apex `__Share` DML

**What happens:** The team defers sharing calculations for a bulk load, believing
this suppresses "all sharing work." A trigger on the loaded object continues
inserting `__Share` rows for every record, adding DML volume to an already-heavy
load and producing shares that the eventual full recalculation may then reconcile
away.

**When it occurs:** In orgs where Apex managed sharing coexists with declarative
sharing — the usual case once an implementation is a few years old.

**How to avoid:** Deferral is a platform-side switch over group membership
calculation and sharing rule calculation. It has no visibility into your Apex.
Disable application triggers separately for the load window using a trigger control
mechanism — the repo's canonical one is
[`templates/apex/TriggerControl.cls`](../../../../templates/apex/TriggerControl.cls) —
and then rebuild the application's shares afterwards by invoking the object's
`Database.Batchable` recalculation class explicitly. The LDV guide gives the same
advice generically: "Disable Apex triggers, workflow rules, and validations during
loads; investigate the use of batch Apex to process records after the load is
complete."

---

## Gotcha 9: You Cannot Set a Custom Object's OWD Back to Public if Apex Touches Its Shares

**What happens:** The "set OWD to Public Read/Write during the load" optimisation
from the LDV guide is rejected on a custom object, with no obvious cause.

> "The organization-wide default settings can't be changed from private to public
> for a custom object if Apex code uses the sharing entries associated with that
> object. For example, if Apex code retrieves the users and groups who have sharing
> access on a custom object Invoice__c (represented as `Invoice__share` in the
> code), you can't change the object's organization-wide sharing setting from
> private to public."
> — Salesforce Security Guide, *Organization-Wide Sharing Defaults*

**When it occurs:** Precisely on the objects where the load-time optimisation would
help most, because heavy custom objects are the ones with custom sharing code.

**How to avoid:** Plan the load without the OWD relaxation on those objects, and
rely on Defer Sharing Calculations instead. If the relaxation is essential, the
referencing Apex must be removed from the org first — which is a code change with
its own release, not a load-window action.

---

## Gotcha 10: `UserRecordAccess` Ignores Restriction Rules

**What happens:** A post-recalculation verification probe queries
`UserRecordAccess` and reports `HasReadAccess = true`, yet the user still cannot
see the record in the UI. The verification says access is fine; the user says it
is not; both are correct.

> "This object is read only and is available in API version 24.0 and later. This
> object doesn't consider whether a user's access is blocked by a restriction
> rule."
> — Object Reference, *UserRecordAccess*

Sharing grants; restriction rules subtract. `UserRecordAccess` reports only the
grant side.

**When it occurs:** In orgs that adopted restriction rules — increasingly common,
because they are the supported way to *reduce* access below what sharing grants.

**How to avoid:** Treat `UserRecordAccess` as an assertion about the sharing model
specifically, which is what you want after a recalculation. When the org uses
restriction rules, pair it with a spot check performed as the actual user (or a
`System.runAs` assertion in a test org) for at least one record per persona, and
say in the verification report which instrument produced which claim.
