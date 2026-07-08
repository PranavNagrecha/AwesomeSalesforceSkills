# SOQL Aggregate Field-Type — Compatibility Card & Pre-Flight Worksheet

Use this before writing (or reviewing) any SOQL aggregate query. Part 1 is a fixed
reference matrix; Part 2 is a worksheet you fill in per query.

---

## Part 1 — Compatibility Matrix (reference)

| Field type(s) | AVG | SUM | COUNT | COUNT_DISTINCT | MIN | MAX |
|---|:--:|:--:|:--:|:--:|:--:|:--:|
| **Numeric** — int, double, currency, percent | Yes | Yes | Yes | Yes | Yes | Yes |
| **Date/time** — date, dateTime | No | No | Yes | Yes | Yes | Yes |
| **Text-like** — reference/lookup, ID, email, phone, url, textarea, picklist, combobox, DataCategoryGroupReference | No | No | Yes | Yes | Yes | Yes |
| **No support** — base64, boolean, time, multipicklist, address, location, encryptedstring | No | No | No | No | No | No |
| **Calculated (formula)** | Apply the row that matches the formula's **return type** |

Notes that don't fit a cell:

- `MIN()` / `MAX()` on a **picklist** uses the picklist's defined value **sort order**, not
  alphabetical order.
- All aggregate functions ignore **null** values **except** `COUNT()` and `COUNT(Id)`, which count
  every row.
- In a **multi-currency** org, aggregate results on **currency** fields default to the corporate
  (system) currency.
- `MAX()` is available in API version **18.0 and later**. This field-type support is longstanding
  core SOQL reference behavior — the docs give it **no** GA/Beta/Pilot label; do not assert one.
- `LIMIT` is not allowed on an aggregate query that has **no** `GROUP BY`.

---

## Part 2 — Per-Query Pre-Flight Worksheet

**Query / intent:** _(what are you trying to summarize?)_

**Object:** `______________________`

**Multi-currency org?** ☐ Yes ☐ No

### Fields to aggregate

| Field API name | Data type (or formula return type) | Function you want | Supported? (matrix) | If No → replacement |
|---|---|---|:--:|---|
| | | | ☐ Yes ☐ No | |
| | | | ☐ Yes ☐ No | |
| | | | ☐ Yes ☐ No | |

### Sign-off checks

- [ ] No `AVG()` / `SUM()` on a non-numeric field (date, text, picklist, boolean, …)
- [ ] No aggregate function on base64, boolean, time, multipicklist, address, location, or encryptedstring
- [ ] COUNT semantics deliberate — `COUNT(Id)`/`COUNT()` = all rows; `COUNT(field)`/`COUNT_DISTINCT` = non-null only
- [ ] Formula-field aggregates checked against the formula's **return type**
- [ ] Multi-currency currency aggregate → `GROUP BY CurrencyIsoCode` or documented as corporate-currency total
- [ ] `MIN()`/`MAX()` on a picklist gives the value expected under **picklist sort order**
- [ ] No `LIMIT` on an aggregate query without `GROUP BY`
- [ ] Ran `scripts/check_soql_aggregate_field_type_support.py` (optionally with `--field-types`) and confirmed in the Query Editor

### Notes / deviations

_(record any place you intentionally diverge from the matrix and why)_
