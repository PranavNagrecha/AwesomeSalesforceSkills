# LLM Anti-Patterns — NFR Definition for Salesforce

Common mistakes AI coding assistants make when generating or advising on NFR definition for Salesforce implementations. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Generating NFRs with vague adjectives instead of measurable thresholds

**What the LLM generates:**
```
NFR-001: The system must respond quickly to user actions.
NFR-002: The system must be highly available.
NFR-003: The system must be secure.
```

**Why it happens:** LLMs pattern-match on NFR examples from generic software engineering training data, where "fast," "reliable," and "secure" are common placeholder phrases. Without Salesforce-specific context, the model defaults to adjective-based requirements.

**Correct pattern:**
```
NFR-PERF-001: Lightning record page load (p95) < 3 seconds in Full sandbox
               with 200 concurrent users and 5M records on target object.
NFR-AVAIL-001: Infrastructure availability: the contract's figure (platform-owned;
               no fetched source states 99.9%, see gotchas.md Gotcha 3).
               Application availability: 99.5% during business hours (team-owned),
               RTO = 4 hours, RPO = 1 hour.
NFR-SEC-001: SSN and DOB fields are in the active Shield Platform Encryption
             policy, verified in UAT by policy and key-state review (gotchas.md Gotcha 5).
```

**Detection hint:** Scan generated NFRs for the words "quickly," "fast," "highly," "secure," "compliant," "reliable" without an associated numeric threshold and measurement method. Flag any such NFR for revision.

---

## Anti-Pattern 2: Conflating Salesforce's infrastructure SLA with full application availability

**What the LLM generates:**
```
NFR-AVAIL-001: System availability: 99.9% — satisfied by Salesforce Trust SLA.
               No further action required.
```

**Why it happens:** LLMs frequently reference the Salesforce 99.9% SLA as a complete answer to availability questions. The shared responsibility model (infrastructure vs. application) is underrepresented in training data compared to the SLA number itself.

**Correct pattern:**
```
Availability must be specified at two levels:
1. Salesforce infrastructure: the figure in the customer's contract (Salesforce-owned,
   not verifiable by team). UNVERIFIED (2026-10-03): a published 99.9% SLA was not found.
2. Application availability: Team-owned. Includes custom Apex, Flows, integrations,
   scheduled jobs. Define RPO and RTO. Define monitoring. Define rollback procedure.
```

**Detection hint:** If the availability NFR section references only the Salesforce Trust SLA and contains no RPO, RTO, or owner for customer-side availability, the LLM has missed the shared responsibility split.

---

## Anti-Pattern 3: Writing compliance NFRs at the regulation level, not the control level

**What the LLM generates:**
```
NFR-SEC-001: The system must be GDPR compliant.
NFR-SEC-002: The system must meet HIPAA requirements.
```

**Why it happens:** Regulations are often cited as single-line requirements in project documentation. LLMs reproduce this pattern without decomposing it into the specific technical controls that require Salesforce configuration.

**Correct pattern:**
```
Each regulation generates multiple control-level NFRs:

GDPR:
  NFR-GDPR-001: Right to erasure — personal data anonymised within 30 days of SAR receipt.
  NFR-GDPR-002: Consent audit log — immutable log of consent with timestamp and source.
  NFR-GDPR-003: Data residency — org provisioned in EU region instance.

HIPAA:
  NFR-HIPAA-001: Encryption at rest — PHI fields encrypted via Shield Platform Encryption.
  NFR-HIPAA-002: Audit trail — Field History Tracking or Event Monitoring active on PHI objects.
  NFR-HIPAA-003: BAA — Salesforce HIPAA Business Associate Agreement executed before go-live.
```

**Detection hint:** Count the number of NFR rows per named regulation. If GDPR, HIPAA, or PCI-DSS generates only one NFR row, the LLM has almost certainly produced a regulation-level placeholder rather than control-level requirements.

---

## Anti-Pattern 4: Ignoring governor limits when writing scalability NFRs

**What the LLM generates:**
```
NFR-SCALE-001: The system must process 500,000 records per day via the integration.
```

**Why it happens:** The LLM produces business-level volume targets without mapping them to Salesforce platform ceilings. Governor limits are a Salesforce-specific constraint with no direct equivalent in most other SaaS platforms, so they are underweighted in cross-platform training data.

**Correct pattern:**
```
NFR-SCALE-001: ERP integration processes 500,000 records per day via Bulk API v2.
  Platform ceiling check:
    - 500,000 records / 10,000 per Bulk API job = 50 jobs/day (well within Bulk API limits).
    - REST API equivalent: 500,000 calls/day = 50% of Enterprise 100-user daily allocation.
    - Decision: Use Bulk API v2. REST API approach rejected — exceeds 80% allocation ceiling.
  Threshold: 500,000 records/day processed within 4-hour nightly batch window.
  Method: Monitor via Bulk API job status and Salesforce Limits API (/services/data/vXX/limits).
```

**Detection hint:** Any scalability NFR that mentions "records" or "transactions" per day without a corresponding Salesforce limit type and utilisation percentage is incomplete.

---

## Anti-Pattern 5: Recommending Developer Pro sandbox for performance validation

**What the LLM generates:**
```
Test the performance NFR in a Developer or Developer Pro sandbox before committing to the threshold.
```

**Why it happens:** Developer and Developer Pro sandboxes are the most commonly referenced sandbox types in general Salesforce development guidance. Their limitations for performance testing are a platform nuance that is underrepresented in LLM training data relative to general sandbox usage guidance.

**Correct pattern:**
```
Performance NFRs must be validated in a Full sandbox with production-equivalent data volume.
Developer sandboxes hold 200 MB and Developer Pro sandboxes 1 GB of data (Tooling API,
SandboxInfo), and neither replicates production record distribution. (Corrected: an earlier
version gave Developer Pro as 200 MB.) Query performance, index selectivity, and page load times measured in Developer
Pro are not representative of production behaviour at scale.

If a Full sandbox is unavailable, the NFR must be marked "unverified — go-live risk" and
escalated to the project sponsor rather than signed off as met.
```

**Detection hint:** Any performance testing recommendation that names a Developer, Developer Pro, or Partial Copy sandbox without explicitly stating the data volume limitation is applying the wrong environment.

---

## Anti-Pattern 6: Omitting usability NFRs entirely

**What the LLM generates:** NFR registers that cover performance, scalability, availability, and security — but contain no usability requirements.

**Why it happens:** Usability is the NFR category most frequently omitted in technical architecture documents. LLMs reproduce this gap because training data from architecture templates and RFPs underrepresents usability as a formal NFR category.

**Correct pattern:**
```
Usability NFRs must include at minimum:
  NFR-UX-001: Page load time (often overlaps with NFR-PERF-001 — cross-reference rather than duplicate).
  NFR-UX-002: Field count per page layout — maximum 30 visible fields per layout to manage cognitive load.
  NFR-UX-003: Mobile readiness — X% of core user workflows completable via Salesforce Mobile App.
  NFR-UX-004: Accessibility — WCAG 2.1 AA compliance for all custom LWC components on public-facing pages.
```

**Detection hint:** If the NFR register has no rows with "ux," "usability," "layout," "mobile," or "accessibility" in the category or tag column, usability NFRs have been omitted.

---

## Anti-Pattern 7: Stating Integration Throughput Only As Calls Per Day, Proven In A Full Sandbox

**What the LLM generates:**
```
NFR-INT-001: The order integration must support 150,000 API calls per day.
             Verified by load test in the Full sandbox: no limit errors.
```

**Why it happens:** The daily allocation is the best-known API limit, and a clean load test reads as proof.

**Correct pattern:**
```
NFR-INT-001: Order integration
  Daily volume:  <= 30% of production's 24-hour allocation (edition formula,
                 not the Full sandbox's flat 5,000,000)
  Concurrency:   <= 10 concurrent requests lasting 20 s or longer
                 (production limit: 25; beyond it REQUEST_LIMIT_EXCEEDED)
  Latency:       p95 < 2 s per request
  Measured by:   DailyApiRequests from REST /limits, middleware concurrency metrics
```

**Detection hint:** Flag throughput NFRs with no concurrency or duration term, and any load-test evidence that quotes a Full sandbox's allocation as the ceiling.
