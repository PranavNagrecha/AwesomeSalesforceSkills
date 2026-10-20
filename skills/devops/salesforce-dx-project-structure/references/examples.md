# Examples — Salesforce DX Project Structure

## Example 1: Minimal Single-Package Project Setup

**Context:** A solo developer starting a new Salesforce project for a small business. One team, no package versioning needed.

**Problem:** Without a valid `sfdx-project.json`, the directory is not a DX project (sfdx_dev 264 L2299-2300). New developers often create the file manually and miss required fields; `sf project generate --name` scaffolds it (L1398).

**Solution:**

```json
{
  "packageDirectories": [
    {
      "path": "force-app",
      "default": true
    }
  ],
  "namespace": "",
  "sourceApiVersion": "62.0",
  "sfdcLoginUrl": "https://login.salesforce.com"
}
```

Directory structure:

```
my-project/
  sfdx-project.json
  force-app/
    main/
      default/
        classes/
        triggers/
        lwc/
        objects/
        flows/
        permissionsets/
  .gitignore
```

**Why it works:** The `packageDirectories` array has one entry, which is assumed default (sfdx_dev 264 L2363-2364); `"default": true` is harmless and required once a second entry is added. The `namespace` is blank, as in the guide's sample (L2314). `sourceApiVersion` is a string, as in the guide's sample (L2316).

---

## Example 2: Multi-Package Mono-Repo with Dependencies

**Context:** An enterprise team has three workstreams — core data model, sales automation, and service extensions. Each team needs independent versioning and deployment.

**Problem:** Without structured packageDirectories and explicit dependencies, changes in the core model can silently break downstream packages. Deployment order becomes guesswork.

**Solution:**

```json
{
  "packageDirectories": [
    {
      "path": "packages/core-data-model",
      "default": true,
      "package": "CoreDataModel",
      "versionName": "Spring 25",
      "versionNumber": "1.4.0.NEXT"
    },
    {
      "path": "packages/sales-automation",
      "package": "SalesAutomation",
      "versionName": "Spring 25",
      "versionNumber": "2.0.0.NEXT",
      "dependencies": [
        {
          "package": "CoreDataModel",
          "versionNumber": "1.4.0.LATEST"
        }
      ]
    },
    {
      "path": "packages/service-extensions",
      "package": "ServiceExtensions",
      "versionName": "Spring 25",
      "versionNumber": "1.1.0.NEXT",
      "dependencies": [
        {
          "package": "CoreDataModel",
          "versionNumber": "1.4.0.LATEST"
        }
      ]
    }
  ],
  "namespace": "",
  "sourceApiVersion": "62.0"
}
```

Directory structure:

```
enterprise-project/
  sfdx-project.json
  packages/
    core-data-model/
      main/default/objects/
      main/default/classes/
    sales-automation/
      main/default/classes/
      main/default/flows/
      main/default/lwc/
    service-extensions/
      main/default/classes/
      main/default/flows/
```

**Why it works:** Each package has its own directory, version, and explicit dependencies. UNVERIFIED (2026-10-20): that the CLI builds packages in dependency order. Directory locations are local only and carry no association with the package in the org (sfdx_dev 264 L2485-2487).

---

## Example 3: Mixed Packaged and Unpackaged Metadata

**Context:** An ISV ships a managed package but also needs to deploy org-specific post-install configuration (admin profiles, permission set assignments, page layout assignments) that should never be packaged.

**Problem:** Including org-specific metadata in a package causes installation failures in subscriber orgs with different profiles or layouts.

**Solution:**

```json
{
  "packageDirectories": [
    {
      "path": "packages/managed-app",
      "default": true,
      "package": "MyManagedApp",
      "versionName": "GA Release",
      "versionNumber": "3.0.0.NEXT"
    },
    {
      "path": "config/unpackaged",
      "default": false
    }
  ],
  "namespace": "myns",
  "sourceApiVersion": "62.0"
}
```

The `config/unpackaged/` directory contains profiles, permission sets, and sample data scripts that deploy via `sf project deploy`. UNVERIFIED (2026-10-20): that it is excluded from `sf package version create` and that the packaging engine ignores a directory with no `package` key.

**Why it works:** The guide's own sample includes a plain `unpackaged` path entry (sfdx_dev 264 L2311) and describes package directories as able to hold "unpackaged source files" (L2354), so the entry is valid; deploy it by path with `--source-dir`.

---

## Anti-Pattern: Hardcoding Build Numbers Without Incrementing Them

**What practitioners do:** Set `versionNumber` to `"1.0.0.4"` and leave it there across several package version creations.

**What goes wrong:** "To avoid creating multiple package versions with the same MAJOR.MINOR.PATCH.BUILD number, you must increment the versionNumber before creating a new package version", and the guide advises against creating several versions with the same number (sfdx_dev 264 L14869-14871, L16160). UNVERIFIED (2026-10-20): that the CLI rejects a repeated build number.

**Correct approach:** Use `NEXT` in the build slot, `"1.0.0.NEXT"`, to take "the next available build for the package" (L14872-14873), or bump the number deliberately.
