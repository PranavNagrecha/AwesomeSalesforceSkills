# Gotchas - Oauth Flows And Connected Apps

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: The Correct Flow Can Still Be Overpowered

**What happens:** The architecture uses Client Credentials or JWT bearer correctly, but the underlying principal has excessive permissions.

**When it occurs:** Teams treat OAuth scopes as the entire authorization model.

**How to avoid:** Review permission sets, integration user design, and connected app policy together.

---

## Gotcha 2: Token Expiration Becomes A Production Event

**What happens:** Everything works in test, then jobs start failing with auth errors in production.

**When it occurs:** Rotation and refresh handling were never rehearsed.

**How to avoid:** Define token lifecycle handling before go-live and alert on repeated auth failures.

---

## Gotcha 3: Connected Apps Outlive Their Owners

**What happens:** A connected app remains active but nobody knows who owns or audits it.

**When it occurs:** Setup work is treated as one-time implementation instead of governed access.

**How to avoid:** Require ownership, purpose, and revoke runbooks for every connected app.
