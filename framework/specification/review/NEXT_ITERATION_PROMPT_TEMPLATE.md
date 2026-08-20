# Next-iteration Cursor prompt template

Use this only after reviewing a returned milestone ZIP.

```text
You are correcting the local SfSkills V2 implementation at reviewed head <SHA>.

Read:
- the imported SFAEF specification;
- <product-owner-review-path>;
- implementation/REVIEW_RETURN_CONTRACT.md.

Preserve these accepted strengths:
- ...

Fix only these blockers and their direct regression tests:
1. <severity, requirement IDs, exact behavior, evidence>
2. ...

Do not begin the next milestone. Do not broaden the product, refactor unrelated code, rewrite accepted history, push, publish, open a PR, or mutate a customer/non-disposable org.

For each blocker:
- reproduce it from the reviewed head;
- add the narrowest failing test;
- implement the correction;
- run focused and full required gates;
- perform actual host/live verification when the defect concerns that lane;
- create one or more honest local commits;
- package the exact return ZIP contract.

The return ZIP must include before/after evidence for every blocker and all regression logs. Stop after all blockers pass or a truthful P0 external blocker is proven.
```
