# Gotchas - Flow Governance

## Weak Names Survive Longer Than Anyone Plans

**What happens:** Temporary or copied names remain in production for months or years.

**When it occurs:** Teams postpone naming cleanup because the flow "works for now."

**How to avoid:** Enforce naming standards before activation rather than as optional cleanup afterward.

---

## Inactive Versions Still Distort Understanding

**What happens:** Operators waste time comparing versions or copied flows because the real production path is unclear.

**When it occurs:** The org accumulates stale versions with no retirement review.

**How to avoid:** Review and retire ambiguity on a regular schedule instead of waiting for a crisis.

---

## Interview Labels Are Part Of Supportability

**What happens:** Logs and user-reported failures point to unhelpful interview names.

**When it occurs:** Teams focus only on builder labels and ignore how runtime history will be read later.

**How to avoid:** Use interview labels and descriptions as operational metadata, not just decoration.

---

## Unowned Flows Become Incident Risks

**What happens:** Production issues stall because no team has clear responsibility for a flow.

**When it occurs:** Ownership exists informally but is never recorded in the governance process.

**How to avoid:** Require an owning team or accountable maintainer for every production flow.
