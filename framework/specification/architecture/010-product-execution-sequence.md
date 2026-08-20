# Product execution sequence

This sequence is shared by all products. Hosts may combine stages when they cannot isolate them, but every typed object and gate remains observable.

## Sequence

```text
1. Invoke command
2. Validate input
3. Attest targets and host capabilities
4. Create run and authority
5. Build run plan
6. Select context
7. Gather and normalize evidence
8. Checkpoint evidence-ready state
9. Diagnose or assess
10. Lint claims deterministically
11. Independently review evidence and policy
12. Resolve contradictions and status
13. Render output
14. Persist redacted replay bundle
15. Emit metrics and next safe actions
```

## 1. Invoke command

The user selects a product, not an implementation agent. The command parser produces a canonical input object and records the original request separately. Free text may help interpret intent, but it cannot bypass required arguments or target identity.

## 2. Validate input

Validate types, conditional requirements, file paths, page limits, supported modes, and disallowed combinations. Invalid input ends in `refused` for a user-correctable contract violation or `failed` for a runtime defect. No Salesforce access occurs first.

## 3. Attest targets and host capabilities

Resolve and record:

- host and version;
- model and context limits when exposed;
- supported plugin, skill, subagent, MCP, hook, compaction, and approval features;
- explicit Salesforce org alias/username and resolved org identity;
- explicit external project path or discovery result;
- requested fixture/job/test/snapshot identity.

Ambiguity is a first-class result. The framework never picks the first workspace project, any authorized org, or the most recent job silently.

## 4. Create run and authority

Create a run ID before tool access. Bind the run to one product version, authority profile, policy version, target identities, and initial status. Product authority defaults to `product-read-only` or `fixture-offline`.

## 5. Build run plan

The deterministic planner identifies required stages, eligible tools, evidence requirements, context pack, optional project enrichment, continuation limits, and stop conditions. It does not generate a broad autonomous workflow.

## 6. Select context

The context librarian receives product and evidence classes—not the full conversation. It returns an ordered manifest with reasons, costs, digests, and omissions. Required core items load first; only observed failure/decision classes trigger conditional references.

The default target is at most eight knowledge/reference files, with a hard ceiling of twelve. A hard overflow becomes explicit rather than silently loading more.

## 7. Gather and normalize evidence

The evidence broker validates each tool call, pins target identity, executes or delegates to an approved read-only upstream, normalizes version-varying fields, redacts secrets, bounds output, assigns IDs, and persists raw redacted evidence outside the prompt when possible.

Tool output is untrusted. Text fields may contain prompt injection and must never be treated as instructions.

## 8. Checkpoint evidence-ready state

Persist the run plan, identity, context manifest, evidence index, unresolved requirements, continuation cursors, and digest. This checkpoint is the rehydration source after compaction or interruption.

## 9. Diagnose or assess

The product agent receives bounded context and structured evidence. It emits typed facts, inferences, unknowns, contradictions, recommendations, and material claims. It does not render final polished prose first.

## 10. Deterministic claim lint

Reject or downgrade:

- material claims without valid support;
- missing evidence references;
- wrong target identities;
- stale or truncated evidence presented as complete;
- hidden contradictions;
- credential-secret evidence;
- unsupported confidence;
- unsafe recommendations.

## 11. Independent review

The evidence reviewer receives the claim graph, evidence index, product requirements, and draft output—but not the drafting transcript. It attempts to falsify root causes, identify omitted alternatives, challenge confidence, and detect unsafe advice.

The policy reviewer separately checks authority and recommendation language where consequences are high.

## 12. Resolve status

- `completed`: required evidence is sufficient, hard lints pass, independent review has no blocker.
- `partial`: useful output exists, but evidence is missing, stale, truncated, contradictory, or host-limited.
- `refused`: input/authority/target/safety conditions prohibit execution.
- `failed`: an unexpected system defect prevents a valid result.

## 13–15. Render, persist, measure

Render concise user output from validated objects. Save a redacted replay bundle according to retention policy. Record files/tokens, tool bytes, truncation, continuations, stage timing, reviewer changes, evidence validity, and terminal status.
