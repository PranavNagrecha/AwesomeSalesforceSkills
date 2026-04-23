# Retriever Design Template

## Topic

- Topic name:
- User questions it must answer (≥ 10):

## Fact Classification

| Fact | Instructional (in prompt) | Grounded (retriever) | Action-derived |
|---|---|---|---|
|   |   |   |   |

## Retrievers

| Retriever | Type (structured/vector/hybrid) | Source DMO / Index | Filter | k | Rerank |
|---|---|---|---|---|---|
|   |   |   |   |   |   |

## Sharing Enforcement

- Layer 1 (Data Cloud data space):
- Layer 2 (retriever filter passing user context):
- Layer 3 (response scrubbing, defensive only):

## Freshness SLA

- Documented max staleness:
- Ingestion cadence to meet it:
- Cache TTL:

## Citation Format

- Field(s) returned to agent:
- Response template:

## Sign-Off

- [ ] Every fact classified.
- [ ] Every retriever has a filter, k, and rerank decision.
- [ ] Sharing enforced at layer 2 (not only layer 3).
- [ ] Freshness SLA explicit.
- [ ] Citation format defined.
