# Gotchas — Campaign Planning And Attribution

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.
Line references are into the plain-text extracts of the Summer '26 (v62)
[Object Reference](https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf)
and [Metadata API Developer Guide](https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf).

## Gotcha 1: The Parent Campaign's `ActualCost` Is Not a Rollup — the Hierarchy Total Has a Different Name

**What happens:** A dashboard built on the parent campaign's `ActualCost`,
`AmountWonOpportunities` or `NumberOfResponses` shows only what was typed on that one
record, and reads as zero for a program whose spend all sits on its children. The Object
Reference defines `ActualCost` as "the amount of money spent to run the campaign"
(object_reference.txt:57100–57105) — this campaign, full stop. Hierarchy aggregation
lives in two independently named families of calculated fields: `HierarchyActualCost`,
`HierarchyBudgetedCost`, `HierarchyExpectedRevenue`, `HierarchyAmountAllOpportunities`,
`HierarchyAmountWonOpportunities`, `HierarchyNumberOfLeads`, `HierarchyNumberOfResponses`
(object_reference.txt:57273–57359) and `TotalAmountAllOpportunities`,
`TotalAmountAllWonOpportunities`, `TotalNumberofLeads`, `TotalNumberofOpportunities`,
`TotalNumberofResponses`, `TotalNumberofWonOpportunities`
(object_reference.txt:57704–57810).

**When it occurs:** Every first attempt at a program ROI dashboard, because the field
picker shows the short names first and they look like the obvious ones. It also surfaces
when someone copies a report from an org where all spend happened to be entered on the
root record, so the two field families agreed by accident.

**How to avoid:** Choose one family per report — `Hierarchy*` or `Total*` — and say
which in the report description; a dashboard mixing them looks inconsistent for reasons
no viewer can see. Reserve the short-name fields for single-campaign tactic reporting.
Note also that `HierarchyNumberOfLeads` and `HierarchyNumberOfResponses` are documented
with type `currency` even though they hold counts (object_reference.txt:57338, 57354),
so a formula or Apex that assumes `Integer` on those two fields will not behave.

---

## Gotcha 2: CCI and Campaign Influence 1.0 Are Mutually Exclusive by Contract, Not Merely in Conflict

**What happens:** Runbooks that say "disable standard Campaign Influence before enabling
CCI" describe a step that cannot exist. `CampaignSettings.enableCampaignInfluence2` is
documented as "Indicates whether Customizable Campaign Influence is enabled (true) or not
(false). When true, Campaign Influence 1.0 is hidden from users and is no longer active.
The default value is **true**" (api_meta.txt:111568–111571). The 1.0-era switch,
`enableAutoCampInfluenceDisabled`, carries the reciprocal constraint:
"`enableCampaignInfluence2` must be **false** to use this setting"
(api_meta.txt:111556–111559). And `CampaignInfluence` itself is CCI-only — the Object
Reference stamps "This information applies only to Customizable Campaign Influence and
not to Campaign Influence 1.0" on both the object and its model
(object_reference.txt:57898, 58007). The two systems do not both write
`CampaignInfluence` rows.

**When it occurs:** An admin follows a years-old blog post, hunts Setup for
auto-association rules that are no longer reachable, and concludes the org is broken.
Or a plan budgets a data-hygiene phase for "duplicate influence records from two
systems" that were never going to exist.

**How to avoid:** Retrieve `settings/Campaign.settings-meta.xml` and read
`enableCampaignInfluence2` before writing any step about enabling or disabling
anything. If it is true, CCI is on and 1.0 is already inactive; the real work is the
model configuration. Treat `enableCampaignHistoryTrackEnabled`,
`enableCampaignMemberTWCF` and `enableSuppressNoValueCI2` as retrieve-only — all three
are documented as read-only and reserved for system use
(api_meta.txt:111566, 111573, 111585).

---

## Gotcha 3: Deactivating an Influence Model Deletes Its Records

**What happens:** Setting `isActive` to false on a `CampaignInfluenceModel` does not
park the model — it destroys its data. The Metadata API guide is unambiguous: "Active
models can generate campaign influence records. **Deactivating a model deletes its
campaign influence records.** Custom models are always active and this field is ignored"
(api_meta.txt:31892–31895). Reactivating the model does not bring the rows back; a
custom model has to regenerate them, and a locked model can only be repopulated through
the API. There is no recycle bin step in the documented behaviour.

**When it occurs:** Quarter-end tidy-up, when someone deactivates last quarter's
experimental model to clean the picker. Also during a deploy: pushing a
`.campaignInfluenceModel` file with `isActive` flipped to false is a data-deleting
deploy that no validation-only run will warn about, because the deploy itself is valid.

**How to avoid:** Treat `isActive` as a data-retention flag, not a visibility flag.
Name an owner for model lifecycle in the plan record and put deactivation in the release
change-control list alongside field deletions. If a model needs to stop appearing to
users, change which model is default (`isDefaultModel`) — that changes what shows in the
related lists without touching rows. Export the model's `CampaignInfluence` rows to a
file before any deactivation you cannot avoid.

---

## Gotcha 4: An Invalid Campaign Member Status Is Silently Coerced, Not Rejected

**What happens:** A `CampaignMember` insert or update carrying a `Status` the campaign
does not define does **not** fail. The Object Reference spells out both branches: "If
the specified Status value isn't a valid status, the API assigns the default status to
the Status field and updates the HasResponded field with the associated value. However,
if the given Campaign doesn't have a default status, the API assigns the value specified
in the call to the Status field, and the HasResponded field is set to false"
(object_reference.txt:58572–58577). The load reports 100% success and the funnel is
wrong. A second trap sits next to it: `HasResponded` is read-only and can only be moved
by `Status`, and "when you create or update campaign members, use the text value for
Status instead of the ID from the CampaignMemberStatus object"
(object_reference.txt:58504–58513) — a payload built from an Id lookup coerces on every
row.

**When it occurs:** Any Data Loader or middleware run whose status column came from a
spreadsheet, a different campaign's status set, or a system with its own vocabulary.
Also on the first load after someone renames a status label.

**How to avoid:** Validate the status column against
`SELECT Label FROM CampaignMemberStatus WHERE CampaignId = :id` before the load, not
after. After any load, reconcile counts by status rather than by row count — the row
count will always match. Design status sets so that the default is the least harmful
value (`Sent`, `Invited`, `Targeted`), never the responded one, so a coercion
under-reports instead of inventing responses.

---

## Gotcha 5: Only the Default Model's Records Appear in the UI

**What happens:** A second or third attribution model is configured, rows exist, SOQL
returns them — and the Campaign Influence related list on opportunities, the Influenced
Opportunities related list on campaigns, and the Campaign Statistics section on campaigns
all show nothing new. `IsDefaultModel` controls exactly those three surfaces:
"CampaignInfluence records associated with the default model appear in 3 locations…
The value of IsDefaultModel can only be true for 1 model at a time"
(object_reference.txt:58055–58066). The metadata field adds that "a model must be active
to become the default model" (api_meta.txt:31897–31902).

**When it occurs:** When a team builds first-touch and last-touch side by side and
expects both in the opportunity page layout. Also when a deploy sets `isDefaultModel`
true on a new model, silently demoting the model the sales team had been reading for a
year.

**How to avoid:** Decide the default model as a named business decision, not a deploy
side effect — it is the model whose numbers people will quote in a meeting. Everything
else is report-and-query only, so build those views as reports on `CampaignInfluence`
grouped by `ModelId`, and say so in the report description. A deploy that changes
`isDefaultModel` belongs in the release notes.

---

## Gotcha 6: `CampaignInfluence` Has No Field Called `Revenue`

**What happens:** SOQL, report columns, formulas and Apex written against `Revenue` on
`CampaignInfluence` fail to compile or fail at runtime with "No such column". The
attributed-money field is **`RevenueShare`** — "the amount of revenue from the related
opportunity attributed to the campaign" (object_reference.txt:57987–57992). The full
field list is `CampaignId`, `CampaignMemberId`, `ContactId`, `Influence`, `ModelId`,
`OpportunityContactRoleId`, `OpportunityId`, `RevenueShare`
(object_reference.txt:57915–57992). Two of those, `CampaignMemberId` and
`OpportunityContactRoleId`, are documented as "Not available in the UI" — they exist
only to the API, so a report builder will not show them.

**When it occurs:** Every time a query is copied from a blog post, and whenever an
assistant generates the query from the phrase "attributed revenue". `Influence` is a
percent of the opportunity's `Amount`, not a currency, so substituting it does not help.

**How to avoid:** Query `RevenueShare` for money and `Influence` for the percentage, and
remember that only two of the eight fields are UI-visible when planning a report type —
if the design needs `CampaignMemberId`, it needs the API, not a report.

---

## Gotcha 7: Rows Written Against the Primary Campaign Source Model Are Deleted on Recalculation

**What happens:** An integration or a backfill script writes `CampaignInfluence` rows
under the Primary Campaign Source model, they appear, and then they vanish. The Object
Reference states the rule directly under Usage: "Use this object to create campaign
influence records for your custom campaign influence models. **Don't create campaign
influence records for the Primary Campaign Source model.** Records added to the Primary
Campaign Source model via the API are deleted when the model is recalculated"
(object_reference.txt:57996–57999). Primary Campaign Source is `ModelType` value `1`
and is the model Salesforce supplies (object_reference.txt:58003–58005, 58105–58118).

**When it occurs:** Data migrations that recreate historical attribution and pick the
first model in the list. Also when an integration resolves the model by
`IsDefaultModel = true` and the default happens to be Primary Campaign Source.

**How to avoid:** Resolve the target model by `DeveloperName`, never by "the default" or
"the first one". Write only to custom models, and set `isModelLocked` true on them so the
API is the documented, single writer ("Records for locked models can only be added,
updated, or deleted via the API", object_reference.txt:58068–58074). Add an assertion to
the integration that refuses to write when `Model.ModelType` is `1`.

---

## Gotcha 8: A Campaign Member Is Lead XOR Contact, and Sending Both Succeeds Anyway

**What happens:** A `CampaignMember` "must contain either a ContactId or a LeadId, but
can't contain both. Any attempt to create a single record with both results in a
**successful insert** but only the ContactId is inserted"
(object_reference.txt:58553–58555). No error, no warning — the lead side of the
relationship is dropped and the load looks clean. The guide's own workaround is to create
two separate records on the campaign, one for the lead and one for the contact, and it
notes the one exception: "If you want to track lead-based campaign members you convert to
contacts, provide both a ContactId and a LeadId" (object_reference.txt:58566–58567).
Separately, standard lead and contact fields are exposed on `CampaignMember` but "you
can't query them directly" — a phone number has to come from a subquery against the
parent object (object_reference.txt:58557–58560).

**When it occurs:** Migrations that build a single member row per person from a source
system that has one identity per human, and any middleware that populates every id column
it can resolve "to be safe".

**How to avoid:** Decide per row which side is authoritative and null the other before
the call. Reconcile the load by counting members per campaign split by the `Type` field
("indicates if the campaign member is a lead or a contact") rather than by success count.
When the requirement really is to follow a lead through conversion, send both ids
deliberately and note why in the load spec.

---

## Gotcha 9: A Member Status That Is Default or In Use Cannot Be Deleted

**What happens:** Cleaning up a campaign's status picklist fails on exactly the values
someone most wants gone. The Object Reference puts it in Special Access Rules: "You can't
delete a CampaignMemberStatus if that status is designated as the default status or if
the status is currently used in a Campaign" (object_reference.txt:58609). Two structural
rules sit alongside it, both dating from API version 39.0: "at least one
CampaignMemberStatus on each campaign must have a hasResponded value of true"
(object_reference.txt:58627) and "there must be a default CampaignMemberStatus defined for
every campaign" (object_reference.txt:58636). `SortOrder` is a "unique number order"
(object_reference.txt:58666), so two statuses cannot share a position.

**When it occurs:** Mid-quarter status rationalisation, and template-campaign cloning
where the clone inherits statuses nobody intends to use but which are now in use by
virtue of being on members.

**How to avoid:** Reorder before deleting — promote the replacement to default first,
migrate members off the doomed status with an update that sets the new status *text*,
then delete. Because there is no `CampaignMemberStatus` metadata type, none of this
deploys: it is per-campaign sObject work, and the plan record in
`references/worked-examples.md` § 1 exists so the intended set is reviewable even though
it cannot be shipped as XML.
