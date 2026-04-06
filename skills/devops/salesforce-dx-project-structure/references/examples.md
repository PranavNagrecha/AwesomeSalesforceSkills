# Examples — Salesforce DX Project Structure

## Example 1: Minimal Single-Package Project Setup

**Context:** A solo developer starting a new Salesforce project for a small business. One team, no package versioning needed.

**Problem:** Without a valid `sfdx-project.json`, no `sf` CLI commands work. New developers often create the file manually and miss required fields.

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

**Why it works:** The `packageDirectories` array has exactly one entry with `"default": true`, which satisfies the CLI minimum. The `namespace` is blank (correct for non-managed development). The `sourceApiVersion` matches a known valid API version.

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

**Why it works:** Each package has its own directory, version, and explicit dependencies. The CLI builds packages in dependency order. Teams can deploy their package independently once dependencies are satisfied.

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

The `config/unpackaged/` directory contains profiles, permission sets, and sample data scripts that deploy via `sf project deploy` but are excluded from `sf package version create`.

**Why it works:** The unpackaged directory has no `package` key, so the packaging engine ignores it. But `sf project deploy` still picks it up when you specify that path. This separates product metadata from org configuration cleanly.

---

## Anti-Pattern: Hardcoding Build Numbers in versionNumber

**What practitioners do:** Set `versionNumber` to `"1.0.0.4"` with a specific build number instead of using `NEXT`.

**What goes wrong:** The `sf package version create` command auto-increments the build number. If you hardcode it, the CLI may reject the version create if that build number already exists, or you get conflicting version numbers across branches.

**Correct approach:** Always use `NEXT` as the fourth segment: `"1.0.0.NEXT"`. The CLI resolves this to the next available build number at creation time.
