# LLM Anti-Patterns — Multi-Org Strategy

Common mistakes AI coding assistants make when generating or advising on Salesforce multi-org architecture decisions.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Defaulting to Single-Org Without Evaluating Regulatory Requirements

**What the LLM generates:** "Best practice is to consolidate everything into a single Salesforce org for simplicity and cost savings" without evaluating data residency laws (GDPR, China PIPL), M&A timelines, or business unit autonomy requirements that may mandate separate orgs.

**Why it happens:** Salesforce's own documentation emphasizes single-org simplicity, and most training data examples assume one org. LLMs generalize this into a blanket recommendation without assessing the specific regulatory or organizational constraints.

**Correct pattern:**

```text
Evaluate multi-org need against these drivers before recommending single-org:
1. Data residency: EU GDPR, China PIPL, or sector regulations requiring data
   to remain in a specific geography (Salesforce Hyperforce region matters).
2. M&A timeline: acquired company on Salesforce with active users — merging
   orgs is a 6-18 month project, not an immediate option.
3. Business unit autonomy: separate release cycles, different compliance
   requirements, or incompatible data models.
4. Licensing: separate contracts with different editions or clouds.

If none of these apply, single-org is usually correct. If any apply, multi-org
architecture must be evaluated with an integration topology.
```

**Detection hint:** Flag single-org recommendations that do not include a data-residency or M&A assessment. Look for "consolidate into one org" without a qualifying evaluation.

---

## Anti-Pattern 2: Recommending Salesforce-to-Salesforce (S2S) as the Primary Integration

**What the LLM generates:** "Use Salesforce-to-Salesforce (S2S) to share records between your two orgs" as the default cross-org integration approach, without mentioning that S2S is a legacy feature with limited throughput, manual acceptance workflows, and no support for custom objects created after the connection.

**Why it happens:** Salesforce-to-Salesforce appears in older training data as the built-in cross-org sharing mechanism. LLMs do not recognize that it has been effectively superseded by Salesforce Connect (External Objects), Platform Events, or middleware-based patterns for modern architectures.

**Correct pattern:**

```text
Modern cross-org integration options (preferred over S2S):
1. Salesforce Connect (External Objects): real-time virtual access to records
   in the other org via the Cross-Org adapter. No data duplication.
2. Platform Events: event-driven async data sync between orgs.
3. REST/SOAP API via Named Credentials: direct API calls between orgs using
   OAuth JWT Bearer or Client Credentials flow.
4. Middleware (MuleSoft, etc.): orchestrated integration for complex
   multi-step data flows.

Salesforce-to-Salesforce limitations:
- Only standard objects and pre-existing custom objects
- Manual accept/reject workflow for shared records
- Limited throughput and no bulk support
- No longer receiving feature investment from Salesforce
```

**Detection hint:** Flag any recommendation of "Salesforce-to-Salesforce" as the primary integration. Look for the string "S2S" or "Salesforce-to-Salesforce" without a caveat about its legacy status.

---

## Anti-Pattern 3: Ignoring Cross-Org SSO Complexity

**What the LLM generates:** "Set up SSO across your orgs using SAML" without addressing the identity provider (IdP) architecture, user provisioning strategy, or the fact that each Salesforce org is a separate service provider requiring its own Connected App and SSO configuration.

**Why it happens:** SSO is treated as a single checkbox in many tutorials. LLMs underestimate the complexity of maintaining consistent user identities, license assignments, and session policies across multiple Salesforce orgs with a shared IdP.

**Correct pattern:**

```text
Cross-org SSO requires:
1. Central IdP (Okta, Azure AD, Salesforce as IdP) with each Salesforce org
   registered as a separate SP (service provider).
2. Federation ID or custom attribute to link user identity across orgs.
3. User provisioning strategy: SCIM, JIT provisioning, or manual sync.
4. License management: each org requires its own license allocation.
5. Session policy alignment: timeout, IP restrictions, and MFA requirements
   must be coordinated across orgs.
6. My Domain configuration in each org (required for SAML SSO).

Do NOT assume that enabling SSO in one org automatically extends to others.
```

**Detection hint:** Flag SSO recommendations that do not mention per-org SP configuration, user provisioning, or Federation ID mapping.

---

## Anti-Pattern 4: Underestimating API Limit Consumption in Hub-and-Spoke Topologies

**What the LLM generates:** Integration designs that route all cross-org traffic through a hub org without calculating the API request consumption on the hub. For example, designing a hub that receives 50,000 API calls/day from 4 spoke orgs when the hub's Enterprise Edition allocation is 100,000/day total.

**Why it happens:** LLMs focus on the logical architecture pattern (hub-and-spoke) without modeling the quantitative API consumption. API limits are edition-dependent and license-count-dependent, but training data rarely includes specific allocation math.

**Correct pattern:**

```text
Before finalizing a hub-and-spoke topology, calculate API consumption:

Hub org API allocation = base (per edition) + (user licenses x per-license add)
Example: Enterprise Edition base = 100,000/day

Spoke traffic estimate:
- Spoke A: 15,000 calls/day (real-time sync)
- Spoke B: 8,000 calls/day (scheduled batch)
- Spoke C: 20,000 calls/day (event-driven)
- Internal hub usage: 30,000 calls/day
- Total: 73,000/day — within limit but no headroom

Mitigation options when allocation is tight:
1. Use Platform Events (do not count against REST API limit)
2. Use Composite API to reduce call count (up to 25 subrequests per call)
3. Purchase additional API call packs from Salesforce
4. Move high-volume sync to Bulk API (separate daily allocation)
```

**Detection hint:** Flag hub-and-spoke designs that do not include an API consumption estimate or reference the hub org's edition and license count.

---

## Anti-Pattern 5: Treating Org Mergers as a Simple Data Migration

**What the LLM generates:** "To consolidate two Salesforce orgs, export all data from Org B and import it into Org A using Data Loader" without addressing metadata conflicts, automation conflicts, user deduplication, historical data ownership, or the months-long project timeline.

**Why it happens:** LLMs reduce org consolidation to a data migration because data loading is well-documented. The metadata layer (different picklist values, conflicting page layouts, overlapping automation, incompatible sharing models) and organizational change management are poorly represented in training data.

**Correct pattern:**

```text
Org consolidation requires parallel workstreams, not just data migration:

1. Metadata audit: compare objects, fields, picklist values, record types,
   page layouts, validation rules, and automation between both orgs.
2. Automation conflict resolution: identify overlapping triggers, flows,
   and process builders on the same objects.
3. User and permission model: merge user accounts, reconcile profiles and
   permission sets, handle duplicate usernames (must be globally unique).
4. Data migration: external ID strategy, parent-child sequencing, owner
   reassignment, and historical data volume decisions.
5. Integration re-pointing: update all external systems that integrate
   with Org B to point to Org A.
6. Timeline: typical org merge is 6-18 months depending on complexity.
```

**Detection hint:** Flag org consolidation advice that only mentions data migration without referencing metadata audit, automation conflict resolution, or user deduplication.

---

## Anti-Pattern 6: Assuming Hyperforce Solves All Data Residency Requirements

**What the LLM generates:** "Deploy your org on Hyperforce in the EU region and you satisfy GDPR data residency requirements" without noting that some Salesforce features may process data outside the selected region, that not all Salesforce products are available on Hyperforce, and that contractual DPA terms must still be verified.

**Why it happens:** Hyperforce is marketed as the solution for data residency, and LLMs repeat this without the nuances documented in Salesforce Trust and Compliance documentation.

**Correct pattern:**

```text
Hyperforce and data residency:
- Hyperforce allows selecting a deployment region (e.g., EU, Australia).
- Primary data at rest stays in the selected region.
- However: some features may process data transiently outside the region
  (e.g., Einstein AI, email relay, certain analytics features).
- Not all Salesforce products are available on Hyperforce yet.
- GDPR compliance requires more than data location: data processing
  agreements (DPA), sub-processor lists, and transfer mechanism documentation.
- Verify with Salesforce Trust (trust.salesforce.com) and your legal team.
```

**Detection hint:** Flag Hyperforce recommendations that claim complete GDPR compliance without mentioning transient data processing, DPA requirements, or feature availability caveats.
