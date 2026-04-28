### Apex With / Without / Inherited Sharing — Decision Matrix Template

Use this template when authoring or reviewing the sharing keyword on an
Apex class. Fill in the per-class table below. Treat unfilled `reason`
or `escape-hatch` columns as a review blocker.

## Scope

**Skill:** `apex-with-without-sharing-decision`

**Request summary:** (fill in what the user asked for — e.g., "review
sharing keywords on all classes in the FinanceOps package")

## Decision Matrix

For each class in scope, fill in the row.

| Scenario | Recommended keyword | Why | Per-query escape hatch (if needed) |
|---|---|---|---|
| `@AuraEnabled` controller backing an LWC | `with sharing` | User-invoked surface; respect sharing rules. Never override default. | `WITH SYSTEM_MODE` on a single query that legitimately needs elevation (e.g., loading a config record) — comment why. |
| `@RestResource` exposed to authenticated external users | `with sharing` | External caller authenticates as a user; their perimeter must apply. | `WITH SYSTEM_MODE` only with security review sign-off. |
| `Database.Batchable` system aggregation job | `without sharing` + `// reason:` | Job must process records outside running user's perimeter. | `WITH USER_MODE` on a single query if one lookup should respect sharing (rare). |
| `Schedulable` orchestrator | `without sharing` + `// reason:` | Scheduled context, runs as scheduling user; perimeter would silently drop work. | `WITH USER_MODE` per-query for any user-scoped helper read. |
| Trigger handler class | `without sharing` (typical) — explicit | Trigger body is already system context; handler queries should match unless deliberately user-scoped. | `WITH USER_MODE` for queries that drive user-visible side effects (e.g., chatter posts). |
| Reusable selector / domain / service called from multiple entry points | `inherited sharing` | Caller chooses; selector takes no opinion. | n/a — keep selector neutral; let caller flip per-query. |
| Callable utility (`@InvocableMethod`, called from Flow) | `with sharing` | Flow invokes Apex as the running user; default to user-scoped. | `WITH SYSTEM_MODE` on one query if the utility needs to read configuration outside the user's perimeter. |
| Site / guest-user controller | `with sharing` (mandatory) | Guest perimeter must NEVER be elevated. | None — do not use `WITH SYSTEM_MODE` on guest-context queries; redesign instead. |
| Managed-package internal class | `without sharing` (Salesforce-enforced) — document for subscribers | Package always runs without sharing in subscriber org. | n/a — managed packages cannot be overridden by subscriber. |
| Async Queueable internal helper | `inherited sharing` | Caller (often a service class) chooses. | Match caller's per-query overrides. |

## Justification Template

For every `without sharing` class, record:

```apex
// reason: <one sentence explaining what user-invisible records this
//         class needs to access and why elevation is required>
public without sharing class MyClass { /* ... */ }
```

Generic reasons ("performance", "convenience", "to avoid errors") are
not acceptable. Reasons must reference specific data or a specific
business requirement.

## How to Confirm This is Working Correctly

After applying the decision matrix:

1. **Lint** — run `python3 skills/apex/apex-with-without-sharing-decision/scripts/check_apex_with_without_sharing_decision.py --manifest-dir <path/to/force-app>` and confirm no `ISSUE:` lines on stderr.
2. **Trace** — for every `with sharing` controller, list every helper / service / selector it calls. Confirm each helper has an explicit keyword (`with`, `without`, or `inherited`). No bare classes.
3. **Reverse-call** — for every `without sharing` class, search the codebase for callers. If any caller is an `@AuraEnabled` / `@RestResource` / Site controller, confirm there is a documented reason the elevation is acceptable on that path.
4. **Persona test** — write or update a test class that runs the entry point as a low-privilege user (`System.runAs(lowPrivUser)`) and asserts:
   - `with sharing` paths return only the user's records.
   - `without sharing` paths return the full record set the job is meant to process.
5. **Review the `// reason:` comments** — every `without sharing` class must have a non-generic justification on the line immediately preceding the class declaration.
6. **Aggregate-query review** — list every Apex aggregate (`SELECT COUNT()`, `SUM()`, `AVG()`) and confirm the class keyword matches the intended scope (org-wide vs user-scoped). Surprises here usually indicate a misclassified class.

## Notes

Record any deviations from the standard pattern and why. Cite the
specific business or compliance requirement that justifies the
deviation.
