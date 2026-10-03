# Gotchas: FlexCard Requirements

Non-obvious behaviors that turn incomplete FlexCard requirements into rework or exposure. Sources are listed in `well-architected.md`. Line references cite the `pdftotext -layout` extraction of the Summer '26 PDFs, written as `<guide> L<n>`. The OmniStudio FlexCard guide (help.salesforce.com and atlas) did not return content for this pass, so Card Designer behavior carries an inline `UNVERIFIED (2026-10-03):` marker.

## Gotcha 1: `OmniUiCard` records are internal-use only

**What happens:** The Salesforce Industries Developer Guide lists `OmniUiCard` as "For internal use only. This object and associated records are only for internal use. Don't perform any create, edit, or delete operations on this object. Modifying or deleting this object's records may result in errors with your implementation" (`salesforce_industries_dev_guide L91930-91933`).

**When it occurs:** A team "bulk renames" cards with Data Loader, copies cards between orgs with a data export, or cleans up old versions by deleting records.

**How to avoid:** Write into the requirements that cards move only through supported OmniStudio deployment tooling, and never through record-level data tools. Treat any request to edit card records directly as a change to the deployment approach, not a data task.

---

## Gotcha 2: Guest users have Private OWD that cannot change, and guest sharing is Read Only

**What happens:** "Guest users' org-wide defaults are set to Private for all objects, and this access level can't be changed." A guest user sharing rule "is a special type of criteria-based sharing rule and the only way to grant record access to unauthenticated guest users. Guest user sharing rules can only grant Read Only access" (Salesforce Security Guide, `salesforce_security_impl_guide L2868-2869`, `L2985-2987`).

**When it occurs:** A FlexCard designed for internal users is placed on a public Experience Cloud page. Its fields render blank for visitors, or an action that edits a record fails.

**How to avoid:** Record every placement and audience. For guest audiences, specify the guest user sharing rules (Read Only) and remove any edit actions, or move the edit into an authenticated flow.

---

## Gotcha 3: An Integration Procedure is the documented multi-source data source

**What happens:** "An Integration Procedure can be called from an Omniscript, an API, or an Apex method, and can be a data source for a Flexcard. Integration Procedures can handle multiple data sources to read and write data." Data Mappers "typically supply data to Omniscripts, Integration Procedures, Flexcards, and Apex classes" (`salesforce_industries_dev_guide L91954-91962`).

**When it occurs:** Requirements list fields without sources, the developer binds everything to a single-object source, and aggregated or external fields come back empty.

**How to avoid:** Map every field group to a source in the requirements. Name the Integration Procedure for any field that needs more than one object or an external system. UNVERIFIED (2026-10-03): earlier versions of this skill said a card bound to an inactive Integration Procedure returns empty data silently; confirm with the developer.

---

## Gotcha 4: Server-side actions run with the user's access

**What happens:** A FlexCard action that invokes Apex, a Data Mapper, or an Integration Procedure executes for the user who clicks it. Users need access to the Apex class and to the objects and fields the action reads or writes. Permission sets grant this through `classAccesses`, `objectPermissions`, and `fieldPermissions` (Metadata API Developer Guide, PermissionSet, `api_meta L94772-94840`).

**When it occurs:** An action is tested by an administrator and then fails for service agents or portal users.

**How to avoid:** Add a permission column to the action register, and turn it into a permission set per audience (see `metadata-examples.md`). Test every action as a user from each audience. UNVERIFIED (2026-10-03): which OmniStudio permission sets or licences each audience needs in addition is help-only.

---

## Gotcha 5: OmniAnalytics tracking exists only in OmniStudio Standard

**What happens:** `OmniTrackingGroup` "represents a group of FlexCard and OmniScript components that have their user interactions tracked together in OmniAnalytics", and `OmniTrackingComponentDef` represents a FlexCard or OmniScript in a group. Both are available from API 60.0, and both carry the note "This object is part of OmniStudio Standard, not OmniStudio for Vlocity" (`salesforce_industries_dev_guide L91660-91664`, `L91775-91779`).

**When it occurs:** Stakeholders ask for card usage analytics after go-live in an org that runs OmniStudio for Vlocity.

**How to avoid:** Ask about analytics during requirements, record the org's OmniStudio runtime, and include the tracking group in the build if analytics are needed.

---

## Gotcha 6: The older OmniStudio Business REST APIs were deprecated in API 55.0

**What happens:** The expression set (calculation procedure) and decision matrix Business REST APIs under `/connect/omnistudio/evaluation-services` carry the note: "These APIs have been deprecated as of API version 55.0. In API version 55.0 and later, use the new Business APIs in Business Rules Engine" (`salesforce_industries_dev_guide L91936-91941`).

**When it occurs:** A card action or its Integration Procedure is specified to call a calculation through the old endpoints copied from older material.

**How to avoid:** For any action that runs a calculation, name the Business Rules Engine API in the requirements, not the deprecated evaluation-services resources.

---

## Gotcha 7: Activation order, state compilation, and LWC dependencies are unconfirmed claims

**What happens:** Earlier versions of this skill stated four Card Designer behaviors as fact: state templates compile to LWC at activation, so edits need reactivation; a parent card cannot be activated until its child cards are active; a card bound to an inactive Integration Procedure shows empty data; and a card embedding a custom LWC cannot be activated until the LWC is deployed. UNVERIFIED (2026-10-03): none of these appears in the guides that fetched for this pass.

**When it occurs:** A build plan schedules parent and child cards in parallel, or a state change is made in production during business hours.

**How to avoid:** Keep a build-order section in the requirements anyway (children, Integration Procedures, and LWCs before the parent), make state changes in a sandbox first, and ask the developer to confirm activation behavior in this org's Card Designer.
