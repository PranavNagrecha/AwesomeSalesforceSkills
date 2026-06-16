# Examples — Metadata API Retrieve / Deploy

Two worked scenarios and one anti-pattern showing how to drive
`sf project retrieve start` / `sf project deploy start` against
a hand-authored `package.xml`, and why git-tracked manifests are
the only sane substrate for cross-org metadata movement at scale.

---

## Example 1: Surgical change-set deploy with explicit members (vs wildcard for a tenant snapshot)

**Context:** A team is shipping a new `Account.HealthScore__c` field
plus the `AccountHealthScoreTrigger` ApexTrigger and its handler
class `AccountHealthScoreHandler`. The change rides on a CI pipeline
that retrieves from a `int` sandbox, runs validation against `staging`,
and then `quick`-deploys to `prod`. A separate periodic job dumps the
full tenant for archival.

**Problem:** Engineers reach for `<members>*</members>` because it's
fewer keystrokes. Wildcards on `ApexClass` pull every class in the
org (often 600+) into the diff; reviewers can't see what's actually
changing, and the deploy validation runtime explodes because the
target evaluates all 600 classes for changes even when only 2
differ. Worse, a wildcard `CustomField` retrieve doesn't include
standard-object fields unless each parent standard object is also
named (`Account`, `Contact`, `Opportunity`, etc.), so the "snapshot"
is silently incomplete — see also the sibling skill
`apex/metadata-api-and-package-xml`.

**Solution: explicit-member manifest for the change-set deploy.**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Account.HealthScore__c</members>
        <name>CustomField</name>
    </types>
    <types>
        <members>AccountHealthScoreTrigger</members>
        <name>ApexTrigger</name>
    </types>
    <types>
        <members>AccountHealthScoreHandler</members>
        <members>AccountHealthScoreHandlerTest</members>
        <name>ApexClass</name>
    </types>
    <version>60.0</version>
</Package>
```

Retrieve from the source sandbox, then validate-then-quick into prod:

```bash
sf project retrieve start \
  --target-org int-sandbox \
  --manifest manifest/package.xml \
  --output-dir force-app

# Commit the diff, open PR, merge.

sf project deploy validate \
  --target-org prod \
  --manifest manifest/package.xml \
  --test-level RunSpecifiedTests \
  --tests AccountHealthScoreHandlerTest \
  --wait 60
# captures a job ID — e.g. 0Af3X00001abcDef

sf project deploy quick \
  --job-id 0Af3X00001abcDef \
  --target-org prod
```

**Why explicit beats wildcard here:** the diff in source control
is exactly the four components changing. Reviewers see what's
shipping. The validation deploy compares 4 components on the
target, not 600. The `RunSpecifiedTests` test level needs a known
test list — wildcards on `ApexClass` would have included unrelated
tests the developer never intended to gate the deploy on.

**Solution: wildcard manifest for the full-tenant archival snapshot.**

For the nightly snapshot job, the goal is "capture everything so we
have a rollback baseline." A wildcard manifest is the right call —
but you have to name the standard objects explicitly and call out
`installedPackage` separately (see Gotcha 1):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types><members>*</members><name>ApexClass</name></types>
    <types><members>*</members><name>ApexTrigger</name></types>
    <types><members>*</members><name>CustomObject</name></types>
    <types>
        <members>Account</members>
        <members>Contact</members>
        <members>Lead</members>
        <members>Opportunity</members>
        <members>Case</members>
        <name>CustomObject</name>
    </types>
    <types><members>*</members><name>Flow</name></types>
    <types><members>*</members><name>Layout</name></types>
    <types><members>*</members><name>Profile</name></types>
    <version>60.0</version>
</Package>
```

The split rule: **wildcards for "what does the tenant currently
look like?"; explicit members for "what is changing in this PR?"**

---

## Example 2: Deleting a deprecated field with `destructiveChanges.xml`

**Context:** The legacy `Account.OldTerritory__c` text field is being
retired in favor of a Region lookup. The new metadata has been live
for two sprints; the old field is verified unreferenced. The deploy
needs to drop the field and run `RunLocalTests` because there's a
governance rule against any prod deploy with `NoTestRun`.

**Problem:** Practitioners often try to delete metadata by removing
it from `package.xml` and re-deploying. That doesn't delete anything
— `package.xml` is an add/update manifest, never a delete manifest.
The component stays in the target org indefinitely.

**Solution: pair an empty `package.xml` with a `destructiveChanges.xml`.**

`manifest/package.xml` — note it has NO `<types>` block but still
needs the `<version>` element so the API knows which version's
metadata-type catalog to evaluate against:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <version>60.0</version>
</Package>
```

`manifest/destructiveChanges.xml` — runs AFTER any adds (the
default). For this use case there are no adds; pre vs post is moot:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Account.OldTerritory__c</members>
        <name>CustomField</name>
    </types>
</Package>
```

Deploy:

```bash
sf project deploy start \
  --target-org prod \
  --manifest manifest/package.xml \
  --post-destructive-changes manifest/destructiveChanges.xml \
  --test-level RunLocalTests \
  --wait 120
```

**Gotcha to surface up-front:** `RunLocalTests` against a deploy
with a `destructiveChanges.xml` means tests run against **both
the new state AND the deleted state**. If any test class still
has `SELECT OldTerritory__c FROM Account`, the test class
compilation fails post-delete and the entire deploy rolls back
even though the field-deletion itself was valid. Audit test code
before bundling a destructive deploy with a non-`NoTestRun` test
level. The safest sequence for risky removals: ship the test-code
update in deploy N (no destructive), then ship the destructive
in deploy N+1 against a now-clean test suite.

**Why it works:** the empty `package.xml` is the platform's
required "scope" envelope (the API rejects a destructive deploy
with no manifest at all). The post-destructive flag tells the
sf CLI to upload the destructive manifest alongside and process
it after additions. The platform's deploy engine resolves
dependencies in this order: adds → tests run → deletes → final
validation — which is why a test class that breaks because of the
delete still fails the deploy even though deletes happen last.

---

## Anti-Pattern: "Save As" Change Sets across orgs instead of git-tracked source

**What practitioners do:** In the source sandbox, click Setup →
Outbound Change Sets → New, manually click Add for every component,
hit Upload, then on the target log in, navigate to Inbound Change
Sets, click Deploy. Repeat for every release. Bonus pain: clone the
change set with "Save As" when something needs to roll forward to
another sandbox.

**What goes wrong, in order of severity:**

1. **No diff, no review.** A change set is an opaque list of
   component names; no reviewer can see what changed inside an
   `ApexClass` or `Flow` without manually retrieving both
   versions. Code review effectively disappears.

2. **No rollback narrative.** Once a change set is deployed, the
   target org has the new state with no record of the old state
   beyond Setup Audit Trail. If a release breaks prod at 2am,
   there's no `git revert` — the on-call has to manually reverse
   every component change or restore from a sandbox refresh
   point (often days old).

3. **Dependency-graph blindness.** Change Sets do not auto-include
   referenced components. If your new `OpportunityProfitMargin__c`
   field is referenced by `OpportunityProfitMarginFormula__c`,
   three Lightning page layouts, and a Report, none of those get
   pulled in unless the human clicker remembers them. The deploy
   half-succeeds and the report silently returns null for every
   row — a failure source-format `sf project deploy` would have
   caught at validation time.

4. **No CI gate.** Change Sets can't be deployed by a script —
   there is no `sf change-set deploy`. The release pipeline
   becomes "click Deploy in the target org": no automated test
   gate, no manifest-lint, no security scanner pre-check, no
   `validate → quick` window for high-risk releases.

5. **No cross-environment idempotency.** Change Sets are point-
   to-point between connected orgs. A promotion path int → uat
   → staging → prod requires re-uploading from int into each
   downstream org (re-authoring) or re-retrieving from each
   intermediate sandbox to build a new change set. Either way,
   the "thing being promoted" diverges from the thing that was
   originally tested.

**Correct approach:** Author `package.xml` in source control once.
Drive every cross-org deploy with `sf project deploy validate`
(captures a job ID) followed by `sf project deploy quick --job-id`
(reuses the validation tests). Tag the manifest + job ID in git on
every prod release; rollback is `git checkout <prev-tag>` plus
re-deploy of the prior manifest. Every reviewer sees a diff in the
PR. Every release runs through the same pipeline against every
environment in the promotion path. The Change Set UI becomes a
legacy debugging tool, not the release substrate.
