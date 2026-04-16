# LLM Anti-Patterns — API Contract Documentation

Common mistakes AI coding assistants make when generating or advising on Salesforce API contract documentation.

---

## Anti-Pattern 1: Fabricating Specific Numeric Rate Limits

**What the LLM generates:** "Salesforce allows 15,000 API calls per day for Enterprise Edition."

**Why it happens:** LLMs have seen various Salesforce limit numbers in training data without knowing they are dynamic, org-specific values.

**The correct pattern:** API request limits vary by org edition and add-on licenses. Never document a hardcoded number. Always retrieve the actual limit from `GET /services/data/vXX.0/limits` (returns `DailyApiRequests.Max`) or reference the Salesforce Developer Limits Quick Reference cheatsheet.

**Detection hint:** Any specific numeric daily API limit in documentation without a source from the `/limits` resource or official cheatsheet is unverified and potentially wrong.

---

## Anti-Pattern 2: Assuming OpenAPI Beta Covers All APIs

**What the LLM generates:** "Use the Salesforce OpenAPI beta endpoint to generate documentation for all your APIs including custom Apex REST."

**Why it happens:** LLMs generalize the OpenAPI generator to all Salesforce APIs without knowing the scope limitation.

**The correct pattern:** The Salesforce OpenAPI beta covers only standard sObjects REST API (CRUD operations). Custom Apex `@RestResource` endpoints, Composite API, and Connect REST API require hand-authored specs.

**Detection hint:** Any recommendation to use the OpenAPI beta for custom Apex REST endpoint documentation is incorrect.

---

## Anti-Pattern 3: Treating 403 REQUEST_LIMIT_EXCEEDED the Same as 429 Throttling

**What the LLM generates:** "Implement exponential backoff retry on all 4xx errors including 403."

**Why it happens:** LLMs generalize error handling patterns without knowing the semantic difference between 403 (resource exhausted) and 429 (transient throttle).

**The correct pattern:** HTTP 403 `REQUEST_LIMIT_EXCEEDED` means the 24-hour daily budget is exhausted. Exponential backoff will not help until the rolling window resets. Document these as separate error conditions with separate recovery procedures.

**Detection hint:** Any error handling guide that applies the same retry logic to 403 and 429 is conflating two different error conditions.

---

## Anti-Pattern 4: Documenting SLA Percentages from Developer Docs

**What the LLM generates:** "Salesforce guarantees 99.9% uptime for REST API calls."

**Why it happens:** LLMs extrapolate SLA numbers from general cloud service expectations or training data about other platforms.

**The correct pattern:** Salesforce API SLA uptime and latency commitments are in trust.salesforce.com and Order of Service agreements — not in developer documentation. Do not document SLA percentages based on developer docs; reference trust.salesforce.com instead.

**Detection hint:** Any SLA percentage cited from developer documentation is unverified. SLA commitments require checking trust.salesforce.com and the Order of Service.

---

## Anti-Pattern 5: Not Including the Sforce-Limit-Info Header in Monitoring Design

**What the LLM generates:** API contract documentation that describes rate limits in text but does not include guidance on the `Sforce-Limit-Info` response header.

**Why it happens:** LLMs describe limits as static documentation rather than as runtime observability signals.

**The correct pattern:** The `Sforce-Limit-Info: api-usage=X/Y` header is present on every REST API response and provides real-time consumption visibility. Consumer teams must log this header and alert when X/Y exceeds a threshold (e.g., 80%). Documentation must include the header format and monitoring guidance.

**Detection hint:** API rate limit documentation that does not include the `Sforce-Limit-Info` header is missing the operational monitoring requirement.
