# LLM Anti-Patterns — SOQL USING SCOPE Clause

Common mistakes AI coding assistants make when generating or advising on the SOQL USING SCOPE
clause. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Placing USING SCOPE after WHERE (SQL/Java bleed)

**What the LLM generates:**

```sql
SELECT Id FROM Account WHERE Industry = 'Tech' USING SCOPE mine
```

**Why it happens:** ANSI SQL has no `USING SCOPE` clause, so the model appends it at the end like
a modifier or slots it wherever it "reads" naturally, rather than in the fixed SOQL position.

**Correct pattern:**

```
SELECT Id FROM Account USING SCOPE mine WHERE Industry = 'Tech'
```

**Detection hint:** any `WHERE` token that appears *before* `USING SCOPE` in the same query — the
included `check_soql_using_scope_clause.py` flags this.

---

## Anti-Pattern 2: Selling USING SCOPE mine as record-level security

**What the LLM generates:** "Use `USING SCOPE mine` so users can only see their own records" — with
no `WITH USER_MODE`, often from a `without sharing` class.

**Why it happens:** "mine" reads like an access control, and the model conflates an ownership
*filter* with sharing *enforcement*.

**Correct pattern:**

```apex
[SELECT Id FROM Opportunity USING SCOPE mine WHERE IsClosed = false WITH USER_MODE]
```

**Detection hint:** advice that presents `USING SCOPE mine` as a security control, or a scoped
query with no `WITH USER_MODE` / `WITH SECURITY_ENFORCED` / `with sharing` alongside it.

---

## Anti-Pattern 3: Inventing scope values that don't exist

**What the LLM generates:** `USING SCOPE all`, `USING SCOPE owned`, `USING SCOPE my_accounts`,
`USING SCOPE me`, or similar plausible-sounding tokens.

**Why it happens:** the model pattern-fills a "scope word" from English rather than the closed
enumeration, and guesses `all` instead of the real `everything`.

**Correct pattern:** only these eight values — `delegated`, `everything`, `mine`,
`mine_and_my_groups`, `my_territory`, `my_team_territory`, `scopingRule`, `team`.

**Detection hint:** a `USING SCOPE <token>` where `<token>` is not in the eight-value set; the
checker reports it as an unknown scope.

---

## Anti-Pattern 4: Using Metadata API list-view casing/values in SOQL

**What the LLM generates:** `USING SCOPE Everything`, `USING SCOPE Queue`, `USING SCOPE
AssignedToMe`, or `USING SCOPE SalesTeam`.

**Why it happens:** training data mixes the Metadata API `ListView.filterScope` enum (PascalCase,
with `Queue`/`AssignedToMe`/`SalesTeam`) with the SOQL clause, and the model can't tell them apart.

**Correct pattern:** SOQL uses the lowercase enumeration; `Queue`, `AssignedToMe`, and `SalesTeam`
are list-view metadata values with no SOQL equivalent. Use `everything`, `mine`, `team`, etc.

**Detection hint:** a scope token that matches a Metadata API list-view value; the checker calls
these out specifically as "Metadata API ListView value, not a SOQL scope."

---

## Anti-Pattern 5: Applying mine_and_my_groups to arbitrary objects

**What the LLM generates:** `SELECT Id FROM Case USING SCOPE mine_and_my_groups` (or on Lead,
Task, etc.).

**Why it happens:** the "me and my queues" idea generalizes cleanly in prose, so the model applies
it anywhere queues exist.

**Correct pattern:** `mine_and_my_groups` "applies only to the `ProcessInstanceWorkItem` object."
For queue-owned rows on other objects, filter by owner type / queue membership instead.

**Detection hint:** `USING SCOPE mine_and_my_groups` whose `FROM` object is not
`ProcessInstanceWorkItem` — the checker flags the mismatch.

---

## Anti-Pattern 6: Forgetting EVERYTHING (or nesting it partially) in scoping rules

**What the LLM generates:** a scoping-rule SOQL operator that omits `USING SCOPE EVERYTHING`, uses
`mine`, or adds it to the outer query but not the nested subquery.

**Why it happens:** the model treats the scoping-rule query like any SOQL and applies the general
"scope is optional" mental model.

**Correct pattern:** `USING SCOPE EVERYTHING` on the outer *and* every nested `SELECT` — "the only
valid scope clause syntax for scoping rules."

**Detection hint:** a scoping-rule SOQL operator missing `USING SCOPE EVERYTHING` on any `SELECT`,
or any non-`everything` scope value in that context.

---

## Anti-Pattern 7: Asserting a GA/Beta status the docs don't state

**What the LLM generates:** "USING SCOPE is a GA feature since Spring '15" or "this Beta clause…".

**Why it happens:** models pattern-fill maturity labels onto any capability.

**Correct pattern:** state only what the docs say — the clause is "Available in API version 32.0
and later," with no GA/Beta/Pilot label attached to the clause itself. The *Scoping Rules SOQL
operator* is separately edition-gated to Lightning Experience Performance and Unlimited Editions;
cite that where relevant and don't extend it to the base clause.

**Detection hint:** any "Generally Available"/"Beta"/"Pilot" claim about the clause that isn't
backed by a release-notes citation.
