# Metadata Examples: Package Development Strategy

Two complete project files: an internal multi-package unlocked layout and a managed 2GP ISV layout. Both are `sfdx-project.json` at the project root. Keys follow the Salesforce DX Developer Guide and the Second-Generation Managed Packaging Developer Guide (Summer '26).

## 1. Internal org decomposition with unlocked packages

`sfdx-project.json`

```json
{
  "packageDirectories": [
    {
      "path": "packages/shared-core",
      "package": "Shared-Core",
      "versionName": "Shared core objects and utilities",
      "versionNumber": "1.4.0.NEXT",
      "default": true
    },
    {
      "path": "packages/service-core",
      "package": "Service-Core",
      "versionName": "Case handling",
      "versionNumber": "2.5.0.NEXT",
      "dependencies": [
        { "package": "Shared-Core", "versionNumber": "1.4.0.RELEASED" }
      ]
    },
    {
      "path": "packages/sales-core",
      "package": "Sales-Core",
      "versionName": "Opportunity process",
      "versionNumber": "3.1.0.NEXT",
      "dependencies": [
        { "package": "Shared-Core", "versionNumber": "1.4.0.RELEASED" }
      ]
    }
  ],
  "name": "acme-internal-platform",
  "namespace": "",
  "sfdcLoginUrl": "https://login.salesforce.com",
  "sourceApiVersion": "67.0",
  "packageAliases": {
    "Shared-Core": "0HoXXXXXXXXXXXXXXX",
    "Service-Core": "0HoXXXXXXXXXXXXXXX",
    "Sales-Core": "0HoXXXXXXXXXXXXXXX"
  }
}
```

Notes:
- `NEXT` increments the build number. Without it, a forgotten `versionNumber` update reuses the previous number.
- `RELEASED` pins the dependency to the latest promoted version of that `MAJOR.MINOR.PATCH`. `LATEST` would pick up unreleased builds.
- The `0Ho` IDs are written by `sf package create`; the placeholders above are replaced on creation.

Commands (flags checked against `sf <command> --help`, CLI 2.151.7):

```bash
# Create each package once (namespace and Dev Hub are fixed from here on)
sf package create --name "Shared-Core" --path packages/shared-core --package-type Unlocked --no-namespace --target-dev-hub devhub
sf package create --name "Service-Core" --path packages/service-core --package-type Unlocked --no-namespace --target-dev-hub devhub

# Release candidate: full validation plus coverage (a --skip-validation build can't be promoted)
sf package version create --package "Shared-Core" --code-coverage --installation-key-bypass --wait 30 --target-dev-hub devhub
sf package version promote --package "Shared-Core@1.4.0-1" --target-dev-hub devhub

# Install in dependency order; unlocked upgrades choose what happens to removed metadata
sf package install --package "Shared-Core@1.4.0-1" --target-org uat --upgrade-type Mixed --wait 20 --no-prompt
```

## 2. Managed 2GP for an AppExchange product

`sfdx-project.json`

```json
{
  "packageDirectories": [
    {
      "path": "force-app",
      "package": "Expense Manager",
      "versionName": "Winter release",
      "versionNumber": "1.3.0.NEXT",
      "ancestorVersion": "HIGHEST",
      "definitionFile": "config/project-scratch-def.json",
      "default": true
    }
  ],
  "name": "expense-manager",
  "namespace": "expmgr",
  "sfdcLoginUrl": "https://login.salesforce.com",
  "sourceApiVersion": "67.0",
  "packageAliases": {
    "Expense Manager": "0HoXXXXXXXXXXXXXXX"
  }
}
```

Notes:
- `namespace` must already be registered in a namespace org and linked to the Dev Hub. It binds to the package when `sf package create` runs.
- `ancestorVersion: "HIGHEST"` sets the ancestor to the highest promoted version, so existing customers can upgrade. `NONE` would leave existing customers unable to upgrade to that version.
- For a patch (for example `1.3.1.NEXT`), the ancestor must be managed-released with the same major and minor numbers, and patch versioning must be enabled by Partner Support.

```bash
sf package create --name "Expense Manager" --path force-app --package-type Managed --target-dev-hub devhub
sf package version create --package "Expense Manager" --code-coverage --installation-key-bypass --wait 30 --target-dev-hub devhub
sf package version report --package "Expense Manager@1.3.0-1" --target-dev-hub devhub   # shows ancestor and coverage
sf package version promote --package "Expense Manager@1.3.0-1" --target-dev-hub devhub
```

## 3. Installing a managed 1GP dependency through Metadata API

`InstalledPackage` covers first-generation managed packages only. For unlocked and managed 2GP packages, the guide says to use `sf package install`. The file is named after the package's namespace prefix, and it must be the only metadata type in its deployment.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- force-app/main/default/installedPackages/acmegeo.installedPackage-meta.xml -->
<InstalledPackage xmlns="http://soap.sforce.com/2006/04/metadata">
    <activateRSS>true</activateRSS>
    <securityType>AdminsOnly</securityType>
    <versionNumber>2.1.3</versionNumber>
</InstalledPackage>
```

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- manifest/install-1gp.xml : InstalledPackage must be the only type in this manifest -->
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>acmegeo</members>
        <name>InstalledPackage</name>
    </types>
    <version>67.0</version>
</Package>
```

`activateRSS` true keeps the package's Remote Site Settings and CSP Trusted Sites active; the default false installs them inactive, which breaks callouts until someone activates them. Add `<password>` only for installation-key-protected packages, and keep the key out of source control.

## Verification

| Check | Command or place |
|---|---|
| Namespace linked | Dev Hub > Namespace Registries lists the namespace org |
| Ancestor and coverage of a version | `sf package version report --package <alias>` |
| Package list and org-dependent flag | `sf package list --verbose --target-dev-hub devhub` |
| Project file sanity | `python3 skills/devops/package-development-strategy/scripts/check_package_development_strategy.py --project-dir .` |

## Sources

- Salesforce DX Developer Guide (Summer '26): Unlocked Packaging Keywords, Create and Update an Unlocked Package, Skip Validation, Code Coverage for Unlocked Packages, Upgrade a Version of an Unlocked Package.
- Second-Generation Managed Packaging Developer Guide (Summer '26): Namespaces, project file example, Package Ancestors, Patch Versions.
- Salesforce CLI 2.151.7 `--help` for `package create`, `package version create`, `package version promote`, `package version report`, `package install`.
