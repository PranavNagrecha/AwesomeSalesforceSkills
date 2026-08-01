# /design-omnistudio — Design or audit an OmniStudio capability

Wraps [`agents/omnistudio-designer/AGENT.md`](../agents/omnistudio-designer/AGENT.md). Covers the whole OmniStudio stack — OmniScript, FlexCard, DataRaptor, Integration Procedure, Business Rules Engine, Calculation Procedures, document generation — in one design or audit pass.

> **Not `/design-omni-channel`.** OmniStudio (Industries low-code toolset, formerly Vlocity) and Omni-Channel (service work routing: queues, presence, capacity) are different products with confusable names. For queues and routing configurations use `/design-omni-channel`.

---

## Step 1 — Collect inputs

Ask the user:

```
1. Mode?  design | audit
2. Target org alias?  (required for audit; optional for design)
3. Capability in one sentence?  (design only)
4. Layers in scope?  omniscript, flexcard, dataraptor, integration_procedure, business_rules
5. Runtime flavour?  native-omnistudio | vlocity-managed-package
6. User surface?  internal | experience-cloud-authenticated | guest   (design only)
7. Expected volume / peak?  (optional)
8. Repo path to retrieved metadata or a DataPack export?  (optional; used when no org is connected)
```

If any required input is missing, STOP and ask. Do not infer the runtime flavour from the industry — inspect the org or the source tree.

---

## Step 2 — Load the agent

Read `agents/omnistudio-designer/AGENT.md` and every entry in its Mandatory Reads that the request actually touches. Entries 1–8 (contract, rules, deliverable contract, refusal codes, the two `designer_base` harness docs, and the two decision trees) are read on every run.

---

## Step 3 — Execute the plan

Ten steps, in order: tool-boundary gate → runtime flavour and provisioning → UI layer → data and orchestration contract → rules, calculation and documents → failure behaviour and async → security → performance and caching (`standards/decision-trees/performance-tuning.md` Q16) → versioning, promotion, testing and localisation → audit-mode additions.

Capture every tool-call output for the envelope. In audit mode, retrieve the four OmniStudio metadata types and build the cross-component graph by parsing the retrieved JSON bodies — the Tooling API `MetadataComponentDependency` object returns no cross-component edges for OmniStudio, so an impact analysis built on it gives a false safe-to-delete signal.

---

## Step 4 — Deliver the output

Return the Output Contract per `agents/_shared/DELIVERABLE_CONTRACT.md`:

- Markdown report at `docs/reports/omnistudio-designer/<run_id>.md`
- JSON envelope at `docs/reports/omnistudio-designer/<run_id>.json`
- Chat: short confirmation + envelope JSON block

This agent is multi-dimensional. Every one of its ten dimensions must appear in `dimensions_compared[]` or `dimensions_skipped[]` — a dimension you could only count is `state: count-only`, not covered.

---

## Step 5 — Recommend follow-ups

- `/audit-lwc` when the journey embeds custom Lightning Web Component elements
- `/scan-security` when an Apex action's sharing context or a stored credential is the real exposure
- `/plan-release-train` when component promotion is ad hoc and needs a pipeline
- `/build-flow` when the tool-boundary gate concludes a layer belongs in Flow instead

---

## What this command does NOT do

- Does not deploy, activate, or deactivate anything, and does not run DataPack import/export or the `vlocity` CLI.
- Does not design Omni-Channel routing, queues, presence configuration, or agent capacity.
- Does not author LWC bundles or Apex classes — it specifies their contracts.
- Does not run design and audit in the same invocation.
