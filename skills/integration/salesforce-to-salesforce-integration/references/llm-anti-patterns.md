# LLM Anti-Patterns — Salesforce-to-Salesforce Integration

Common mistakes AI coding assistants make when generating or advising on Salesforce-to-Salesforce integration. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending Native S2S as the Default Cross-Org Pattern

**What the LLM generates:** "Enable Salesforce to Salesforce in both orgs, then create a Connection and Connection Objects to share records bidirectionally."

**Why it happens:** "Salesforce-to-Salesforce" sounds like the canonical tool for cross-org integration. The native S2S feature is prominently documented and appears frequently in older Salesforce resources.

**Correct pattern:**
```
Native S2S is a legacy mechanism with severe constraints:
- CANNOT be disabled once enabled (permanent org change)
- Consumes SOAP API limits on BOTH orgs simultaneously
- Unsuitable for high-volume scenarios

Modern cross-org patterns:
1. REST API callouts with Named Credential + Connected App (bidirectional sync)
2. Platform Event bridge via Pub/Sub API (event-driven)
3. Salesforce Connect Cross-Org (read-only real-time access)
4. MuleSoft (enterprise-scale orchestration)
```

**Detection hint:** Recommendation includes "enable Salesforce to Salesforce in Setup" or references PartnerNetworkConnection setup.

---

## Anti-Pattern 2: Not Warning About S2S Irreversibility

**What the LLM generates:** Instructions for enabling native S2S without any warning about irreversibility.

**Why it happens:** LLMs don't consistently flag product-specific permanent actions. The S2S documentation on help.salesforce.com describes the feature without making the irreversibility immediately obvious.

**Correct pattern:**
```
BEFORE enabling native S2S:
⚠ WARNING: Salesforce-to-Salesforce CANNOT be disabled once enabled.
This is a permanent org configuration change.
Confirm business acceptance of permanent nature before proceeding.
Consider using REST API-based sync which is fully reversible.
```

**Detection hint:** Any S2S setup instructions without an explicit irreversibility warning.

---

## Anti-Pattern 3: Treating External Objects Like Native Objects

**What the LLM generates:** Complex SOQL queries against External Objects — `SELECT Id, COUNT(LineItems), SUM(Amount) FROM ExternalOrder__x WHERE Status != 'Closed' OFFSET 100`.

**Why it happens:** LLMs treat all Salesforce objects as equivalent. External Objects look like native objects in SOQL syntax but have significant feature gaps.

**Correct pattern:**
```
External Objects (Salesforce Connect) SOQL limitations:
- No OFFSET support
- Limited aggregate functions (COUNT may work; SUM/AVG often not)
- Limited relationship traversal
- No WHERE on all field types
Verify the specific External Object's supported SOQL features before designing queries.
```

**Detection hint:** SOQL against tables ending in `__x` (External Object naming convention) using OFFSET, SUM/AVG aggregates, or complex relationship joins.

---

## Anti-Pattern 4: Using Native S2S for High-Volume Record Sharing

**What the LLM generates:** Workflow or integration design that uses native S2S for sharing 10,000+ records between orgs.

**Why it happens:** LLMs don't model the SOAP API limit impact of S2S at scale. They see it as a "built-in" feature and assume it scales like standard Salesforce functionality.

**Correct pattern:**
```
Native S2S at high volume:
- 10,000 record shares/day = 10,000 SOAP API calls in EACH org (20,000 total)
- Standard SOAP API daily limit: 15,000 (Developer), 100,000-1,000,000 (Enterprise+)
- High-volume cross-org sync should use REST API with Bulk API 2.0 above 2,000 records/job
```

**Detection hint:** S2S recommended for scenarios described as "daily sync of thousands of records" or "near-real-time high-volume sharing."

---

## Anti-Pattern 5: No Error Handling for Cross-Org API Failures

**What the LLM generates:** Cross-org sync code that calls the target org REST API without error handling, retry logic, or handling of 401/403 authentication failures.

**Why it happens:** LLMs generate the "happy path" API call code without modeling cross-org failure modes — target org down, authentication token expired, API limit reached on target org.

**Correct pattern:**
```java
// Cross-org callout must handle:
try {
    HttpResponse response = http.send(request);
    if (response.getStatusCode() == 401) {
        // Refresh OAuth token via Named Credential
    } else if (response.getStatusCode() == 429) {
        // Target org API limit reached — queue for retry
    } else if (response.getStatusCode() >= 500) {
        // Target org service error — dead letter queue
    }
} catch (System.CalloutException e) {
    // Target org unreachable — log and retry via Queueable
}
```

**Detection hint:** Cross-org callout code with no status code checking or exception handling beyond a generic try/catch.
