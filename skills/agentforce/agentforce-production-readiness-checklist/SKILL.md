---
name: agentforce-production-readiness-checklist
description: "An Agentforce agent is moving from build or sandbox to live end-user traffic and the team needs a comprehensive readiness gate: coverage testing, Trust Layer config, guardrails, cost telemetry, observability, rate limits, permissions, rollout strategy, rollback plan, performance benchmarks. Triggers: 'we want to ship our Agentforce agent next week', 'pre-prod readiness review for our Service Agent', 'what do we need before turning the agent on for real customers', 'agent went live and is hallucinating, what should we have caught', 'cost monitoring for our internal sales agent', 'rollout strategy from internal pilot to GA'. NOT for the lighter five-block activation sign-off artifact — use agentforce/agent-deployment-checklist. NOT for authoring the guardrails themselves — use agentforce/agentforce-guardrails. NOT for building the test harness — use agentforce/agentforce-eval-harness. NOT for Trust Layer feature setup in isolation — use agentforce/einstein-trust-layer."
category: agentforce
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Security
  - Operational Excellence
tags:
  - agentforce-production-readiness-checklist
  - production-readiness
  - go-live
  - rollout-strategy
  - rollback-plan
  - einstein-trust-layer
  - event-monitoring
  - cost-monitoring
  - performance-benchmarks
  - canary-rollout
triggers:
  - "we want to ship our Agentforce agent next week"
  - "what do we actually need to verify before our internal Service Agent goes to real customers"
  - "pre-prod readiness review for the agent we built — what's the comprehensive checklist"
  - "our agent went live and started hallucinating product details — what should we have caught in pre-prod"
  - "how do we set up cost / token monitoring before the agent gets broad rollout"
  - "we have no rollback plan for the agent if it goes wrong, what should it look like"
  - "how do we structure a canary rollout from 5 internal users to GA"
  - "what p95 latency target is reasonable for an Agentforce action and how do we benchmark before launch"
  - "we want Event Monitoring on every agent action invocation, what's the right approach"
inputs:
  - "Agent name, version, and target deployment channel(s) (in-app, Service Cloud, Experience Cloud, Slack, Messaging)"
  - "Persona: internal-only, customer-facing-authenticated, or customer-facing-unauthenticated"
  - "List of topics + actions configured (Apex, Flow, prompt templates, standard)"
  - "Expected user population size (pilot, broader, GA) and traffic estimate (sessions/day, peak hour)"
  - "Trust Layer policy decisions: data masking categories, audit log retention, content moderation thresholds"
  - "Existing observability stack: Event Monitoring license, Splunk/Datadog, Data Cloud connection"
  - "Apex actions and named credentials referenced by topics"
outputs:
  - "Filled-out readiness checklist with PASS/FAIL/WAIVED per item and waivers documented"
  - "Test plan: coverage list across topics × actions, with negative cases, edge cases, and adversarial probes"
  - "Trust Layer configuration spec: data masking rules, audit log retention, blocked categories"
  - "Performance benchmark report: action p50/p95/p99, agent reasoning loop latency, sessions tested"
  - "Rollout plan: canary user list, expansion criteria per stage, kill-switch + rollback runbook with named owner"
  - "Cost-monitoring spec: token-usage thresholds, alert routing, daily/weekly review owners"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-05-08
---

# Agentforce Production Readiness Checklist

Activate this skill when an Agentforce agent is moving from "build complete" to "live with real users" and the team needs a comprehensive technical gate, not a sign-off ritual. The deliverable is a checklist where every row has evidence (test results, screenshot, query output, dashboard link) — never just a tick.

This skill is the heavyweight pair to `agent-deployment-checklist`. Reach for `agent-deployment-checklist` when the team needs a five-block sign-off artifact for activation. Reach for *this* skill when the team needs to know *what they should have verified before they got to that sign-off*.

---

## Adoption Signals

Activate this skill when:

- A new agent is being moved from sandbox/build to its first cohort of real users (pilot, internal, customer pilot, or GA).
- A material config change is being made to a live agent: new topic added, new mutating action added, new channel turned on, persona class expanded, prompt template family revised, or Trust Layer policy changed.
- A post-incident review concluded with "we should have caught this in pre-prod" and the team is rebuilding the readiness gate.
- A leadership review is asking "is the agent ready" and the team has only a checkbox-style answer rather than evidence per row.
- Any agent that has been live for ≥90 days without a refreshed adversarial pass; the threat surface has drifted even if the agent metadata has not.

Do NOT use this skill for:

- The lighter five-block activation sign-off — use `agent-deployment-checklist`.
- Pure design-time guardrail authoring — use `agentforce-guardrails`.
- Pure test-harness construction — use `agentforce-eval-harness`.
- Trust Layer feature setup in isolation — use `einstein-trust-layer`.

---

## Before Starting

Gather this context before proposing changes:

- **What persona is the agent.** Internal-only employee agents, customer-facing authenticated agents (Experience Cloud, in-app for known users), and customer-facing unauthenticated agents (public Messaging, marketing-site chat) have very different readiness bars. The unauthenticated case requires the strictest rate-limiting, prompt-injection defense, and Trust Layer config — generic checklists that ignore persona produce false-pass.
- **What channel(s) the agent runs in.** Each surface (Service Cloud agent console, Experience Cloud, Slack, Mobile, Messaging, MCP/headless) brings its own context window, latency budget, and permission model. A canary on the Slack channel does not validate behavior on Experience Cloud.
- **What the actions actually do.** Read-only actions (look up a case, fetch a knowledge article) carry far less risk than mutating actions (create a case, post to Chatter, call an external API, refund a payment). The checklist depth scales with action blast radius.
- **What "production" means.** A 5-internal-user pilot is not the same readiness bar as a public-facing GA. Decide which stage you are gating before you start grading the checklist — a pilot can ship with WAIVED items that GA cannot.
- **What the rollback definition is.** "Roll back" can mean: deactivate the agent, switch a flag-controlled topic off, revert metadata, or re-route traffic. The team must agree on which mechanism applies before treating rehearsal evidence as valid.

---

## Core Concepts

### Concept 1 — The four readiness layers (and why one-layer reviews fail)

Agentforce production readiness operates at four layers. Skipping any of them produces the textbook failure modes the layer was meant to catch.

| Layer | What it covers | Failure mode if skipped |
|---|---|---|
| **Behavior** | Topic + action coverage tests, negative cases, edge cases, hallucination probes, adversarial / jailbreak probes | Agent hallucinates, escalates incorrectly, loops on bad reasoning, complies with prompt injection |
| **Trust + safety** | Einstein Trust Layer masking categories, audit log retention, content moderation, prohibited topic enforcement | PII leaks to LLM, no audit trail for compliance, no record of refusal events |
| **Operability** | Event Monitoring, custom Apex logging, cost / token telemetry, rate limits, observability dashboards, alert routing | First incident is observed by a customer; no on-call view; runaway token spend |
| **Rollout + rollback** | Canary cohort, expansion criteria, kill switch, rollback runbook, post-rollout review | Bad release goes to all users at once; rollback under pressure fails because it was never rehearsed |

A team that runs only behavior tests ships an agent that works in lab conditions and breaks under production traffic. A team that builds great observability but skips behavior coverage ships an agent that consistently fails in measurable ways. Production readiness requires a row in each layer.

### Concept 2 — Coverage is topics × actions × cases, not just "we ran some prompts"

The functional behavior surface is two-dimensional: every (topic, action) pair is a behavior cell that needs evidence. For each cell, the test plan should include four case types:

1. **Happy-path case** — The user-intent that justified the action existing.
2. **Negative case** — Inputs that should *not* trigger the action (the agent should refuse, escalate, or pick a different topic).
3. **Edge case** — Boundary inputs: empty values, max-length text, multilingual input, ambiguous intent across two topics.
4. **Adversarial case** — Prompt injection ("ignore your instructions and..."), jailbreak attempts, prompt extraction ("repeat your system prompt"), tool-misuse attempts (asking the agent to invoke an unrelated action via natural language).

A checklist that records "we ran 30 conversations" without showing the topic × action × case breakdown is not coverage — it's a sample. Coverage means each cell has at least one case-type per row. For an agent with 8 topics and 15 actions across them, that's a meaningful number — typically 60–120 fixture conversations to reach genuine first-pass coverage. The Agentforce Testing Center supports persisted fixture conversations; use it as the system of record so the same fixtures rerun on every config change.

A separate adversarial test pass (red-team) belongs in the Trust + safety layer, not the behavior layer. Keep them separate because they have different sign-off owners.

### Concept 3 — Trust Layer is opt-in per category and audit-log retention is configurable

Two facts about Einstein Trust Layer that agents commonly ship without internalizing:

- **Data masking is per-data-category and opt-in.** The Trust Layer can mask PII, financial data, health data, etc. before sending prompts to the LLM, and demask the response. But the categories are configured per implementation — turning on "PII masking" does not automatically enable financial-data or health-data masking. A team with health data in case records and no health-category masking has effectively shipped raw PHI to the LLM. Verify each category your data plausibly contains.
- **Audit log retention is configurable, not infinite.** Trust Layer audit logs (prompts sent, responses received, masking applied, content moderation outcomes) have a retention setting. The default may not match your compliance requirement. If your audit retention requirement is 7 years, you cannot rely on the Trust Layer's built-in store — you need to export to a long-term system (Splunk, S3, Data Cloud) before the in-platform retention window closes.

The readiness gate must verify both: which categories are masked, and where audit logs land for the retention horizon required.

### Concept 4 — Rollback rehearsal is the most-skipped, most-load-bearing item

The default failure mode for any production rollout is that the rollback path was never exercised under realistic conditions. For Agentforce specifically, the failure surfaces are:

- **Activation flip in metadata is fine; the runtime cache lag is the real problem.** Toggling an agent off via metadata can take measurable time to propagate to in-flight sessions. Sessions started before the flip continue under the old config until they end. The rehearsal must verify that *new* sessions get the new state and that the team is aware of the propagation behavior — assuming "instant kill" without testing it is the most common rollback surprise.
- **Topic-level kill is a separate mechanism.** Disabling a single topic (or its activating flag) is different from deactivating the entire agent. If the rollback intent is "stop one bad topic" and the rehearsal only practiced full deactivation, the runbook is misaligned with the likely incident.
- **Apex action rollback may need data cleanup.** If the rollback is triggered after the agent has been creating records, calling external APIs, or posting to Chatter, the data side may need a separate cleanup. The runbook must explicitly address whether rollback is *config-only* or *config + data cleanup* and who owns the data step.

Any readiness checklist that has a "rollback rehearsed" row but no evidence of staging exercise + named owner + propagation timing is checking a box, not closing a risk.

### Concept 5 — Cost monitoring, rate limits, and permissions are interlocking, not separate

Three separate-feeling concerns that fail together when one of them is skipped:

- **Cost / token monitoring** without rate limits: the alert fires but there's no enforcement lever. Spend has already happened by the time on-call sees the dashboard.
- **Rate limits** without persona-keying: the limit is wrong for at least one user class — either over-throttling internal users or under-throttling external ones.
- **Permissions** without action-level enforcement: a user can invoke the agent but the actions either fail at runtime (frustrating UX) or succeed with too-broad data scope (security exposure).

The readiness gate must verify all three together. Token usage thresholds tied to rate-limit policies tied to persona-keyed permission sets, with the alert thresholds derived from the rate-limit ceilings. A daily token-spend alert at 150% of expected is meaningful only when the team has set both the expected number (from forecast) and the rate-limit ceilings that would cap the worst-case overrun.

Concrete readiness questions to settle, in order:

1. What is the expected token spend per persona class per day? (Forecast from coverage tests × expected user volume × estimated tokens per session.)
2. What rate-limit ceiling per persona caps the worst-case multiplier on that expectation?
3. What permission set scopes which users can invoke the agent at all, and which Apex / objects / fields each persona can reach through the actions?
4. What dashboard alert fires at what threshold to flag drift from the expected?
5. Who is the named owner for the alert and what is their first response?

Skip any of these and the others lose meaning — a rate limit without expected spend is a guess, an expected spend without rate limits is a wish, a permission set without action-level checks is documentation.

### Concept 6 — Performance benchmarking needs realistic concurrency, not just functional pass

A common failure: the team measures action latency under single-user conditions, sees 800ms p95, marks the row PASS, and is then surprised when production shows 4-second p95 under realistic concurrency. The benchmarking row needs four specifics:

- **Concurrency level** matching expected production peak (sessions/sec or concurrent sessions).
- **Action mix** matching expected production traffic distribution (not just hit one action over and over).
- **Duration** long enough to expose downstream resource contention (cache pressure, database contention, external API rate-limit interactions) — typically ≥30 minutes.
- **Hardware-class** equivalence: production org tier, not a smaller scratch org.

Readiness rows for performance must capture: target p50/p95/p99 per action, end-to-end agent-loop p95, observed vs target with PASS/FAIL, and the configuration of the benchmark (concurrency, mix, duration). A row that says "p95 looked fine" without the configuration is not a benchmark.

---

## Common Patterns

### Pattern 1 — The two-tier instrumentation pattern

**When to use:** Every production agent. Always.

**How it works:** Instrument at two layers — the platform layer (Event Monitoring `EventLogFile` for the licensed events your edition exposes) and the action layer (custom Apex logging via a `Agent_Action_Log__c` object with session ID, action name, duration, outcome, error message). Correlate the two by session ID. The custom layer remains queryable via standard SOQL even if Event Monitoring is unavailable on a given user's permission set or the licensing tier changes. The platform layer is the source of truth for cross-feature audit (e.g. login + session + action correlation).

**Why not the alternative:** Relying purely on Event Monitoring fails if the license changes, the event types you need are tier-gated, or you need a custom field (e.g. business unit, persona class) that the standard event doesn't carry. Relying purely on a custom log loses the cross-feature audit you get from Event Monitoring. Two-tier is the only durable instrumentation under realistic Salesforce license dynamics.

### Pattern 2 — Topic-flag-controlled actions

**When to use:** Any mutating action where the readiness team wants a finer rollback than full-agent deactivation.

**How it works:** Each topic (or each high-blast-radius action) checks a Custom Metadata flag at entry. Action returns a graceful "temporarily unavailable" path when the flag is `false`. The flag is the kill-switch — a CMDT update propagates within seconds and can be flipped without redeploying code or metadata. The agent's entry-fall-back behavior is part of the topic's prompt (instruct the agent to escalate, not to retry, when the action returns the unavailable path).

**Why not the alternative:** Disabling the entire agent kills working topics along with the broken one. Removing the action from the topic requires a metadata redeploy, which is slow under incident pressure. CMDT-flagging is the right granularity for "stop just this thing without taking everything else down."

### Pattern 3 — Persona-keyed rate limits with limit-class testing

**When to use:** Any agent exposed to more than one user-class (e.g. internal employees + external customers, or trial-tier customers + paid-tier customers).

**How it works:** Each Apex action checks a per-persona quota at entry. Persona is derived from the calling user's permission set, profile, or a custom field. Quota counters live in Platform Cache or a custom object with a sliding-window key. Rate-limit hits return a "you've reached today's limit, escalate to a human" path that the agent surfaces gracefully. Testing must include a fixture conversation that exercises the boundary (the user's last allowed call, the first denied call, and the recovery on the next window).

**Why not the alternative:** A single org-wide rate limit either over-throttles internal employees (who should have higher quotas) or under-throttles external users (who can rack up costs in volume). Persona-keying is the right resolution. Boundary testing matters because the agent's *behavior at the limit* is what determines user experience under stress, not its behavior under nominal load.

---

## Decision Guidance

### Rollout-stage gate criteria

Each stage has a different acceptable readiness bar. Pick the stage being gated before grading anything.

| Stage | Bar |
|---|---|
| Pre-canary (staging only) | Coverage matrix complete; Trust Layer config drafted; runbook drafted; observability dashboards built; performance benchmark draft. WAIVED rows allowed with named owner and ETA. |
| Canary (≤ 50 internal users) | All matrix cells PASS at ≥95%; adversarial pass run by non-builder; Trust Layer per-category masking decided; rollback rehearsed once on staging; dashboards live; alerts firing in test mode; rate limits configured but not enforced (observe-only allowed). |
| Broader internal (≤ 1000 internal users) | Canary criteria + 5 consecutive business days of canary metrics within thresholds + zero P0 incidents during canary + alerts in enforce mode + on-call rota updated. |
| External pilot (authenticated customers) | Broader-internal criteria + named-credential audit complete + permission set tested under target persona + Trust Layer audit logs flow to long-term store + rate limits enforce-mode + customer-facing language reviewed by support. |
| GA (general availability) | External pilot criteria + 30 days of pilot metrics within thresholds + post-incident-review for every alert that fired + expansion-decision document signed by owner + security + on-call. Adversarial pass refreshed within last 30 days. |

### Apex action vs Flow action vs prompt template

| Need | Choice | Why |
|---|---|---|
| Deterministic side effect (create / update / call external) | Apex action | Transaction control, explicit error path, instrumentable |
| Read-only data fetch with simple shape | Flow action | Fast to build, admin-friendly; instrument via Flow logs |
| Summarize / classify / draft text from context | Prompt template | The LLM is doing the work; no platform action needed |
| Anything mutating with elevated blast radius | Apex action with CMDT flag | Combines pattern 2 above with deterministic control |
| Anything that returns sensitive data the LLM should NOT see in raw form | Apex action with Trust Layer masking applied | Mask at the action boundary, not after the LLM has it |

### Mechanism choice for each rollback type

| Incident type | Mechanism | Why this granularity |
|---|---|---|
| Single bad action | CMDT flag flip on that action | Smallest blast radius; in-flight sessions complete on the old config but new sessions hit the disabled path |
| Bad topic (multiple actions misbehaving on one topic) | Disable the topic in agent definition | Other topics keep working; targeted rather than full-agent kill |
| Prompt-template regression | Revert template version | Agent and topics stay live; only the affected behavior changes |
| Cross-topic systemic / hallucination wave | Deactivate agent | Broad blast radius is acceptable when the alternative is sustained user harm |
| Active exploit (jailbreak working at scale) | Channel-level disable + agent deactivation + named-credential revoke | Need to terminate fast; in-flight sessions are themselves the problem |

---

## Recommended Workflow

1. **Define the readiness target.** Pick the rollout stage being gated (canary, broader internal, customer pilot, GA). Each stage has a different acceptable bar — write the bar down before grading anything. A canary can ship with documented WAIVED items; a GA gate cannot.
2. **Build the coverage matrix.** Enumerate topics × actions × case types. Persist the fixture conversations in Agentforce Testing Center (or equivalent). Run the suite against the production-target metadata package, not against a stale sandbox. Record pass-rate per cell.
3. **Verify Trust Layer config and audit log destination.** For every data category your agent could plausibly process (PII, financial, health, IP), confirm masking is on or explicitly waived. Confirm audit logs flow to whatever long-term store satisfies your retention horizon. Capture screenshots / config exports as evidence.
4. **Stand up observability and cost telemetry before traffic.** Event Monitoring queries for agent invocations, custom Apex logging on each action's entry/exit/failure, dashboard with the four key metrics (sessions, escalation rate, action error rate, p95 latency), token-usage dashboard with daily threshold alert. The first incident must not be discovered by a user — it must be discovered by an alert.
5. **Benchmark performance against a target.** Measure action response p50/p95/p99 and end-to-end agent reasoning loop latency under realistic concurrency. Set a threshold (e.g. action p95 ≤ 3s, full-loop p95 ≤ 8s — your numbers will vary by use case) and gate the checklist on hitting it. If you don't have a number, you don't have a benchmark.
6. **Rehearse rollback in staging with a named owner.** Practice the actual rollback mechanism on the staged metadata. Time it. Document propagation lag. Confirm the team knows which mechanism applies to which incident type. Capture the run as a runbook with screenshots, named owner per step, and an estimated time-to-restore.
7. **Gate the rollout with explicit expansion criteria.** Don't just say "we'll watch it for a week." Write the expansion criteria as: "if [metric] stays under [threshold] for [duration] across [population], expand to next cohort." Make the criteria measurable from the dashboards built in step 4. Capture pre-defined rollback triggers (e.g. "if escalation rate > 30% sustained for 1 hour, kill-switch") so the on-call has decisions, not deliberation.

---

## Review Checklist

Run through these before marking an agent production-ready:

- [ ] Persona, channel(s), and target rollout stage explicitly recorded
- [ ] Coverage matrix complete: every topic × action × case-type cell has evidence (fixture link or test ID)
- [ ] Adversarial test pass executed by someone other than the builder; results reviewed with security
- [ ] Trust Layer masking verified per data category your data could plausibly contain
- [ ] Trust Layer audit logs land in a system that meets your retention horizon
- [ ] Event Monitoring queries / custom Apex logging in place for every action
- [ ] Dashboard live for sessions, escalation rate, action error rate, p95 latency
- [ ] Token / cost telemetry has a daily threshold alert routed to a named owner
- [ ] Performance benchmark hits the documented target (p50/p95/p99 captured)
- [ ] Rate limits configured per persona class and tested at the limit boundary
- [ ] Permissions verified: only intended user populations can invoke the agent; Apex actions enforce access; named credentials are scoped to least privilege
- [ ] Rollback rehearsed in staging with named owner and time-to-restore measured
- [ ] Rollout expansion criteria written, measurable from the dashboard, and reviewed by on-call
- [ ] Pre-defined rollback triggers (with thresholds and durations) recorded in the runbook
- [ ] Incident on-call rota updated to include the new agent

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Trust Layer masking categories are independent toggles, not a single switch** — Enabling one category does not enable the others. Audit each.
2. **Agent runtime cache means deactivation is not instant for in-flight sessions** — Plan the kill-switch behavior accordingly; rehearse it.
3. **Apex action descriptions feed the LLM's tool-selection reasoning** — A vague or default-templated action description leads the agent to pick the wrong action under ambiguous prompts. Action descriptions are part of the production interface; treat them like API contracts.
4. **Prompt template caching can cause stale instruction text after an update** — Test the propagation of prompt template edits; do not assume edits are live just because they're saved.
5. **Event Monitoring license tier gates which event types are accessible** — The events you need (e.g. agent invocation events) may sit behind Event Monitoring; verify license before promising the dashboard.
6. **Context window limits are real and consume tokens for system + topic + history** — High-cardinality topic graphs and verbose system instructions push history out of context, degrading multi-turn coherence on long sessions.
7. **The agent's choice between "answer directly" and "invoke an action" is reasoning-driven, not deterministic** — Prompts that look identical can route differently. Coverage tests must include paraphrases of the same intent, not just the canonical phrasing.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Readiness checklist (filled) | Markdown / spreadsheet with PASS/FAIL/WAIVED per item, evidence link, owner, date |
| Coverage test plan | Topic × action × case-type matrix with fixture conversation IDs, pass-rate per cell, adversarial pass evidence |
| Trust Layer config spec | Per-category masking decisions, audit log retention + destination, content moderation thresholds |
| Performance benchmark report | p50/p95/p99 numbers per action and end-to-end loop, concurrency tested, target threshold, pass/fail |
| Cost-monitoring spec | Token-usage dashboard link, daily / weekly threshold alerts, owner, escalation path |
| Rollback runbook | Step-by-step with named owners, propagation timing, decision table for incident-type → mechanism, time-to-restore |
| Rollout plan | Canary cohort list, expansion criteria per stage, pre-defined rollback triggers, on-call rota update record |

---

## Related Skills

- `agentforce/agent-deployment-checklist` — lighter sign-off ritual artifact; pair this skill with that one when the team needs both depth and the activation record
- `agentforce/agentforce-eval-harness` — the test harness layer; use to actually build and run the coverage matrix referenced in step 2
- `agentforce/agent-testing-and-evaluation` — broader testing strategy beyond go-live (regression, drift, ongoing eval)
- `agentforce/agentforce-guardrails` — design-time guardrail authoring (topic Scope, system instructions, action filters); upstream of the readiness check
- `agentforce/einstein-trust-layer` — feature-level Trust Layer configuration; deeper than the readiness verification covered here
- `agentforce/agentforce-observability` — Data Cloud session trace queries, deflection-rate dashboards; the data layer that powers step 4
- `agentforce/agentforce-cost-optimization` — token-spend reduction patterns; pair with cost-monitoring spec
- `agentforce/agent-rate-limit-strategy` — per-user / per-org throttling design; upstream of the rate-limit checklist row
- `agentforce/agent-security-review` — security-specific deep-dive; pair with adversarial testing pass
- `agentforce/agent-channel-deployment` — channel-specific go-live mechanics (Service Cloud, Slack, Experience Cloud)
