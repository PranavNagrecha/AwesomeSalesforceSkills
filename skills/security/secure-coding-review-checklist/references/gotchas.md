# Gotchas — Secure Coding Review Checklist

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: WITH USER_MODE Throws Exceptions Instead of Returning Empty Results

**What happens:** When a SOQL query with `WITH USER_MODE` encounters a field the running user cannot access, the platform throws a `System.FlsException` at runtime rather than silently omitting the field or returning an empty result set. This is different from the older `isAccessible()` describe pattern, which let developers gracefully skip inaccessible fields.

**When it occurs:** Any time a query with `WITH USER_MODE` includes a field that the running user's profile or permission set does not grant read access to. This is common in managed packages deployed across orgs with varying permission configurations. The error surfaces at runtime, not at compile time or during deployment.

**How to avoid:** Wrap queries in try-catch blocks that handle `System.FlsException` and `System.CrudException`. Alternatively, use `Security.stripInaccessible()` on query results instead of `WITH USER_MODE` when graceful degradation is required — it silently removes inaccessible fields from the SObject map without throwing.

---

## Gotcha 2: A Trigger's Sharing Declaration Is Fixed, but Its Access Mode Decides What Is Actually Enforced

**What happens:** The trigger's fixed *declaration* gets mistaken for a fixed *outcome*, and the reviewer stops looking. The declaration half is real: "Apex triggers can't have an explicit sharing declaration. Triggers always run implicitly in a without sharing context, which means that they bypass the sharing rules of the current user." That is the trigger body's baseline, and no version changes it. But the guide continues: "However, database operations within trigger bodies, including SOQL queries, SOSL queries, DML statements, and Database methods, run in user mode unless system mode is explicitly specified." And user mode is not merely a CRUD/FLS setting — "User mode overrides the trigger's without sharing context and effectively enforces a with sharing context in the trigger body", because `AccessLevel.USER_MODE` is the mode "in which the object permissions, field-level security, and sharing rules of the current user are enforced." So a bare query in a 67.0+ trigger enforces object permissions, FLS, **and** record sharing.

**When it occurs:** Whenever a reviewer assumes the trigger body is unenforced by definition. The access mode is written per operation, and `WITH SYSTEM_MODE`, `as system`, and `AccessLevel.SYSTEM_MODE` are legal inside a trigger. The guide's worked `AccountUpdateTrigger` example shows both forms side by side and is labelled *API version 67.0 and later*; the gate is the `<apiVersion>` in the trigger's own `.trigger-meta.xml`, not the org's release, the same way a class is gated on its `.cls-meta.xml`. Below 67.0 the old default holds and a bare trigger-body operation runs in system mode. The opt-out is where the baseline reappears, and its consequence is worth stating plainly: under `WITH SYSTEM_MODE` object- and field-level permissions are ignored, and "Record sharing remains governed by the trigger's own without sharing context, so all records are visible regardless of the user running the query."

**How to avoid:** Read the trigger body rather than scoring it. Record the trigger's `.trigger-meta.xml` `<apiVersion>`, then check each query and DML statement for an explicit access mode; flag `WITH SYSTEM_MODE` / `as system` that carries no stated reason, and do not flag `WITH USER_MODE` — it is the documented, recommended way to write a trigger-body query. The guide's own recommendation is that "you set explicit access mode on all database operations in your trigger and handler classes", so ambiguity is the finding, not user mode. Still move business logic into a handler class that declares `with sharing`: it keeps the enforcement decision reviewable in one place and it is what the AppExchange review team expects. If the trigger legitimately needs to bypass sharing (e.g., cross-object rollup calculations), it must say so with an explicit system-mode access mode — document the justification in a code comment and be prepared to explain it during the review.

---

## Gotcha 3: String.escapeSingleQuotes Does Not Prevent All SOQL Injection Vectors

**What happens:** `String.escapeSingleQuotes()` only escapes the single-quote character (`'`). It does not protect against injection via LIKE wildcards (`%`, `_`), backslash sequences, or SOQL operators inserted into numeric or boolean filter contexts where single quotes are not used.

**When it occurs:** When dynamic SOQL builds a WHERE clause with a numeric comparison (e.g., `Amount > ' + userInput`) or a LIKE clause where the user can inject `%` to match all records. The developer applies `escapeSingleQuotes()` and assumes the input is safe, but the injection bypasses the single-quote defense entirely.

**How to avoid:** Use bind variables (`:variableName`) or `Database.queryWithBinds()` instead of string concatenation wherever possible. When dynamic SOQL is unavoidable, sanitize the input type explicitly: cast numeric inputs to `Integer` or `Decimal`, validate enum values against an allowlist, and escape LIKE wildcards by replacing `%` and `_` with `\%` and `\_` before interpolation.

---

## Gotcha 4: HTMLENCODE in Visualforce Does Not Protect JavaScript Contexts

**What happens:** `HTMLENCODE()` converts characters like `<`, `>`, `&`, and `"` to their HTML entity equivalents. This prevents XSS in HTML body contexts, but inside a `<script>` block, the browser interprets the content as JavaScript before HTML entity decoding occurs. An attacker payload like `';alert(1);//` passes through `HTMLENCODE()` intact because it contains no HTML special characters.

**When it occurs:** Visualforce pages that embed merge field values inside `<script>` tags using `HTMLENCODE({!userInput})` instead of `JSENCODE({!userInput})`. This is a common copy-paste error because `HTMLENCODE` is the most frequently referenced encoding function in documentation examples.

**How to avoid:** Use `JSENCODE()` for values placed inside JavaScript string literals, `HTMLENCODE()` for values placed in HTML body context, and `URLENCODE()` for values placed in URL parameters. When a value appears in a nested context (e.g., a JavaScript string inside an HTML attribute), apply both encoders from inner to outer: `HTMLENCODE(JSENCODE({!value}))`.

---

## Gotcha 5: @AuraEnabled Methods Are Accessible to Any Authenticated User by Default

**What happens:** Any method annotated with `@AuraEnabled` can be called by any authenticated user in the org, regardless of whether the corresponding LWC or Aura component is exposed on a page they can access. The caller simply needs to invoke the Apex method via the Aura/LWC runtime endpoint. Profile-based component visibility does not restrict access to the underlying Apex method.

**When it occurs:** Developers build an admin-only LWC that calls an `@AuraEnabled` method performing sensitive operations (e.g., modifying sharing rules, querying all records without sharing). They restrict the LWC's visibility to admin profiles via page layout or Lightning app assignment but assume the Apex method is equally restricted. A standard user can still invoke the method directly.

**How to avoid:** Enforce access control inside the Apex method itself. Check `FeatureManagement.checkPermission('Custom_Permission_Name')` or validate `UserInfo.getProfileId()` before executing sensitive logic. Declare the class `with sharing` to ensure sharing rules apply. For managed packages, consider using the `@AuraEnabled` method's `cacheable` parameter carefully — cacheable methods cannot perform DML, which limits the damage surface but does not prevent data exfiltration.
