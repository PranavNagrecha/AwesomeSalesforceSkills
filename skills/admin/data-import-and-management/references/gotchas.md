# Gotchas: Data Import and Management

---

## Upsert Without a Stable Match Key

**What happens:** The team says they are doing an "upsert" but matches are based on Name or Email. Some source rows match the wrong records, some create duplicates, and nobody notices until reporting breaks.

**When it bites you:** Legacy migrations, spreadsheets from business teams, and integrations that do not have External IDs.

**How to avoid it:** Use an immutable External ID or source-system key. Validate uniqueness in the source file before the load starts.

**Example:**
```csv
Email,FirstName,LastName
sales@example.org,Ana,Lopez
sales@example.org,Devon,Price
```

---

## Validation Rules and Flows at Volume

**What happens:** The first 100 records load fine in sandbox. Production load of 250,000 rows starts failing because record-triggered flows, duplicate rules, and validation formulas all execute at scale.

**When it bites you:** Weekend cutovers, mass owner changes, large historical backfills.

**How to avoid it:** Test with realistic batch size, define bypass controls deliberately, and use maintenance windows when recalculation or automation volume is high.

**Example:**
```text
Load objective: 300,000 Cases
Observed issue: flow updates parent Account on every Case insert
Result: locks and failed batches
Fix: bypass non-critical automation during cutover, then backfill downstream logic separately
```

---

## Duplicate Rules in Alert Mode Still Affect Operations

**What happens:** Teams assume alert mode is harmless because it does not block saves. The load completes, but thousands of near-duplicates get through because alerts were ignored by the service account or not reviewed afterward.

**When it bites you:** Contact imports, Account merges, and any migration with dirty source data.

**How to avoid it:** Test blocking vs alert behavior intentionally, assign an owner for duplicate review, and reconcile duplicates in the same cutover window.

**Example:**
```text
Duplicate rule: Alert on Contact email match
Load result: 40,000 Contacts loaded, 3,200 duplicate alerts ignored
Operational impact: sales reps now have multiple Contact records for the same person
```

---

## Child Rows Loaded Before Parent Rows

**What happens:** Contacts or Opportunities are loaded before the parent Account records exist. Lookup resolution fails and the error file grows fast.

**When it bites you:** Any multi-object load run by separate teams or separate jobs without a runbook.

**How to avoid it:** Load parent objects first, then child objects, and use External IDs for lookup resolution.

**Example:**
```text
Wrong order: Contacts -> Accounts
Correct order: Accounts -> Contacts -> Opportunities
```
