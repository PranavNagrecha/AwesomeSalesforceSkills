# LLM Anti-Patterns — Custom Metadata in Apex

Common mistakes AI coding assistants make when generating or advising on Custom Metadata Types in Apex.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Replacing SOQL with `getInstance` "to save a query"

**What the LLM generates:**

```apex
List<MyConfig__mdt> configs = [SELECT Id, Value__c FROM MyConfig__mdt WHERE DeveloperName = 'Default'];
MyConfig__mdt config = configs[0]; // "Wastes a SOQL query"
```

...and then rewrites it as `getInstance('Default')` with the justification that the SOQL cost a governor limit.

**Why it happens:** LLMs carry the custom-settings rule over to custom metadata. The rewrite is often right, but the *reason* is wrong twice over, and the wrong reason produces wrong code elsewhere:

- SOQL against `__mdt` costs nothing either. "This limit doesn't apply to custom metadata types. In a single Apex transaction, custom metadata records can have unlimited SOQL queries." (Apex Developer Guide L19616–19619.)
- `getAll()` and `getInstance()` are the ones with a hidden cost: "Only the first 255 characters are returned for any field in a custom metadata type record, so longer text fields get truncated. If you want all the field data from a custom metadata type record, use a SOQL query." (Apex Reference Guide L204569–204572.)

**Correct pattern:**

```apex
// Short scalars, whole small table, keyed by DeveloperName -> cache accessor.
Map<String, MyConfig__mdt> allConfigs = MyConfig__mdt.getAll();
MyConfig__mdt config = MyConfig__mdt.getInstance('Default');

// Filtering, ordering, or a field that could exceed 255 characters -> SOQL.
// This costs nothing against the 100-query limit.
List<MyConfig__mdt> active = [
    SELECT DeveloperName, Long_Template__c
    FROM MyConfig__mdt
    WHERE Is_Active__c = true
    ORDER BY Priority__c
];
```

**Detection hint:** `\[SELECT.*FROM.*__mdt` alone is **not** a finding. The finding is a `__mdt` SOQL statement *inside a loop* where `getAll()` outside the loop would do, and a `getAll()`/`getInstance()` read of a field that can exceed 255 characters.

---

## Anti-Pattern 2: Assuming Custom Metadata records are editable via standard DML

**What the LLM generates:**

```apex
MyConfig__mdt config = MyConfig__mdt.getInstance('Default');
config.Value__c = 'Updated';
update config; // rejected — DML is not the write path for custom metadata
```

**Why it happens:** LLMs treat `__mdt` records like Custom Settings and attempt standard DML. "Apex code can create, read, and update (but not delete) custom metadata records… You can edit records in memory but not upsert or delete them. Apex code can deploy custom metadata records, but not via a DML operation. Moreover, DML operations aren't allowed on custom metadata in the Partner or Enterprise APIs." (Metadata API Developer Guide L41317–41322.) The Object Reference lists the supported calls as `describeSObjects(), describeLayout(), query(), retrieve()` and nothing else (Object Reference L5671–5672). **UNVERIFIED (2026-09-05):** the exact exception type raised at runtime for `update` on a `__mdt` sObject is not named in the Apex Developer Guide, the Apex Reference Guide, the Metadata API Developer Guide, or the Object Reference — do not assert `TypeException` or any other specific type.

**Correct pattern:**

```apex
// Use the Apex Metadata API for programmatic updates
Metadata.CustomMetadata customMetadata = new Metadata.CustomMetadata();
customMetadata.fullName = 'MyConfig.Default'; // type name without __mdt, then the record
customMetadata.label = 'Default';

Metadata.CustomMetadataValue field = new Metadata.CustomMetadataValue();
field.field = 'Value__c';
field.value = 'Updated';
customMetadata.values.add(field);

Metadata.DeployContainer container = new Metadata.DeployContainer();
container.addMetadata(customMetadata);
Metadata.Operations.enqueueDeployment(container, new MyDeployCallback());
```

Note `fullName`: the `__mdt` suffix is dropped, and in a namespace both halves are qualified — `myPackage__MDType1__mdt.myPackage__Component1` is the *component* full name form the Apex Developer Guide gives (L28199–28203), while `Metadata.CustomMetadata.fullName` takes `'MetadataTypeName.MetadataRecordName'` (Apex Reference Guide L170844–170845, L170852–170855). A worked end-to-end version is in `references/code-examples.md` § 6.

**Detection hint:** `insert`/`update`/`upsert`/`delete` applied to a variable or list whose declared type ends in `__mdt`.

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
    insert testConfig; // Fails — no DML path exists for __mdt
}
```

**Why it happens:** LLMs generate test data factories that create `__mdt` records via DML. Two separate facts get conflated. First, custom metadata deployed to the org **is** visible in tests without `SeeAllData=true`: test isolation covers "standard objects, custom objects, and custom settings data", but "objects that are used to manage your organization or metadata objects can still be accessed in your tests" (Apex Developer Guide L40707–40709, L40727–40729) — unlike custom settings, where "Apex tests must use `SeeAllData=true` to see existing custom settings data in the organization" (L13515–13516). Second, records still cannot be *created* by DML, only edited in memory (Metadata API Developer Guide L41318–41319).

**Correct pattern:** build the row in memory and inject it through a `@TestVisible` seam, so the test states its own configuration rather than depending on whatever the org happens to hold.

```apex
// Production class exposes exactly one seam:
//   @TestVisible private static Map<String, MyConfig__mdt> cache;

@IsTest
static void usesTheInjectedConfiguration() {
    MyConfigSelector.cache = new Map<String, MyConfig__mdt>{
        'Default' => new MyConfig__mdt(Value__c = 'TestValue')   // no DML, no DeveloperName
    };

    Assert.areEqual('TestValue', MyConfigSelector.valueFor('Default'));
}
```

`DeveloperName` is deliberately not assigned — it is documented with the properties *Defaulted on create, Filter, Group, Sort* (Object Reference L5681–5683), so the map key carries the name instead. `@TestVisible` "allows test methods to access private or protected members of another class outside the test class… This annotation doesn't change the visibility of members if accessed by non-test classes." (Apex Developer Guide L6290–6296.)

**Detection hint:** `insert`/`update` on a `__mdt` variable inside a class annotated `@IsTest`, and `new .*__mdt\(` with a `DeveloperName =` assignment.

---

## Anti-Pattern 4: Confusing Custom Metadata Types with Custom Settings for hierarchy access

**What the LLM generates:**

```apex
// Trying to use Custom Metadata like Hierarchy Custom Settings
MyConfig__mdt config = MyConfig__mdt.getInstance(UserInfo.getProfileId());
MyConfig__mdt userConfig = MyConfig__mdt.getInstance(UserInfo.getUserId());
```

**Why it happens:** LLMs conflate Custom Metadata with Hierarchy Custom Settings, whose hierarchy "checks the organization, profile, and user settings for the current user and returns the most specific, or 'lowest,' value" (Apex Developer Guide L13523–13526). Custom metadata has no hierarchy at all. Its `getInstance` has three overloads and none of them resolves a User or Profile: `getInstance(recordId)` takes **the custom metadata record's own Id**, `getInstance(developerName)` takes the record's developer name, and `getInstance(qualifiedApiName)` takes `namespacePrefix__developerName` (Apex Reference Guide L204588–204612, L204618–204620, L204659–204681). Passing a User Id compiles — the parameter is a `String` — and returns `null`.

**Correct pattern:**

```apex
// Custom Metadata: pass the record's DeveloperName
MyConfig__mdt config = MyConfig__mdt.getInstance('Default');

// Per-profile behaviour is a modelled field plus explicit resolution, not a hierarchy.
// Build the index once; getAll() reads the application cache, not the database.
Map<Id, MyConfig__mdt> byProfile = new Map<Id, MyConfig__mdt>();
for (MyConfig__mdt row : MyConfig__mdt.getAll().values()) {
    if (row.Profile_Id__c != null) {
        byProfile.put((Id) row.Profile_Id__c, row);
    }
}
MyConfig__mdt forMe = byProfile.containsKey(UserInfo.getProfileId())
    ? byProfile.get(UserInfo.getProfileId())
    : MyConfig__mdt.getInstance('Default');
```

If a real user/profile/org hierarchy is what the requirement needs, that is `apex/apex-custom-settings-hierarchy`, not this skill.

**Detection hint:** `__mdt\.getInstance\(UserInfo` — passing User/Profile IDs to Custom Metadata `getInstance`. Also `__mdt.getInstance(` called inside a loop over users or profiles.

---

## Anti-Pattern 5: Not null-checking getInstance results

**What the LLM generates:**

```apex
MyConfig__mdt config = MyConfig__mdt.getInstance('FeatureFlag');
Boolean enabled = config.Enabled__c; // NullPointerException if record does not exist
```

**Why it happens:** LLMs assume the Custom Metadata record always exists. All three `getInstance` overloads are documented as returning "null if no record matches the parameter" (Apex Reference Guide L204588, L204618–204620, L204659), and `getAll()` "returns an empty map" when the type has no records (L204569). A misspelled developer name, a record that was never deployed to this org, or a `protected` record the calling namespace cannot read all produce the same silent null.

**Correct pattern:**

```apex
MyConfig__mdt config = MyConfig__mdt.getInstance('FeatureFlag');
if (config == null) {
    // Fail safe, and say which record is missing — this is a deployment defect.
    System.debug(LoggingLevel.WARN, 'Missing Custom Metadata record: MyConfig.FeatureFlag');
    return false;
}
Boolean enabled = config.Enabled__c;
```

The named-fallback version — resolve the business-unit record, fall through to a `Default` record, log when even that is missing — is in `references/code-examples.md` § 3.

**Detection hint:** `__mdt\.getInstance\(` immediately followed by field access on the next line without a null check.

---

## Anti-Pattern 6: Using Custom Metadata for high-volume or fast-changing data

**What the LLM generates:**

```apex
// One Metadata.CustomMetadata component per row, built in a loop
Metadata.DeployContainer container = new Metadata.DeployContainer();
for (FieldMapping fm : mappings) {
    Metadata.CustomMetadata cmd = new Metadata.CustomMetadata();
    cmd.fullName = 'FieldMap.' + fm.apiName;
    container.addMetadata(cmd);
}
Metadata.Operations.enqueueDeployment(container, callback);
```

**Why it happens:** LLMs see "configurable without a code deployment" and reach for custom metadata for everything, including data that changes daily. Four documented properties of the write path make that wrong:

- It is asynchronous. "Deployment is queued for asynchronous processing." (Apex Developer Guide L28194–28196.)
- The job and its callback "are counted as asynchronous jobs in the current org" and are subject to governor limits, and Salesforce limits "the number of Metadata API deployments originating from Apex that can be enqueued at a time" (L28226–28230).
- Deletion is not available at all: "you can create and update components but not delete them" (L28195–28197).
- A loop over a collection will happily add two components with the same `fullName`, which the platform warns against: "Avoid adding components to a Metadata.DeployContainer that have the same Metadata.Metadata.fullName because it causes deployment errors." (Apex Reference Guide L171293–171295.)

**UNVERIFIED (2026-09-05):** the frequently repeated "10 MB / 1,000-row custom metadata limit" is not in the Apex Developer Guide, the Apex Reference Guide, the Metadata API Developer Guide, the Object Reference, or the Salesforce App Limits cheat sheet. The only 10 MB figures in those sources are the Platform Cache allocation for Enterprise Edition (Apex Developer Guide L28467–28472) and the Metadata API zip file limit (App Limits cheat sheet L762) — neither is a `DeployContainer` cap. Do not quote a number here; argue from the asynchronous write path instead.

**Correct pattern:**

```apex
// Custom metadata is for values that change on a release cadence and must promote
// through environments as metadata: feature flags, thresholds, routing tables,
// per-business-unit policy. One deliberate change, one component, one deployment.
Metadata.CustomMetadata record = new Metadata.CustomMetadata();
record.fullName = 'Retry_Policy.EMEA_Standard';
Metadata.CustomMetadataValue attempts = new Metadata.CustomMetadataValue();
attempts.field = 'Max_Attempts__c';
attempts.value = 7;
record.values.add(attempts);

// Rows that users edit, that change hourly, or that are deleted as a matter of course
// belong in a custom object or a List Custom Setting instead. Deleting a custom
// metadata record is not something Apex can do at all.
```

**Detection hint:** `Metadata.Operations.enqueueDeployment` reachable from a trigger, a `@future`, or a loop body; `addMetadata` called inside a `for` loop with no de-duplication by `fullName`.
