# LLM Anti-Patterns — OmniStudio Scalability Patterns

Common mistakes AI coding assistants make when generating or advising on OmniStudio scalability. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Conflating Fire-and-Forget With Queueable Chainable

**What the LLM generates:** When asked how to fix governor limit errors in an Integration Procedure under portal concurrency, the LLM recommends enabling `useFuture: true` (fire-and-forget async mode), describing it as "running the IP asynchronously to avoid hitting limits."

**Why it happens:** LLMs associate "async" with "no governor limits" because async Apex has higher CPU and heap limits than synchronous Apex. They do not distinguish between future-method async (same SOQL/DML limits, higher CPU/heap) and Queueable async (same SOQL/DML limits, higher CPU/heap). SOQL limit errors are not addressed by either — but fire-and-forget is incorrectly perceived as the lighter-weight "async" solution.

**Correct pattern:**
```
Fire-and-forget (useFuture: true):
  Purpose: Remove UI blocking
  SOQL limit: 100 (same as sync)
  CPU limit: 60,000ms (higher)
  Governor limit escape: NO

Queueable Chainable:
  Purpose: Escape governor limits + remove UI blocking
  SOQL limit: 100 (same as sync — NOT higher)
  CPU limit: 60,000ms (higher)
  Heap limit: 12MB (higher)
  Governor limit escape: YES — fresh transaction context
  
Note: Neither async mode increases the SOQL limit.
To reduce SOQL consumption, consolidate queries or use DataRaptor caching.
```

**Detection hint:** Any recommendation that claims "fire-and-forget will avoid governor limit errors" or "running asynchronously removes SOQL limits" is wrong. Reject it.

---

## Anti-Pattern 2: Recommending IP Chainable When Queueable Chainable Is Needed

**What the LLM generates:** For an Integration Procedure that hits CPU or SOQL limits when invoked under high concurrent load, the LLM recommends "using IP Chainable to split the IP into smaller steps that run separately."

**Why it happens:** "Chainable" appears in both IP Chainable and Queueable Chainable names, leading to conflation. LLMs also reason that "smaller steps = less limit consumption per step" — which is true for some patterns but not for IP Chainable, which runs all chained steps in the same synchronous transaction.

**Correct pattern:**
```
IP Chainable: Links multiple Integration Procedures in sequence.
  Execution: SYNCHRONOUS — all steps share one Apex transaction
  Governor limits: SHARED across all chained steps
  Use case: Modularity, code separation
  Does NOT escape governor limits

Queueable Chainable: Runs designated steps as Queueable Apex jobs.
  Execution: ASYNCHRONOUS — each step gets a fresh transaction
  Governor limits: ISOLATED per step
  Use case: Governor limit relief under concurrency
  DOES provide fresh governor limit context per step
```

**Detection hint:** If a recommendation describes "IP Chainable" as a solution to governor limit errors, flag it. IP Chainable is a modularity tool, not a scalability tool.

---

## Anti-Pattern 3: Ignoring the 25-Concurrent-Long-Running-Apex Org-Wide Limit

**What the LLM generates:** A scalability design for a 500-user concurrent portal that focuses exclusively on per-session governor limits (SOQL, CPU per IP execution) without accounting for the org-wide concurrent Apex request ceiling.

**Why it happens:** LLMs are well-trained on per-transaction governor limits (the SOQL 100, DML 150, CPU 10,000ms numbers appear frequently in documentation). The concurrent long-running Apex limit (25 requests exceeding 20 seconds, org-wide) appears less frequently and is an org-wide constraint rather than a per-transaction one, making it less salient in training data.

**Correct pattern:**
```
Org-wide concurrent long-running Apex limit: 25 requests > 20 seconds

Design implications for portal deployments:
1. Any IP that takes > 20s under load consumes this org-wide slot
2. 500 concurrent users with IPs averaging 25s = immediate ceiling breach
3. Batch jobs scheduled during peak portal hours consume slots from the same pool
4. Mitigation: ensure common-case IP execution < 20s; use Queueable Chainable 
   only for genuinely long operations; schedule batch away from peak portal hours
```

**Detection hint:** Any portal scalability recommendation that omits the 25-concurrent-request limit should be flagged for incompleteness. Ask: "What is the impact of the org-wide concurrent long-running Apex limit on this design?"

---

## Anti-Pattern 4: Not Enabling Direct Platform Access for Read-Heavy IPs (Spring '25+)

**What the LLM generates:** A performance recommendation for a read-heavy Integration Procedure on a Spring '25+ org that suggests adding Queueable Chainable, reducing DataRaptor field counts, and optimizing SOQL WHERE clauses — without mentioning Direct Platform Access mode.

**Why it happens:** Direct Platform Access is a Spring '25 feature and may not be well represented in LLM training data predating that release. LLMs default to prior-generation OmniStudio performance patterns (query optimization, step reduction) that are valid but incomplete on Spring '25+ orgs.

**Correct pattern:**
```
For read-heavy Integration Procedures on Spring '25+ orgs with LWR sites:
1. Enable Direct Platform Access in IP Execution Settings
2. DPA bypasses Apex CPU governors for all read operations (DataRaptor Extracts,
   SOQL queries, Salesforce Object GET operations)
3. Result: read-heavy IPs no longer accumulate CPU time toward the 10,000ms limit
4. Constraint: write operations (insert/update/delete) still consume Apex CPU

When DPA is not applicable:
- Org is not on Spring '25+
- Site is on Aura runtime (not LWR)
- IP contains write operations that cannot be separated
```

**Detection hint:** For any recommendation about IP performance on a Spring '25+ org, check whether Direct Platform Access was considered. If it was not mentioned for a read-heavy IP, flag it.

---

## Anti-Pattern 5: Missing LWR + CDN as a Prerequisite for Experience Cloud High-Volume Deployments

**What the LLM generates:** A high-volume Experience Cloud portal design that recommends IP-level caching, Queueable Chainable, and SOQL optimization — but deploys on an Aura runtime site without LWR or CDN configuration.

**Why it happens:** LLMs understand OmniStudio-level optimizations well. LWR runtime and CDN configuration are separate Experience Cloud architectural decisions that are not always associated with OmniStudio scalability in training data. LLMs may treat LWR as an optional modernization rather than a hard prerequisite.

**Correct pattern:**
```
High-volume Experience Cloud portal deployment requirements:
1. LWR (Lightning Web Runtime) — REQUIRED, not optional
   - Enables CDN delivery of static page structure
   - Aura does NOT support CDN page caching
2. CDN caching — REQUIRED for static assets (page shell, JS bundles, CSS)
   - Enabled in Experience Cloud site Administration settings
   - Without CDN, every session request hits Salesforce application servers
3. IP-level and DataRaptor caching — REQUIRED for reference data
   - Reduces redundant SOQL across concurrent sessions

Without LWR + CDN:
- Page rendering cost grows linearly with concurrent users
- IP-level caching helps data calls but not page shell rendering
- Aura-based portal cannot scale to hundreds of concurrent users without
  severe degradation
```

**Detection hint:** Any high-volume Experience Cloud design that does not specify LWR runtime and CDN caching as explicit prerequisites should be flagged. Ask: "Is the site on LWR? Is CDN configured?"

---

## Anti-Pattern 6: Conflating Single-Session Performance Tuning With Multi-User Concurrency Patterns

**What the LLM generates:** When asked about OmniStudio scalability for high-volume portals, the LLM recommends single-session optimizations: reducing OmniScript steps, minimizing DataRaptor field counts, compressing HTTP response payloads. These recommendations are from the single-session performance domain (`omnistudio/omnistudio-performance`), not the multi-user concurrency domain.

**Why it happens:** "Performance" and "scalability" are treated as synonyms in general software engineering contexts. In OmniStudio, they address different failure modes. Single-session performance tuning improves one user's experience. Multi-user concurrency patterns prevent the platform from being exhausted across all users simultaneously.

**Correct pattern:**
```
Single-session performance (omnistudio/omnistudio-performance skill):
- OmniScript step count and layout optimization
- DataRaptor field selection minimization
- IP HTTP timeout and response compression
- Symptom: one user's OmniScript is slow

Multi-user concurrency patterns (this skill):
- Queueable Chainable for governor limit escape
- Direct Platform Access for read-heavy IPs
- LWR + CDN for portal page delivery
- IP-level caching for concurrent reference data requests
- 25-concurrent-long-running-Apex limit management
- Symptom: OmniStudio degrades or errors under many simultaneous users
```

**Detection hint:** If a "scalability" recommendation contains only single-session performance tuning suggestions with no mention of concurrency limits, async execution modes, or CDN, it is addressing the wrong problem space. Route to the correct skill.
