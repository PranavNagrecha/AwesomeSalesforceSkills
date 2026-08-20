# SFAEF-140 — Product quality and evaluation

## Evaluation layers

1. Schema and structure.
2. Routing and product selection.
3. Context selection and budget.
4. Tool policy and evidence normalization.
5. Claim/evidence validity.
6. Independent review behavior.
7. Required-finding outcome quality.
8. Host integration and usability.
9. Real Salesforce behavioral qualification.
10. Regression and version drift.

## Requirements

SFAEF-140-001. CI gates MUST be deterministic and credential-free unless explicitly run in a protected environment.

SFAEF-140-002. Model-based judging MUST not be the sole gate for safety, evidence validity, required facts, or schema compliance.

SFAEF-140-003. Known-truth labels MUST be versioned, reviewable, and independent of the prompt being evaluated.

SFAEF-140-004. Scenarios MUST score required finding recall, unsupported claim rate, evidence-reference validity, harmful recommendation rate, status correctness, and context efficiency.

SFAEF-140-005. Exact prose matching SHOULD NOT be the primary behavioral criterion.

SFAEF-140-006. Every reported quality number MUST include dataset/scenario version, sample size, run date, host/model version, scoring method, and confidence/uncertainty where appropriate.

SFAEF-140-007. Flagship products MUST be compared with the same host/model without SfSkills.

SFAEF-140-008. Tests MUST include missing evidence, contradictory evidence, stale evidence, malformed upstream data, auth failure, target mismatch, secret-shaped data, and unsafe requests.

SFAEF-140-009. Reviewer tests MUST include deliberately persuasive but unsupported drafts.

## Release thresholds

Initial release thresholds are defined in `qa/release-thresholds.json`. P0 criteria include:

- zero product mutation;
- zero accepted material unsupported claims in the release scenario set;
- valid evidence references for at least 98% of material claims;
- explicit status correctness for all hard missing/unsafe cases;
- all deterministic gates passing;
- actual host smoke tests for shipped adapters.

Thresholds may be tightened with evidence. They must not be weakened solely to make a release pass.
