# Gotchas — Apex REST Services

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## `RestContext` Must Be Set In Tests

**What happens:** Unit tests call the REST method directly and hit null references.

**When it occurs:** `RestContext.request` and `RestContext.response` are not initialized in the test.

**How to avoid:** Create and assign both objects before invoking the REST method.

---

## Authentication Into Salesforce Does Not Finish The Security Job

**What happens:** A valid integration user can call the endpoint, but the resource class still overexposes or overupdates data.

**When it occurs:** Teams assume caller authentication removes the need for explicit sharing and CRUD/FLS review.

**How to avoid:** Declare sharing intentionally and secure data access paths explicitly.

---

## Always Returning `200` Makes Client Behavior Worse

**What happens:** Clients cannot distinguish validation failure, not-found, and server error cases.

**When it occurs:** Endpoints use one status code and one vague message shape for everything.

**How to avoid:** Define status codes and error bodies as part of the contract.

---

## Versioning Is Harder To Add Later

**What happens:** An endpoint initially ships without versioning, then incompatible changes become painful.

**When it occurs:** Teams optimize for speed and delay contract planning.

**How to avoid:** Version the endpoint deliberately from the beginning when external consumers will depend on it.
