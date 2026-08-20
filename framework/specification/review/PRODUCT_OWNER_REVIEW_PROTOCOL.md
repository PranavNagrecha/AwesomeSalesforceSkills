# Product-owner review protocol

## Review objective

Determine whether the implementation delivers the specified user job safely and reproducibly. Do not accept a milestone because the diff is large, tests are green on mocks, or a report is persuasive.

## Review order

### 1. Artifact integrity

- Validate ZIP structure and checksums.
- Verify the Git bundle and offline reconstruction.
- Compare tree digest with source archive.
- Confirm branch, baseline, head, local commits/tags, and clean status.
- Confirm secret scan and sanitized evidence.

A package that cannot reconstruct the reviewed code is rejected before architecture review.

### 2. Scope and milestone truth

- Identify the exact milestone and applicable requirement set.
- Check that later-phase files are not being used to claim an earlier clean range.
- Distinguish implemented, partial, blocked, not run, and deferred.
- Reject placeholder products or reports that claim behavior without execution.

### 3. Product behavior

Run the credential-free fixture path from a clean reconstruction. Inspect command discovery, input validation, standalone/project/live behavior, statuses, output, and replay. Evaluate whether the result resolves the user job rather than merely restating evidence.

### 4. Architecture conformance

Trace the product through typed input, target attestation, run/state, context, evidence broker, product agent, deterministic lint, independent review, renderer, and bundle. Review deviations and ADRs.

### 5. Context quality

Inspect selected files, reasons, costs, omitted candidates, tool bytes, truncation, checkpoints, compaction/resume, and second-task tests. A hard limit passing while the selected context is irrelevant is still a defect.

### 6. Evidence and claims

Resolve every material claim to evidence. Check target/time/source compatibility, directness, contradiction handling, confidence rationale, and unknowns. Seed or inspect an unsupported persuasive claim and verify the reviewer catches it.

### 7. Safety and authority

Review product tool allowlist, unknown-tool deny, parsed shell policy, target identity, host enforcement matrix, prompt injection, secrets, path traversal, and customer-org mutation. Verify scratch authority is separate and guarded.

### 8. QA truth

Separate deterministic fixtures, actual Cursor host smoke, live read-only org checks, and scratch known truth. Inspect exact logs and scenario grades. No lane substitutes for another.

### 9. Regression and compatibility

Run existing repository tests, plugin/export drift checks, MCP tests, legacy path, and V2 tests from the reconstructed tree. Determine whether failures existed at baseline.

### 10. Market/product readiness

Inspect first-fifteen-minute UX, limitations, docs, comparison to vanilla/raw evidence, actual user metrics if available, and qualification label. Do not accept broad claims based on scenario-only results.

## Decision

- **Accept:** no blocker; all required gates/evidence present; limitations truthful.
- **Accept with follow-up:** no safety/product-truth blocker; bounded P2/P3 debt recorded.
- **Changes requested:** implementation direction is sound but one or more P0/P1 blockers remain.
- **Reject/rework:** architecture or scope fundamentally violates the product contract.
- **Blocked:** external host/credential/platform condition prevents the milestone; artifact proves the blocker honestly.

## Review output

The review report contains:

1. decision and qualification;
2. product/user-job verdict;
3. P0/P1/P2 findings with requirement IDs;
4. architecture and safety verdict;
5. context/evidence/QA measurements;
6. exact unrun items;
7. preserved strengths;
8. required correction scope;
9. next return-ZIP requirements.
