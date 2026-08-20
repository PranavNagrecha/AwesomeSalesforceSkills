# Context lifecycle

## Why this is a product subsystem

SfSkills already reduces startup discovery cost through routers. V2 must also prevent execution-time context rot: broad mandatory reads, noisy tool results, repeated transcripts, long conversations, and compaction that preserves plausible summaries but drops exact evidence or authority.

## Lifecycle

```text
Discover metadata
  -> classify task/evidence
  -> select core context
  -> add conditional packs
  -> bound evidence pages
  -> execute isolated stage
  -> emit structured handoff
  -> checkpoint durable state
  -> release stage context
  -> rehydrate only what next stage requires
```

## Budgets

Default product policy:

- three to five core knowledge/reference files;
- target total at most eight;
- hard total at most twelve;
- single model-visible tool page at most 32 KiB;
- reserve at least 15% of available context for output/review;
- no complete transcript handoff.

Products may tighten these values. Raising them requires an evidence-backed ADR and context-quality comparison.

## Selection

Every context item records ID, type, source, reason, required/conditional status, priority, estimated tokens/bytes, digest, conflicts, and stage. Selection is deterministic after relevance/classification inputs. Duplicates are removed by canonical ID/digest.

The context librarian does not diagnose. It chooses the smallest relevant set and reports omitted candidates. Product agents may request another pack only through the run plan and remaining budget.

## Structured handoff

A handoff contains:

- `run_id` and task/stage;
- facts and evidence references;
- hypotheses clearly marked;
- unknowns and contradictions;
- recommendation for the next stage;
- context/tool metrics;
- no hidden reasoning or full transcript.

The receiver validates all evidence references rather than trusting the sender.

## Compaction

Host compaction is observed when possible; it is not trusted to preserve product state. Before a likely compaction boundary, checkpoint:

- product/run/version/authority;
- exact target identities;
- state and next allowed transitions;
- context manifest and digests;
- evidence index and continuation cursors;
- claim graph and open blockers;
- policy/reviewer results;
- unresolved user decisions.

After compaction, the run resumer validates checkpoint version/digests, reattests mutable targets when needed, and rehydrates a bounded stage context. It never summarizes from memory alone.

## Second-task isolation

A new user job creates a new run by default. It may reference prior evidence only through an explicit replay/import action and target compatibility check. Old task context, org identity, project path, and hypotheses do not leak into the next run.

## Context QA

Test distractor skills, broad candidate sets, duplicate guidance, conflicting references, huge evidence, multiple pages, long first task followed by a second task, compaction/resume, missing checkpoint, changed project, changed default org, and reviewer independence.
