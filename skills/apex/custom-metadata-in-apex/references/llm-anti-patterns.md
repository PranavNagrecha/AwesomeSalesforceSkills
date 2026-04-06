# LLM Anti-Patterns — Custom Metadata in Apex

Common mistakes AI coding assistants make when generating or advising on Custom Metadata Types in Apex.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Querying Custom Metadata with SOQL instead of using getInstance methods

**What the LLM generates:**

```apex
List<MyConfig__mdt> configs = [SELECT Id, Value__c FROM MyConfig__mdt WHERE DeveloperName = 'Default'];
MyConfig__mdt config = configs[0]; // Wastes a SOQL query
```

**Why it happens:** LLMs treat Custom Metadata like regular SObjects and query them with SOQL. While SOQL works for `__mdt`, it is unnecessary — Custom Metadata reads via `getInstance()` or `getAll()` do not count against the SOQL governor limit.

**Correct pattern:**

```apex
// Zero SOQL cost — does not count against governor limits
MyConfig__mdt config = MyConfig__mdt.getInstance('Default');
if (config != null) {
    String value = config.Value__c;
}

// Or get all records:
Map<String, MyConfig__mdt> allConfigs = MyConfig__mdt.getAll();
```

**Detection hint:** `\[SELECT.*FROM.*__mdt` — SOQL queries against Custom Metadata Types that could use `getInstance` or `getAll`.

---

## Anti-Pattern 2: Assuming Custom Metadata records are editable via standard DML

**What the LLM generates:**

```apex
MyConfig__mdt config = MyConfig__mdt.getInstance('Default');
config.Value__c = 'Updated';
update config; // TypeException: DML not allowed on Custom Metadata
```

**Why it happens:** LLMs treat `__mdt` records like Custom Settings and attempt standard DML. Custom Metadata records are metadata, not data — they cannot be inserted, updated, or deleted via standard DML. You must use the Metadata API (deploy) or `Metadata.Operations.enqueueDeployment()`.

**Correct pattern:**

```apex
// Use the Apex Metadata API for programmatic updates
Metadata.CustomMetadata customMetadata = new Metadata.CustomMetadata();
customMetadata.fullName = 'MyConfig__mdt.Default';
customMetadata.label = 'Default';

Metadata.CustomMetadataValue field = new Metadata.CustomMetadataValue();
field.field = 'Value__c';
field.value = 'Updated';
customMetadata.values.add(field);

Metadata.DeployContainer container = new Metadata.DeployContainer();
container.addMetadata(customMetadata);
Metadata.Operations.enqueueDeployment(container, new MyDeployCallback());
```

**Detection hint:** `update ` or `insert ` or `delete ` DML operations on variables of type `__mdt`.

---

## Anti-Pattern 3: Expecting test classes to see Custom Metadata records created with DML

**What the LLM generates:**

```apex
@IsTest
static void testConfig() {
    MyConfig__mdt testConfig = new MyConfig__mdt(
        DeveloperName = 'TestConfig',
        Value__c = 'TestValue'
    );
    insert testConfig; // Fails — cannot insert __mdt in tests
}
```

**Why it happens:** LLMs generate test data factories that create `__mdt` records via DML. This does not work. Custom Metadata records deployed to the org ARE visible in tests by default (unlike Custom Settings which need `@TestVisible` or SeeAllData). You do not need to create them in tests.

**Correct pattern:**

```apex
@IsTest
static void testConfig() {
    // Custom Metadata records from the org are automatically visible in tests
    // No need to create them — just ensure the org has the expected records deployed
    MyConfig__mdt config = MyConfig__mdt.getInstance('Default');
    System.assertNotEquals(null, config, 'Expected Default config record to exist');

    // If you need to test with different values, use dependency injection:
    // Pass config values as parameters to the method under test
    String result = MyService.process(config.Value__c);
}
```

**Detection hint:** `insert.*__mdt` or `new.*__mdt(` in `@IsTest` classes — Custom Metadata cannot be DML-created in tests.

---

## Anti-Pattern 4: Confusing Custom Metadata Types with Custom Settings for hierarchy access

**What the LLM generates:**

```apex
// Trying to use Custom Metadata like Hierarchy Custom Settings
MyConfig__mdt config = MyConfig__mdt.getInstance(UserInfo.getProfileId());
// Or:
MyConfig__mdt config = MyConfig__mdt.getInstance(UserInfo.getUserId());
```

**Why it happens:** LLMs conflate Custom Metadata with Hierarchy Custom Settings. Hierarchy Custom Settings support `getInstance()` with a User, Profile, or Org ID that traverses the hierarchy. Custom Metadata `getInstance()` takes the `DeveloperName` string — not a User or Profile ID.

**Correct pattern:**

```apex
// Custom Metadata: pass the DeveloperName
MyConfig__mdt config = MyConfig__mdt.getInstance('Default');

// If you need per-profile config, design the CMT with a Profile__c field
// and query/filter by profile name
Map<String, MyConfig__mdt> allConfigs = MyConfig__mdt.getAll();
for (MyConfig__mdt c : allConfigs.values()) {
    if (c.Profile__c == UserInfo.getProfileId()) {
        // use this config
    }
}
```

**Detection hint:** `__mdt\.getInstance\(UserInfo` — passing User/Profile IDs to Custom Metadata getInstance.

---

## Anti-Pattern 5: Not null-checking getInstance results

**What the LLM generates:**

```apex
MyConfig__mdt config = MyConfig__mdt.getInstance('FeatureFlag');
Boolean enabled = config.Enabled__c; // NullPointerException if record does not exist
```

**Why it happens:** LLMs assume the Custom Metadata record always exists. If the DeveloperName is misspelled, the record was not deployed, or it was deleted, `getInstance()` returns null.

**Correct pattern:**

```apex
MyConfig__mdt config = MyConfig__mdt.getInstance('FeatureFlag');
if (config == null) {
    // Fail safe or use a default
    System.debug(LoggingLevel.WARN, 'Missing Custom Metadata: FeatureFlag');
    return false;
}
Boolean enabled = config.Enabled__c;
```

**Detection hint:** `__mdt\.getInstance\(` immediately followed by field access on the next line without a null check.

---

## Anti-Pattern 6: Using Custom Metadata for high-volume transactional data

**What the LLM generates:**

```apex
// Storing API response mappings as Custom Metadata — one record per API field
// With 500+ field mappings, deployment time becomes unmanageable
Metadata.DeployContainer container = new Metadata.DeployContainer();
for (FieldMapping fm : mappings) {
    Metadata.CustomMetadata cmd = new Metadata.CustomMetadata();
    cmd.fullName = 'FieldMap__mdt.' + fm.apiName;
    // ...
    container.addMetadata(cmd);
}
Metadata.Operations.enqueueDeployment(container, callback);
```

**Why it happens:** LLMs see "configurable without deployment" and suggest Custom Metadata for everything. But Custom Metadata deployments are asynchronous, have a 10 MB container limit, and changes require a metadata deploy — not a simple record save. For high-volume or frequently changing configuration, Custom Settings (List type) or a custom object are more appropriate.

**Correct pattern:**

```apex
// For high-volume config that changes frequently, use a Custom Object or List Custom Setting
// Custom Metadata is ideal for: deployment-time config, package defaults, lookup tables under 1000 rows
// that change rarely and should promote through environments as metadata
```

**Detection hint:** `Metadata.Operations.enqueueDeployment` in code that runs frequently (triggers, scheduled jobs) or with large `DeployContainer` populations.
