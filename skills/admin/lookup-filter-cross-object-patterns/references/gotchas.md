# Gotchas — Lookup Filter Cross Object Patterns

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Required filter does not retroactively invalidate stored data

**What happens:** You flip a filter to required. Reports of records "violating" the new rule keep running fine. Then weeks later, a user edits one and gets blocked.

**When it occurs:** Whenever existing records do not match the new filter at the time of deploy. Salesforce never re-evaluates filters against existing data — only the next save is checked.

**How to avoid:** Run a report counting non-conforming records before flipping to required. Backfill or grant a profile bypass before the change.

---

## Gotcha 2: `$Source` cannot traverse two parents

**What happens:** `$Source.Account.Owner.Region__c` is rejected at filter design time, even though the path is valid in formulas elsewhere.

**When it occurs:** Whenever your right-hand side needs a value two relationships away from the source.

**How to avoid:** Add a formula field on the *first* parent (e.g., `Account.Owner_Region__c`) that flattens the deep traversal, then reference `$Source.Account.Owner_Region__c`.

---

## Gotcha 3: Admin bypass exempts only the System Administrator profile

**What happens:** Custom admin profiles ("Sales Admin", "Data Migration Lead") still get blocked despite the bypass setting.

**When it occurs:** Any time the profile is not literally `System Administrator`. Permission sets with "Modify All Data" do not change the behavior.

**How to avoid:** Either give those users the standard System Administrator profile temporarily (rare and risky), or build the bypass into the filter directly — `OR($Profile.Name = "Data Migration", Contact.AccountId = $Source.AccountId)`.

---

## Gotcha 4: Field deletion silently breaks the filter

**What happens:** Someone deletes the field referenced on the right-hand side. The filter shows as "broken" only when an admin opens it in Setup; saves keep going through, but the picker now returns *no* records, so users can't fill the lookup at all.

**When it occurs:** During cleanup PRs that remove "unused" custom fields without checking lookup filter dependencies.

**How to avoid:** Add referenced fields to the data dictionary's "do-not-delete" list. Validate filter integrity in CI by parsing the field metadata XML before any field deletion.

---

## Gotcha 5: Field-level security is enforced before the filter

**What happens:** A profile cannot read `Account.Region__c`. The lookup filter referencing that field returns zero records for those users — the picker is silently empty.

**When it occurs:** Whenever the running user lacks read access to any field cited on either side of the filter.

**How to avoid:** Make every field referenced in a lookup filter readable to every profile that needs to save the source object. Document this requirement near the filter so future FLS audits don't accidentally tighten it.
