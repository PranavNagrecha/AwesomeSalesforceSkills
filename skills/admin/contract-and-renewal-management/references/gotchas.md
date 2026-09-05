# Gotchas — Contract and Renewal Management

Non-obvious platform behaviors that cause real production problems in the contract
and renewal domain.

Gotchas 1–5 are Salesforce CPQ (`SBQQ__*`) managed-package behaviour and rest on the
CPQ sources listed in `well-architected.md`. Gotchas 6–12 are the **standard**
`Contract` / `Order` object graph underneath it and are grounded line-by-line in the
Object Reference and the Metadata API Developer Guide. The CPQ layer inherits every
standard-object rule below it: an activated CPQ contract is an activated standard
`Contract`, with the same locked `Status` field.

## Gotcha 1: Amendment Pricing Locks Existing Lines to Original Contracted Price

**What happens:** When an amendment quote is generated from an active contract, all existing subscription lines display the price from the original Quote Line, not the current price book entry. Fields like Unit Price and List Price on these lines are read-only in the CPQ quote editor. Updating the product's price book entry after the contract was activated has no effect on the amendment quote.

**When it occurs:** Every time an amendment quote is created on a contract that contains previously contracted subscription lines. This is the default and non-configurable behavior for existing lines. It catches admins off guard when a price book update was expected to flow through to an amendment.

**How to avoid:** Do not promise customers or internal teams that a mid-contract price book update will affect existing subscription pricing on an amendment. New lines added during the amendment do pick up current price book pricing. If a price correction on an existing line is genuinely required, the only supported path is to use a `SBQQ__ContractedPrice__c` record for the account/product combination before creating the amendment, which CPQ will then use as the override price for that line.

---

## Gotcha 2: Co-Termination Can Silently Shorten Line Terms

**What happens:** When a contract contains subscription lines with different start dates (common when products are added via multiple amendments), CPQ co-termination logic forces all lines on a new amendment to end on the date of the earliest-ending subscription. A line that was supposed to run 24 months may be co-termed to end in 8 months if there is an older line expiring sooner.

**When it occurs:** Any time an amendment is created on a contract with heterogeneous subscription end dates. This is the default CPQ behavior unless the CPQ Setting for co-termination is changed to "End of Term" rather than "Earliest End Date."

**How to avoid:** Before creating an amendment on a contract with mixed-term lines, query the `SBQQ__Subscription__c` records to identify the earliest `SBQQ__EndDate__c`. Communicate to the customer that all lines will be co-termed to that date. If the customer objects, evaluate whether the CPQ co-termination setting should be changed org-wide, or whether some lines should be split into a separate contract. Do not attempt to manually override end dates on the amendment quote — this produces inconsistent subscription state.

---

## Gotcha 3: Renewal Reprices at Current List — Not Contracted Prices

**What happens:** Renewal quotes reprice all lines at the current price book rate, regardless of the price the customer was paying during the original contract. If prices have increased since the original contract was signed, the renewal quote will reflect those higher prices without any warning.

**When it occurs:** Every time a renewal quote is generated. This is opposite to amendment behavior (where existing lines are locked). The intent is that renewals represent a fresh negotiation, but it surprises admins who expect renewal pricing to match the expiring contract.

**How to avoid:** If the customer has a negotiated rate that should carry into renewals, create a `SBQQ__ContractedPrice__c` record for the account/product combination. CPQ will use the contracted price record instead of the price book entry when generating the renewal quote. Without contracted prices, the renewal will always price at list. Build a review step into the renewal process to compare renewal quote prices against the expiring contract before presenting to the customer.

---

## Gotcha 4: SBQQ__RenewedContract__c Must Be Set for Lifecycle Integrity

**What happens:** If a renewal quote is created by cloning the original opportunity and quote (rather than using the Renew button on the contract), the `SBQQ__RenewedContract__c` lookup on the Renewal Opportunity is never set. CPQ uses this field to chain contract history. Contracted price records, revenue rollups, and contract lineage reports will all be broken because the system does not know this opportunity represents a renewal of the expiring contract.

**When it occurs:** When admins take shortcuts by cloning instead of using the Renew button, or when a third-party integration creates renewal opportunities without setting this field.

**How to avoid:** Always use the **Renew** button on the Contract record, or programmatically set `SBQQ__RenewedContract__c` on the Renewal Opportunity when creating renewals via API or automation. Validate this field is populated before closing a renewal opportunity as Won.

---

## Gotcha 5: Async Amendment Does Not Surface Errors Prominently

**What happens:** When using `SBQQ.ContractManipulationAPI.amend()` for large-scale amendments, failures in the async batch job are written to `AsyncApexJob.ExtendedStatus` and the Apex Job log — not to any visible UI element on the Contract record. Admins who trigger an async amendment and then wait for the amendment quote to appear on the Contract will wait indefinitely if the job failed.

**When it occurs:** Any large-scale amendment using the async API path fails (due to data issues, permission errors, or governor limit overruns in the batch context).

**How to avoid:** After triggering an async amendment, build explicit monitoring into the process. Query `AsyncApexJob` where `ApexClass.Name` contains `Amendment` and check `Status` and `ExtendedStatus`. Consider implementing a post-processing notification (email alert or platform event) when the batch job completes or fails. Do not assume silence means success.

---

## Gotcha 6: Activating a Contract Is a One-Field, One-Way Save

**What happens:** On the update that activates a contract, `Status` is the only field
the platform will accept — "the `Status` field is the only field you can update when
activating the Contract" (object_reference.txt L81520–L81522). Send `Status` plus the
signature dates plus the renewal owner in one `update()` and the whole call is
rejected. And it is one-way: "After a Contract has been activated, your client
application can't change its status", and contracts can be deleted only while their
status is `Draft` or `InApproval` (object_reference.txt L81523–L81525).

**When it occurs:** Every activation done through the API, Data Loader, Flow or Apex —
which is every activation an integration or a bulk backfill performs. The UI hides it
because a user typically saves the field edits and the status change as separate saves.
It also bites the reverse direction: a mis-activated contract cannot be walked back to
`Draft` and cannot be deleted, so a bad bulk activation is permanent.

**How to avoid:** Split every activation into two DML operations — first the payload
update (dates, owner, custom fields), then a second update carrying `Status` alone.
Validate the payload before the second call, because after it there is no undo.
Contract activation is the one place in this domain where a sandbox dry run on a copy
of the real data is not optional.

---

## Gotcha 7: `Status` Is a Label, `StatusCode` Is the Category — and Only One of Them Is the Same Field on Order

**What happens:** `Contract.Status` is a label picklist whose values each sit in a
category held by `Contract.StatusCode`. The Object Reference's own example is a
status picklist containing "Ready to Ship, Shipped, Received as values within the
`Activated` `StatusCode`" (object_reference.txt L81474–L81477). So a filter, formula
or validation rule written against `Status = 'Activated'` silently stops matching the
moment an admin adds any other Activated-category label. `Contract.StatusCode`
properties are `Filter, Group, Restricted picklist, Sort` — there is no `Create` and no
`Update` (object_reference.txt L81486–L81487), so it cannot be written directly either.
`Order.StatusCode` is *not* the same: its properties include `Update`
(object_reference.txt L196833–L196836).

**When it occurs:** The day someone adds a status label for a work queue — the single
most common contract customisation there is. Renewal reports, entry criteria and
validation rules built on the label all go quiet rather than erroring.

**How to avoid:** Filter and group on `StatusCode` in every SOQL query, report and Flow
entry condition. Reserve `Status` for what the user sees and for formulas, which cannot
reach the category — and when a formula must test activation, enumerate every
Activated-category label and treat that list as a maintained artefact, not a constant.
`references/metadata-examples.md` §3 and §4 show both halves.

---

## Gotcha 8: `Contract.EndDate` Is Read-Only and Silently Null Without `ContractTerm`

**What happens:** `EndDate` is "Read-only. Calculated end date of the contract. This
value is calculated by adding the `ContractTerm` to the `StartDate`", and it becomes
editable only when the Auto-calculate Contract End Date setting is disabled
(object_reference.txt L81153–L81160) — the `autoCalculateEndDate` element on
`ContractSettings` (api_meta.txt L113225). Load a contract with a `StartDate` and no
`ContractTerm` and `EndDate` comes back null with no error, because nothing was
violated: the calculation simply had no term to add.

**When it occurs:** On any data migration or integration that maps a source end date
straight to `EndDate` while auto-calculate is on. The write is dropped, the load
reports success, and every renewal query keyed on `EndDate` skips those rows forever.

**How to avoid:** Decide `autoCalculateEndDate` before the load, not after. With it on,
map the source term to `ContractTerm` (months) and never map `EndDate` at all; with it
off, map `EndDate` and accept that term and end date can now disagree. Then run the
count of activated contracts with a null `EndDate` as a post-load gate —
`references/metadata-examples.md` §9b is that query.

---

## Gotcha 9: `ContractLineItem` Is a Service Contract Entitlement, Not a Commercial Contract Line

**What happens:** The object whose name most obviously reads as "the products on a
contract" is not that. `ContractLineItem` "represents a product covered by a service
contract (customer support agreement)" (object_reference.txt L81635) and its `AssetId`
is a required field — "Required. ID of the Asset associated with the contract line
item. Must be a valid asset ID" (object_reference.txt L81661). It hangs off
ServiceContract in the Entitlement Management model, not off `Contract`.

**When it occurs:** Whenever someone models "what did the customer buy on this
contract" by writing to `ContractLineItem`. The insert fails on the missing Asset, or
succeeds against a ServiceContract and quietly builds a support-entitlement structure
that no revenue report will ever read.

**How to avoid:** For commercial lines on a standard Contract, use `Order` and
`OrderItem` with `Order.ContractId` pointing at the contract. Reach for
`ContractLineItem` only when the work is Service Cloud entitlements — see
`admin/design-entitlements` territory, not this skill.

---

## Gotcha 10: `Terminated` and `Expired` Are Real Status Codes You Cannot Use

**What happens:** The `ContractStatus` object documents five status codes, then says of
two of them: "Two other values (`Terminated` and `Expired`) are defined but are not
available for use via the API" (object_reference.txt L82295–L82296). They exist in the
data model and appear in the object's own summary description, so a developer reading
the schema reasonably plans a termination flow around them — and then cannot set them.

**When it occurs:** During design, when contract lifecycle states are being mapped, and
again at build time when the `update()` setting `StatusCode` fails. The failure is late
and the redesign is not small, because "terminated" usually needs its own reporting.

**How to avoid:** Model termination and expiry as your own `Status` labels inside the
`Activated` category, or as a separate custom field, and decide up front which one
reporting will group by. Do not design a state machine on `StatusCode` beyond `Draft`,
`InApproval` and `Activated`.

---

## Gotcha 11: Reducing an Activated Order Has Three Preconditions, and Deleting the Line Instead Is Irreversible

**What happens:** Quantity on an activated order is reduced through a reduction order,
and that path has preconditions that fail in different places. `enableReductionOrders`
must be on and it requires `enableOrders` (api_meta.txt L123698–L123700). The line must
still be reducible: `AvailableQuantity` "must be greater than or equal to 0. An order
product is reducible only if `AvailableQuantity` is greater than 0", and it is "always
0 if the order product's parent order is a reduction order" (object_reference.txt
L199127–L199135). And once reduction order products exist, the parent order can no
longer be reverted — an activated order's status can go back to `Draft` "but only if
the order doesn't have any child reduction order products" (object_reference.txt
L197099–L197101). The tempting shortcut is worse: "When `OrderItem` records are
directly deleted, they aren't sent to the recycle bin and can't be undeleted"
(object_reference.txt L200181–L200183).

**When it occurs:** The first time a customer reduces quantity mid-term on an org where
orders were enabled but reduction orders were not, or where someone "cleaned up" a line
by deleting it.

**How to avoid:** Turn `enableReductionOrders` on at the same time as `enableOrders`,
before any order data exists — see `references/metadata-examples.md` §2. Check
`AvailableQuantity` before promising a reduction. Never delete an `OrderItem` to
correct an activated order; there is no recycle bin to recover it from.

---

## Gotcha 12: `OwnerExpirationNotice` Accepts Six Values and No Others

**What happens:** The platform's built-in renewal reminder hook is
`Contract.OwnerExpirationNotice`, a **restricted** picklist of "Number of days ahead of
the contract end date (15, 30, 45, 60, 90, and 120)" (object_reference.txt
L81230–L81236). A renewal process designed around a 75-day or 180-day window cannot use
it, and because the picklist is restricted the write fails rather than rounding.

**When it occurs:** When a renewal SLA is agreed in the business before anyone checks
the field, and again on any data load that maps a source notice period through
unchanged.

**How to avoid:** Either fit the process to one of the six values, or accept that the
notice field is decorative and drive reminders from a schedule-triggered flow filtered
on `EndDate` and `StatusCode` — the flow intent and its query are in
`references/metadata-examples.md` §6. Do not do both: two reminder mechanisms on the
same contract produce duplicate emails that owners learn to ignore.
