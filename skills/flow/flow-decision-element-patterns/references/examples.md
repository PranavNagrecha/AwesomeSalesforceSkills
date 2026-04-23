# Examples — Decision Patterns

## Example 1: Named Default

Outcomes:

1. `VIP_Premium` — `Account.Rating = 'Hot'` AND `Account.AnnualRevenue > 1000000`
2. `VIP_Standard` — `Account.Rating = 'Hot'`
3. `Tier_Mid` — `Account.Rating = 'Warm'`
4. **Default: `Tier_Low`** — renamed from "execute default" to make
   clear the fallback is intentional.

## Example 2: Null-Safe Branching

**Bad:**

Outcome: `{!Lead.Company} = 'Acme'`.

Hides the "Company is null" case inside the default, losing the ability
to route the blank-company case.

**Good:**

- Outcome 1: `{!Lead.Company} = 'Acme'` → Acme handler
- Outcome 2: `ISBLANK({!Lead.Company})` → ask-for-company screen
- Default: generic flow

## Example 3: Pick-List By API Value

Status pick-list values: "In Progress" (label) / `in_progress` (API).

Correct: `{!Case.Status} = 'in_progress'`.

Wrong: `{!Case.Status} = 'In Progress'` — works in English-only org,
breaks on translated user.

## Example 4: Extract Repeated Condition

The expression
`{!Account.Type} = 'Customer - Direct' OR {!Account.Type} = 'Customer - Channel'`
appears in 3 decisions.

**Fix:** Formula resource `isCustomerAccount` evaluating the OR once.
All decisions reference the formula.

## Example 5: Flatten 3-Deep Nested Decision

Original: Decision → (yes → Decision → (yes → Decision)).

Refactor: one Decision with 4 explicit outcomes covering all
combinations, plus a sub-flow for the compound action.
