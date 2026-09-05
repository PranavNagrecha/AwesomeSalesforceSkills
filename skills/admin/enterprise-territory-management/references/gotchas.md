# Gotchas — Enterprise Territory Management

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Activating a Territory Model Triggers Immediate Full Assignment Recalculation

**What happens:** The moment a territory model is transitioned from Planning to Active, Salesforce queues a background job to run all account assignment rules across the entire model. This is not deferred until business hours — it starts immediately. For orgs with tens of thousands of accounts, this job can run for several hours, during which assignment data is transitional and reports may show incomplete territory coverage.

**When it occurs:** Every time a model is activated (Planning → Active). There is no way to defer or batch this recalculation.

**How to avoid:** Schedule activation during off-peak hours (nights or weekends). Before activation, validate rule coverage in preview mode. Monitor the `Territory2AlignmentLog` object to track job completion. Do not treat territory reports or forecasts as reliable until the log shows all rules have finished running.

---

## Gotcha 2: Assignment Rules Are Not Retroactive — New Rules Don't Apply to Existing Accounts

**What happens:** When you create a new account assignment rule or modify an existing one, the rule is not automatically applied to accounts that already exist. Only accounts created or updated after the rule is saved (with IsActive = true) will be evaluated automatically. Existing accounts remain in their current territory assignments unchanged.

**When it occurs:** Any time a new rule is added or a rule's criteria are changed in an active model. This catches practitioners off guard when they add a new territory mid-year and expect all qualifying accounts to immediately appear in it.

**How to avoid:** After creating or modifying an assignment rule, manually run assignment rules at the territory level (for targeted updates) or the model level (for comprehensive recalculation). Do this during off-peak hours for large account volumes. Build this step into your territory change runbook.

---

## Gotcha 3: Archived Territory Models Cannot Be Reactivated

**What happens:** When a territory model is moved to Archived state, it becomes permanently read-only. The model cannot be promoted back to Active or Planning. If you accidentally archive your active model or archive a model you intended to reuse, you must recreate the entire structure from scratch — hierarchy, territory types, assignment rules, and user memberships.

**When it occurs:** Any time an admin clicks "Archive" on a territory model, including accidentally archiving the wrong model or archiving a Planning model that was being iterated.

**How to avoid:** Treat the Archive action as permanent and irreversible — build a confirmation step into your change process. Keep alternative territory designs in Planning state, not Archived. Before archiving, export the territory hierarchy structure and rule configurations for reference. Consider deploying a backup of the model configuration via Metadata API before archiving.

---

## Gotcha 4: Territory Forecast Sharing Is Not Supported

**What happens:** Territory-based forecast types do not support the forecast sharing feature that role-based forecast types offer. If a user tries to share their territory forecast with a colleague, the action has no effect. This is by design — Salesforce explicitly documents this limitation — but it frequently surprises teams migrating from role-based to territory-based forecasting.

**When it occurs:** When an organization enables territory-based forecasting and sales managers expect the same forecast sharing behavior they had with role-based forecasts.

**Corroborating evidence in the API surface:** the *legacy* `Territory` object and metadata type both carry a `MayForecastManagerShare` field — "Indicates whether the forecast manager can manually share their own forecast." Neither the `Territory2` object nor the `Territory2` metadata type has any equivalent. The capability was not carried forward. **UNVERIFIED (2026-09-04): the extracted Metadata API and Object Reference guides do not contain a sentence stating the limitation outright**; the absence of the field is inference, not a quotation. Confirm in Salesforce Help before telling a stakeholder it is by design.

**How to avoid:** Document this limitation during the territory design phase. If forecast sharing is a hard requirement, consider whether the organization can remain on role-based forecasting for forecast purposes while using territory-based assignment for account access and coverage. There is no workaround within ETM.

---

## Gotcha 5: Territory Membership Grants Access Regardless of Account Owner — OWD Still Sets the Floor

**What happens:** Territory membership adds access to accounts assigned to a territory, regardless of account ownership. This is intentional and useful, but it means that users gain visibility to accounts they do not own — sometimes surprising account owners or managers who expect OWD Private to fully restrict access.

Conversely, if OWD for Account is already set to "Public Read/Write," territory membership adds no additional access — the OWD floor already grants everyone access. Territory access is purely additive and cannot be used to restrict access below the OWD setting.

**When it occurs:** When admins configure territory membership assuming it can restrict access (it cannot), or when account owners are surprised that reps in their territory can see "their" accounts.

**How to avoid:** Treat territory membership as an access-expansion tool, not an access-restriction tool. If fine-grained restriction is needed, design OWD and sharing rules first (see the sharing-and-visibility skill), then layer ETM access on top. Communicate to account owners that territory membership is intentional and by design.

---

## Gotcha 6: `AccountTerritoryAssignmentRule` Is the Legacy Object — ETM Rules Are `ObjectTerritory2AssignmentRule`

**What happens:** Code, a Data Loader mapping or a SOQL audit written against
`AccountTerritoryAssignmentRule` returns nothing useful in an ETM org, because that object belongs to
the original Territory Management feature. Its Object Reference entry cross-references `Territory` and
`UserTerritory` — the pre-Territory2 objects — and its `TerritoryId` field points at `Territory`, not
`Territory2`. The ETM equivalents are `ObjectTerritory2AssignmentRule` (fields `DeveloperName`,
`MasterLabel`, `ObjectType`, `BooleanFilter`, `Territory2ModelId`) and `ObjectTerritory2AssignmentRuleItem`
(`Field`, `Operation`, `Value`, `SortOrder`, `RuleId`). In Metadata API the type is `Territory2Rule`.

Both objects are described as "Available if Sales Territories has been enabled," so the availability
sentence is no help in telling them apart.

**When it occurs:** Whenever an audit script, an LLM-generated query, or a migration mapping is written
from the older name — which is still the more common one in search results and in older org
documentation.

**How to avoid:** Search for `Territory2` in any object name before trusting it. In a rule audit, query
`ObjectTerritory2AssignmentRule` filtered by `Territory2ModelId`, not `AccountTerritoryAssignmentRule`.
Note the structural difference too: the ETM rule belongs to a **model**, not to a territory. The link to
a territory is a separate association — `ruleAssociations` in Metadata API — so a rule can exist,
deploy cleanly and assign nothing because no territory points at it.

---

## Gotcha 7: Sales Territories Metadata Cannot Travel in a Change Set

**What happens:** The Usage section of every Sales Territories metadata type — `Territory2`,
`Territory2Model`, `Territory2Rule`, `Territory2Type` and `Territory2Settings` — repeats the same
sentence: "Sales Territories components don't support packaging or change sets and aren't supported in
CRUD calls." A team on a change-set release process discovers this at the point of building the change
set, when the component types simply are not offered.

`Territory2` carries one narrow carve-out for packaging: "For unlocked packaging, Territory2 requires
packages without a namespace." `Territory2Model` states "Namespaces aren't supported for unlocked
packages." Neither of those reopens the change-set path.

**When it occurs:** At the first attempt to promote a territory model from a sandbox on a release train
whose only deployment mechanism is change sets.

**How to avoid:** Plan the ETM release as a source deploy (`sf project deploy start` with a manifest)
from the start, and get the Manage Territories permission provisioned for whoever runs it — the guide
requires it for every `deploy()` call on a territory management entity. See `admin/assignment-rules`
for the neighbouring case of rules that *do* ship in change sets, so the difference is explicit in the
release plan.

---

## Gotcha 8: The Access-Level Vocabulary Differs Between Metadata API and the SOAP/UI Picklists

**What happens:** `Territory2.accountAccessLevel` in Metadata API accepts `Read`, `Edit`, `All`. The same
setting on the `Territory2` **object** is a restricted picklist whose values are `Read Only`,
`Read/Write`, `Owner`. `opportunityAccessLevel`, `caseAccessLevel` and `contactAccessLevel` accept
`None`, `Read`, `Edit` in XML but appear as `Private`, `Read Only`, `Read/Write` on the object. Copying
a value seen in Setup or in a report into a `.territory2-meta.xml` file produces a deploy error rather
than a silent mis-set, but copying the other direction — writing `Read` into a Data Loader mapping for
`Territory2.AccountAccessLevel` — fails against a restricted picklist.

The org's sharing model then narrows the XML values further. If the Account sharing model is Public
Read/Write, the only valid `accountAccessLevel` values are `Edit` and `All`. For opportunities and cases
under Public Read/Write, and for contacts under Public Read/Write or Controlled By Parent, the guide
says to specify **no value at all** — an omitted element, not an empty one.

**When it occurs:** Hand-writing territory XML, or generating it from a spreadsheet that captured what
an admin saw on screen.

**How to avoid:** Retrieve one real territory first and copy its spelling. Confirm the Account OWD before
choosing `accountAccessLevel`, and leave the object's access element out entirely where the guide says
to specify no value. An omitted element is not a gap — it falls back to the matching
`default*AccessLevel` in `Territory2Settings`.

---

## Gotcha 9: Territory Type Priority — The Highest Integer Wins, Values Must Be Unique, and a Tie Assigns Nothing

**What happens:** The intuition that "priority 1" means "first" is backwards here. The Metadata API
guide's `Territory2Type.priority` description reads: "the filter examines all territories assigned to the
account that the opportunity is assigned to. The account-assigned territory whose territory type
priority is highest is then assigned to the opportunity. The `priority` field value on each territory
type must be unique." The Apex Reference Guide's own reference implementation confirms the direction in
code — it keeps a territory when `ota.Territory2.Territory2Type.Priority > tp.priority`.

Two consequences follow. Duplicate priority values across types are rejected. And when an account is
assigned to two territories that tie at the top priority, the opportunity gets **no** territory: the
guide says no territory is assigned, and the reference implementation writes `null` into the result map
for that opportunity, which clears any Territory2Id already set.

**When it occurs:** In any overlay design — a named-account or industry overlay layered on a geographic
tree — where an account legitimately belongs to two territories at once. It surfaces as opportunities
quietly dropping out of the territory forecast, not as an error.

**How to avoid:** Assign priorities so that the level you want to win OTA carries the largest integer,
and give the overlay type a value that is strictly greater or strictly less than the geographic type —
never equal. Before activation, run the tie query in `references/metadata-examples.md`
(`ObjectTerritory2Association` ordered by `Territory2.Territory2Type.Priority DESC`) against a sample of
multi-territory accounts and confirm no account has two rows at the top priority.

---

## Gotcha 10: Filter-Based Opportunity Territory Assignment Requires an Apex Class — There Is No Declarative Filter

**What happens:** Practitioners look for a filter builder in Setup and do not find one. Filter-based OTA
is configured through `Territory2Settings.opportunityFilterSettings`, whose subtype
`Territory2SettingsOpportunityFilter` has exactly three meaningful fields: `apexClassName`,
`enableFilter`, `runOnCreate`, plus `runMultiThreaded` (API 62.0+). The named class must implement
`TerritoryMgmt.OpportunityTerritory2AssignmentFilter` and its single method
`getOpportunityTerritory2Assignments(List<Id> opportunityIds)` returning `Map<Id,Id>`.

Two behaviours of that contract are easy to get wrong. Salesforce supplies only opportunities whose
`IsExcludedFromTerritory2Filter` is false. And the return map is three-valued, not two: an opportunity
mapped to a territory Id is assigned, an opportunity mapped to `null` has its existing `Territory2Id`
**cleared**, and an opportunity **absent from the map** keeps whatever it had. A filter that returns
`null` for everything it cannot classify will strip territories off opportunities that were correct.

`runMultiThreaded` carries its own warning: "Set this value to true only if you're assigning opportunity
or opportunity product splits, and your Apex code can run with multithreading."

**When it occurs:** As soon as territory-based forecasting is required, because an opportunity with no
`Territory2Id` does not appear in a territory forecast.

**How to avoid:** Budget for Apex, not configuration. Start from the `OppTerrAssignDefaultLogicFilter`
reference implementation in the Apex Reference Guide, which reproduces the default logic (0 territories
→ null, 1 → that territory, 2+ → the highest-priority one unless there is a tie). Be deliberate about
the omit-versus-null distinction, and set `IsExcludedFromTerritory2Filter` on opportunities that another
process owns rather than special-casing them inside the filter.

---

## Gotcha 11: Two Switches Silently Stop Assignment Rules From Evaluating a Record

**What happens:** An active rule looks correct, the model is Active, the account's field values match —
and the account still is not assigned. Two documented escapes bypass evaluation without logging
anything on the account.

The first is per record. Both the Metadata API `Territory2Rule.active` description and the Object
Reference `IsActive` descriptions carry the same exception: active rules run automatically on create
and edit "The exception is when the value of the `IsExcludedFromRealign` field on an object record is
true, which prevents record assignment rules from evaluating that record."

The second is org-wide and load-shaped. `Territory2Settings.tm2BypassRealignAccInsert` (API 53.0+): "If
true, account assignment rules don't run during account insert jobs." A data migration that flipped it
to reduce load, and a settings deploy that carried the value forward, both leave newly inserted accounts
unassigned indefinitely — there is no error and no queued work.

**When it occurs:** After a bulk load, a migration, or a settings file copied between orgs.

**How to avoid:** When triaging an unassigned account, check `IsExcludedFromRealign` on the record and
`tm2BypassRealignAccInsert` in `Territory2.settings` **before** re-reading the rule criteria. After any
load that ran with the bypass on, run assignment rules at the model level to backfill, and confirm
completion in `Territory2AlignmentLog` rather than assuming the job finished.

---

## Gotcha 12: A Model Archived in the Target Org Blocks Deployment of the Same Developer Name Forever

**What happens:** Model state gates `deploy()`, not just the UI. The guide: "You can only do a `deploy()`
operation for models in `Planning` or `Active` state. The same requirement applies to territories and
rules associated with those models." It then names the exact trap: "sometimes you can have a model in
`Planning` state on a sandbox org, and a model with the same developer name in `Archived` state on your
production org. The `deploy()` operation on production fails because that model's state is `Archived`
and that state prevents changes to the model."

Because developer names must be unique, Metadata API cannot route around it by creating a second model:
"if you have territory models in different orgs with identical developer names and you attempt a
`deploy()` operation, Metadata API attempts to create new models. However, that operation fails because
of the developer name conflict."

**When it occurs:** On the second attempt at a territory redesign — someone archived last year's `FY25`
model in production, and the sandbox rebuild reuses the name.

**How to avoid:** Version the developer name (`FY26_NA`, not `NA_Model`) so a retired model never blocks
its successor. Before promoting, query the target org for `SELECT DeveloperName, State FROM
Territory2Model` and confirm the incoming developer name either does not exist there or is in `Planning`
or `Active`. Deleting is not an escape either: `delete()` moves the model to `Deleting` and cascade
deletes all territories, rules and user associations in it.

---

## Gotcha 13: `Territory2ObjSharingConfig` Is a Read-Mostly SOAP Object for Leads — Not the Metadata That Controls Opportunity and Contact Access

**What happens:** Runbooks and generated advice frequently instruct the reader to "configure
`Territory2ObjSharingConfig`" to set territory members' access to Opportunities and Contacts. There is no
such metadata type to deploy. `Territory2ObjSharingConfig` is a SOAP object available in API version 56.0
and later whose supported calls are `describeSObjects()`, `query()`, `retrieve()` and `update()` — no
`create()` and no `delete()` — and it hangs off `TerritoryMgmtObjectConfig`, the org-level configuration
for the objects enabled through `Territory2Settings.supportedObjects`. That field's `objectType` is
documented with a single supported value: "The only supported object type is `Lead`."

Access to Accounts, Opportunities, Contacts and Cases is set somewhere else entirely: the
`accountAccessLevel`, `opportunityAccessLevel`, `contactAccessLevel` and `caseAccessLevel` fields on each
`Territory2`, falling back to the four `default*AccessLevel` fields in `Territory2Settings`. The
Metadata API surface that does correspond to `Territory2ObjSharingConfig` is `Territory2.objectAccessLevels`
(the `Territory2AccessLevel` subtype, API 57.0+, with `accessLevel` values `Read`, `Edit`, `Transfer`,
`All` and an `objectType` the guide illustrates with `Lead`).

**When it occurs:** Any time an ETM runbook, checklist or checker script is generated from an
authoritative-sounding but unsourced description of the feature, and again when a reviewer looks for a
`territory2ObjectSharing` file in source and does not find one.

**How to avoid:** Put Opportunity and Contact access in the territory files where it belongs, and treat
`Territory2ObjSharingConfig` purely as something you **query** to verify what Lead territory assignment
resolved to. If a checklist tells you to deploy it, the checklist is wrong.

---

## Gotcha 14: `UserTerritory2Association` Has No `update()` Call, and Removing a User Removes Their Access

**What happens:** `UserTerritory2Association` documents its supported calls as `create()`, `delete()`,
`describeSObjects()`, `query()` and `retrieve()`. `update()` is not among them, and the object "doesn't
support adding custom fields." So a change of `RoleInTerritory2` from `Sales Rep` to `Administrator` is
a delete plus an insert, not an update — and between those two DML statements the user is not a member
of the territory.

**UNVERIFIED (2026-09-04): the extracted guides do not state how quickly access is withdrawn when the
association row is deleted.** What they do document is that the row is the grant: territory-derived
`AccountShare` rows carry `RowCause` `Territory` (rule-assigned) or `Territory2AssociationManual`
(manually assigned), and access flows from membership. Treat the delete as immediately access-affecting
until you have measured otherwise in a sandbox.

Two related facts make the audit trail recoverable. `UserTerritory2AssocLog` (API 57.0+) records
assignment and unassignment with `StartDate` and `EndDate`, but only if Sales Territory and User
Tracking is switched on — `Territory2Settings.tm2EnableUserAssignmentLog` — **and a territory model has
been activated**, which is when tracking starts. Turn it on before the realignment, not after.

**When it occurs:** During an annual realignment executed as a Data Loader delete followed by a Data
Loader insert, and during any role correction on a live territory.

**How to avoid:** Sequence realignment inserts before deletes where the user stays in the org, so
coverage never drops to zero mid-run. Enable `tm2EnableUserAssignmentLog` and activate the model before
the realignment window so the log actually captures it. Bulk API guidance lists "Updating territory
hierarchies" among the operations "likely to cause lock contention" — if the load hits lock timeouts,
resubmit in serial concurrency mode rather than shrinking batches. The downstream sharing recalculation
cost of a large membership change is the same recalculation described in `admin/sharing-and-visibility`;
size the window from there, not from the row count.
