# LLM Anti-Patterns — Platform Cache

Common mistakes AI coding assistants make when generating or advising on Salesforce Platform Cache usage in Apex.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Not handling cache misses (null returns)

**What the LLM generates:**

```apex
String value = (String) Cache.Org.get('local.MyPartition.configKey');
// Immediately use value without null check — NPE if cache is empty or evicted
processConfig(value.toUpperCase());
```

**Why it happens:** LLMs treat the cache as a reliable data store. Platform Cache is ephemeral — data can be evicted at any time due to capacity pressure, partition rebalancing, or org restart. `get()` returns null when the key does not exist or was evicted.

**Correct pattern:**

```apex
String value = (String) Cache.Org.get('local.MyPartition.configKey');
if (value == null) {
    // Cache miss — fetch from source of truth and repopulate
    value = [SELECT Value__c FROM AppConfig__mdt WHERE DeveloperName = 'configKey'].Value__c;
    Cache.Org.put('local.MyPartition.configKey', value, 3600); // TTL: 1 hour
}
processConfig(value.toUpperCase());
```

**Detection hint:** `Cache\.(Org|Session)\.get\(` without a subsequent null check before using the returned value.

---

## Anti-Pattern 2: Caching user-specific data in Org cache

**What the LLM generates:**

```apex
// Store user preferences in Org cache
Cache.Org.put('local.MyPartition.prefs_' + UserInfo.getUserId(), userPrefs);
```

**Why it happens:** LLMs use Org cache as a general-purpose store. Org cache is shared across all users and transactions in the org. Storing per-user data in Org cache creates thousands of keys that waste cache capacity and create key collision risks. User-specific data belongs in Session cache.

**Correct pattern:**

```apex
// User-specific data goes in Session cache
Cache.Session.put('local.MyPartition.prefs', userPrefs, 1800);

// Org cache is for shared reference data
Cache.Org.put('local.MyPartition.picklistValues', picklistValues, 3600);
```

**Detection hint:** `Cache\.Org\.put\(.*UserInfo\.getUserId\(\)` — user-specific keys in Org cache.

---

## Anti-Pattern 3: Caching non-serializable objects

**What the LLM generates:**

```apex
HttpResponse response = new Http().send(req);
Cache.Org.put('local.MyPartition.lastResponse', response); // Not serializable
```

**Why it happens:** LLMs cache the result of an operation without considering serializability. `HttpResponse`, `Database.QueryLocator`, `Savepoint`, and other platform types are not serializable and throw a `Cache.CacheException` when you try to store them.

**Correct pattern:**

```apex
HttpResponse response = new Http().send(req);
// Cache the serializable data, not the transport object
Cache.Org.put('local.MyPartition.lastResponseBody', response.getBody(), 300);
Cache.Org.put('local.MyPartition.lastResponseStatus', response.getStatusCode(), 300);
```

**Detection hint:** `Cache\.(Org|Session)\.put\(` with values of type `HttpResponse`, `HttpRequest`, `Savepoint`, or `Database.QueryLocator`.

---

## Anti-Pattern 4: Using hardcoded partition names without the namespace prefix

**What the LLM generates:**

```apex
Cache.Org.put('MyPartition.configKey', value); // Missing 'local.' prefix
```

**Why it happens:** LLMs omit the namespace qualifier. For unpackaged code, the prefix must be `local.`. For managed package code, it must be the namespace. Without it, the cache operation throws `Cache.Org.OrgCacheException: Invalid key`.

**Correct pattern:**

```apex
// For unpackaged code
Cache.Org.put('local.MyPartition.configKey', value, 3600);

// For managed package code
Cache.Org.put('myns.MyPartition.configKey', value, 3600);
```

**Detection hint:** `Cache\.(Org|Session)\.(put|get)\('(?!local\.)(?!\w+\.)` — cache keys without a namespace prefix.

---

## Anti-Pattern 5: Caching sensitive data without considering cache visibility

**What the LLM generates:**

```apex
// Cache an API token for reuse
Cache.Org.put('local.MyPartition.apiToken', bearerToken, 3600);
// Any Apex code in the org can read this
String token = (String) Cache.Org.get('local.MyPartition.apiToken');
```

**Why it happens:** LLMs cache tokens and credentials for performance without considering that Org cache is readable by any Apex code in the org (including managed packages in the same namespace). Sensitive tokens should not be stored in Platform Cache — use Named Credentials for authentication.

**Correct pattern:**

```apex
// Do NOT cache API tokens — use Named Credentials instead
// Named Credentials handle token storage, refresh, and per-callout injection
HttpRequest req = new HttpRequest();
req.setEndpoint('callout:MyNamedCredential/api/data');
// Authentication is handled automatically by the Named Credential

// Cache ONLY non-sensitive reference data
Cache.Org.put('local.MyPartition.picklistValues', picklistValues, 3600);
```

**Detection hint:** `Cache\.(Org|Session)\.put\(.*[Tt]oken|[Kk]ey|[Ss]ecret|[Pp]assword` — sensitive data in cache keys.

---

## Anti-Pattern 6: Not specifying TTL and relying on default cache duration

**What the LLM generates:**

```apex
Cache.Org.put('local.MyPartition.rates', exchangeRates);
// No TTL — uses partition default, which may be too long for volatile data
```

**Why it happens:** LLMs omit the TTL parameter, relying on the partition's default TTL. For volatile data like exchange rates, stock prices, or feature flags, the default TTL may cause stale data to be served for hours.

**Correct pattern:**

```apex
// Explicit TTL in seconds based on data freshness requirements
Cache.Org.put('local.MyPartition.rates', exchangeRates, 300);    // 5 min for volatile data
Cache.Org.put('local.MyPartition.config', appConfig, 3600);       // 1 hour for stable config
Cache.Org.put('local.MyPartition.schema', fieldMap, 86400);       // 24 hours for metadata
```

**Detection hint:** `Cache\.(Org|Session)\.put\(` with only 2 arguments (no TTL parameter).
