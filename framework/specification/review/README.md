# Product-owner review system

Cursor implements. The product owner reviews the returned evidence against the specification.

- `PRODUCT_OWNER_REVIEW_PROTOCOL.md` — review order and decision rules.
- `MILESTONE_SCORECARD.md` — scoring and blockers.
- `DEFECT_TAXONOMY.md` — consistent defect classification.
- `NEXT_ITERATION_PROMPT_TEMPLATE.md` — how a failed review becomes a bounded Cursor correction.

The exact files Cursor must return are defined in `implementation/REVIEW_RETURN_CONTRACT.md` and validated by `scripts/verify_cursor_return_zip.py`.
