# Examples — Migration From Change Sets To SFDX

## Example 1: Retrieving and Converting Apex Classes as the First Migration Batch

**Context:** A team of 4 developers has 120 Apex classes deployed via change sets. They want to start the migration with Apex because it has the clearest one-file-per-component mapping and changes most frequently.

**Problem:** Without a targeted retrieval strategy, running `sf project retrieve start` with `<members>*</members>` for ApexClass pulls every Apex class in the org — including managed-package classes the team does not own. Committing all of these pollutes the repository and creates false ownership.

**Solution:**

```xml
<!-- package.xml — targeted Apex retrieval -->
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>AccountService</members>
        <members>AccountServiceTest</members>
        <members>OpportunityTriggerHandler</members>
        <members>OpportunityTriggerHandlerTest</members>
        <members>CaseEscalationBatch</members>
        <members>CaseEscalationBatchTest</members>
        <!-- List every class the team maintains -->
        <name>ApexClass</name>
    </types>
    <types>
        <members>OpportunityTrigger</members>
        <name>ApexTrigger</name>
    </types>
    <version>62.0</version>
</Package>
```

```bash
# Retrieve in mdapi format
sf project retrieve start \
  --manifest package.xml \
  --target-org prod \
  --output-dir mdapi-output/

# Convert to source format
sf project convert mdapi \
  --root-dir mdapi-output/ \
  --output-dir force-app/

# Verify file count matches expectations
find force-app/main/default/classes -name "*.cls" | wc -l
# Should match the number of ApexClass members in package.xml

# Validate round-trip deploy
sf project deploy start \
  --source-dir force-app/ \
  --target-org dev-sandbox \
  --dry-run
```

**Why it works:** Listing specific members prevents managed-package classes from entering the repo. The round-trip deploy confirms that the conversion preserved all metadata without corruption. Starting with Apex is low-risk because Apex classes map 1:1 to files in both formats.

---

## Example 2: Converting Custom Objects With Field Decomposition

**Context:** The team has 5 custom objects with 30-80 fields each, plus validation rules and list views. They have been deploying object changes via change sets and want to move these into source format.

**Problem:** In mdapi format, each custom object is a single large XML file (e.g., `objects/Account_Review__c.object`). This file contains every field, every validation rule, every list view. Git diffs on a 2,000-line XML file are unreadable, and merge conflicts are frequent when two developers modify different fields.

**Solution:**

```bash
# Retrieve the objects in mdapi format
sf project retrieve start \
  --manifest object-package.xml \
  --target-org prod \
  --output-dir mdapi-objects/

# Convert — source format decomposes each object
sf project convert mdapi \
  --root-dir mdapi-objects/ \
  --output-dir force-app/

# Resulting structure (decomposed):
# force-app/main/default/objects/Account_Review__c/
#   Account_Review__c.object-meta.xml        (object-level settings)
#   fields/
#     Review_Date__c.field-meta.xml          (one file per field)
#     Reviewer__c.field-meta.xml
#   validationRules/
#     Require_Review_Date.validationRule-meta.xml
#   listViews/
#     All_Reviews.listView-meta.xml
```

```bash
# Commit with a meaningful message
git add force-app/main/default/objects/
git commit -m "Add Account_Review__c and related objects from production"

# Validate
sf project deploy start \
  --source-dir force-app/main/default/objects/ \
  --target-org dev-sandbox
```

**Why it works:** Source format decomposes the monolithic object XML into individual files per field, validation rule, and list view. Two developers can now modify different fields on the same object without merge conflicts. Git history shows exactly which field changed in each commit.

---

## Example 3: Setting Up .forceignore for a Clean Migration

**Context:** After converting all metadata, the team notices that the source directory contains standard object metadata (Account.object-meta.xml with standard fields), managed-package components, and profile metadata they do not want to track or deploy.

**Problem:** Without `.forceignore`, every `sf project deploy start` attempts to deploy standard object definitions and managed-package components, causing errors ("Cannot modify managed component") or unintended overwrites.

**Solution:**

```bash
# .forceignore — placed in the SFDX project root
# Managed packages
**/installedPackages/**

# Standard objects the team does not customize
**/objects/Account/fields/Name.field-meta.xml
**/objects/Account/fields/Industry.field-meta.xml

# Profiles (use permission sets instead)
**/profiles/**

# Admin-owned metadata not in source control
**/reports/unfiled$public/**
**/dashboards/**

# Scratch org settings files
**/settings/OrgPreference*
```

**Why it works:** `.forceignore` excludes files from both deploy and retrieve operations. This prevents accidental deployment of metadata the team does not own and keeps the repository focused on team-maintained components. Unlike `.gitignore`, `.forceignore` is respected by the Salesforce CLI during deploy and retrieve — not just by git.

---

## Anti-Pattern: Big-Bang Conversion With Wildcard Retrieval

**What practitioners do:** Run `sf project retrieve start` with `<members>*</members>` for every metadata type, convert the entire result in one pass, and commit it as a single "Initial migration" commit with 3,000+ files.

**What goes wrong:** The repository contains managed-package metadata the team cannot redeploy. Standard object definitions create noise in diffs. A single commit with thousands of files makes `git blame` useless — every line traces back to "Initial migration." If any component fails the round-trip deploy, the team cannot isolate which batch introduced the problem.

**Correct approach:** Use targeted `package.xml` manifests listing only team-maintained components. Retrieve and convert one metadata type group at a time. Commit each batch separately with descriptive messages. Validate each batch with a round-trip deploy before moving to the next.
