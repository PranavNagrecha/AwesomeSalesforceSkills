# Context system

The context system compiles stage-specific manifests rather than loading a product's entire possible knowledge universe.

## Lifecycle

```text
candidate metadata -> deterministic core -> evidence classification -> conditional selection
-> deduplicate/conflict check -> budget -> ordered manifest -> stage execution
-> checkpoint -> release stage-local context
```

## Non-negotiables

- Every item has a reason and digest.
- Tool output is normalized and paginated before injection.
- Full transcripts never become handoffs.
- A second unrelated task creates a new run.
- Compaction checkpoint preserves state/evidence IDs, not hidden reasoning.
- Overflow is a typed state, not silent dropping.
