# Confidence model

Confidence is a property of a claim, not the answer's tone.

## Inputs

- required evidence coverage;
- authority and directness;
- freshness;
- target identity certainty;
- truncation and sampling;
- contradictions;
- deterministic validation;
- independent reviewer outcome;
- scenario-specific historical reliability.

## Labels

- **High:** load-bearing claims have direct/authoritative evidence, target identity is certain, no blocking contradiction, and review passes.
- **Medium:** plausible and meaningfully supported, but one material dimension is indirect, incomplete, sampled, or mildly contradictory.
- **Low:** sparse/indirect evidence, unresolved contradiction, stale data, or a hypothesis that needs verification.

A low-confidence useful result can be `partial`. A high-confidence unsupported result is a defect.
