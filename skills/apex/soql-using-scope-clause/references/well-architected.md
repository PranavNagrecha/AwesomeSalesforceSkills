# Well-Architected Notes — SOQL USING SCOPE Clause

## Relevant Pillars

- **Security** — the load-bearing caveat of this skill. `USING SCOPE` narrows *which rows* a query
  returns by ownership/team/territory, but it enforces no CRUD, FLS, or sharing. Never treat a
  scoped query as an access control: pair every `USING SCOPE` with `WITH USER_MODE` (Summer '23+)
  or a `with sharing` context plus `SecurityUtils` CRUD/FLS checks. The audience filter and the
  security boundary are orthogonal, and a query almost always needs both.
- **Performance** — scope is also a selectivity lever. `USING SCOPE mine`/`my_territory` cuts the
  candidate set to the running user's slice, which can keep a query within heap and query-row
  governor limits; `USING SCOPE everything` deliberately removes that filter and can pull very large
  result sets on high-volume objects. Choose `everything` only where it is required (the Scoping
  Rules SOQL operator) or genuinely intended, not as a default.
- **Operational Excellence** — supported scopes are object- and edition-specific. Confirm support
  via `describeSObject()` / sObject Describe and verify prerequisites (territory management, an
  active scoping rule, the Performance/Unlimited edition gate for the Scoping Rules operator) before
  deploying, so a scope that works in one org doesn't fail in another.
- **Reliability** — `mine` and territory scopes bind to "the running user," which differs across
  interactive, scheduled, batch, and system contexts. Pin down that principal so an automation
  doesn't silently return the wrong user's (or zero) records.

## Architectural Tradeoffs

- **Scope keyword vs. explicit WHERE filter.** `USING SCOPE mine` is maintained and describe-backed,
  capturing platform ownership semantics a hand-written `OwnerId` filter misses; an explicit filter
  is more portable across execution contexts where "the running user" is ambiguous. Prefer the scope
  for interactive user queries; prefer an explicit owner filter in automation that must target a
  specific user.
- **Scoped selectivity vs. completeness.** Narrow scopes improve selectivity and limit-safety but
  hide records the caller may legitimately need; `everything` is complete but unbounded. Match the
  scope to the actual requirement rather than defaulting to either extreme.

## Anti-Patterns

1. **Scope-as-security** — shipping `USING SCOPE mine` as record-level access control with no
   `WITH USER_MODE`/`with sharing`. It filters, it does not enforce.
2. **Blind `everything`** — using `USING SCOPE everything` as a default on a large object, pulling
   unbounded rows into heap instead of scoping (or paginating) to what's needed.
3. **Context-blind `mine`** — relying on `mine`/territory scopes in async/scheduled code where the
   running user isn't the intended principal, producing silently wrong results.

## Official Sources Used

- SOQL SELECT — USING SCOPE (filterScope enumeration, API v32.0+) — https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_soql_select_using_scope.htm
- SOQL SELECT statement syntax (clause ordering: USING SCOPE after FROM, before WHERE) — https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_soql_select.htm
- Scoping Rules — Use the SOQL Operator (USING SCOPE EVERYTHING requirement; edition availability) — https://developer.salesforce.com/docs/atlas.en-us.scoping_rules.meta/scoping_rules/scoping_rules_quickstart_use_soql_operator.htm
- Metadata API Developer Guide — ListView (the *different* filterScope enum) — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_listview.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
