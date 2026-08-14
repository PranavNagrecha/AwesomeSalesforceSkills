# Examples — Deployment Automation Architecture

## Example 1: A destructive release that deletes a field an Apex class still references

**Context:** A release removes `Account.Legacy_Segment__c`. `SegmentService` reads the field, so the field cannot be
deleted until the class stops referencing it. Both changes must land in one promotion — leaving a half-applied state in
production is not acceptable.

**Problem:** The reflex is two deployments: one to update the class, one to drop the field. That doubles the change
window, and the interval between them is a state nobody tested. The single-deployment alternative fails if the
manifests are wired the default way, because "By default, deletions are processed before component additions" — the
platform tries to delete the field while the old class still references it.

**Solution:** One deployment, with the deletion moved *after* the additions via `destructiveChangesPost.xml`.

`package.xml` — what to add or update:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>SegmentService</members>
        <name>ApexClass</name>
    </types>
    <version>67.0</version>
</Package>
```

`destructiveChangesPost.xml` — what to delete once the class no longer references it:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Account.Legacy_Segment__c</members>
        <name>CustomField</name>
    </types>
</Package>
```

**Why it works:** The `Post` manifest defers the deletion until after `SegmentService` has been updated, which clears
the dependency inside a single transaction. Note that "Post destructive changes are processed before running any
tests", so the test run executes against the post-deletion state — which is the state you want tested. The
`<version>67.0</version>` in `package.xml` is not decoration: "The API version that the deployment uses is the API
version that's specified in `package.xml`", and at 67.0 the redeployed class picks up user mode as its default access
mode.

---

## Example 2: Validation-then-promote pipeline stage with explicit deploy options

**Context:** A mid-size team wants a PR gate that proves a change is deployable to production without deploying it, and
a promotion step that reuses the validated result.

**Problem:** Teams leave `rollbackOnError` unset in the lower environments and set it only for production. Because the
documented default is `false`, the sandbox stage then tolerates partial application and the pipeline reports green on
changes production will refuse.

**Solution:** State every option explicitly at every stage. The two stages differ in exactly one field — `checkOnly`.

```yaml
# .github/workflows/salesforce-pipeline.yml (excerpt)
jobs:
  validate:                       # runs on pull_request
    steps:
      - name: Validate against production
        run: |
          sf project deploy validate \
            --manifest manifest/package.xml \
            --post-destructive-changes manifest/destructiveChangesPost.xml \
            --test-level RunSpecifiedTests \
            --tests SegmentServiceTest AccountTriggerTest \
            --target-org prod \
            --wait 60
    # DeployOptions in effect: checkOnly=true, rollbackOnError=true,
    # testLevel=RunSpecifiedTests, ignoreWarnings=false, purgeOnDelete=false
    # (purgeOnDelete only functions in Developer Edition or sandboxes, never production)

  promote:                        # runs on merge to main, gated on `validate`
    steps:
      - name: Deploy the validated set
        run: |
          sf project deploy start \
            --manifest manifest/package.xml \
            --post-destructive-changes manifest/destructiveChangesPost.xml \
            --test-level RunSpecifiedTests \
            --tests SegmentServiceTest AccountTriggerTest \
            --target-org prod \
            --wait 60
```

**Why it works:** `RunSpecifiedTests` keeps the gate fast, but it carries a per-component floor — "Each class and
trigger in the deployment package must be covered by the executed tests for a minimum of 75% code coverage" — so the
`--tests` list has to be derived from the changed components, not maintained by hand. Running the identical option set
in both stages means the validation stage fails for the same reasons the promotion stage would, which is the entire
point of a validation stage.

---

## Anti-Pattern: Governing access through Profile files in the pipeline

**What practitioners do:** Retrieve Profiles, commit them, and treat the diff as the record of who can do what — then
rely on the deploy to apply revocations.

```xml
<!-- profiles/Sales_User.profile-meta.xml — the revocation that never lands -->
<fieldPermissions>
    <field>Opportunity.Discount__c</field>
    <editable>true</editable>
    <readable>true</readable>
</fieldPermissions>
<!-- the security team "revoked" access by DELETING this block -->
```

**What goes wrong:** Deleting the block revokes nothing. Profile deployment is designed "to overlay the existing
Profile settings in a target org", and "if you disable permissions for a profile, the newly disabled permission
information isn't exported" — an absent element is an instruction to leave the target alone, not to remove access. The
diff looks like a revocation in review and is a no-op in the org. The retrieve side compounds it: a Profile only
includes field-level security for fields whose objects were in the same `RetrieveRequest`, so the committed file was
never a complete picture to begin with.

**Correct approach:** Write revocations explicitly, and move governance to Permission Sets, which deploy as complete
objects.

```xml
<!-- profiles/Sales_User.profile-meta.xml — explicit revocation -->
<fieldPermissions>
    <field>Opportunity.Discount__c</field>
    <editable>false</editable>
    <readable>false</readable>
</fieldPermissions>
```

Then add a post-deploy verification step that reads the permission back from the target org, because a green deploy is
the weakest possible evidence that an access change took effect.
