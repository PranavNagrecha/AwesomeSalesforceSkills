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

## The Default Sharing Mode Changed In API 67.0

**What happens:** A class that used to run without enforcing sharing suddenly enforces it after an API-version bump, and records that were previously visible disappear from query results — or a `without sharing`-by-habit class that lost its keyword during a refactor starts filtering rows.

**When it occurs:** In API version 67.0 and later, a class with no explicit sharing declaration runs in `with sharing`. Older undeclared code being uplifted, or newly scaffolded classes, inherit this default.

**How to avoid:** Never rely on the version default. Declare `with`, `without`, or `inherited sharing` explicitly on every class so behavior is stable across API-version changes.

---

## Sharing Does Not Flow From The Call Site Or The Outer Class

**What happens:** A reviewer assumes wrapping a call in a `with sharing` class makes the callee enforce sharing, or that a `with sharing` outer class protects its inner classes. Neither is true, so records leak.

**When it occurs:** A method's enforcement is fixed by where it is defined, not by the caller; inner classes do not adopt the container class's mode; and only an undeclared class that `extends` a parent adopts the parent's mode.

**How to avoid:** Verify each class and inner class has its own intended declaration, and judge cross-call behavior by where each method is defined.

---

## Ambiguous Sharing Intent Slows Reviews

**What happens:** A reusable class omits a sharing declaration. Reviewers cannot tell whether user context or elevated access was intended.

**When it occurs:** Teams rely on implicit defaults instead of declaring `with`, `without`, or `inherited sharing`.

**How to avoid:** Declare the sharing model explicitly, even when the logic seems obvious.
