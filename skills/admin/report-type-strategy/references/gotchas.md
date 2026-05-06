# Gotchas — Report Type Strategy

Non-obvious Custom Report Type behaviors that bite in production.

---

## Gotcha 1: The CRT's join shape cannot be changed after creation

Once you click Save with "must have at least one related",
switching to "may or may not have" later requires deleting the
CRT and recreating it. All reports built on the CRT break. Get
the join semantics right the first time.

---

## Gotcha 2: 60-field display limit, 1,000-field hard limit

The CRT layout shows 60 fields by default. Past 60, fields are
findable only via search in the report builder. The hard cap is
1,000 fields; past 1,000, the CRT will not save. Curate fields
intentionally — most CRTs need under 50.

---

## Gotcha 3: Cross Filter is the way to do "without"

Salesforce supports "Accounts without Opportunities" through the
Cross Filter mechanism (the report's Filters tab), not through a
CRT join. Trying to model this in the CRT alone produces wrong
results.

---

## Gotcha 4: Person Account fields appear on both Account and Contact

In a Person Account org, fields you defined on Contact also
appear on Account in CRTs. This is expected but confusing — the
report builder may show "Account: Email" sourced from the Contact
side. Always check the field's source object before relying on
its values.

---

## Gotcha 5: Standard report types update implicitly with object changes

Standard report types add new fields to their layout when admins
add fields to the object — without a manual update. CRTs do not.
A new field on Account does not appear in your CRT until an admin
adds it. This is an upside (no surprises) and a downside (stale
field lists drift).

---

## Gotcha 6: Master-detail traversal is automatic; lookup is not

In a CRT, you can pull fields from a master-detail parent
automatically through the parent's API name. For a lookup parent,
you must add the parent as a "related via lookup" object on the
CRT — it is not auto-resolved.

---

## Gotcha 7: Deleted CRTs delete every report on them

Reports built on a deleted CRT do not migrate; they show "report
type unavailable" and must be rebuilt against a different CRT.
Before deleting, list dependent reports (Setup → Reports →
filter by Report Type).

---

## Gotcha 8: Activity reports are special

Tasks and Events have a custom storage model and do not appear as
a normal secondary object on most CRTs. The "Tasks and Events"
standard report type, the "Activities with X" standard report
types, and a few CRT options exist. Avoid trying to add Task as
a generic secondary — it produces incomplete data.

---

## Gotcha 9: Joined reports cannot use cross-block bucket fields

Bucket fields work per-block in joined reports. There is no
cross-block bucket. If you need a bucket grouping that spans
blocks, build the bucket as a formula field on the underlying
record before reporting.
