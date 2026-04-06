# LLM Anti-Patterns — Migration From Change Sets To SFDX

Common mistakes AI coding assistants make when generating or advising on migration from change sets to SFDX source-driven development. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Using Deprecated SFDX Commands Instead of Modern SF CLI

**What the LLM generates:** `sfdx force:mdapi:convert --rootdir mdapi-output/ --outputdir force-app/` or `sfdx force:source:push` — using the legacy `sfdx` binary and `force:` namespace that was deprecated in favor of the `sf` CLI.

**Why it happens:** Training data contains a large volume of pre-2023 Salesforce DX tutorials and Stack Overflow answers that use the older `sfdx force:` command namespace. The LLM defaults to the more frequently seen syntax.

**Correct pattern:**

```bash
# Modern SF CLI equivalents
sf project convert mdapi --root-dir mdapi-output/ --output-dir force-app/
sf project retrieve start --manifest package.xml --target-org prod --output-dir mdapi-output/
sf project deploy start --source-dir force-app/ --target-org sandbox
```

**Detection hint:** Flag any command starting with `sfdx force:` — all `force:` commands have `sf` equivalents and the `sfdx` binary is deprecated.

---

## Anti-Pattern 2: Recommending Wildcard Retrieval for the Entire Org

**What the LLM generates:** "Retrieve all metadata with `<members>*</members>` for every type in your package.xml" — suggesting a full-org retrieve as the starting point for migration.

**Why it happens:** Wildcard retrieval is the simplest instruction to generate and appears to be comprehensive. The LLM does not account for the fact that a production org contains thousands of standard and managed-package components the team does not own.

**Correct pattern:**

```xml
<!-- Targeted retrieval — list only team-maintained components -->
<types>
    <members>MyApexClass</members>
    <members>MyApexClassTest</members>
    <name>ApexClass</name>
</types>
```

**Detection hint:** Flag `<members>*</members>` in migration-context package.xml generation. Wildcards are acceptable for small metadata types (CustomApplication, CustomTab) but dangerous for ApexClass, CustomObject, Profile, FlowDefinition, and Report.

---

## Anti-Pattern 3: Assuming Source Tracking Works in All Sandbox Types

**What the LLM generates:** "After migrating, just use `sf project deploy start` and `sf project retrieve start` — the CLI will automatically track what changed" — implying source tracking is universal.

**Why it happens:** Source tracking in scratch orgs is a prominent feature in Salesforce DX documentation. The LLM generalizes this to all orgs without noting the sandbox-type limitation.

**Correct pattern:**

```text
Source tracking is available in:
- Scratch orgs (always)
- Developer sandboxes and Developer Pro sandboxes (since Spring '21)

Source tracking is NOT available in:
- Partial Copy sandboxes
- Full Copy sandboxes
- Production orgs

For non-tracked orgs, use manifest-based deployment:
sf project deploy start --manifest package.xml --target-org <org>
```

**Detection hint:** Flag advice that mentions automatic source tracking without specifying the org/sandbox type. If the target is a partial-copy, full-copy sandbox, or production, source tracking does not apply.

---

## Anti-Pattern 4: Omitting .forceignore Configuration

**What the LLM generates:** Migration instructions that end after the `sf project convert mdapi` step without mentioning `.forceignore`. The generated project has no exclusion rules, causing deploy failures when the team runs their first `sf project deploy start`.

**Why it happens:** `.forceignore` is a Salesforce-specific concept with no direct equivalent in standard git workflows. LLMs default to mentioning `.gitignore` (which only affects git, not the CLI) and skip `.forceignore` entirely.

**Correct pattern:**

```bash
# .forceignore — required in SFDX project root
# Managed packages
**/installedPackages/**
# Profiles (manage via permission sets)
**/profiles/**
# Standard value sets the team does not customize
**/standardValueSets/**
```

**Detection hint:** Flag any migration guide that does not mention `.forceignore`. Also flag advice to "add managed-package components to `.gitignore`" — `.gitignore` prevents git tracking but does not prevent the CLI from attempting to deploy files already in the working directory.

---

## Anti-Pattern 5: Telling Users to Delete Files to Remove Org Components

**What the LLM generates:** "To remove the old custom field from production, just delete the field file from your source directory and redeploy" — implying that absence in the source equals deletion in the org.

**Why it happens:** In most infrastructure-as-code tools (Terraform, CloudFormation), removing a resource from the config file deletes it from the target. The LLM applies this mental model to Salesforce, which does not work the same way.

**Correct pattern:**

```xml
<!-- destructiveChangesPost.xml -->
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Account.Old_Field__c</members>
        <name>CustomField</name>
    </types>
</Package>
```

```bash
sf project deploy start \
  --manifest package.xml \
  --post-destructive-changes destructiveChangesPost.xml \
  --target-org prod
```

**Detection hint:** Flag any instruction that says "delete the file and redeploy" or "remove the component from source and deploy" without mentioning `destructiveChangesPost.xml` or `destructiveChangesPre.xml`.

---

## Anti-Pattern 6: Conflating sfdx-project.json packageDirectories With Unlocked Packages

**What the LLM generates:** "Add a `packageDirectories` entry for each team in your sfdx-project.json — this creates separate packages for each team" — conflating directory configuration with package creation.

**Why it happens:** The `packageDirectories` array in `sfdx-project.json` defines source paths, and the `package` property within a directory entry links it to a package. LLMs conflate defining a directory with creating a package, skipping the `sf package create` step.

**Correct pattern:**

```text
packageDirectories in sfdx-project.json define source paths for the CLI.
They do NOT create packages by themselves.

To create an unlocked package:
1. Define the directory in sfdx-project.json
2. Run: sf package create --name MyPackage --package-type Unlocked --path force-app/
3. The CLI updates sfdx-project.json with the package ID

For manifest-based deploys (the typical first step after migrating from change sets),
you only need a single packageDirectories entry pointing to force-app/.
```

**Detection hint:** Flag advice that suggests `packageDirectories` entries alone create packages, or that recommends multiple `packageDirectories` during initial migration without explaining the difference between source paths and packages.
