# Gotchas — Invocable Methods

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Flow-Friendly Does Not Mean Single-Record Safe

**What happens:** The action is implemented for one record because the Flow canvas makes it look singular.

**When it occurs:** Teams ignore the list-oriented invocable contract.

**How to avoid:** Design bulk-safe query and DML behavior from day one.

---

## Wrapper Fields Are Part Of The User Experience

**What happens:** Flow builders see unclear labels or cannot understand which variable to map.

**When it occurs:** `@InvocableVariable` metadata is treated as optional documentation.

**How to avoid:** Provide meaningful labels, descriptions, and result semantics.

---

## Throwing On First Failure Can Limit Orchestration Value

**What happens:** One bad input causes the whole action to fault when the Flow really needed per-record outcomes.

**When it occurs:** Error behavior is inherited from service code without considering the Flow contract.

**How to avoid:** Decide whether the action should throw or return structured results based on the orchestration need.

---

## Invocable Classes Become Mini-Services Easily

**What happens:** The annotation class becomes the permanent home of business logic.

**When it occurs:** There is no separate service boundary.

**How to avoid:** Keep the invocable as an adapter and delegate real work.
