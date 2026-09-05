# LLM Anti-Patterns — Custom Metadata Types And Settings

Common mistakes AI coding assistants make when generating or advising on Custom Metadata Types and Custom Settings. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending Custom Settings For Deployable Configuration

**What the LLM generates:** "Store your feature flag in a Custom Setting so admins can easily toggle it in each org without a deployment."

**Why it happens:** LLMs conflate "admin-editable" with "deployable." Custom Settings are admin-editable, but they are not deployable. The training data contains many examples of Custom Settings used for configuration because it was a common pattern before CMT existed.

**Correct pattern:**

```
Use Custom Metadata Types for feature flags and configuration that must be consistent
across orgs or travel with releases. CMT records are included in change sets, packages,
and SFDX source pushes. Custom Settings are org-specific data that do not deploy.
```

**Detection hint:** Look for phrases like "store in Custom Settings so it deploys" or "add to change set with Custom Settings." Custom Settings records cannot be included in a change set.

---

## Anti-Pattern 2: Using `getValues()` Instead of `getInstance()` For Hierarchy Resolution

**What the LLM generates:**

```apex
// LLM-generated code
String threshold = My_Setting__c.getValues('OrgDefault').Threshold__c;
```

**Why it happens:** LLMs confuse the two method families. `getValues(dataSetName)` belongs to **list** settings, where the Apex Reference Guide says it "returns the exact same object as `getInstance(dataSetName)`". `getValues(userId)` and `getValues(profileId)` belong to **hierarchy** settings and are not equivalent to `getInstance` at all: they return only the row defined at that exact level and null for every field set higher up, while `getInstance` merges the levels field by field.

**Correct pattern:**

```apex
// Hierarchy setting — merges User > Profile > Org Default, per field
My_Setting__c settings = My_Setting__c.getInstance();
My_Setting__c forUser  = My_Setting__c.getInstance(userId);
My_Setting__c orgOnly  = My_Setting__c.getOrgDefaults();

// getValues(id) on a hierarchy setting: THAT LEVEL ONLY, no merge.
// Correct in seeding/migration code that needs to know whether a row exists;
// wrong anywhere a resolved runtime value is expected.
My_Setting__c userRowOnly = My_Setting__c.getValues(userId);

// List setting — keyed by data set name; getInstance and getValues are identical
Foundation_Countries__c row = Foundation_Countries__c.getValues('United States');
Map<String, Foundation_Countries__c> all = Foundation_Countries__c.getAll();
```

**Detection hint:** `getValues('<string literal>')` against a setting declared `customSettingsType=Hierarchy`, or `getAll()` against one, is a type mismatch that compiles. `getValues(someId)` feeding a runtime decision is the subtler version: it works in the developer's org, where the value happens to be set at the user level, and returns null everywhere else.

---

## Anti-Pattern 3: Claiming CMT SOQL Consumes Governor Limits

**What the LLM generates:** "Be careful querying Custom Metadata Types in a loop — each SELECT statement counts against your 100 SOQL limit."

**Why it happens:** LLMs apply the general rule "SOQL costs governor limits" without the CMT exception. This causes unnecessary code complexity (caching CMT results in static variables, wrapping queries in conditional blocks) that is not needed.

**Correct pattern:**

```
Custom Metadata Type SOQL queries do NOT consume the SOQL governor limit: "In a
single Apex transaction, custom metadata records can have unlimited SOQL queries."

Custom Settings accessed through the Apex custom settings methods (getInstance,
getValues, getAll, getOrgDefaults) also cost nothing: the data is served from the
application cache, so "you don't have to use SOQL queries that count against your
governor limits."

The one access path that DOES cost a query is a SOQL statement against the custom
setting object itself: "querying custom settings data using SOQL doesn't use the
application cache and is similar to querying a custom object."
```

**Detection hint:** Two symptoms, opposite directions. If generated code adds a `private static Map<String, MyType__mdt> cmtCache` purely to avoid governor limits, the LLM invented a cost that does not exist. If it rewrites `My_Setting__c.getInstance()` into `[SELECT ... FROM My_Setting__c WHERE SetupOwnerId = :uid]` to "bulkify" a trigger, it has created the one real cost by hand.

---

## Anti-Pattern 4: Suggesting New List Custom Settings

**What the LLM generates:** "Create a List Custom Setting called `Integration_Config__c` with a Name key for each integration endpoint. Use `getValues('PaymentGateway')` to retrieve it."

**Why it happens:** List Custom Settings appear in older Salesforce training material and documentation, and LLMs reproduce the pattern by default. The counter-argument is deployability, not deprecation: UNVERIFIED (2026-09-05) — no extracted Salesforce guide states that List Custom Settings are deprecated, and `SchemaSettings.enableListCustomSettingCreation` defaulting to false means the real risk is that the org cannot create one at all.

**Correct pattern:**

```
Prefer a Custom Metadata Type over a new List Custom Setting. The reason is that
CMT records deploy and list setting rows do not, and that creating list settings
depends on SchemaSettings.enableListCustomSettingCreation, which defaults to false.
For flat, non-hierarchical configuration:

CREATE: Integration_Config__mdt with DeveloperName (standard) and Endpoint_URL__c
ACCESS: SELECT Endpoint_URL__c FROM Integration_Config__mdt WHERE DeveloperName = 'PaymentGateway' LIMIT 1

Benefits: the records deploy with the release, they are packageable, and no org
switch has to be enabled first. (Both storage types are cached; read cost is not
the differentiator.)
```

**Detection hint:** Any recommendation to create a new Custom Setting of type "List" or any code using `CustomSettingName__c.getValues('StringKey')` for a new implementation is applying a deprecated pattern.

---

## Anti-Pattern 5: Not Handling Null Returns From Custom Settings

**What the LLM generates:**

```apex
Integer limit = (Integer) My_Setting__c.getInstance().Record_Limit__c;
```

**Why it happens:** LLMs generate "happy path" code. They assume the Custom Setting record exists because it exists in the example org where the pattern was trained. In reality, Custom Setting records do not deploy and may be absent in any org that has not had the post-deploy setup script run.

The over-correction is just as common and equally wrong: an LLM told to "add a null check" wraps the record. `getInstance()` and `getOrgDefaults()` do not return null in any modern org — "If no custom setting data is defined for the user, this method returns a new custom setting object … contains an ID set to null and merged fields from higher in the hierarchy." Only Apex saved using API version 21.0 or earlier returned null. The null that actually reaches production is on the **field**.

**Correct pattern:**

```apex
My_Setting__c settings = My_Setting__c.getInstance(); // never null
Integer recordLimit = settings.Record_Limit__c == null
    ? 100                                   // safe default
    : (Integer) settings.Record_Limit__c;
```

Or, for CMT, handle the case where the record does not exist:

```apex
List<Feature_Flag__mdt> flags = [
    SELECT Is_Enabled__c FROM Feature_Flag__mdt
    WHERE DeveloperName = 'My_Flag' LIMIT 1
];
Boolean isEnabled = !flags.isEmpty() && flags[0].Is_Enabled__c;
```

**Detection hint:** Look for `getInstance().Field__c` or `[SELECT ...][0].Field__c` feeding a cast or a comparison with no default. Equally, treat `if (settings == null)` around a `getInstance()` result as dead code that is standing in for the field guard that is missing.

---

## Anti-Pattern 6: Treating CMT As A Replacement For All Custom Settings

**What the LLM generates:** "You should always use Custom Metadata Types instead of Custom Settings. Custom Settings are deprecated."

**Why it happens:** LLMs overgeneralize from community advice about list settings into a claim that all Custom Settings are deprecated. Hierarchical Custom Settings remain the platform's per-user and per-profile override mechanism, with merge semantics that CMT has no equivalent for.

**Correct pattern:**

```
Custom Settings are not deprecated. Hierarchical Custom Settings are the correct
choice whenever behavior must legitimately vary by User or Profile, and list
settings remain a documented feature (see Anti-Pattern 4 for what is actually true).

CMT has no built-in hierarchy resolution. If you replace a Hierarchical Custom Setting
with CMT and need per-user overrides, you must build custom resolution logic —
which recreates work the platform already does.

Use CMT for deployable org-level config.
Use Hierarchical Custom Settings for per-user and per-profile overrides.
```

**Detection hint:** If a recommendation to use CMT involves creating records named after users, profiles, or including user/profile IDs in `DeveloperName`, the LLM has likely recommended CMT where Hierarchical Custom Settings belong.
