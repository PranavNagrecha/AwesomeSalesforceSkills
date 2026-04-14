# Gotchas — API-Led Connectivity Architecture

Non-obvious behaviors that cause real production problems when designing API-led connectivity for Salesforce integrations.

## Gotcha 1: Three Tiers for Every Integration — Latency and Maintenance Multiplied Needlessly

**What happens:** Architects apply System + Process + Experience layers to every integration, including simple single-consumer pass-throughs. A read-only product catalog sync that could be one HTTP call instead traverses three API layers, three separate MuleSoft policies, and three separate network hops. Latency increases and three separate catalog entries, versioning policies, and monitoring dashboards are required — for an integration that has one consumer and no orchestration logic.

**When it occurs:** When architects follow the pattern prescriptively without evaluating whether all three layers provide value for a given integration. Often driven by governance mandates that say "all integrations must be three-tier" without documented exceptions.

**How to avoid:** Evaluate consumer count and orchestration complexity before assigning tiers. Single-consumer, no-orchestration integrations justify a System API only. Document the layer-skip decision in the Architecture Decision Log with a re-evaluation trigger (e.g., "if a second consumer is added, add an Experience API within 30 days"). The documentation is the governance artifact — not adding layers for its own sake.

---

## Gotcha 2: Rate Limits Designed Bottom-Up — Cascade Exhaustion at Peak Load

**What happens:** Rate limits are set on the System API based on the backend system's capacity, then Process and Experience APIs are configured to stay under that limit individually. At peak load, multiple Experience APIs all fire simultaneously and fan into the Process API, which fans into the System API. The combined request volume exceeds the System API limit even though each individual Experience API is within its own limit.

**When it occurs:** When rate limit design starts with the backend capacity constraint and works up, rather than starting with consumer traffic patterns and working down. Particularly acute when Agentforce agents are added as a consumer — agents can execute many concurrent tool calls during an autonomous task, generating burst traffic that was not anticipated in the original bottom-up rate limit design.

**How to avoid:** Always design rate limits top-down. Start with the Experience API consumer limit for each consumer type. Sum all Experience API limits that fan into the same Process API; add 20% headroom. That sum becomes the Process API rate limit. Repeat for System API. Then validate the resulting System API limit against the backend's published capacity. If the System API limit exceeds backend capacity, revise Experience API limits downward and re-validate.

---

## Gotcha 3: Salesforce Treated as Consumer-Only — Missing Salesforce System API

**What happens:** Integration architecture treats Salesforce purely as a consumer of external systems. When a downstream system (ERP, billing, warehouse) needs to read Salesforce data (e.g., account status, opportunity stage, contract terms), that system calls the Salesforce REST API directly using its own hardcoded credentials and schema assumptions. The ERP team owns and maintains a direct Salesforce API integration that no one in the integration team controls or monitors.

**When it occurs:** When the API-led design exercise is scoped as "Salesforce consuming external systems" rather than "integrating Salesforce into a two-way API ecosystem." Common in projects where the integration architect is embedded in the Salesforce team and designs only outbound integrations.

**How to avoid:** In the integration inventory step, explicitly identify all systems that need to READ from Salesforce, not only all systems that Salesforce needs to call. For any external system reading Salesforce data, design a Salesforce System API (e.g., `system-salesforce-accounts-api`) that abstracts the Salesforce REST API behind a stable contract. This prevents external systems from being broken by Salesforce schema changes (field renames, object restructuring) and centralizes Salesforce API credential management.

---

## Gotcha 4: No Deprecation Enforcement — Breaking Changes Deployed Without Warning

**What happens:** A Process API owner makes a breaking change (renames a field, removes an endpoint) and deploys it as a minor version bump. Experience API consumers that depend on the renamed field begin failing silently or with cryptic JSON parse errors. The deprecation timeline (90 days) was not enforced because it was documented in a spreadsheet rather than in the API Exchange catalog with an automated policy.

**When it occurs:** When governance is documented but not enforced at the tooling level. Exchange catalog entries that describe a deprecation policy but do not enforce it with an automated SLA policy or alert consumers directly.

**How to avoid:** Treat versioning policy enforcement as a tooling requirement, not a documentation exercise. Every MAJOR version bump must trigger: (1) an automated notification to all registered consumers of the old version, (2) a deprecation policy that rejects the old version after 90 days, (3) a migration guide published in Exchange before the old version is decommissioned. The 90-day window must be enforced by API policy, not by a manual process.
