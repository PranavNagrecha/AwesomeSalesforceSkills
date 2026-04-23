# LLM Anti-Patterns — Apex Custom Settings Hierarchy

## Anti-Pattern 1: Null-Checking The Record From `getInstance()`

**What the LLM generates:**

```apex
MySetting__c s = MySetting__c.getInstance();
if (s == null) return defaultVal;
Integer v = s.MaxRetries__c.intValue();
```

**Why it happens:** LLMs treat all SOQL-like APIs as returning nullable. `getInstance()` for Hierarchy Custom Settings never returns `null` — it always returns a merged record.

**Correct pattern:**

```apex
MySetting__c s = MySetting__c.getInstance();
Integer v = (s.MaxRetries__c != null) ? s.MaxRetries__c.intValue() : defaultVal;
```

**Detection hint:** `getInstance()` result compared to `null` in the next line.

---

## Anti-Pattern 2: Using `getOrgDefaults()` When `getInstance()` Was Intended

**What the LLM generates:**

```apex
Boolean flag = MySetting__c.getOrgDefaults().Enabled__c;
```

**Why it happens:** `getOrgDefaults` sounds like "the right default" to an LLM. But it skips user/profile overrides that admins actually rely on.

**Correct pattern:** `MySetting__c.getInstance().Enabled__c` for the running user.

**Detection hint:** `getOrgDefaults()` with no justifying comment about bypassing hierarchy.

---

## Anti-Pattern 3: Inserting Custom Settings In A Loop

**What the LLM generates:**

```apex
for (Id userId : userIds) {
    insert new PerUserFlag__c(SetupOwnerId = userId, Enabled__c = true);
}
```

**Why it happens:** LLMs emit one-record DML when iterating; governor-awareness isn't automatic.

**Correct pattern:** Accumulate and `upsert` with a single DML. `upsert rows SetupOwnerId` handles both new and existing tiers.

**Detection hint:** `insert` or `upsert` on a Custom Setting inside a `for` loop.

---

## Anti-Pattern 4: Storing Deployable Config In Custom Settings

**What the LLM generates:**

```apex
IntegrationConfig__c cfg = IntegrationConfig__c.getOrgDefaults();
HttpRequest req = new HttpRequest();
req.setEndpoint(cfg.EndpointUrl__c);
```

**Why it happens:** LLMs reach for the familiar Hierarchy Setting pattern for any config, but integration endpoints are deploy-time and packageable — CMDT fits better.

**Correct pattern:** `[SELECT EndpointUrl__c FROM Integration_Config__mdt WHERE DeveloperName = 'Default']` or the Apex SOQL-free `IntegrationConfig__mdt.getInstance('Default')`.

**Detection hint:** Custom Setting storing a URL, retry count, or any value that is stable across runtime but changes per environment.

---

## Anti-Pattern 5: Setting `SetupOwnerId` To A Random Id

**What the LLM generates:**

```apex
PerUserFlag__c s = new PerUserFlag__c();
s.SetupOwnerId = someAccountId; // wrong — not a User or Profile
```

**Why it happens:** LLMs treat `SetupOwnerId` as "any record owner" and don't know it's restricted to User/Profile/Organization.

**Correct pattern:** Validate the Id is a User (`005` prefix), Profile (`00e` prefix), or Organization Id before insert.

**Detection hint:** `SetupOwnerId` assigned from a variable whose SObject type is not obviously User or Profile.

---

## Anti-Pattern 6: Assuming Test Context Reads Production Values

**What the LLM generates:**

```apex
@IsTest
static void testFeature() {
    System.assertEquals(true, FeatureFlag.isEnabled());
}
```

**Why it happens:** LLMs write terse tests that assume data exists. Apex test context isolates data from the org.

**Correct pattern:** Always seed the setting in the test setup.

```apex
@IsTest
static void testFeature() {
    insert new FeatureFlags__c(SetupOwnerId = UserInfo.getOrganizationId(), Enabled__c = true);
    System.assertEquals(true, FeatureFlag.isEnabled());
}
```

**Detection hint:** A test method reads a feature flag without any `insert` / `Test.setMock` setup for it.

---

## Anti-Pattern 7: Querying Custom Setting Via SOQL When An Accessor Exists

**What the LLM generates:**

```apex
MySetting__c s = [SELECT Enabled__c FROM MySetting__c
                  WHERE SetupOwnerId = :UserInfo.getUserId() LIMIT 1];
```

**Why it happens:** LLMs default to SOQL for any object read. For Custom Settings, the platform-provided `getInstance()` is free (cached, no SOQL consumed).

**Correct pattern:** `MySetting__c.getInstance()` — consumes no SOQL, reads the transaction cache.

**Detection hint:** SOQL against a Custom Setting (object annotated `CustomSetting` in the XML) instead of using the generated accessor.
