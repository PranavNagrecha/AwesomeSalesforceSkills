# SOQL FOR VIEW / FOR REFERENCE — Decision Worksheet & Safe Snippet

Use this template when a custom surface must make records it fetches appear in the user's
Recent Items / global-search auto-complete. Fill in the worksheet, then copy the matching
snippet. The SOQL clause belongs in the selector layer — see `templates/apex/BaseSelector.cls`.

## Scope

**Skill:** `soql-for-view-and-for-reference`

**Request summary:** (what the user asked for — e.g. "records opened in our custom LWC viewer
don't show in Recent Items")

## Eligibility gate (all must be YES before you add the clause)

- [ ] A **logged-in user** is viewing (or referencing) the records in *this* request.
- [ ] The code path is **user-facing** — NOT a trigger, batch, `@future`, Queueable, scheduled
      job, or integration-user context.
- [ ] The query can be **bounded** to the specific record(s) the user is looking at
      (`WHERE Id = :id` / `WHERE Id IN :ids`) with a `LIMIT`.
- [ ] The target object exposes `LastViewedDate` / `LastReferencedDate` — standard objects do; a
      **custom object needs a custom tab** (visibility not required) or the query throws
      `No such column`.

> If any box is NO, do **not** add the clause. The docs: use it "only when you are sure that the
> retrieved records will definitely be viewed by the logged-in user, else the clause incorrectly
> updates the usage information for the records."

## Clause choice

| The interaction is… | Use | Field written |
|---|---|---|
| A full view of the record in a custom UI | `FOR VIEW` | `LastViewedDate` (→ Recent Items) |
| A lighter reference (mobile card, custom page, preview) | `FOR REFERENCE` | `LastReferencedDate` |
| You think you need both | Pick the one matching the real interaction | (no documented combined single-query syntax) |

**Chosen clause:** ________________  **Object:** ________________

## Canonical safe snippet (fill in the blanks)

```apex
public with sharing class __ObjectViewSelector extends BaseSelector {
    // Call ONLY from a user-facing controller when the user opens/references this record.
    public __SObjectType selectForView(Id recordId) {
        assertNotNull(recordId, 'recordId');
        List<__SObjectType> rows = Database.queryWithBinds(
            'SELECT Id, Name ' +                         // add the fields the UI needs
            'FROM __SObjectType ' +
            'WHERE Id = :recordId ' +                    // bound to the viewed record
            'LIMIT 1 ' +
            'FOR VIEW',                                   // or FOR REFERENCE — see table above
            new Map<String, Object>{ 'recordId' => recordId },
            userMode()                                   // AccessLevel.USER_MODE
        );
        return rows.isEmpty() ? null : rows[0];
    }
}
```

## Verification

- [ ] Ran `scripts/check_soql_for_view_and_for_reference.py --manifest-dir <src>` — no warnings.
- [ ] Opened the surface as a test user; the viewed record appears in Recent Items /
      search auto-complete.
- [ ] Confirmed unrelated records were **not** polluted (no unexpected Recent Items entries).
- [ ] Confirmed no reporting/compliance logic relies on `RecentlyViewed` (it ages out at 90 days
      and truncates to 200 rows per object).

## Notes

(Record any deviation from the standard pattern and why — e.g. why a custom tab was created, or
why the clause was intentionally omitted in a shared selector method reused by async code.)
