# LLM Anti-Patterns — Agentforce Production Readiness Checklist

Common mistakes AI assistants make when generating or advising on a production-readiness review for an Agentforce agent. These patterns help the consuming agent self-check its own output before producing a checklist or rollout plan.

---

## Anti-Pattern 1: Producing a checklist with ticks but no evidence schema

**What the LLM generates:** A markdown checklist with rows like:

```
- [x] Tests passing
- [x] Trust Layer configured
- [x] Rollback plan in place
```

**Why it happens:** Generic "production readiness checklist" content in training data is mostly checklist-shaped, not evidence-shaped. The LLM autocompletes the checklist shape and stops.

**Correct pattern:** Each row must specify *what evidence makes it PASS*. Example structure:

```
| Item | Evidence required | Status | Owner | Link |
|---|---|---|---|---|
| Subagent × action coverage | Fixture IDs and pass-rate per cell | PASS (24/24) | Builder | [link to Testing Center fixture set] |
| Trust Layer masking per category | Config export listing each category's state | PASS | Security | [link to config export] |
| Rollback rehearsed | Staging run log with timing + named owner | PASS | On-call | [link to runbook] |
```

**Detection hint:** If the checklist has more rows with checkboxes than rows with linked artifacts, the output is theatre, not a gate.

---

## Anti-Pattern 2: Treating "we ran some prompts" as coverage

**What the LLM generates:** "We tested the agent with 30 representative prompts and all passed, so it's ready for production."

**Why it happens:** LLMs don't naturally generate the subagent × action × case-type matrix (subagents were called topics before April 2026); they generate plausible-sounding test counts.

**Correct pattern:** Coverage is two-dimensional (subagent × action) with at least four case types per cell (happy / negative / edge / adversarial). The output should always include the matrix or a reference to it. Without the matrix, "30 prompts tested" is a sample, not coverage.

**Detection hint:** No matrix, no enumeration of (subagent, action) pairs, no separation between adversarial cases and behavior cases.

---

## Anti-Pattern 3: Recommending a single rollback mechanism for all incident types

**What the LLM generates:** "If something goes wrong, deactivate the agent." End of rollback plan.

**Why it happens:** "Deactivate the agent" sounds like a complete answer and matches the shape of one-line rollback instructions in unrelated runbook content.

**Correct pattern:** Rollback is a decision table: incident-type → mechanism → owner → expected time-to-restore. Mutating-action incidents need data cleanup; subagent-only incidents need subagent-level kill; full-compromise needs full deactivation. Each branch must be rehearsed.

**Detection hint:** Rollback section has fewer than three distinct mechanisms, or no decision table mapping incident types to mechanisms.

---

## Anti-Pattern 4: Treating Einstein Trust Layer as a single switch

**What the LLM generates:** "Make sure Einstein Trust Layer is enabled before going to production."

**Why it happens:** Trust Layer is often described in marketing-shaped content as a single feature; LLMs autocomplete the single-feature framing.

**Correct pattern:** The recommendation must enumerate per-category masking decisions (PII, financial, health, IP, customer identifiers), audit log retention vs the team's compliance horizon, audit log destination if the in-platform retention is shorter than required, and content-moderation threshold per persona.

**Detection hint:** Trust Layer mentioned only at the level of "enable it"; no list of categories; no audit retention discussion.

---

## Anti-Pattern 5: Skipping rate limits, permissions, and named credentials because they "feel like ops, not readiness"

**What the LLM generates:** A readiness plan focused on testing and rollout without a permissions row, without a per-user/per-org rate-limit decision, and without naming the named credentials referenced by Apex actions.

**Why it happens:** LLMs trained on generic LLM-app readiness content often inherit a different operational model where these concerns sit elsewhere. In a Salesforce org, permission sets, rate limits, and named credentials are first-class production concerns and often the path through which an agent breaks or leaks.

**Correct pattern:** The readiness output explicitly addresses: (a) permission set covering exactly which users can invoke the agent and which Apex / objects / fields the actions touch, (b) per-user and per-org rate limits with tested boundary behavior, (c) named credential inventory with per-environment scoping and rotation cadence.

**Detection hint:** The plan does not mention permission sets, rate limits, or named credentials; or mentions them only generically without enumerating the agent's actual references.

---

## Anti-Pattern 6: Writing rollout expansion as "we'll watch it for a week" instead of measurable criteria

**What the LLM generates:** "Pilot for one week, then expand to broader audience if everything looks good."

**Why it happens:** Soft language is easy to autocomplete; hard criteria require commitment to specific thresholds.

**Correct pattern:** Expansion criteria must be measurable from the dashboards built in step 4 of the workflow. Example: "Expand from 50 reps to 500 reps when all of the following hold for 5 consecutive business days: action error rate <2% per action, escalation rate <20%, p95 action latency <3s, daily token spend within 110% of expected, zero P0 incidents." On-call should be able to evaluate the criteria from the dashboard without interpretation.

**Detection hint:** Words like "looks good," "stable," "no major issues" appear in the expansion criteria. No specific thresholds tied to specific dashboard panels.

---

## Anti-Pattern 7: Inventing Salesforce metadata API surface for agent objects

**What the LLM generates:** Confident references to non-existent metadata types or invented field names on real metadata types — e.g. claiming an attribute that doesn't exist, or describing the agent definition's metadata shape with the wrong precision.

**Why it happens:** Agent metadata API has evolved across releases (`Bot`, `BotVersion`, and more recent `GenAi*` types). Training data may snapshot one version; the LLM may compose fragments from multiple eras into a single confident-sounding answer.

**Correct pattern:** When advising on agent metadata, cite only what is verifiable in the local repo (`knowledge/imports/`) or in the linked official docs. If the team needs a precise field-by-field shape for their version, refer them to the live Metadata API Developer Guide rather than producing a possibly-stale answer. Mark version-bound claims as version-bound, not as universal.

**Detection hint:** The output describes specific metadata fields/attributes for agent definitions without citing the docs or specifying the version those fields apply to.
