# Worked Runbook — Retrieve, Validate, Quick Deploy, With a Post-Destructive Delete

**Release:** add `Invoice__c.Due_Date__c`, ship a new version of `InvoiceService` that no longer reads `Invoice__c.Legacy_Code__c`, and delete `Legacy_Code__c` in the same production release.

This is the case the Metadata API guide uses to explain `destructiveChangesPost.xml`. You can't delete a component while an Apex class still references it. One deployment can update the class to clear the reference and then delete the component after the additions (api_meta.txt L4655–4667).

## 1. The manifest directory

```text
manifest/
├── package.xml                 # what is added or updated; carries the API version
└── destructiveChangesPost.xml  # what is deleted after the additions
```

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- manifest/package.xml -->
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>InvoiceService</members>
        <members>InvoiceServiceTest</members>
        <name>ApexClass</name>
    </types>
    <types>
        <members>Invoice__c.Due_Date__c</members>
        <name>CustomField</name>
    </types>
    <version>67.0</version>
</Package>
```

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- manifest/destructiveChangesPost.xml: same format as package.xml, but no wildcards and no <version> -->
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Invoice__c.Legacy_Code__c</members>
        <name>CustomField</name>
    </types>
</Package>
```

The deployment runs at the API version declared in `package.xml` (L4691), so `<version>` there is not optional. Pre and Post manifests need API 33.0 or later. Without them, deletions are processed before additions (L4601–4605, L4648–4654). Here that order would try to delete the field while the old `InvoiceService` still uses it, so the deletion has to go in Post.

## 2. Static gate

```bash
python3 skills/devops/metadata-api-retrieve-deploy/scripts/check_metadata_api_retrieve_deploy.py \
  --manifest-dir manifest --strict
```

On the two files above the checker exits 0. It would exit 1 in any of these cases:

- `destructiveChangesPost.xml` used `<members>*</members>`.
- `package.xml` were missing from the directory.
- `package.xml` declared a version below 33.0.
- `Invoice__c.Legacy_Code__c` were listed in both files.

## 3. Retrieve from the source org

```bash
sf project retrieve start --manifest manifest/package.xml --target-org dev-sandbox
```

Commit what the retrieve wrote, so that the git tag and the deploy are the same thing (sfdx_dev.txt L14211–14213).

## 4. Validate against production

A validation is a deploy with `checkOnly` set to true. It runs the tests and checks the components without saving anything (api_meta.txt L4170–4176). For an add/update-only release, the documented command is:

```bash
sf project deploy validate --manifest manifest/package.xml --target-org prod-org \
  --test-level RunSpecifiedTests --tests InvoiceServiceTest
```

It returns the job ID that the quick deploy uses (sfdx_dev.txt L14258–14269). With `RunSpecifiedTests`, `InvoiceServiceTest` on its own has to cover each class and trigger in the package at 75% or more (api_meta.txt L4287–4293). This release also deletes an Apex reference. The guide therefore recommends running all local tests "to detect any remaining references", so use `--test-level RunLocalTests` here (L4688–4689). Post-destructive deletions are processed before the tests run (L4687), which means a test that still touches `Legacy_Code__c` fails the validation, not production.

**Attaching the destructive manifest.** The Metadata API accepts `destructiveChangesPost.xml` next to `package.xml` in the deployed bundle (L4614–4631, L4664–4685). The corpus does not document the CLI side, but `sf project deploy validate --help` and `sf project deploy start --help` (Salesforce CLI 2.151.7) both list `--pre-destructive-changes` and `--post-destructive-changes`, each taking the file path of the manifest, alongside `--manifest`. For this release:

```bash
sf project deploy validate --manifest manifest/package.xml \
  --post-destructive-changes manifest/destructiveChangesPost.xml \
  --target-org prod-org --test-level RunLocalTests
```

Check `--help` on the CLI version your pipeline pins before relying on the flag names. Another route is a metadata-format folder deployed with `sf project deploy start --metadata-dir` (sfdx_dev.txt L2809–2810), which `sf project convert source --output-dir mdapiOut --source-dir force-app` produces (L2824–2825).

## 5. Quick deploy

```bash
sf project deploy quick --job-id <JOB_ID> --target-org prod-org
```

This works only while the validation is recent. The components must have been validated against this target within the last 10 days, with passing tests and coverage met (api_meta.txt L3450–3460, L4864–4866). If the release slips past day 10, validate again.

## 6. Options to set on purpose

| Option | Value for this release | Why |
|---|---|---|
| `rollbackOnError` | true | It must be true for production. The REST deploy reference gives its default as true (L3329), but the SOAP `DeployOptions` table says "The default is false" (L4255–4261). Set it explicitly in any tool that calls the API directly. On the CLI, never add `--ignore-errors` to a production job (sfdx_dev.txt L13523). |
| `purgeOnDelete` | unset | It only works in Developer Edition and sandbox orgs. In production, deleted fields go to the Recycle Bin (L4234–4241). |
| `allowMissingFiles` / `autoUpdatePackage` | unset | Both carry the note "Don't set this argument for deployment to production orgs" (L4160–4167). |
| `ignoreWarnings` | false | With false, a warning fails the deploy the same way an error does (L4215–4224). |

## 7. Archive

Tag the commit. Store `manifest/`, the validation job ID, and the quick-deploy result together. If you need to roll back later, redeploy the previous tag's manifest. In production the deleted field went to the Recycle Bin and was not purged (L4234–4241), so any data recovery starts there, not with a redeploy.
