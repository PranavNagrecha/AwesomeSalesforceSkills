# Unlocked Package Development — Work Template

Use this template when designing, creating, or troubleshooting an unlocked package. Fill in every section before writing commands or configuration.

---

## Scope

**Skill:** `unlocked-package-development`

**Request summary:** (fill in what the practitioner asked for)

**Mode:**
- [ ] Mode 1 — Build: Create a new package or publish a new version
- [ ] Mode 2 — Review/Audit: Inspect version status, coverage, or dependency chain
- [ ] Mode 3 — Troubleshoot: Diagnose and fix a failing version create, install, or promotion

---

## Context Gathered

Answer these before taking any action:

| Question | Answer |
|---|---|
| Dev Hub org alias | |
| Package name(s) | |
| Namespace strategy (namespace-less / namespaced) | |
| Namespace string (if namespaced) | |
| Package ID(s) (`0Ho...`) — or "new" if not yet created | |
| Target subscriber org(s) (scratch / sandbox / production) | |
| Known inter-package dependencies | |
| Installation key required? | Yes / No |
| Apex code coverage current estimate | % |
| Is this a beta or released version install? | |

---

## Package Directory Configuration

Fill in the `sfdx-project.json` block for this package. Use the structure below:

```json
{
  "packageDirectories": [
    {
      "path": "<REPLACE: relative path to package source, e.g. force-app>",
      "default": true,
      "package": "<REPLACE: package name matching packageAliases key>",
      "versionName": "<REPLACE: human-readable version label, e.g. Spring 2025>",
      "versionNumber": "<REPLACE: e.g. 1.0.0.NEXT>",
      "dependencies": [
        {
          "package": "<REPLACE: dependency alias from packageAliases>",
          "versionNumber": "<REPLACE: e.g. 1.0.0.LATEST>"
        }
      ]
    }
  ],
  "namespace": "<REPLACE: empty string for namespace-less, or registered namespace>",
  "sfdcLoginUrl": "https://login.salesforce.com",
  "sourceApiVersion": "<REPLACE: e.g. 63.0>",
  "packageAliases": {
    "<REPLACE: package name>": "<REPLACE: 0Ho... package ID from sf package create>"
  }
}
```

---

## Commands

### Package Creation (run once per package)

```bash
sf package create \
  --name "<REPLACE: package name>" \
  --package-type Unlocked \
  --path <REPLACE: source path> \
  --target-dev-hub <REPLACE: Dev Hub alias>
# Capture the 0Ho... Package ID from output and add to sfdx-project.json packageAliases
```

### Version Creation

```bash
sf package version create \
  --package "<REPLACE: package name or 0Ho... ID>" \
  --installation-key-bypass \        # Remove this line and use --installation-key if key is required
  --code-coverage \
  --wait 20 \
  --target-dev-hub <REPLACE: Dev Hub alias>
# Capture the 04t... Version ID from output
```

### Version Status Check

```bash
sf package version report \
  --package <REPLACE: 04t... version ID> \
  --target-dev-hub <REPLACE: Dev Hub alias>
```

### Promote to Released

```bash
sf package version promote \
  --package <REPLACE: 04t... version ID> \
  --no-prompt \
  --target-dev-hub <REPLACE: Dev Hub alias>
```

### Install in Subscriber Org

```bash
sf package install \
  --package <REPLACE: 04t... version ID> \
  --target-org <REPLACE: subscriber org alias> \
  --installation-key <REPLACE: key, or omit if no key> \
  --wait 10
```

### Check Installed Packages in Subscriber Org

```bash
sf package installed list --target-org <REPLACE: org alias>
```

---

## Dependency Install Order

List dependencies in the order they must be installed. Install all dependencies before installing the main package.

| Install Order | Package | Version ID (`04t...`) | Notes |
|---|---|---|---|
| 1 | | | |
| 2 | | | |
| 3 (main package) | | | |

---

## Review Checklist

- [ ] Dev Hub has Unlocked Packages and Second-Generation Packaging enabled
- [ ] `sfdx-project.json` has correct `package`, `versionNumber`, and `path` in all packageDirectories
- [ ] All declared packages have `0Ho...` IDs in `packageAliases`
- [ ] All dependency aliases resolve to valid `04t...` version IDs in `packageAliases`
- [ ] All dependency packages are installed in the target org before the main package
- [ ] Apex code coverage >= 75% confirmed via `sf package version report` before promotion
- [ ] Version promoted to Released before any production org install
- [ ] Installation key (if used) is stored in secrets management, not in source control
- [ ] `sf package installed list` confirms all expected packages are installed in subscriber org
- [ ] Namespace decision is documented and matches Dev Hub configuration

---

## Troubleshooting Log

Record issues encountered and how they were resolved:

| Error Encountered | Root Cause | Resolution |
|---|---|---|
| | | |
| | | |

---

## Notes

Record any deviations from the standard pattern and why:

(fill in)
