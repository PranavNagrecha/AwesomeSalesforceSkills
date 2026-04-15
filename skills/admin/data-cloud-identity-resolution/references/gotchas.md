# Gotchas — Data Cloud Identity Resolution

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Hard 2-Ruleset Org Limit Counts the Starter Data Bundle Auto-Created Ruleset

**What happens:** When the Starter Data Bundle is provisioned in a Data Cloud org, Data Cloud automatically creates one identity resolution ruleset. This consumes one of the two available ruleset slots at the org level. Practitioners who are unaware of this arrive at the Identity Resolution setup page expecting two free slots, find only one, and sometimes mistakenly believe their permissions are insufficient or that a bug has occurred.

**When it occurs:** Any org that has provisioned the Starter Data Bundle. This includes trial orgs, partner developer orgs with the Starter Data Bundle enabled, and production orgs that activated the bundle during initial Data Cloud provisioning.

**How to avoid:** Before planning any identity resolution configuration, navigate to Data Cloud Setup > Identity Resolution and count the existing rulesets. If one already exists from the Starter Data Bundle, document this constraint in the architecture decision record. If both BU stakeholders require a separate ruleset configuration, escalate to architecture review immediately — the only resolutions are: (a) share one ruleset across BUs, (b) use separate Data Cloud orgs, or (c) use separate data spaces within the same org with a shared ruleset. There is no support-escalation path to raise the limit.

---

## Gotcha 2: Fuzzy Match Is Silently Skipped in Real-Time Resolution

**What happens:** A ruleset containing a Fuzzy match rule on Individual > First Name behaves differently depending on whether it is triggered by a batch scheduled run or a real-time event. During real-time resolution (triggered by a new ingestion event), only Exact and Exact Normalized match methods are evaluated. The Fuzzy rule is silently skipped. Downstream consumers (segments, activations, Agentforce grounding) may therefore see a Unified Individual count that differs depending on when the resolution was last run and whether the most recent run was batch or real-time.

**When it occurs:** Any ruleset that includes a Fuzzy match rule and is expected to produce consistent resolution results in both batch and real-time contexts. It also occurs when an admin adds a Fuzzy rule to a ruleset that was originally designed for real-time use, without realizing the real-time path ignores it.

**How to avoid:** Explicitly document in the ruleset's design specification which match rules are batch-only. If the use case requires real-time resolution fidelity (e.g., a next-best-action agent that fires within minutes of a customer event), remove or bypass Fuzzy rules. Use Compound rules with Exact fields to achieve name-similarity matching in a real-time-safe way. When Fuzzy is genuinely needed for batch quality, accept that real-time clusters will be a subset of batch clusters and design downstream logic accordingly.

---

## Gotcha 3: Changing a Reconciliation Rule Forces a Full Cluster Re-Run, Not an Incremental Update

**What happens:** When a reconciliation rule is modified on a ruleset that has already run and produced Unified Individual clusters, Data Cloud does not incrementally update the affected attributes in existing clusters. Instead, the platform marks the entire ruleset as needing a full re-run. On the next scheduled or manual run, all clusters are recomputed from scratch. This process can take hours for orgs with large data volumes. During the re-run window, any downstream process (segmentation, activation, data action) that reads Unified Individual attributes receives the pre-change values, potentially causing stale or inconsistent behavior.

**When it occurs:** Any time a reconciliation rule setting is changed — switching from Most Recent to Source Priority, reordering source priority ranks, or switching the target field. Also occurs if match rules are added or removed, since the cluster membership must be recomputed.

**How to avoid:** Treat reconciliation rule changes as a scheduled maintenance operation. Communicate the expected re-run duration to all downstream teams before making the change. Schedule the change during a low-traffic window (typically late night or weekend). For large orgs, estimate the re-run duration by timing the most recent scheduled run. Do not make reconciliation rule changes during campaign launch windows or periods when near-real-time segments are being actively evaluated.

---

## Gotcha 4: Ruleset 4-Character ID Is Permanently Locked After Creation

**What happens:** When a new identity resolution ruleset is created, the admin assigns a 4-character alphanumeric ID. This ID is embedded in the platform's internal references and cannot be changed after the ruleset is saved. If the ID was chosen arbitrarily (e.g., `TEST` or `TMP1`), those characters become the permanent identifier for that ruleset in all downstream references, API calls, activation targets, and Data Cloud configuration exports.

**When it occurs:** Most commonly during initial configuration when an admin creates a "quick test" ruleset without treating the ID as permanent, or when a naming convention is established after some rulesets have already been created.

**How to avoid:** Define the ruleset ID naming convention before creating any rulesets. A useful pattern is a 4-character abbreviation reflecting the primary match attribute and org/BU context (e.g., `EMLP` for email-primary, `PHNC` for phone-compound). Document the chosen IDs in the org's architecture decision record before creating the rulesets. If a poorly-named ruleset already exists and the slot must be reclaimed, delete the ruleset, update all downstream references, then recreate with the correct ID — accepting that the prior ID cannot be reused.

---

## Gotcha 5: Manual Run Frequency Is Capped at 4 Per 24-Hour Period Per Ruleset

**What happens:** Data Cloud enforces a limit of 4 manual identity resolution runs per ruleset within any rolling 24-hour window. The 5th and subsequent manual run attempts within that window fail silently or return an error in the UI without a clear explanation. Automated scheduled runs (set via the ruleset's run schedule configuration) do not count against this limit. However, practitioners who rely on manual runs during iterative configuration testing can exhaust the limit within a few hours of active work.

**When it occurs:** During initial ruleset configuration and testing phases when a practitioner makes several configuration changes and manually triggers runs to validate each one. Also during incident response when a practitioner attempts to force a re-run multiple times to diagnose a cluster quality issue.

**How to avoid:** Plan configuration testing iterations to stay within the 4-run limit. Space out manual runs by at least 6 hours if more than 4 runs are needed in a day. During incident response, remember that if a manual run is failing silently, the cause may be the frequency cap rather than a configuration error. Check the run history and timestamps before concluding that the ruleset itself is broken.
