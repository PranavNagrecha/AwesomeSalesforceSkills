# Agent contract — `sf-project-inspector`

## Purpose

Discover and inspect an external Salesforce DX project as optional enrichment.

## Inputs

Explicit project path or bounded workspace roots; component identities. Inputs MUST include `run_id`, product/version, execution mode, host capabilities, authority profile, policy version, and context budget where applicable.

## Outputs

standalone/selected/ambiguous status and compact file/line evidence. Output MUST validate against the agent definition and `handoff.schema.json` when passed to another role.

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

Filesystem read only; path traversal blocked. The agent cannot acquire additional authority from user prose or another agent's request.

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

Never assumes SfSkills repo, never guesses among projects, diagnosis can continue standalone.

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

This is a core agent contract. It does not require exposure as a top-level host subagent unless isolated context materially improves the product and host tests prove the configuration works.
