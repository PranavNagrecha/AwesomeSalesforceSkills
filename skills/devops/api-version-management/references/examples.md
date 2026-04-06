# Examples — API Version Management

## Example 1: Full Codebase Version Audit Before Retirement Deadline

**Context:** A team receives a Salesforce notification that API versions 21.0-30.0 will be retired. Their org has 400+ Apex classes, some inherited from a 2015 implementation. They need to identify every affected component.

**Problem:** Without a systematic audit, the team manually searches a few classes and finds some on version 28.0, but misses triggers on version 25.0 and Visualforce pages on version 29.0. After retirement, deployments start failing and a critical integration breaks.

**Solution:**

```bash
# Step 1: Check the project baseline
grep '"sourceApiVersion"' sfdx-project.json
# Output: "sourceApiVersion": "58.0"

# Step 2: Find all components below the retirement threshold
grep -r '<apiVersion>' force-app/ --include='*-meta.xml' \
  | awk -F'[<>]' '{print $3, $0}' \
  | awk '$1 < 31 {print}' \
  | sort -n

# Step 3: Count affected components by version
grep -roh '<apiVersion>[0-9.]*</apiVersion>' force-app/ --include='*-meta.xml' \
  | sort | uniq -c | sort -rn

# Example output:
#   142  <apiVersion>58.0</apiVersion>
#    45  <apiVersion>50.0</apiVersion>
#    12  <apiVersion>28.0</apiVersion>
#     3  <apiVersion>25.0</apiVersion>
```

**Why it works:** Automated scanning catches every versioned file regardless of type (classes, triggers, pages, components). Sorting by version immediately reveals the retirement-critical tier and the magnitude of drift.

---

## Example 2: Incremental Upgrade of a Large Codebase with Limited Test Coverage

**Context:** An ISV has 600 Apex classes spanning versions 35.0 through 55.0. Their test coverage is 78% but concentrated on newer classes. Upgrading everything to 63.0 in one shot risks breaking untested legacy code.

**Problem:** A big-bang upgrade changes behavior in `String.format()`, SOQL polymorphic relationship resolution, and trigger order-of-execution refinements across 20+ version increments. Three production bugs appear simultaneously and the team cannot isolate which version change caused which failure.

**Solution:**

```bash
# Tier 1: Upgrade components on versions 35-40 to 45.0 (smallest, oldest group)
find force-app/ -name '*-meta.xml' -exec grep -l '<apiVersion>3[5-9]\|<apiVersion>40' {} \;
# Update each file's <apiVersion> to 45.0
# Run: sf project deploy start --target-org sandbox --test-level RunLocalTests

# Tier 2: After Tier 1 passes, upgrade 41-50 to 55.0
# Tier 3: After Tier 2 passes, upgrade 45-55 to 63.0
# Tier 4: Update sourceApiVersion in sfdx-project.json to 63.0
```

**Why it works:** Each tier upgrade narrows the behavior change window. If tests fail after Tier 1, the team knows the regression is caused by the 35-40 to 45.0 jump and can consult specific release notes for that range. Untested code gets exercised in smaller increments.

---

## Example 3: LWC Explicit Version Declaration (Spring '25 Requirement)

**Context:** A project has 30 LWC components. Before Spring '25, none had explicit `<apiVersion>` in their `.js-meta.xml` files because the platform used the org's current version implicitly.

**Problem:** After the Spring '25 upgrade, the team notices inconsistent behavior in wire adapters. Some components silently inherit the org version (63.0) while others that were retrieved at an earlier release carry stale implicit versions.

**Solution:**

```xml
<!-- After: .js-meta.xml with explicit version -->
<?xml version="1.0" encoding="UTF-8"?>
<LightningComponentBundle xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>63.0</apiVersion>
    <isExposed>true</isExposed>
    <targets>
        <target>lightning__RecordPage</target>
    </targets>
</LightningComponentBundle>
```

```bash
# Find LWC bundles missing explicit apiVersion
find force-app/ -name '*.js-meta.xml' -exec grep -L '<apiVersion>' {} \;

# Add apiVersion to each missing file using sed
for f in $(find force-app/ -name '*.js-meta.xml' -exec grep -L '<apiVersion>' {} \;); do
  sed -i '' '/<isExposed>/i\
    <apiVersion>63.0</apiVersion>' "$f"
done
```

**Why it works:** Explicit version declaration eliminates ambiguity about which wire adapters and base components are available. All LWC bundles now run at a known, consistent version.

---

## Anti-Pattern: Updating sourceApiVersion Without Updating Components

**What practitioners do:** They update `sourceApiVersion` in `sfdx-project.json` to 63.0 and assume all components are now running at that version.

**What goes wrong:** Every component continues to execute at the version declared in its own `-meta.xml` file. The sourceApiVersion only affects CLI operations (deploy, retrieve, generate). A class with `<apiVersion>45.0</apiVersion>` still runs as version 45.0 regardless of what sourceApiVersion says. The team has a false sense of currency while running on legacy behavior.

**Correct approach:** Update `sourceApiVersion` *and* update every component's `<apiVersion>` element. Use a version audit script to verify consistency. Treat `sourceApiVersion` as a project intent declaration, not a runtime override.
