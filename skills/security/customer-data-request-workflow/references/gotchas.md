# Gotchas — Customer Data Subject Request (DSR) Workflow

## Gotcha 1: Person Accounts complicate identity

**What happens:** Contact + Account deletion breaks if PersonAccount is referenced in Orders.

**When it occurs:** B2C orgs.

**How to avoid:** Use Privacy Center (handles Person Accounts) or pseudonymize instead of delete.


---

## Gotcha 2: Field History Retention

**What happens:** FHRetention stores values for up to 10 years; they survive DML.

**When it occurs:** Shield FHR enabled.

**How to avoid:** Delete matching FieldHistoryArchive rows via the Archive API as part of the runbook.


---

## Gotcha 3: Missing audit

**What happens:** Regulator demands proof; you cannot show what you deleted.

**When it occurs:** Ad-hoc Apex script.

**How to avoid:** Always log DSR_Action__c before the DML with the field hash.

