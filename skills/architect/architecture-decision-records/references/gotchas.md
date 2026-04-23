# Gotchas — ADRs

## 1. ADR Is Not A Design Doc

An ADR records the decision. The design doc describes the solution.
Keep them separate — the ADR is short (one page), the design doc can
be long.

## 2. Alternatives Considered Is Not Optional

An ADR with no alternatives is just a declaration. Future readers need
to know what was rejected to evaluate whether the context still holds.

## 3. Status Flips Are Cheap; Deletions Are Not

Never delete an ADR. Flip status to Deprecated or Superseded and link
forward. The history is the value.

## 4. Date The Decision, Not The Document

Edits to wording happen; the decision date is fixed. Add a "Last
edited" footer if wording changes.

## 5. Consequences Must Include Negatives

"Consequences: faster deploys, happier team." No. The negative side
forces honest thinking. If you cannot name a tradeoff, the ADR is
premature.

## 6. Numbering Is Sequential, Not Per-Domain

Global sequence (0001, 0002, ...) across the repo. Easier to reference
than per-domain numbering, which collides when teams reorganise.

## 7. Deciders Are Named People, Not Roles

"Tech Lead" loses information when the role changes hands. Record
names + role at the time.

## 8. ADRs Stored In The Repo They Describe

If the decision is about the Salesforce repo, the ADRs live in that
repo. External wikis go stale. Source control is the anchor.
