### Well-Architected Notes — Apex With / Without / Inherited Sharing Decision

## Relevant Pillars

- **Security** — the entire decision is a security control. The chosen
  keyword determines whether a user invoking Apex code can see records
  outside their sharing perimeter. Defaulting to `without sharing` is
  the most common Apex security regression in production code reviews;
  defaulting to `with sharing` on a system job silently under-processes
  data and creates correctness gaps that masquerade as data quality
  issues.

## Architectural Tradeoffs

- **Safety vs. operability.** `with sharing` everywhere is the safest
  default but makes legitimate cross-perimeter system jobs awkward;
  `without sharing` everywhere is operationally simple but ships an
  insecure-direct-object-reference vulnerability the moment a
  controller surface is added. The middle ground — `with sharing` for
  user-facing entry points, `without sharing` (with `// reason:`) for
  background jobs, `inherited sharing` for shared services — keeps both
  surfaces correct.
- **Class-level vs. statement-level enforcement.** Class keywords are
  coarse but visible in code review. `WITH USER_MODE` /
  `WITH SYSTEM_MODE` are precise but easy to miss in review. Prefer
  class-level keywords for the dominant mode and per-statement
  overrides only for exceptions.
- **Inheritance discipline.** Bare classes save a few characters but
  shift sharing semantics to whoever calls them. Explicit
  `inherited sharing` costs nothing and makes the contract auditable.

## Anti-Patterns

1. **Bare classes shipped to production.** A class with no sharing
   keyword is a latent bug — its behavior depends on the calling
   context. Even if it appears to work today, a future refactor that
   changes the call path silently changes its security posture.
2. **`without sharing` without a `// reason:` comment.** A reviewer
   has no way to tell whether the elevation is deliberate or a
   copy-paste mistake. The comment is mandatory in this repo's
   convention; the checker enforces it.
3. **Flipping the class keyword to fix one query.** When 95% of a class
   is correct in one mode and one statement needs the other, change the
   query (`WITH USER_MODE` / `WITH SYSTEM_MODE`), not the class. Class
   flips have wide blast radius and break the inheritance contract for
   every callee.

## Official Sources Used

- Apex Developer Guide — Using the with sharing, without sharing, and inherited sharing Keywords —
  https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_classes_keywords_sharing.htm
- Apex Developer Guide — Enforcing User Mode for Database Operations —
  https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_classes_perms_enforcing.htm
- Salesforce Security Guide — Sharing Rules —
  https://help.salesforce.com/s/articleView?id=sf.security_sharing_rules.htm&type=5
- Apex Reference Guide — System.AccessLevel —
  https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_class_System_AccessLevel.htm
- Salesforce Well-Architected — Trusted (Security) —
  https://architect.salesforce.com/well-architected/trusted/secure
