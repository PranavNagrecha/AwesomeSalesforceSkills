# Gotchas — Agentforce Production Readiness Checklist

Non-obvious Agentforce platform behaviors that bite teams during pre-prod readiness review and the first weeks after rollout.

---

## Gotcha 1: Einstein Trust Layer data masking is opt-in per category, not a single switch

**What happens:** A team enables Trust Layer with the assumption that it now masks "PII" everywhere. In production, financial data and health-related strings still flow to the LLM unmasked because those categories were never enabled.

**When it occurs:** Any time the team treats "Trust Layer is on" as a binary instead of auditing each category. Often surfaces in compliance reviews after launch.

**How to avoid:** Enumerate the data categories the agent will plausibly process (PII, financial, health, IP, customer-identifiers-as-secondary-keys), and confirm the masking decision per category — either *masked* with rationale, or *intentionally unmasked* with a documented business justification. Make this a mandatory readiness row, not a checkbox.

---

## Gotcha 2: The agent's choice between answering directly and invoking an action is reasoning-driven and non-deterministic across paraphrases

**What happens:** During build, "show me the case status of 12345" routes correctly to `GetCaseStatus`. In production, "what's going on with case 12345?" sometimes routes to a different topic, sometimes answers directly from the LLM with hallucinated content, and sometimes correctly invokes the action — across visually similar prompts.

**When it occurs:** Topic and action descriptions are too generic, or two topics have overlapping scope language, or the system instructions don't strongly disambiguate. The LLM picks based on the closest semantic match it sees in its tool list at each turn.

**How to avoid:** Treat action and topic descriptions as production interface contracts. Tighten them so each has a clearly distinguishing scope phrase the LLM can latch on to. Test paraphrases of the same intent in the coverage matrix — three to five paraphrase variants per happy-path case, not just the canonical phrasing.

---

## Gotcha 3: Action chaining can loop when an action's result reads ambiguous to the agent

**What happens:** The agent invokes an action, the action returns a partial result, the agent re-reasons and invokes the *same or related* action again, accumulating turns and tokens until either the context runs out or a turn limit is hit. Final outcome to the user: long latency, silently dropped or escalated, unexplained token spike.

**When it occurs:** Apex actions return success messages that don't clearly state the action is *complete and final*, or return ambiguous "see partial results" payloads that look to the LLM like an invitation to retry. Most likely on data-fetch actions where the result is empty or sparse — the agent reasons "maybe I should try again with different parameters."

**How to avoid:** Action result payloads must explicitly state the action's terminal state. Empty results should say "no records found — do not retry with the same parameters." Add per-session turn caps and per-action invocation caps in the operability layer; alert when the cap is hit. In the readiness review, pick three actions whose results could be ambiguous and verify the agent does not loop on them.

---

## Gotcha 4: Prompt template caching can serve stale instruction text after an update

**What happens:** Team updates a prompt template to fix a behavior. Tests in build show the new behavior. Production traffic keeps showing the old behavior for some time afterward.

**When it occurs:** Prompt template references are cached at the runtime layer; an edit and save does not always immediately propagate to the agent's runtime config across all in-flight sessions. New sessions may pick up the new template; in-flight sessions complete on the old.

**How to avoid:** Verify propagation behavior in staging with a small fixture before assuming the production change is live. Tag prompt template versions in metadata and include the version in your custom action logging so you can correlate "session showed old behavior" with "session ran on template v7 vs v8." Treat prompt template edits as deploys — they change behavior at scale and need the same review rigor.

---

## Gotcha 5: Context window spent on system + topic catalog + history degrades multi-turn coherence on long sessions

**What happens:** The agent answers correctly for the first few turns, then mid-session starts losing the thread — forgetting earlier user-provided details, rerunning lookups it already did, or contradicting earlier answers.

**When it occurs:** The agent has a high-cardinality topic graph (many topics, each with rich descriptions) and verbose system instructions, leaving little context budget for actual conversation history. Long sessions push the earliest turns out of context.

**How to avoid:** During readiness review, run a fixed-length stress test (e.g. 20-turn fixture) and verify coherence at turn 15 and turn 20, not just turn 3. Trim topic descriptions to the minimum that still disambiguates. Compress system instructions. If you cannot fit topics + history into the budget, split the agent into multiple smaller agents with topic-domain handoffs rather than one giant agent.

---

## Gotcha 6: Apex action permissions are checked at action invocation, not at agent permission

**What happens:** A user is granted access to the agent. They ask a question that routes to an action whose backing Apex class they don't have access to. The action throws a permission error, the agent surfaces a generic "I couldn't complete that" — and the team thinks the agent is broken.

**When it occurs:** Permission set for the agent's user population includes the agent itself but not all the Apex classes its actions reference (or all the objects/fields the actions read/write). Easy to miss when the agent is built and tested as System Admin.

**How to avoid:** Build a permission set that explicitly grants every Apex class, every object, and every field the agent's actions touch. Test the agent under a non-admin user that has *only* this permission set, not as the builder. Add a readiness row that says "agent tested under target-persona permission set, not admin."

---

## Gotcha 7: Named credentials referenced by Apex actions need explicit per-environment configuration and least-privilege scoping

**What happens:** Agent works in sandbox because the named credential there points to a permissive dev endpoint. In production, the named credential is unset or points to prod with broader scope than needed, and either the action fails on first call or it succeeds with too-broad permissions.

**When it occurs:** Named credentials are environment-bound metadata, easy to forget to migrate or scope. Sandbox refresh can also reset them.

**How to avoid:** Inventory every named credential cited by any Apex action. For each, document: source endpoint (per environment), authentication mechanism (least-privilege OAuth scope or service-account permissions, never broad admin tokens), and rotation cadence. Add this inventory to the readiness checklist with a row per named credential.

---

## Gotcha 8: Agentforce activation toggling does not instantly drain in-flight sessions

**What happens:** Incident detected, on-call deactivates the agent. The team assumes new and existing sessions all stop. In fact, in-flight sessions complete under the old config; the deactivation only affects *new* sessions starting after the cache propagation completes.

**When it occurs:** Any rollback action that relies on a single metadata flip. Especially confusing under incident pressure when the team expects "kill switch" to mean "instant kill."

**How to avoid:** Document the propagation timing observed during rehearsal in the runbook. Brief on-call: "deactivation stops new sessions, not in-flight." If the incident class genuinely requires in-flight termination (e.g. the agent is leaking PII *right now* to a connected user), the runbook needs a higher-blast-radius mechanism (channel-level disable, named-credential revoke) — and that mechanism also needs to be rehearsed.
