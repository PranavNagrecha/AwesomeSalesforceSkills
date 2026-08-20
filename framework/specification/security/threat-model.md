# Threat model

## Assets

- Salesforce credentials, org identity, metadata, records, logs, and job results.
- Customer repositories and proprietary source.
- Skill/source integrity and benchmark labels.
- Product policies, adapters, generated plugins, and run bundles.
- User trust in diagnoses and recommended actions.

## Threat actors and failure sources

- Malicious user or repository content.
- Prompt injection embedded in Salesforce data, metadata, logs, or code comments.
- Compromised/upstream MCP tool or dependency.
- Model hallucination or instruction-following failure.
- Accidental wrong-org or wrong-project selection.
- Maintainer error in scenario truth or policy.
- Host capability differences and plugin drift.
- Insider or CI credential misuse.

## High-risk attack paths

1. Evidence text instructs the agent to ignore policy or call a mutating tool.
2. A plausible tool name bypasses a substring denylist.
3. `DEFAULT_TARGET_ORG` changes under the run and evidence crosses orgs.
4. A cached deployment/test ID is associated with a different org.
5. A local project symlink/path escapes allowed roots.
6. Long output hides truncation or drops contradictory evidence.
7. Compaction removes authority or target identity and the agent continues.
8. Scratch setup points to sandbox/production or cleanup fails.
9. Benchmark labels are edited to fit current output.
10. Review artifacts omit files while reports claim tests passed.

## Controls

- deny-by-default tool broker;
- explicit target attestation and revalidation;
- typed evidence objects and source digests;
- context checkpoints and target identity in every stage;
- independent deterministic evidence lint;
- isolated evidence reviewer;
- bounded output/pagination;
- secret classification/redaction/scanning;
- separate scratch setup authority;
- clean commit, Git bundle, logs, checksums, and offline review reconstruction;
- scenario label governance.

## Residual risk

No prompt, policy, or benchmark eliminates model error. The framework reduces and exposes error by limiting authority, grounding claims, preserving contradictions, and measuring behavior. Stable release claims must remain scoped to tested products, scenarios, hosts, models, and dates.
