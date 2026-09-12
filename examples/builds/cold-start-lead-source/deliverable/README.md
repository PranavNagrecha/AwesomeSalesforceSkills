# Preserve Lead Source Through Conversion — "Original Lead Source" on Opportunity

**Client request:** "When a Lead is converted, the new Opportunity should carry the Lead's Lead
Source in a custom field called Original Lead Source, so marketing can report on it later without
it being overwritten."

**Status:** Design complete, not deployed. No org was available and none was touched. Everything
below is a review-ready spec + deploy-ready metadata for an admin/developer to deploy from a
sandbox. Nothing here was run against a live org.

**Confidence: HIGH** on the mechanism and the metadata shape (grounded in the SfSkills repo's
`admin/lead-management-and-conversion` skill and the platform doc quotes it carries). **MEDIUM** on
two business assumptions called out below, which I answered myself in the client's absence — see
"Questions Asked, and How I Answered Them."

---

## 1. Why this isn't a one-checkbox change

The natural-sounding plan — "map Lead Source to a new Opportunity field in Setup > Map Lead
Fields" — does not work, for a reason worth stating up front so it isn't rediscovered the hard way:

- **Map Lead Fields only accepts *custom* Lead fields as the source.** Standard fields (First Name,
  Phone, Company, **Lead Source**, etc.) already have a hardcoded platform mapping that "cannot be
  removed, only supplemented" (`skills/admin/lead-management-and-conversion/SKILL.md`, "Lead
  Conversion Field Mapping"). You cannot point `LeadSource` at a different, additional target
  through that UI or through the `LeadConvertSettings.objectMapping` metadata — that block "carries
  **custom** fields only" (`references/metadata-examples.md` §1).
- **The good news: you don't need to.** `LeadSource` is one of the platform's standard-to-standard
  mappings, and Opportunity already has a standard `LeadSource` field — it is in fact the *same*
  global picklist definition shared across `Account.AccountSource`, `Contact.LeadSource`,
  `Lead.LeadSource`, and `Opportunity.LeadSource` ("one edit hits five fields",
  `references/metadata-examples.md`, "How to read the table"). So **Opportunity.LeadSource is
  already populated automatically** the moment a Lead converts. Nothing to configure there.
- **The actual problem is that `Opportunity.LeadSource` is an ordinary, editable field.** Once the
  Opportunity exists, any user with edit access can change it — re-attributing a deal, cleaning up
  what looks like a wrong value, or reusing the field for something else mid-pipeline. There is no
  platform mechanism that protects a standard field from being overwritten after creation. That is
  precisely what the client means by "without it being overwritten": marketing needs an **immutable
  snapshot** of what Lead Source was *at the moment the Opportunity was created*, independent of
  whatever the mutable standard field says six months later.

So the real deliverable is: a new custom field that captures the value once, at creation, and is
never written to again by anyone but the automation that sets it.

---

## 2. Design

### 2a. New field: `Opportunity.Original_Lead_Source__c`

Text(255), not required, not unique, history tracking on. Text rather than a picklist deliberately —
a picklist copy of the global Lead Source value set would need to be kept in sync by hand every time
someone adds a Lead Source value (the exact trap flagged as Gotcha 5 in the source skill: "Picklist
Value Mismatches on Field Mapping Cause Silent Transfer Failure" — same failure mode applies to any
picklist that has to mirror another picklist's value set over time). A Text field snapshotting
whatever string `LeadSource` held sidesteps that maintenance burden entirely, at the cost of not
being restricted-picklist-clean for reporting (it will always match a valid Lead Source value at the
moment it's written, since it's copied verbatim from a real picklist selection — so this is a
theoretical cost, not a practical one).

File: `force-app/main/default/objects/Opportunity/fields/Original_Lead_Source__c.field-meta.xml`
(this package).

### 2b. Automation: before-save Flow, not a Setup mapping, not Apex

Per `standards/decision-trees/automation-selection.md`, Q1 → Q2: *"A record change... Does the
logic run in under ~10s and touch only fields on the record itself? Yes → **Before-save
record-triggered Flow**."* This is exactly that shape — one field on the triggering record, set from
another field on the same record, no cross-object DML, no callout. Apex would be over-engineering
for a same-record field copy; the repo's own strategic default ranks Flow above Apex for new work of
this shape.

Before-save (not after-save) specifically, because before-save flows are described in
`templates/flow/RecordTriggered_Skeleton.flow-meta.xml`'s own choice matrix as "field updates on the
triggering record only. ~10x faster than after-save" — no reason to pay the after-save cost for a
same-record assignment.

**Trigger:** Opportunity, `RecordBeforeSave`, `Create` only.
**Entry criteria (on the start element, so the interview doesn't even spin up otherwise):**
- `LeadSource` is not null
- `Original_Lead_Source__c` is null

**Action:** one Assignment element — `Original_Lead_Source__c := LeadSource`.

**Why "on create" and not "on every conversion":** Opportunity has no standard field pointing back
to the Lead it was converted from (the pointer only exists in the other direction —
`Lead.ConvertedOpportunityId`). There is no clean, declarative way to test "was this Opportunity
just created by a lead conversion" from the Opportunity side. The entry criteria above (`LeadSource`
populated, snapshot field still blank) achieve the same result without needing that signal: they
fire once, at creation, whether the Opportunity came from a Lead conversion or was created directly
with a Lead Source chosen on the New Opportunity form — and the guard (`Original_Lead_Source__c` is
null) makes the flow inert on every subsequent save, so a rep changing `LeadSource` later cannot
retrigger it. I flagged this as a scoping decision below rather than assuming it silently.

File: `force-app/main/default/flows/Opportunity_Capture_Original_Lead_Source.flow-meta.xml`.

### 2c. Field History Tracking (recommended, not strictly required)

`trackHistory` is set `true` on the new field so marketing/ops can see in Field History that the
value was set once at creation and never touched again — useful the first time someone asks "are we
sure this never changes?" This only takes effect if:
- Field History Tracking is enabled at the Opportunity object level (`enableHistory` on
  `objects/Opportunity/Opportunity.object-meta.xml`), and
- The object is under its 20-tracked-fields cap.

Both must be confirmed in the target org before deploy — I have no org access to check either, so
this is called out explicitly rather than assumed. If either is already maxed out or off, deploy
with `trackHistory` `false` instead; it does not change the field's core behavior.

### 2d. Deploy order

1. `CustomField` — `Opportunity.Original_Lead_Source__c` (the Flow references it, so it must exist
   first).
2. `Flow` — `Opportunity_Capture_Original_Lead_Source`, active.

`package.xml` in this folder lists both in that order.

---

## 3. Questions Asked, and How I Answered Them

The source skill's own "Questions to Ask Before Configuring" table is written for the full lead
management/conversion surface; most of it (Web-to-Lead volume, queue-owned leads, bulk conversion
limits) doesn't apply to a single-field snapshot. Two questions from it *do* apply here, and no one
was available to answer them in real time. I answered as a reasonable, business-minded client would,
and I'm recording that explicitly rather than quietly picking a default:

| Question | Why it matters here | How I answered it, as the client | Confidence |
|---|---|---|---|
| Should this only capture Lead Source from Opportunities created via Lead conversion, or from every Opportunity (including ones sales creates directly)? | Determines whether the flow needs a conversion-specific signal (which doesn't exist declaratively) or a simpler creation-time snapshot | **Every Opportunity.** The stated goal is a stable source-of-truth for marketing reporting; excluding directly-created Opportunities would just create a second, inconsistent reporting gap. A rep manually picking a Lead Source on a new Opportunity is exactly the kind of value marketing also wants preserved. | MEDIUM — reasonable default, but confirm with marketing before go-live in case they specifically only want conversion-sourced Opportunities counted |
| Text field or restricted picklist for `Original_Lead_Source__c`? | Affects reporting cleanliness vs. ongoing maintenance | **Text.** Avoids the picklist-value-drift failure mode the source skill documents (Gotcha 5) for any field that has to mirror another picklist's values over time; a snapshot field only ever receives values that were already valid picklist selections, so reporting cleanliness is not actually at risk. | HIGH |
| Should the field be visible/editable on page layouts? | An "immutable" field that's editable on the layout isn't really immutable | **Read-only for all profiles** (add to layouts as a display-only field, or omit `fieldPermissions` edit access in the permission set layer). Not included in this deliverable's metadata — page layout and permission-set changes are per-org and out of scope for a metadata patch; flagged as a deployment follow-up below. | HIGH |

---

## 4. Test Plan (sandbox — nothing here touches production)

Adapted from the source skill's own verification pattern (`references/metadata-examples.md` §8,
Query 3 — "a row where the source field is populated but the target is null is a mapping that did
not take"):

1. Deploy the field and the Flow (active) to a sandbox.
2. Convert a test Lead that has a Lead Source value set, creating an Opportunity. Confirm
   `Original_Lead_Source__c` on the resulting Opportunity matches `LeadSource`.
3. Manually change `LeadSource` on that Opportunity to a different value. Confirm
   `Original_Lead_Source__c` does **not** change — this is the actual acceptance test for "without
   it being overwritten."
4. Create a second Opportunity directly (not via conversion) with a Lead Source chosen manually.
   Confirm the same snapshot behavior.
5. Create a third Opportunity with no Lead Source at all. Confirm `Original_Lead_Source__c` stays
   null (no error, no blank-string default) — the entry criteria should simply not fire.
6. Run this SOQL to check for any conversion where the snapshot didn't take (the batch-level version
   of step 2):

```sql
SELECT Id, Name, LeadSource, Original_Lead_Source__c, CreatedDate
FROM Opportunity
WHERE LeadSource != null
  AND Original_Lead_Source__c = null
ORDER BY CreatedDate DESC
LIMIT 200
```

Any row this query returns after go-live is either a record created before the Flow was activated
(expected — this deliverable does not backfill historical Opportunities; see below) or a real
regression.

**Not covered by this deliverable — flagged for a decision, not silently skipped:** historical
Opportunities created before this Flow goes live will have `Original_Lead_Source__c` blank even
though `LeadSource` is populated. Backfilling them is a one-time Data Loader update
(`UPDATE Opportunity SET Original_Lead_Source__c = LeadSource WHERE Original_Lead_Source__c = null
AND LeadSource != null`, run as an update, not through this Flow). I did not run it — it touches
existing production data — but it's a five-minute job once someone approves it.

---

## 5. Review Checklist

- [ ] `Original_Lead_Source__c` deployed to Opportunity, Text(255), not required
- [ ] `Opportunity_Capture_Original_Lead_Source` Flow deployed and **Active** (a deployed-but-Draft
      flow silently does nothing — easy to miss)
- [ ] Field History Tracking enabled at the Opportunity object level if `trackHistory` is to take
      effect, and the object has room under its 20-field tracking cap
- [ ] New field added to the Opportunity page layout(s) marketing/sales use, as read-only
- [ ] Field-level security: read access for whoever runs marketing reports, no edit access for
      anyone (enforces "never overwritten" at the UI layer, not just the Flow layer)
- [ ] Sandbox test conversion run; snapshot verified against a manual `LeadSource` edit (test 3 above)
- [ ] Decision on historical backfill made and, if yes, executed and verified
- [ ] Marketing/reporting team confirmed the "every Opportunity, not just conversion-sourced" scope
      decision in §3

---

## 6. Process Observations

**What was healthy:** the exact scenario this client described — a custom field that must survive
Lead conversion — already had a documented, source-grounded pattern in the toolkit
(`admin/lead-management-and-conversion`, "Pattern: Zero Data Loss Lead Conversion Field Mapping"),
including the specific gotcha (silent overwrite / silent drop) that motivates the request. No new
skill content was needed.

**What was concerning:** the literal ask ("map Lead Source to a new field via conversion mapping")
does not map onto an actual platform mechanism, because Lead Source is a standard field and Map Lead
Fields only accepts custom source fields. An implementer following the client's wording verbatim,
without checking `LeadConvertSettings.objectMapping`'s "custom fields only" constraint, could easily
spend time trying to configure a mapping that Setup will not offer. Anticipating that
misunderstanding — rather than just answering the literal request — is where most of the value in
this deliverable sits.

**What was ambiguous:** whether the snapshot should be scoped to conversion-created Opportunities
only, versus every Opportunity. I resolved it as documented in §3 and flagged the confidence level;
it is the one place a real client conversation could change the design (narrowing the entry
criteria would require a different signal than "Opportunity has no back-pointer to its source Lead"
allows declaratively — likely an Apex-side flag set during `Database.convertLead`, which would pull
`apex/lead-conversion-customization` into scope. Not needed for the stated ask.).

**Suggested follow-ups (not auto-chained, per the repo's agent rules):**
- `permission-set-architect` / a plain profile review, for the field-level-security "read-only for
  everyone" decision in §3.
- A short marketing-reporting-requirements pass
  (`skills/admin/marketing-reporting-requirements`) if this snapshot field is going to feed a
  specific dashboard or KPI, to confirm the field name and rollup the marketing team expects.
- The historical-backfill Data Loader job in §4, as a separate, explicitly-approved change.

---

## 7. Citations

- `skills/admin/lead-management-and-conversion/SKILL.md` — "Lead Conversion Field Mapping" section
  (standard-field mappings are fixed and cannot be redirected); "Pattern: Zero Data Loss Lead
  Conversion Field Mapping"; "Questions to Ask Before Configuring" table (source for the
  question-and-consequence framing reused in §3)
- `skills/admin/lead-management-and-conversion/references/gotchas.md` — Gotcha 1 (unmapped fields
  silently dropped, the failure mode this whole request exists to prevent) and Gotcha 5 (picklist
  value-set drift, grounds the Text-vs-picklist decision in §2a)
- `skills/admin/lead-management-and-conversion/references/metadata-examples.md` — `objectMapping`
  "carries custom fields only"; `LeadSource` global-picklist sharing across Account/Contact/Lead/
  Opportunity; §8 verification-query pattern reused in §4
- `skills/admin/lead-management-and-conversion/references/examples.md` — Example 2 (closest existing
  worked example: custom-field-survives-conversion, same shape of problem)
- `skills/apex/lead-conversion-customization/SKILL.md` — read to confirm this request stays
  declarative; its own scope note explicitly excludes "configuring lead conversion field mapping in
  Setup UI," which is what confirmed the admin skill (not this one) is the right source
- `skills/admin/custom-field-creation/references/metadata-examples.md` §1 — canonical `CustomField`
  XML shape (`required`, `trackHistory`/object-level `enableHistory` dependency, description vs.
  inlineHelpText) used to build §2a's field
- `standards/decision-trees/automation-selection.md` — Q1 → Q2, resolves Flow vs. Apex for this
  request; before-save specifically justified against `templates/flow/RecordTriggered_Skeleton.flow-meta.xml`'s
  choice-matrix comment
- `templates/flow/RecordTriggered_Skeleton.flow-meta.xml` — base template adapted for
  `Opportunity_Capture_Original_Lead_Source.flow-meta.xml`

## 8. What This Deliverable Does NOT Do

- Does not deploy anything to any org. No `sf` deploy command was run.
- Does not touch the SfSkills repository itself (no skill, agent, or registry file was modified —
  this is a client engagement, not a library change; nothing here belongs under `skills/`,
  `registry/`, or `docs/reports/` in that repo).
- Does not backfill historical Opportunity records (§4).
- Does not design page layout or permission-set changes beyond the field-level-security
  recommendation in §3 (flagged as a follow-up, not designed here).
- Does not verify against a real org — no `target_org_alias` was supplied and none was available;
  every claim above is grounded in the cited skill content and official-source quotes it carries,
  not in a live describe/tooling-query.
