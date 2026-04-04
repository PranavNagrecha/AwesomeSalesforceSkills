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

**Why it happens:** LLMs confuse `getValues()` (List Custom Setting method by name) with `getInstance()` (Hierarchical Custom Setting method). Both methods exist on Custom Settings, but they have different semantics. `getValues('name')` is for List Custom Settings and retrieves a specific named record. `getInstance()` is for Hierarchical Custom Settings and resolves the User > Profile > Org Default hierarchy automatically.

**Correct pattern:**

```apex
// Hierarchical Custom Setting — resolves User > Profile > Org Default
My_Setting__c settings = My_Setting__c.getInstance();

// Or for a specific user (in batch/trigger contexts)
My_Setting__c settings = My_Setting__c.getInstance(userId);

// getValues() with no-arg or org-id is for getting org default only
// getValues(name) is for List Custom Settings — avoid for new code
```

**Detection hint:** Any code calling `getValues('SomeStringName')` on a Hierarchical Custom Setting is using the wrong method and will return null if no record with that Name exists.

---

## Anti-Pattern 3: Claiming CMT SOQL Consumes Governor Limits

**What the LLM generates:** "Be careful querying Custom Metadata Types in a loop — each SELECT statement counts against your 100 SOQL limit."

**Why it happens:** LLMs apply the general rule "SOQL costs governor limits" without the CMT exception. This causes unnecessary code complexity (caching CMT results in static variables, wrapping queries in conditional blocks) that is not needed.

**Correct pattern:**

```
Custom Metadata Type SOQL queries do NOT consume the Salesforce SOQL governor limit.
The platform serves CMT queries from a metadata cache. You can query CMT in loops,
triggers, batch contexts, and helper methods without SOQL budget concerns.

Custom Settings DO consume SOQL governor limits on the first call per transaction
(subsequent calls within the same transaction are cached). This is the key difference.
```

**Detection hint:** If generated code adds a `private static Map<String, MyType__mdt> cmtCache` pattern purely to avoid governor limits, the LLM has applied the wrong concern. CMT caching is still a valid pattern for application performance, but it is not necessary for governor compliance.

---

## Anti-Pattern 4: Suggesting New List Custom Settings

**What the LLM generates:** "Create a List Custom Setting called `Integration_Config__c` with a Name key for each integration endpoint. Use `getValues('PaymentGateway')` to retrieve it."

**Why it happens:** List Custom Settings appear in older Salesforce training material and documentation. LLMs trained on historical Salesforce content surface this pattern without knowing it is deprecated in Lightning Experience.

**Correct pattern:**

```
Do NOT create new List Custom Settings. They are deprecated in Lightning Experience.
For flat, non-hierarchical configuration use Custom Metadata Types instead:

CREATE: Integration_Config__mdt with DeveloperName (standard) and Endpoint_URL__c
ACCESS: SELECT Endpoint_URL__c FROM Integration_Config__mdt WHERE DeveloperName = 'PaymentGateway' LIMIT 1

Benefits: deployable, zero SOQL cost, packageable, supported in Lightning.
```

**Detection hint:** Any recommendation to create a new Custom Setting of type "List" or any code using `CustomSettingName__c.getValues('StringKey')` for a new implementation is applying a deprecated pattern.

---

## Anti-Pattern 5: Not Handling Null Returns From Custom Settings

**What the LLM generates:**

```apex
Integer limit = (Integer) My_Setting__c.getInstance().Record_Limit__c;
```

**Why it happens:** LLMs generate "happy path" code. They assume the Custom Setting record exists because it exists in the example org where the pattern was trained. In reality, Custom Setting records do not deploy and may be absent in any org that has not had the post-deploy setup script run.

**Correct pattern:**

```apex
My_Setting__c settings = My_Setting__c.getInstance();
Integer limit = 100; // safe default
if (settings != null && settings.Record_Limit__c != null) {
    limit = (Integer) settings.Record_Limit__c;
}
```

Or, for CMT, handle the case where the record does not exist:

```apex
List<Feature_Flag__mdt> flags = [
    SELECT Is_Enabled__c FROM Feature_Flag__mdt
    WHERE DeveloperName = 'My_Flag' LIMIT 1
];
Boolean isEnabled = !flags.isEmpty() && flags[0].Is_Enabled__c;
```

**Detection hint:** Any code that chains directly from `getInstance()` or a CMT query to a field access without a null check is a fragile pattern. Look for `getInstance().Field__c` or `[SELECT ...][0].Field__c` without null/empty-list guards.

---

## Anti-Pattern 6: Treating CMT As A Replacement For All Custom Settings

**What the LLM generates:** "You should always use Custom Metadata Types instead of Custom Settings. Custom Settings are deprecated."

**Why it happens:** LLMs overgeneralize from the List Custom Settings deprecation to claim that all Custom Settings are deprecated. Hierarchical Custom Settings are not deprecated and remain the correct tool for per-user and per-profile override patterns.

**Correct pattern:**

```
Only List Custom Settings are deprecated. Hierarchical Custom Settings are fully
supported and are the correct choice when behavior must vary by User or Profile.

CMT has no built-in hierarchy resolution. If you replace a Hierarchical Custom Setting
with CMT and need per-user overrides, you must build custom resolution logic —
which recreates work the platform already does.

Use CMT for deployable org-level config.
Use Hierarchical Custom Settings for per-user and per-profile overrides.
```

**Detection hint:** If a recommendation to use CMT involves creating records named after users, profiles, or including user/profile IDs in `DeveloperName`, the LLM has likely recommended CMT where Hierarchical Custom Settings belong.
