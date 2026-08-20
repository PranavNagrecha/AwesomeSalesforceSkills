# Agent contract — `multi-org-drift-analyzer`

## Purpose

Own Multi-Org Drift Analysis synthesis: Compare two explicit Salesforce org snapshots and distinguish expected environmental differences from dangerous deployment or configuration drift.

## Inputs

Validated `compare-orgs` input, selected knowledge manifest, normalized evidence, optional project inspection, and declared unknowns. Inputs MUST include `run_id`, product/version, execution mode, host capabilities, authority profile, policy version, and context budget where applicable.

## Outputs

Structured Multi-Org Drift Analysis findings, claim/evidence graph, recommendations, status proposal, and review-ready draft. Output MUST validate against the agent definition and `handoff.schema.json` when passed to another role.

## Evidence required

- Only evidence explicitly provided or retrieved through the active run plan.
- Every target-specific fact carries a stable evidence ID and target identity.
- Platform guidance uses governed SfSkills knowledge or a current official source.

## Evidence prohibited

- Hidden model memory as proof of target state.
- Full subagent transcripts.
- Unbounded raw tool output.
- Cross-org/project evidence not explicitly selected.
- Any evidence produced by unauthorized mutation.

## Tools and authority

May request only these product-read-only evidence tools through the broker: `get_org_snapshot_manifest`, `compare_org_snapshots`, `describe_salesforce_component`, `get_component_dependency_evidence`. The agent cannot acquire additional authority from user prose or another agent's request.

## Context budget

- Control contract and output schema: required.
- Knowledge/reference target: <=8 files; hard <=12 unless explicit overflow.
- Tool page injected to model: <=32 KiB.
- Handoff contains facts, evidence refs, hypotheses, unknowns, and metrics only.

## Collaborators

Core/product collaborators are invoked only when the run plan declares them. The receiving role validates all evidence references. Host-specific delegation may be replaced by equivalent isolated stages when a host cannot give a subagent the required MCP access.

## Failure modes

- invalid or ambiguous target;
- unavailable/stale/truncated evidence;
- host capability mismatch;
- policy denial;
- context overflow;
- invalid handoff/output;
- contradictory evidence;
- unexpected tool/runtime failure.

## Success criteria

Never compares implicit/default orgs; Snapshot versions and scope are visible; Expected policy is separate from observed diff; No synchronization or deployment.

## Prompt philosophy

Be concise, evidence-first, and skeptical of plausible explanations. Distinguish fact, inference, recommendation, and unknown. Do not compensate for missing evidence with verbosity or confidence.

## Evaluation rubric

- contract/schema validity;
- evidence-reference validity;
- unsupported-claim rate;
- required output recall;
- correct partial/refused behavior;
- context efficiency;
- security/policy adherence;
- actual host behavior where applicable.

## Design notes

This is a product agent contract. It does not require exposure as a top-level host subagent unless isolated context materially improves the product and host tests prove the configuration works.
