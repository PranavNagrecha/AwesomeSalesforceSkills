# Data and control flow

The framework communicates through typed objects. Natural language is content inside those objects, not the control protocol.

## Core objects

| Object | Created by | Consumed by | Purpose |
|---|---|---|---|
| Product definition | maintainer | router/runtime/adapters | user job, modes, agents, tools, evidence, gates |
| Command input | host adapter | preflight | typed invocation and explicit targets |
| Host capability | adapter smoke/preflight | planner/policy | actual enforceable host features |
| Run | runtime | every stage | identity, product, authority, versions, state |
| Run plan | deterministic planner | context/evidence/agents | required stages and bounds |
| Context manifest | context compiler | model stage/replay | selected files, reasons, cost, omissions |
| Evidence | broker/fixture/project inspector | product agent/reviewer | normalized observation with provenance |
| Handoff | agent stage | next stage | bounded facts, refs, hypotheses, unknowns, metrics |
| Claim | product agent | lint/reviewer/renderer | material fact/inference/recommendation/unknown |
| Review result | deterministic lint/reviewer | status resolver | blockers, downgrades, edits, unresolved risks |
| Output envelope | runtime | user/integrations | terminal status and artifact references |
| QA result | grader | release gate | known-truth and safety metrics |

## Control flow versus evidence flow

Control objects determine what may happen. Evidence objects describe what was observed. A Salesforce log line, source comment, or metadata description can never modify control flow directly.

```text
User prose ---------------------------> interpreted intent
Typed command ------------------------> control
Policy + authority -------------------> control
Host capability ----------------------> control
Evidence text ------------------------> untrusted observation
Skill content ------------------------> advisory knowledge
Model draft --------------------------> untrusted proposed claims
Validated claim graph ----------------> product result
```

## Identity propagation

Every target-specific evidence item carries the applicable target identity:

- Salesforce org ID/alias resolution and observation time;
- deployment/test/snapshot identifier;
- local project canonical path and digest;
- host/session/run identity;
- upstream tool and version.

Every handoff and checkpoint includes `run_id`. A downstream stage must reject evidence from another run or target unless an explicit comparison product authorizes it.

## Provenance precedence

For a target-state question, direct current observation outranks captured target observation, which outranks deterministic local source for deployed state, which outranks governed platform guidance, which outranks model inference. Different evidence can answer different dimensions and must not be collapsed into one total order.

For example, a local metadata file proves local source content; it does not prove deployment to the selected org. A deployment result proves a job response; it does not prove a proposed fix is safe. A skill explains platform behavior; it does not prove a profile is assigned to the user.

## Pagination and raw retention

The broker stores raw redacted evidence outside model context where policy permits. It gives the model bounded normalized pages with source counts, cursors, truncation flags, and digests. A summary never destroys the ability to resolve the evidence ID back to the retained observation.

## Errors

Errors are typed as input, authentication, target mismatch, unavailable, timeout, rate/limit, malformed upstream, policy denial, context overflow, schema failure, reviewer blocker, or unexpected. The final status resolver translates these into an honest terminal state and user action.
