# LLM Anti-Patterns — Feature Flags and Kill Switches

Common mistakes AI coding assistants make when generating or advising on feature flag and kill switch patterns in Salesforce.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Using Custom Settings instead of Custom Metadata Types for feature flags

**What the LLM generates:** Hierarchical Custom Settings as the primary feature flag mechanism:
```apex
Feature_Settings__c settings = Feature_Settings__c.getOrgDefaults();
if (settings.Enable_New_Flow__c) {
    // new logic
}
```

**Why it happens:** Custom Settings have been in Salesforce longer and appear more frequently in training data. LLMs default to the older, more common pattern.

**Correct pattern:**
```apex
Feature_Flag__mdt flag = Feature_Flag__mdt.getInstance('Enable_New_Flow');
if (flag != null && flag.IsEnabled__c) {
    // new logic
}
```
Custom Metadata Types are deployable, packageable, and can be changed without a code deploy. Custom Settings require data migration across orgs.

**Detection hint:** `__c.getOrgDefaults()` or `__c.getInstance()` used for boolean feature toggles — regex: `__c\.(getOrgDefaults|getInstance)\(`

---

## Anti-Pattern 2: Hallucinating FeatureManagement.setPackageBooleanValue() for non-ISV contexts

**What the LLM generates:** Using `FeatureManagement` class methods for general feature flags:
```apex
FeatureManagement.setPackageBooleanValue('MyFeature', true);
```

**Why it happens:** The LLM finds `FeatureManagement` class in Apex reference docs and assumes it is a general-purpose feature flag API. It is actually limited to ISV 2GP package feature parameters.

**Correct pattern:**
```apex
// FeatureManagement is ONLY for 2GP managed packages to set feature parameters
// For general feature flags, use Custom Metadata Types:
Feature_Flag__mdt flag = Feature_Flag__mdt.getInstance('MyFeature');
Boolean isEnabled = (flag != null) ? flag.IsEnabled__c : false;
```

**Detection hint:** `FeatureManagement.setPackage` or `FeatureManagement.checkPermission` used outside ISV/2GP context — regex: `FeatureManagement\.(setPackage|checkPackage)`

---

## Anti-Pattern 3: Not handling null CMDT getInstance() return

**What the LLM generates:** Direct field access without null check:
```apex
Boolean enabled = Feature_Flag__mdt.getInstance('My_Feature').IsEnabled__c;
```

**Why it happens:** LLMs generate the happy path. When the CMDT record does not exist (typo in name, record not deployed to target org), this throws a NullPointerException.

**Correct pattern:**
```apex
Feature_Flag__mdt flag = Feature_Flag__mdt.getInstance('My_Feature');
Boolean enabled = (flag != null) ? flag.IsEnabled__c : false;
```
Always default to a safe value (typically `false` — feature off) when the CMDT record is missing. This is especially important for kill switches where the default must be "feature enabled" (i.e., kill switch off).

**Detection hint:** `__mdt.getInstance(` followed immediately by `.` field access on the same line — regex: `__mdt\.getInstance\([^)]+\)\.\w+__c`

---

## Anti-Pattern 4: Using Custom Permissions without checking assignment

**What the LLM generates:** Checking Custom Permissions with `FeatureManagement.checkPermission()` but not verifying the permission is assigned to anyone:
```apex
if (FeatureManagement.checkPermission('Beta_Feature')) {
    // beta logic
}
```
Without creating the Permission Set or assigning it to users.

**Why it happens:** LLMs generate the code check but omit the declarative setup. Custom Permissions must be (1) defined as metadata, (2) included in a Permission Set, and (3) assigned to the user before the check returns true.

**Correct pattern:**
```apex
// 1. Create Custom Permission: Beta_Feature (via metadata or Setup)
// 2. Create Permission Set containing Beta_Feature
// 3. Assign Permission Set to target users
// 4. Then the code check works:
if (FeatureManagement.checkPermission('Beta_Feature')) {
    // only runs for assigned users
}
```

**Detection hint:** `checkPermission(` in Apex without corresponding `.permissionSet-meta.xml` defining the Custom Permission — look for orphaned code-side checks.

---

## Anti-Pattern 5: Querying CMDT with SOQL instead of using getInstance()

**What the LLM generates:** SOQL queries against Custom Metadata Types:
```apex
List<Feature_Flag__mdt> flags = [SELECT IsEnabled__c FROM Feature_Flag__mdt WHERE DeveloperName = 'My_Feature'];
```

**Why it happens:** LLMs default to SOQL as the data access pattern for all sObjects. While CMDT SOQL works, it counts against SOQL query limits.

**Correct pattern:**
```apex
Feature_Flag__mdt flag = Feature_Flag__mdt.getInstance('My_Feature');
// Or for all records:
Map<String, Feature_Flag__mdt> allFlags = Feature_Flag__mdt.getAll();
```
`getInstance()` and `getAll()` do not count against SOQL governor limits. Use them instead of SOQL queries for CMDT access.

**Detection hint:** SOQL `SELECT` from `__mdt` objects — regex: `\[SELECT.*FROM\s+\w+__mdt`

---

## Anti-Pattern 6: Missing test coverage for kill switch off-state

**What the LLM generates:** Tests that only verify the feature-enabled path:
```apex
@isTest
static void testFeatureEnabled() {
    // only tests with flag ON
}
```

**Why it happens:** LLMs generate tests for the default/happy path. Kill switches specifically need testing of the disabled state because that is the emergency scenario.

**Correct pattern:**
```apex
@isTest
static void testFeatureEnabled() {
    // Test with flag ON (normal operation)
}

@isTest
static void testKillSwitchActivated() {
    // Use Test.loadData() or DML to set CMDT IsEnabled__c = false
    // Verify the feature is properly disabled
    // Verify fallback behavior works correctly
}
```

**Detection hint:** Test classes referencing feature flags that only have one test method — look for `Feature_Flag__mdt` in test classes with fewer test methods than flag states.
