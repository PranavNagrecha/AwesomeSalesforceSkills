# Metadata API Retrieve / Deploy — Work Template

Use this template to plan one manifest-driven release. Fill every blank before the first command runs. A worked version of the same plan is in `references/retrieve-deploy-runbook.md`.

## Scope

**Skill:** `metadata-api-retrieve-deploy`

**Request summary:** ______________________ (for example "ship Invoice__c.Due_Date__c and InvoiceService, remove Invoice__c.Legacy_Code__c")

## Context Gathered

| Question (SKILL.md § Questions to Ask) | Answer |
|---|---|
| Source org alias / target org alias | ____ / ____ |
| Is the target production? Does the release contain Apex classes or triggers? | |
| Manifest `<version>` and the newest type in it (check its "available in API version" line) | |
| Wildcards anywhere? (never in a destructive manifest — they are not supported) | |
| Components deleted, and is each one still referenced by something in this release? | |
| Cross-type references that need a split deploy order | |
| Date of validation and planned quick-deploy date (must be within 10 days) | |

## Manifests

- [ ] `manifest/package.xml` — explicit `<members>`, one `<types>` block per type, `<version>` set
- [ ] `destructiveChangesPre.xml` — deletions that must run **before** additions (API 33.0+), or none
- [ ] `destructiveChangesPost.xml` — deletions that must run **after** additions, for example a field an updated class stops using (API 33.0+), or none
- [ ] Every destructive manifest sits in the same directory as a `package.xml` that carries the API version

## Approach

Which pattern from SKILL.md applies, and why:

- [ ] CI deploy gate (validate → quick deploy)
- [ ] Rename a field (Pre destructive + add)
- [ ] Remove a still-referenced component (update the referrer + Post destructive)
- [ ] One-off wildcard retrieve (capture only, never deployed as-is)

Test level: [ ] RunLocalTests  [ ] RunSpecifiedTests — tests: ______________ (each class and trigger needs 75% from these tests alone)

## Commands

```bash
# 1. Retrieve the scope from the source org
sf project retrieve start --manifest manifest/package.xml --target-org <source-alias>

# 2. Static gate on manifests and pipeline scripts
python3 skills/devops/metadata-api-retrieve-deploy/scripts/check_metadata_api_retrieve_deploy.py \
  --manifest-dir manifest --strict

# 3. Validate against the target (returns the job ID)
sf project deploy validate --manifest manifest/package.xml --target-org <target-alias> \
  --test-level RunLocalTests

# 4. After approval, inside the 10-day window
sf project deploy quick --job-id <JOB_ID> --target-org <target-alias>
```

Job ID: ______________  Validated on: ______________

## Checklist

- [ ] Manifest uses explicit members (no unintentional wildcards)
- [ ] Each deletion is in the Pre or Post manifest on purpose
- [ ] Checker exits 0 with `--strict`
- [ ] `rollbackOnError` true for production; no `--ignore-errors` in the production job
- [ ] Test level is `RunLocalTests` or `RunSpecifiedTests` with a named test list
- [ ] Validation job ID archived with the manifest and the git tag

## Notes

Deviations from the standard pattern, and why:

- 
