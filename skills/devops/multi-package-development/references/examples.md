# Examples — Multi-Package Development

## Example 1: Extracting a Base Package from a Monolithic Project

**Context:** A team has a single unlocked package containing 200+ custom objects, Apex classes, and LWC components. Deployments take 45 minutes and unrelated changes block each other.

**Problem:** Without decomposition, every developer works in one package. A failing Apex test in Sales logic blocks a Service team's LWC deployment. Version create times grow linearly with metadata volume.

**Solution:**

1. Identify shared objects and fields used across business domains (Account, Contact, custom junction objects).
2. Create a `force-app-base` directory and move shared metadata there.
3. Update `sfdx-project.json`:

```json
{
  "packageDirectories": [
    {
      "path": "force-app-base",
      "default": true,
      "package": "Acme-Base",
      "versionNumber": "1.0.0.NEXT",
      "dependencies": []
    },
    {
      "path": "force-app-sales",
      "package": "Acme-Sales",
      "versionNumber": "1.0.0.NEXT",
      "dependencies": [
        { "package": "Acme-Base", "versionNumber": "1.0.0.LATEST" }
      ]
    },
    {
      "path": "force-app-service",
      "package": "Acme-Service",
      "versionNumber": "1.0.0.NEXT",
      "dependencies": [
        { "package": "Acme-Base", "versionNumber": "1.0.0.LATEST" }
      ]
    }
  ],
  "packageAliases": {
    "Acme-Base": "0HoXXXXXXXXXXXXX",
    "Acme-Sales": "0HoYYYYYYYYYYYYY",
    "Acme-Service": "0HoZZZZZZZZZZZZZ"
  }
}
```

4. Build `Acme-Base` first, then `Acme-Sales` and `Acme-Service` in parallel (they have no dependency on each other).

**Why it works:** The base package stabilizes shared objects. Sales and Service teams release independently. Build times drop because each package contains only its metadata.

---

## Example 2: CI/CD Pipeline Sequencing for Three-Layer Architecture

**Context:** A project has Base, Domain, and UI packages. The team needs a GitHub Actions workflow that builds and installs all packages in the correct order.

**Problem:** Building packages in arbitrary order fails because `sf package version create` cannot resolve dependency aliases that do not yet exist as versions.

**Solution:**

```yaml
# .github/workflows/package-build.yml
jobs:
  build-base:
    runs-on: ubuntu-latest
    outputs:
      base_version_id: ${{ steps.create.outputs.subscriberPackageVersionId }}
    steps:
      - uses: actions/checkout@v4
      - name: Authenticate Dev Hub
        run: sf org login sfdx-url --sfdx-url-file devhub-auth-url.txt --set-default-dev-hub
      - name: Create Base version
        id: create
        run: |
          RESULT=$(sf package version create --package Acme-Base --wait 30 --json)
          echo "subscriberPackageVersionId=$(echo $RESULT | jq -r '.result.SubscriberPackageVersionId')" >> "$GITHUB_OUTPUT"

  build-sales:
    needs: build-base
    runs-on: ubuntu-latest
    outputs:
      sales_version_id: ${{ steps.create.outputs.subscriberPackageVersionId }}
    steps:
      - uses: actions/checkout@v4
      - name: Authenticate Dev Hub
        run: sf org login sfdx-url --sfdx-url-file devhub-auth-url.txt --set-default-dev-hub
      - name: Pin Base dependency
        run: |
          # Update packageAliases with the just-built Base version
          sf project generate manifest  # placeholder — use jq or sed to update sfdx-project.json
      - name: Create Sales version
        id: create
        run: |
          RESULT=$(sf package version create --package Acme-Sales --wait 30 --json)
          echo "subscriberPackageVersionId=$(echo $RESULT | jq -r '.result.SubscriberPackageVersionId')" >> "$GITHUB_OUTPUT"

  install-all:
    needs: [build-base, build-sales]
    runs-on: ubuntu-latest
    steps:
      - name: Install Base
        run: sf package install --package ${{ needs.build-base.outputs.base_version_id }} --target-org staging --wait 20
      - name: Install Sales
        run: sf package install --package ${{ needs.build-sales.outputs.sales_version_id }} --target-org staging --wait 20
```

**Why it works:** The `needs` keyword enforces topological order. Upstream 04t IDs are passed as outputs to downstream jobs. The install job runs packages in dependency order.

---

## Example 3: Resolving a Circular Dependency

**Context:** Sales package references a `Case_Escalation__c` object owned by Service, and Service references an `Opportunity_Link__c` field owned by Sales.

**Problem:** `sf package version create` fails for both packages because each declares the other as a dependency, forming a cycle.

**Solution:**

1. Identify the shared surface: `Case_Escalation__c` and `Opportunity_Link__c` are both junction/reference objects.
2. Move both into the Base package.
3. Update Sales and Service to depend on Base instead of each other.

```
Before:  Sales <---> Service   (ILLEGAL — circular)
After:   Sales ---> Base <--- Service   (LEGAL — acyclic)
```

**Why it works:** Extracting shared metadata into a lower layer breaks the cycle. Both domain packages depend downward, never sideways.

---

## Anti-Pattern: Duplicating Metadata Across Packages

**What practitioners do:** Copy the same custom object XML into two package directories so both packages "own" it, avoiding the need to create a dependency.

**What goes wrong:** Both packages deploy the same component. The second install overwrites the first's version. If the copies diverge, field definitions become inconsistent. Package uninstall may remove the component even though the other package still needs it.

**Correct approach:** Place shared metadata in exactly one package (typically Base) and declare it as a dependency in all consuming packages.
