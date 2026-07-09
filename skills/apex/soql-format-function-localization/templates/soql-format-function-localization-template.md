# FORMAT() Localization Worksheet + Query Cookbook

Fill this in before writing a query that must return locale-formatted output. It forces the two
decisions that cause most `FORMAT()` bugs: **which fields actually need formatting**, and
**whether a consumer also needs the raw value** (which then triggers the aliasing rule).

## 1. Scope

**Skill:** `soql-format-function-localization`

**Request summary:** (what display output is needed, and for which object/query)

**Execution context:** ☐ REST/SOAP/Bulk query API ☐ dynamic Apex `Database.query` ☐ inline Apex SOQL ☐ report / other
> If inline Apex SOQL, confirm the query compiles in your API version; prefer dynamic SOQL if unsure.

**Whose locale renders the output:** the *running user's* Locale (not the org default). Note the
target locale(s): ________________

## 2. Field map

List every field the query returns. `FORMAT()` supports only **number, date, time, currency**.

| Field | Type (number/date/time/currency/other) | Need raw value? | Need formatted? | Alias (required if raw + formatted) |
|---|---|---|---|---|
| e.g. `Amount` | currency | yes | yes | `amountDisplay` |
| e.g. `CloseDate` | date | no | yes | `closeDisplay` |
| e.g. `StageName` | other → use `toLabel()`, not `FORMAT()` | — | — | — |

Rules to apply from the table:
- Field type is **not** number/date/time/currency → do not wrap in `FORMAT()`.
- "Need raw value" and "Need formatted" both `yes` → the formatted column **must** have an alias.
- Anything a consumer computes on, sorts numerically, or must receive in a fixed format → return
  the **raw** field and format downstream instead.

## 3. Pick a pattern (ready-to-adapt snippets)

**Raw + formatted side by side**
```sql
SELECT Id, Amount, FORMAT(Amount) amountDisplay FROM Opportunity
```

**Localized date, UI parity**
```sql
SELECT Id, FORMAT(CloseDate) closeDisplay FROM Opportunity
```

**Localized aggregate scalar** (read by alias off the AggregateResult)
```sql
SELECT FORMAT(MIN(CloseDate)) earliest FROM Opportunity
```

**Converted currency, multi-currency org** (convertCurrency() must NOT be in WHERE)
```sql
SELECT amount, FORMAT(convertCurrency(amount)) convertedCurrency FROM Opportunity
```

**SOSL RETURNING**
```sql
FIND {Acme} RETURNING Account(Id, LastModifiedDate, FORMAT(LastModifiedDate) FormattedDate)
```

**Reading a formatted column in Apex** (always a String)
```apex
String display = (String) row.get('amountDisplay');
Decimal raw    = (Decimal) row.get('Amount'); // keep the raw field for math
```

## 4. Checklist

- [ ] Every `FORMAT()` wraps a number/date/time/currency field only
- [ ] Formatted columns are aliased wherever the raw field is also selected
- [ ] No `FORMAT()`/`convertCurrency()` in `WHERE`/`HAVING`/`ORDER BY`
- [ ] Consumers needing computation/sort get the raw field
- [ ] No integration contract depends on a per-user, locale-variable string
- [ ] No invented format-mask argument, no invented GA/Beta maturity claim

## 5. Validate

```bash
python3 scripts/check_soql_format_function_localization.py --manifest-dir force-app/main/default
# or sanity-check the checker itself:
python3 scripts/check_soql_format_function_localization.py --self-test
```

## Notes

(Record any deviation from the standard pattern and why — e.g. why a fixed Apex-side format was
used instead of `FORMAT()`.)
