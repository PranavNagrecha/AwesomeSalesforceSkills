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

## The Default Access Mode Flipped In API 67.0 — And Elevation Is Now The Opt-In Half

**What happens:** A batch job, an integration service, or a platform-utility class that has always seen every row starts returning fewer records, or throws on a field the running user cannot read. Nothing about the org's sharing model changed and no query was edited — the class's `apiVersion` was raised.

**When it occurs:** At API version 67.0 and later, SOQL, SOSL, DML, and `Database` methods run in user mode by default and apply the running user's sharing rules, FLS, and object permissions. At 66.0 and earlier, system mode is the default. The gate is the `apiVersion` in the class's `.cls-meta.xml`, not the org's release, so a Summer '26 org runs a class pinned to 58.0 with the old behaviour indefinitely. The same version bump also removes `WITH SECURITY_ENFORCED` from SOQL `SELECT` in Apex, so a query that used it no longer compiles.

**How to avoid:** Before bumping a class to 67.0, inventory every query and DML in it that depends on elevated access and give each one an explicit `WITH SYSTEM_MODE` or `AccessLevel.SYSTEM_MODE` with a `// reason:` comment. Migrate `WITH SECURITY_ENFORCED` to `WITH USER_MODE` in the same pass. Full version matrix: [Apex security idiom by API version](../../../../agents/_shared/AGENT_CONTRACT.md#apex-security-idiom-by-api-version).

---

## A Trigger's `without sharing` Context Says Nothing About Its Access Mode

**What happens:** A reviewer reads that triggers "always run implicitly in a `without sharing` context", concludes the whole trigger body is unenforced, and either signs off on unsafe DML or wastes a release re-elevating code that was never restricted. The opposite error is just as common: assuming the trigger's implicit `without sharing` also bypasses FLS, so no enforcement is written at all.

**When it occurs:** Any trigger. The two axes move independently. The sharing *context* is fixed — a trigger cannot carry a sharing keyword and always runs implicitly `without sharing` — but that context is what an operation falls back to, not an unconditional bypass. The access mode is not fixed, and it overrides the context: per the Apex Developer Guide, "database operations within trigger bodies, including SOQL queries, SOSL queries, DML statements, and Database methods, run in user mode unless system mode is explicitly specified. User mode overrides the trigger's `without sharing` context and effectively enforces a `with sharing` context in the trigger body." That default is version-gated on the trigger's own `.trigger-meta.xml` `apiVersion` — user mode at 67.0+, system mode at ≤66.0.

**How to avoid:** Judge the two axes separately and name the `apiVersion` when you judge the second. Do not tell a reader a trigger sees every row: on a 67.0+ trigger a bare query returns only what the running user can see. Where a trigger-body operation genuinely needs elevated access, say so with `WITH SYSTEM_MODE`, `as system`, or `AccessLevel.SYSTEM_MODE` plus a `// reason:` comment — that operation bypasses object- and field-level permissions and falls back to the trigger's `without sharing` context for record visibility, so it is the one that really does see every row. Keep security-sensitive logic in a handler class, where the sharing axis is also yours to declare.

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
