# Gotchas — Apex Security Patterns

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## `with sharing` Is Not A Full Security Model

**What happens:** A reviewer sees `with sharing` and assumes the class is safe. The code still reads or writes fields the user should not access.

**When it occurs:** Teams conflate row-level sharing with object and field permissions.

**How to avoid:** Treat sharing, CRUD, and FLS as separate review items. Use explicit read and write enforcement patterns in addition to sharing keywords.

---

## `without sharing` Deep In The Call Stack Still Matters

**What happens:** The entry point looks safe, but a lower-level helper is `without sharing` and widens visibility unexpectedly.

**When it occurs:** Security reviews stop at the controller or trigger handler and do not inspect downstream classes.

**How to avoid:** Trace the call chain and document every elevation boundary. Keep privileged code narrow and purpose-built.

---

## Secure Reads And Secure Writes Need Different Controls

**What happens:** The team adds `WITH USER_MODE` to queries and assumes DML is now safe too.

**When it occurs:** A class both reads and mutates data, but the write path is not sanitized.

**How to avoid:** Use a dedicated write-enforcement pattern such as `Security.stripInaccessible` or explicit describe-based checks before DML.

---

## Ambiguous Sharing Intent Slows Reviews

**What happens:** A reusable class omits a sharing declaration. Reviewers cannot tell whether user context or elevated access was intended.

**When it occurs:** Teams rely on implicit defaults instead of declaring `with`, `without`, or `inherited sharing`.

**How to avoid:** Declare the sharing model explicitly, even when the logic seems obvious.
