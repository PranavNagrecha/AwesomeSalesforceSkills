# Salesforce Decision Analysis Gotchas

## A weighted matrix can legalize an impossible option

A high total score does not override missing licenses, unsupported metadata behavior, security policy, governor limits, or an unknown target environment. Apply hard gates before scoring.

## Release identity is evidence

Salesforce behavior, availability, and tooling change across releases. Record the release/API version used by each load-bearing claim. "Salesforce supports it" without a version or availability check is not a gate result.

## Org evidence and documentation answer different questions

Documentation can prove that a capability exists in the platform. It cannot prove that the target org has the license, feature activation, package version, data shape, permissions, or architectural ownership needed to use it.

## Equal weights are still a choice

Equal weights can be valid, but they are not neutral. They assert that every criterion contributes equally to the outcome. Record that rationale and test a plausible alternative weighting.

## Cost is frequently counted three times

Implementation effort, operational burden, and license cost are distinct. Avoid adding a fourth broad "complexity" criterion that duplicates all three.

## No-change is not zero cost

Score existing defects, manual work, compliance exposure, opportunity cost, and future migration cost. No-change can win, but only after its consequences are visible.

## A reversible experiment can still be dangerous

Scratch-org or pilot validation does not establish production approval. Protect customer data, isolate authority, define cleanup, and state what the experiment cannot prove.

## The ADR is not the analysis worksheet

The worksheet may change as evidence changes. An accepted ADR is frozen and records premises, consequences, and review triggers. Do not overwrite the ADR each time the matrix changes.
