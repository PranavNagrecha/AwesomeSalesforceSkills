# LLM Anti-Patterns

Use these patterns during self-review. Each entry names the tempting failure, why a language model tends to produce it, and the correction required by this skill.

## 1. Favorite-first option design

**Mistake:** Develop one preferred option in detail, then add two vague alternatives to make the comparison look complete.

**Why it happens:** The prompt often contains a suggested solution, so the model anchors on it and treats alternatives as rhetorical contrast.

**Correct form:** Define the measurable outcome and hard gates first. Build at least two options a competent Salesforce team could actually choose, including standard, reuse, sequence, or no-change when credible. Give every option comparable scope and evidence.

## 2. Score without evidence

**Mistake:** Fill a 1–5 matrix from general platform familiarity and present the totals as findings.

**Why it happens:** A numeric table looks rigorous even when the underlying claims are assumptions.

**Correct form:** Attach an evidence ID and uncertainty state to every score. Unsupported criteria remain `UNKNOWN`, receive a conservative treatment, and create a validation action.

## 3. Fake precision

**Mistake:** Report totals such as 4.37 versus 4.31 when the inputs are qualitative judgments.

**Why it happens:** Arithmetic creates an illusion that the decision is more certain than the evidence.

**Correct form:** Use defined integer anchors, round transparently, show ranges where appropriate, and run sensitivity tests. When the ranking is fragile, return `experiment` or `conditional-recommend` rather than a false winner.

## 4. Hard-gate averaging

**Mistake:** Allow cost, speed, or user preference to compensate for a failed license, security, authority, platform, or rollback gate.

**Why it happens:** Weighted matrices encourage every concern to be reduced to one comparable score.

**Correct form:** Evaluate gates before scoring. `FAIL` eliminates the option; `UNKNOWN` keeps it provisional and caps confidence. Never average away a prohibition.

## 5. Documentation-as-entitlement

**Mistake:** Treat a Salesforce product page as proof that the target org owns, enables, or permits the capability.

**Why it happens:** Official documentation is authoritative about platform behavior, but not about a particular customer's contract or configuration.

**Correct form:** Separate platform availability from target-org evidence. Verify edition, add-on, licenses, feature activation, permissions, package version, and environment identity when they are load-bearing.

## 6. Decision-tree avoidance

**Mistake:** Create a generic matrix for a choice already governed by a canonical repository decision tree.

**Why it happens:** A fresh table feels customized and lets the model ignore branch conditions.

**Correct form:** Search the decision-tree layer first, cite the exact branch, and use this skill only for the residual cross-cutting choice or when multiple viable branches remain.

## 7. Universal weights

**Mistake:** Reuse the same weighting scheme for every organization, risk profile, and business outcome.

**Why it happens:** Default weights save effort and make packets look comparable.

**Correct form:** Tie each weight to the declared outcome and identify the weight owner. Proposed weights must be labeled unapproved and tested against plausible alternatives.

## 8. Hidden unknowns

**Mistake:** Give missing evidence a neutral score, omit it from the packet, or quietly fill it from memory.

**Why it happens:** A complete matrix is aesthetically preferable to an incomplete one.

**Correct form:** Record `unknown`, explain the confidence impact, and state the smallest evidence request or experiment that resolves it. Unknown is a result, not a formatting defect.

## 9. Sensitivity theater

**Mistake:** Change weights by trivial amounts that cannot challenge the preferred option, then declare the recommendation robust.

**Why it happens:** The model optimizes for confirming its first conclusion.

**Correct form:** Challenge the two most debatable weights, weaken the winner's load-bearing score, and replace key assumptions with conservative values. Name the smallest plausible reversal condition.

## 10. Decision and ADR collapse

**Mistake:** Present the mutable analysis packet as an accepted architecture decision or invent the approving forum.

**Why it happens:** Both artifacts contain options, rationale, and consequences, so their governance boundary is easy to blur.

**Correct form:** Keep analysis mutable. After a named human forum accepts a choice, create a separate ADR with status, premises, consequences, and review triggers. Never mark it Accepted on the model's authority.

## 11. No-change omission

**Mistake:** Force a build-versus-buy comparison even when retaining, reusing, or sequencing the current state is viable.

**Why it happens:** The user asks for action and the model assumes change is mandatory.

**Correct form:** Include no-change or staged experiment when credible. Score the current state's manual effort, defects, compliance exposure, opportunity cost, and future migration cost rather than treating it as free.

## 12. Production-authority creep

**Mistake:** Turn a recommendation into generated metadata, deployment, activation, assignment, or data mutation without a new governed workflow.

**Why it happens:** The model tries to complete the user's broader goal in one turn.

**Correct form:** Stop at the declared analysis boundary. Hand accepted choices to the appropriate design/build process, with explicit target identity, authority, validation, independent review, approval, and rollback controls.
