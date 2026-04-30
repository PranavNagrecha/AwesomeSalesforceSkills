# Decision Tree — Performance Tuning

Where is the time going, and which skill should I open to fix it?
**CPU/heap · SOQL · sharing recalc · LDV · cache · LWC render · Experience Cloud · OmniStudio · async jobs**

Use this tree any time someone says "slow", "timeout", "limit hit",
"recalculation taking forever", "page won't load", or hands you an
unexplained latency number.

Performance work in Salesforce fails in one of two ways:

1. **Optimizing without measuring** — guessing at the hotspot and
   refactoring the wrong thing.
2. **Diagnosing without routing** — identifying the right symptom but
   activating the wrong skill (e.g. opening `apex-cpu-and-heap-optimization`
   for a sharing recalc problem).

This tree fixes the second. The first is fixed by the rule below.

---

## Rule 0 — Diagnose before you optimize

If you do not have a measurement, you are not tuning, you are guessing.

| Symptom domain | Open this profiling skill first |
|---|---|
| Apex transaction slow / unclear hotspot | [`apex/apex-performance-profiling`](../../skills/apex/apex-performance-profiling/SKILL.md) |
| Hitting governor limits at runtime | [`apex/apex-limits-monitoring`](../../skills/apex/apex-limits-monitoring/SKILL.md) |
| Production-only slow paths, no local repro | [`apex/salesforce-debug-log-analysis`](../../skills/apex/salesforce-debug-log-analysis/SKILL.md) |
| End-to-end latency under concurrent users | [`devops/performance-testing-salesforce`](../../skills/devops/performance-testing-salesforce/SKILL.md) |
| Need NFR baselines (SLA / SLO targets) | [`architect/nfr-definition-for-salesforce`](../../skills/architect/nfr-definition-for-salesforce/SKILL.md) |

Only after you have a hotspot — a SOQL query, a CPU-heavy method, a
recalc job, a heavy component — proceed into the symptom routing below.

---

## Symptom → skill routing

```
START: Performance problem reported.

Q1. What is the user-visible symptom?
    ├── "Apex transaction limit error / timeout"     → Q2  (Apex governors)
    ├── "SOQL is slow / Query Plan looks bad"        → Q5  (SOQL & data access)
    ├── "Sharing rule / OWD change blocked the org"  → Q8  (Sharing recalc)
    ├── "Object has millions of rows, design phase"  → Q10 (LDV architecture)
    ├── "Lightning page slow / EPT high"             → Q12 (LWC + page render)
    ├── "Experience Cloud site slow for guests"      → Experience Cloud → Q15
    ├── "OmniScript / Integration Procedure slow"    → OmniStudio → Q16
    ├── "Same query repeats across requests"         → Cache → Q17
    └── "Async job runtime exceeds window"           → Cross to async-selection.md
```

---

## Q2–Q4 — Apex CPU, heap, governor limits

```
Q2. Which limit is being hit?
    ├── CPU time exceeded                            → Q3
    ├── Heap size exceeded                           → Q3
    ├── Too many SOQL queries / DML rows             → Q4
    ├── UNABLE_TO_LOCK_ROW                           → Q5 (lock contention is a SOQL/sharing problem)
    └── Limit varies, can't pin down                 → apex-performance-profiling first

Q3. CPU or heap — is the hotspot a tight loop, JSON, or query result size?
    ├── Nested loops, O(n²) iteration                → apex-cpu-and-heap-optimization (loop refactor patterns)
    ├── JSON serialize/deserialize on big payloads   → apex-cpu-and-heap-optimization (streaming JSON section)
    ├── String concat / regex on large bodies        → apex-cpu-and-heap-optimization (string work)
    ├── Query returns too many rows into memory      → soql-query-optimization (project narrower) THEN apex-cpu-and-heap-optimization
    └── Recurring trigger entry inflating CPU        → governor-limits (recursion guard) + apex-cpu-and-heap-optimization

Q4. Governor count limits (SOQL, DML, callouts) — where are they coming from?
    ├── Loop with SOQL/DML inside                    → governor-limits (bulkification patterns)
    ├── Trigger fires multiple times per transaction → governor-limits (recursion + handler framework) + templates/apex/TriggerHandler.cls
    ├── Already at limit, need graceful degradation  → governor-limit-recovery-patterns (savepoints, partial commit)
    └── Need runtime guard to skip expensive work    → apex-limits-monitoring (Limits class checkpoints)
```

---

## Q5–Q7 — SOQL and data access

```
Q5. Is the query selective (Query Plan tool says cost < 1.0)?
    ├── Yes, still slow                              → Q6
    └── No (TableScan / cost > 1.0)                  → Q7

Q6. Selective query is still slow — why?
    ├── Returns too many rows for the consumer       → soql-query-optimization (projection + pagination)
    ├── Triggered by formula field with cross-object spans → cross-object-formula-and-rollup-performance
    ├── Filter uses a formula field                  → formula-field-performance-and-limits (formulas are non-indexable)
    ├── Returning related lists / N+1 child loads    → soql-query-optimization (nested SOQL vs subquery)
    └── Aggregate query taking minutes               → soql-query-optimization (aggregate + custom index) THEN custom-index-requests

Q7. Non-selective query — what's missing?
    ├── No index on the WHERE field                  → custom-index-requests (deploy via Metadata API or open Support case)
    ├── Standard index but data is highly skewed     → custom-index-requests (two-column composite or skinny table)
    ├── Filter is on a formula                       → formula-field-performance-and-limits (move logic to a stored field) + custom-index-requests
    ├── Query runs across millions of rows daily     → architect/large-data-volume-architecture (skinny tables + archival)
    └── Query needs cross-org joins                  → integration-pattern-selection.md (probably not a SOQL problem at all)
```

---

## Q8–Q9 — Sharing and recalculation

```
Q8. What is the sharing problem?
    ├── A planned OWD/sharing rule change            → sharing-recalculation-performance (pre-flight, batch the change)
    ├── Recalc is already running and blocking work  → sharing-recalculation-performance (monitoring + recovery)
    ├── Single user owns 10k+ records of an object   → admin/data-skew-and-sharing-performance (ownership skew)
    ├── Single parent has 10k+ children              → admin/data-skew-and-sharing-performance (parent-child skew)
    └── Sharing model design from scratch            → cross to sharing-selection.md

Q9. After picking the skill above, also open:
    ├── If LDV org (>2M records on the object)       → architect/large-data-volume-architecture (skew + LDV interplay)
    └── If sales-cloud Account/Opportunity skew      → architect/high-volume-sales-data-architecture
```

---

## Q10–Q11 — Large Data Volume (LDV) architecture

```
Q10. What stage of LDV are you in?
    ├── Designing a new high-volume object           → architect/large-data-volume-architecture (skinny + indexes from day one)
    ├── Existing org breaching reports / queries     → soql-query-optimization + custom-index-requests + Q11
    ├── Historical data should leave the hot path    → external-data-and-big-objects (Big Object + Async SOQL)
    └── Sales-cloud-specific: Opportunity/Account skew → architect/high-volume-sales-data-architecture

Q11. Big Objects vs External Objects vs archival?
    ├── Audit/IoT/event log, append-only, billions   → Big Object via external-data-and-big-objects (Async SOQL only)
    ├── Live data lives in another system            → External Object via integration-pattern-selection.md (Salesforce Connect branch)
    ├── Old records hurting reports but rarely read  → external-data-and-big-objects (archival pattern) OR archive to data lake
    └── Need OLTP-style range queries at scale       → NOT Big Objects — revisit data model design
```

---

## Q12–Q14 — LWC and Lightning page render

```
Q12. What's slow about the page?
    ├── Initial page load (LCP > 2.5s on field data) → lwc-performance (bundle size + lazy load + wire-adapter audit)
    ├── User interaction lag (INP > 200ms)           → lwc-performance (rerender hotspots, large lists)
    ├── Specific component is the hotspot            → Q13
    ├── Whole org is slow for everyone               → Q14
    └── Want to enforce future budgets in CI         → lwc-performance-budgets (bundle/LCP/INP gates)

Q13. Component-level hotspot — which dimension?
    ├── Large list rendering (>200 rows)             → lwc-performance (virtualization + incremental render)
    ├── Wire adapter fires more than expected        → lwc-performance (memoization + cacheable=true Apex)
    ├── Calls Apex from client repeatedly            → cache → Q17 (cacheable Apex / Platform Cache server-side)
    └── DOM mutation thrash from reactive state      → lwc-performance (rerender debug + stable `key=` on iterators)

Q14. Page-level slowness across components?
    ├── Lightning page has 20+ components            → lwc-performance (page audit) + admin/record-page-performance if it exists
    ├── Page is in Experience Cloud                  → architect/experience-cloud-performance (CDN + page layers)
    └── Page slow only for some users (perm-based)   → admin/data-skew-and-sharing-performance (sharing-driven query cost)
```

---

## Q15 — Experience Cloud

```
Q15. Where is the Experience Cloud time going?
    ├── First contentful paint slow for guests       → architect/experience-cloud-performance (CDN config + asset weight)
    ├── Authenticated session slow                   → architect/experience-cloud-performance + lwc-performance
    ├── Search / list views slow                     → soql-query-optimization (most are SOQL hotspots in disguise)
    └── Specific feature (e.g. CMS, Salesforce Files) → architect/experience-cloud-performance (component allow-list)
```

---

## Q16 — OmniStudio runtime

```
Q16. What OmniStudio asset is slow?
    ├── OmniScript step transitions slow             → omnistudio-performance (step-level profiling)
    ├── Integration Procedure end-to-end latency     → omnistudio-performance THEN integration-procedure-cacheable-patterns
    ├── DataRaptor extract/transform slow            → omnistudio-cache-strategies + omnistudio-performance
    ├── Concurrent user load degrading the surface   → architect/omnistudio-scalability-patterns
    └── Salesforce CPQ price calc slow               → omnistudio-performance (CPQ branch) + apex-performance-profiling on CPQ plugins
```

---

## Q17 — Cache routing

```
Q17. What kind of cache is the right answer?
    ├── Apex repeatedly loads the same reference data → apex/platform-cache (Cache.Org)
    ├── Per-user expensive lookup, request-scoped     → apex/platform-cache (Cache.Session)
    ├── Integration Procedure response cacheable      → integration-procedure-cacheable-patterns
    ├── DataRaptor result cacheable                   → omnistudio-cache-strategies
    ├── HTTP response from a Named Credential         → apex/platform-cache (response caching) + integration-pattern-selection.md
    └── Browser-side caching for an LWC               → lwc-performance (wire adapter + Lightning Data Service)
```

Cache is *not* the answer when:

- The data changes per request → cache thrash, no hit rate.
- The slow query is non-selective → caching hides the symptom; one cache
  miss still blows the limit. Fix the SOQL first via Q5–Q7.
- The data is per-user PII → review `omnistudio/integration-procedure-cacheable-patterns`
  Anti-Pattern 5 (no PII in shared partition) before caching.

---

## Cross-tree links

This tree owns symptom routing for performance only. Send users to a
different tree when:

| If the question is really about… | Go to |
|---|---|
| Choosing the async mechanism for a long job | [`async-selection.md`](./async-selection.md) |
| Choosing between SObject / Big Object / External Object / Salesforce Connect | [`integration-pattern-selection.md`](./integration-pattern-selection.md) (data sourcing branch) + Q11 here |
| Picking the sharing model from scratch | [`sharing-selection.md`](./sharing-selection.md) |
| Picking Flow vs Apex vs Approvals for a new process | [`automation-selection.md`](./automation-selection.md) |

---

## Anti-patterns

- **"Add Platform Cache" as a default fix.** Caching a non-selective
  query buys microseconds on hits and still hits the SOQL limit on
  misses. Fix the query first (Q5–Q7), then decide if caching adds value.
- **Refactoring loops before profiling.** `apex-cpu-and-heap-optimization`
  is a hammer; `apex-performance-profiling` is the measurement that tells
  you whether loops are actually the hotspot. Run profiling first.
- **Custom index request without a Query Plan run.** Support will reject
  it. Always attach Query Plan output and selectivity math
  (`custom-index-requests` has the template).
- **Recalculating sharing in a maintenance window without a pre-flight.**
  Recalc on a 50M-row object can run for hours. Use
  `sharing-recalculation-performance` to estimate runtime and stage the
  change.
- **Treating Big Object Async SOQL as "just SOQL".** It is async, target
  must be a regular SObject, and there is no `LIMIT` in the inline
  result. See `external-data-and-big-objects`.
- **LWC bundle bloat under the LCP target.** Without budgets you ship
  performance regressions per release. Adopt `lwc-performance-budgets`
  before a regression incident, not after.
- **EPT chasing.** Experience Page Time is one number; treat it as a
  smoke alarm, not a diagnosis. Combine with `devops/performance-testing-salesforce`
  for repeatable measurements before claiming a regression is fixed.

---

## Related skills (full performance-domain index)

Diagnose:

- [`apex/apex-performance-profiling`](../../skills/apex/apex-performance-profiling/SKILL.md)
- [`apex/apex-limits-monitoring`](../../skills/apex/apex-limits-monitoring/SKILL.md)
- [`apex/salesforce-debug-log-analysis`](../../skills/apex/salesforce-debug-log-analysis/SKILL.md)
- [`devops/performance-testing-salesforce`](../../skills/devops/performance-testing-salesforce/SKILL.md)
- [`architect/nfr-definition-for-salesforce`](../../skills/architect/nfr-definition-for-salesforce/SKILL.md)

Apex CPU / heap / governors:

- [`apex/apex-cpu-and-heap-optimization`](../../skills/apex/apex-cpu-and-heap-optimization/SKILL.md)
- [`apex/governor-limits`](../../skills/apex/governor-limits/SKILL.md)
- [`apex/governor-limit-recovery-patterns`](../../skills/apex/governor-limit-recovery-patterns/SKILL.md)

SOQL and data access:

- [`data/soql-query-optimization`](../../skills/data/soql-query-optimization/SKILL.md)
- [`data/custom-index-requests`](../../skills/data/custom-index-requests/SKILL.md)
- [`apex/formula-field-performance-and-limits`](../../skills/apex/formula-field-performance-and-limits/SKILL.md)
- [`apex/cross-object-formula-and-rollup-performance`](../../skills/apex/cross-object-formula-and-rollup-performance/SKILL.md)

Sharing / data skew:

- [`admin/data-skew-and-sharing-performance`](../../skills/admin/data-skew-and-sharing-performance/SKILL.md)
- [`data/sharing-recalculation-performance`](../../skills/data/sharing-recalculation-performance/SKILL.md)

LDV / architecture:

- [`architect/large-data-volume-architecture`](../../skills/architect/large-data-volume-architecture/SKILL.md)
- [`architect/high-volume-sales-data-architecture`](../../skills/architect/high-volume-sales-data-architecture/SKILL.md)
- [`data/external-data-and-big-objects`](../../skills/data/external-data-and-big-objects/SKILL.md)

LWC / page render:

- [`lwc/lwc-performance`](../../skills/lwc/lwc-performance/SKILL.md)
- [`lwc/lwc-performance-budgets`](../../skills/lwc/lwc-performance-budgets/SKILL.md)

Experience Cloud:

- [`architect/experience-cloud-performance`](../../skills/architect/experience-cloud-performance/SKILL.md)

OmniStudio:

- [`omnistudio/omnistudio-performance`](../../skills/omnistudio/omnistudio-performance/SKILL.md)
- [`omnistudio/omnistudio-cache-strategies`](../../skills/omnistudio/omnistudio-cache-strategies/SKILL.md)
- [`omnistudio/integration-procedure-cacheable-patterns`](../../skills/omnistudio/integration-procedure-cacheable-patterns/SKILL.md)
- [`architect/omnistudio-scalability-patterns`](../../skills/architect/omnistudio-scalability-patterns/SKILL.md)

Cache:

- [`apex/platform-cache`](../../skills/apex/platform-cache/SKILL.md)

## Related templates

- `templates/apex/ApplicationLogger.cls` — instrument code paths with a
  `Request_Id__c` so you can correlate slow runs across the chain.
- `templates/apex/TriggerHandler.cls` + `TriggerControl.cls` — recursion
  control prevents trigger re-entry from inflating CPU and SOQL counts.
- `templates/apex/tests/BulkTestPattern.cls` — reproduce production-scale
  trigger behavior in tests so regressions surface in CI.

## Official sources used

- Salesforce Help — Query & Search Optimization (Query Plan tool, selectivity rules)
- Salesforce Large Data Volumes Best Practices (skinny tables, indexes, archival)
- Apex Developer Guide — Execution Governors and Limits
- Apex Developer Guide — Platform Cache
- Lightning Web Components Developer Guide — Performance
- Salesforce Help — Sharing Architecture & Recalculation
- Well-Architected — Performant pillar
