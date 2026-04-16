# Gotchas — Data Cloud vs CRM Analytics Decision

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: “Replace Data Cloud with CRM Analytics” ignores activation and identity scope

**What happens:** Teams cancel or defer Data Cloud because CRM Analytics can visualize external data when pushed into Salesforce-shaped datasets, then discover they still lack governed identity clusters, segment publication to ad platforms, or consent-aware activation flows native to the customer data platform path.

**When it occurs:** During budget consolidation when products are compared only on charting features instead of on ingestion volume, identity ruleset limits, and activation target requirements.

**How to avoid:** Score each use case against ingestion, harmonization, identity, activation, and analytics. If any activation or cross-source identity requirement scores high, Data Cloud remains in scope regardless of CRM Analytics presence.

---

## Gotcha 2: Direct Data is a DMO contract, not “all lake tables”

**What happens:** Architects promise analysts “everything in Data Cloud” in CRM Analytics without validating which harmonized objects are supported for their connectivity pattern, leading to scope creep toward unsupported shapes or performance surprises.

**When it occurs:** During workshop whiteboarding when lakehouse terminology is used loosely and DMO boundaries are skipped.

**How to avoid:** Name the concrete DMOs and subject areas in the decision record, align with official Direct Data documentation, and stage a proof of concept on a narrow subject area before enterprise rollout.

---

## Gotcha 3: Latency stacks across layers

**What happens:** Stakeholders expect near-real-time dashboards on metrics that depend on batch harmonization, identity resolution runs, and CRM Analytics sync schedules. Missed SLAs are blamed on “the wrong product” instead of the pipeline.

**When it occurs:** When marketing promises sub-hour activation and sales operations expects the same freshness inside CRM Analytics without modeling cumulative lag.

**How to avoid:** Document end-to-end latency as a chain: ingestion mode, DLO-to-DMO processing, identity resolution cadence, CRM Analytics refresh or query semantics, and human change management for each hop.
