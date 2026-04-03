# Examples — Platform Cache

## Example 1: Org Cache Wrapper For Reference Data

**Context:** A service repeatedly loads a country-code mapping used across many transactions.

**Problem:** The same query or metadata load happens over and over.

**Solution:**

```apex
public inherited sharing class CountryCodeCache {
    private static final String PARTITION = 'local.Default';
    private static final String KEY = 'country-code-map:v1';

    public static Map<String, String> getCountryCodeMap() {
        Cache.OrgPartition partition = Cache.Org.getPartition(PARTITION);
        Map<String, String> cachedValue = (Map<String, String>) partition.get(KEY);
        if (cachedValue != null) {
            return cachedValue;
        }

        Map<String, String> freshValue = CountryCodeLoader.loadMappings();
        partition.put(KEY, freshValue, 3600);
        return freshValue;
    }
}
```

**Why it works:** The code uses a cache-aside wrapper with a single namespaced key and a clear miss path.

---

## Example 2: Versioned Invalidation Pattern

**Context:** A configuration-driven rules engine needs cache invalidation when admins deploy new mappings.

**Problem:** A long-lived fixed key serves stale values after a config update.

**Solution:**

```apex
public class PricingRuleCache {
    public static String currentVersionKey() {
        return 'pricing-rules:' + PricingConfig__mdt.getInstance('Default').Cache_Version__c;
    }
}
```

**Why it works:** Versioned keys let new deployments invalidate stale cached values without requiring destructive cache coordination.

---

## Anti-Pattern: Org Cache For Sensitive User-Specific Data

**What practitioners do:** They store user-specific tokens or personally sensitive fields in org cache for convenience.

**What goes wrong:** Org cache is shared too broadly for that use case and the cache is not a durable security boundary.

**Correct approach:** Keep sensitive identity state out of shared org cache and avoid treating Platform Cache as secure storage.
