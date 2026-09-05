# Gotchas — Object Creation and Design

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: The Object Name (API Name) Is Permanent After Save

**What happens:** An admin creates a custom object in a hurry and accepts the auto-populated Object Name without reviewing it. For example, a label of "Customer Success Plan" produces the API name `Customer_Success_Plan__c`. Six months later, the business rebrands the concept to "Engagement Plan." The label can be changed, but the API name cannot. All Apex classes, flows, reports, and integrations that reference `Customer_Success_Plan__c` continue to do so indefinitely, creating a permanent naming inconsistency in the codebase.

**When it occurs:** Any time the Object Name is not carefully reviewed before clicking Save on the object creation form. It is easy to miss because the form auto-populates the API name and the focus naturally shifts to the feature checkboxes below.

**How to avoid:** Treat the Object Name review as a mandatory step, not an auto-accept. Before saving, confirm the API name is:
- Concise and unambiguous (what the object represents, not a project codename)
- Consistent with existing naming conventions in the org (check other custom objects for patterns)
- Reviewed by at least one developer or experienced admin who understands the downstream impact

If the name must change after go-live, the only option is to create a new object with the correct name, migrate all data, update all metadata references, and deprecate the old object — a costly migration effort.

---

## Gotcha 2: Activities and Track Field History Cannot Be Disabled

**What happens:** An admin enables Track Field History on an object "just in case" during initial setup. A year later, the object grows to 3 million records with 5 tracked fields. The History object now contains up to 15 million rows. A query on the History related list on any record takes several seconds. The business wants to remove history tracking to recover performance, but the checkbox in Setup is now greyed out and read-only — it cannot be turned off.

Similarly, if Activities is enabled on a high-volume transactional object (e.g. a log entry object that inserts 1,000 records per day), the Activity framework processes every DML operation against that object even if no activities are ever logged.

**When it occurs:** When features are enabled at object creation without a confirmed use case, and the "cannot be disabled" rule is overlooked.

**How to avoid:**
- Enable Track Field History only when there is a specific audit or compliance requirement.
- Immediately after enabling, configure exactly which fields to track (Setup → Object Manager → [Object] → Fields & Relationships → set the "Track" checkbox only for the required fields). History is not tracked until fields are individually marked.
- Enable Activities only for objects where users will actually log calls, tasks, and emails. Do not enable it for configuration records, junction objects, or log entries.
- Document the reason each feature is enabled in the object's Description field.

---

## Gotcha 3: OWD Changes Trigger Full Sharing Recalculations

**What happens:** An org starts with a custom object set to Public Read/Write OWD. After going live with 800,000 records, the security team determines the object contains sensitive compensation data and requests it be changed to Private. The admin changes the OWD in Sharing Settings. Salesforce queues a background sharing recalculation job. In a large org, this job can run for several hours, during which the sharing state for that object is in transition. Users may temporarily see incorrect access (either too much or too little, depending on the direction of change) while the recalculation runs. The job appears in the Background Jobs section of Setup.

**When it occurs:** Any change to an OWD for an object that already has records and sharing relationships. The larger the record volume and the more complex the role hierarchy, the longer the recalculation takes.

**How to avoid:** Define the correct OWD before any go-live or before record volume grows. If an OWD change is unavoidable on a live org:
1. Schedule the change during a maintenance window or low-activity period.
2. Notify users that temporary access inconsistencies may occur.
3. Monitor the background job in Setup → Environments → Jobs → Background Jobs until it completes.
4. Validate access for a sample of records after the job completes.

---

## Gotcha 4: Managed Package Objects Count Against Your Edition Limit

**What happens:** An Enterprise Edition org appears to have used only 120 of its 200 custom object slots. An admin plans a data model expansion requiring 90 new objects. During implementation, the team discovers that 60 of those "available" slots are actually consumed by objects from installed managed packages (Salesforce CPQ, a mapping tool, a survey package). The true available count is 80 — 10 fewer than needed. Object creation starts failing with "maximum number of custom objects reached" errors.

**When it occurs:** When an org inventory is done using the MASTER_QUEUE or a design document without checking actual real-time usage in Setup.

**How to avoid:** Always check the current object count before beginning data model planning: Setup → Company Information → look at "Used Custom Objects" in the Org Detail section. This shows the live count inclusive of managed package objects. If you are within 20% of the limit, raise an edition upgrade request or review whether unused custom objects can be deleted before adding new ones.

---

## Gotcha 5: A Detail Object Has No Owner, So It Can Never Be a Queue or Sharing-Rule Target

**What happens:** A team models work items as `Project_Request_Task__c` on the detail side of a master-detail relationship, then designs routing on top of it — a Task queue, a sharing rule that opens Tasks to a support group, a manual share for one escalated record. None of it can be built. The Sharing Settings row for the object is fixed at Controlled by Parent and greyed out, the New Sharing Rule button is absent, the object never appears in the queue's supported-object picker, and there is no Owner field to reassign.

The Object Reference states the mechanism directly: on a master-detail relationship "the Owner field on the detail object isn't available and is automatically set to the owner of its associated master record", and therefore "custom objects on the detail side of a master-detail relationship can't have sharing rules, manual sharing, or queues, because these elements require the Owner field" (object_reference.txt L3259–3261).

**When it occurs:** Whenever a master-detail relationship is chosen for referential-integrity reasons (cascade delete, roll-up summary fields) without checking whether the child will ever need routing, independent visibility, or a per-record assignment. It surfaces late, because the relationship is usually built before anyone designs routing.

**How to avoid:** Decide access and routing before the relationship type, not after. If the child object needs its own owner, its own queue, or any share that does not follow the parent, use a lookup relationship and a `Private` OWD instead — you give up cascade delete and roll-up summaries, and you keep the ability to route. Converting master-detail to lookup after the fact requires every child record to have a populated parent and rewrites the whole sharing footprint. Relationship selection belongs in `admin/lookup-and-relationship-design`; this gotcha is the access consequence of that choice.

---

## Gotcha 6: `startingNumber` Cannot Be Retrieved, So a Retrieve/Redeploy Round Trip Silently Resets It

**What happens:** An Auto Number name field is deployed with `<startingNumber>5000</startingNumber>` so that migrated records continue an existing external sequence. Months later someone retrieves the object into version control, edits an unrelated element, and redeploys. The retrieved file has no `startingNumber` element at all — the guide is explicit that "you can't retrieve the starting number of an auto-number field through Metadata API" (api_meta.txt L43623–43635). The redeploy therefore carries no value, and the default applies: "the default starting number for standard fields is 0. The default starting number for custom fields is 1." Numbering restarts and collides with records that already exist.

**When it occurs:** Any retrieve-edit-deploy cycle on an object whose name field is Auto Number with a non-default starting number — which is exactly the workflow a source-controlled org uses every sprint.

**How to avoid:** Treat `startingNumber` as deploy-only configuration, not as retrievable source. Record the intended value in the object's `description` or in the project's data-migration notes so it survives a retrieve, and re-add the element deliberately when the object is deployed into a *new* org (a scratch org, a fresh sandbox, a package install). In an org that already holds records, leave the element out — redeploying it will not move an existing counter backward but it does make the file lie about the org's real state.

---

## Gotcha 7: `enableBulkApi`, `enableSharing` and `enableStreamingApi` Must Be Deployed as a Set

**What happens:** A deployment turns on Bulk API access for an integration and sets only `<enableBulkApi>true</enableBulkApi>`. The deploy fails, or the object comes back with the flag not applied. The three elements are mutually dependent, and each one's description in the guide says the other two must also be enabled: `enableBulkApi` requires `enableSharing` and `enableStreamingApi`; `enableSharing` requires `enableBulkApi` and `enableStreamingApi`; `enableStreamingApi` requires `enableBulkApi` and `enableSharing` (api_meta.txt L42013–42019, L42079–42092). All three are the "Enterprise Application object" classification used for usage tracking, not three independent switches.

**When it occurs:** When a metadata file is hand-edited to add one capability, or when an object file is assembled element by element from the field table rather than copied from a working object.

**How to avoid:** Set all three to the same value in the object file, or set none of them and leave the org default in place. When the requirement is only "the integration must be able to load records in bulk", verify first whether the org already has the trio on — an unnecessary change to these elements is a change to the object's usage classification, not a harmless toggle.

---

## Gotcha 8: Search Is Off by Default on New Custom Objects, and Switches Off Again After 120 Unsearched Days

**What happens:** A custom object is created, a tab is added, records are loaded — and global search returns nothing for them. SOSL queries from Apex return empty result sets. Nothing is broken; the object was simply never made searchable. The guide states that "by default, search is disabled for new custom objects" from API version 35.0 onward, and that `enableSearch` "indicates whether the object's records can be found via SOSL and Salesforce searches" (api_meta.txt L42062–42066).

Worse, an object that *was* searchable can stop being searchable on its own: "to enhance Einstein Search performance, searchability is disabled for custom objects that haven't been searched for more than 120 days" (api_meta.txt L42068–42071). A seasonal or year-end object can go quiet between uses and come back unsearchable.

The same root cause defeats enhanced lookups: `enableEnhancedLookup` needs the object searchable first — "set `enableSearch` as true before setting `enableEnhancedLookup` as true" (api_meta.txt L42024–42033).

**When it occurs:** On every custom object created since API version 35.0 where `enableSearch` was never set explicitly, and on low-traffic objects after four months of no searches.

**How to avoid:** Set `<enableSearch>true</enableSearch>` explicitly in the object file for anything users are meant to find by name, rather than relying on a default. Add "search returns the record by name" to the post-deploy verification rather than assuming it. If a previously searchable object goes quiet, re-enabling searchability is an admin action, not a metadata bug to chase.

---

## Gotcha 9: A Record Created Through the API With No Name Gets Its Record ID as Its Name

**What happens:** An object uses a Text name field. An integration or a Data Loader job inserts records without mapping the `Name` column. No error is raised — the load succeeds. Every record then displays an 18-character record ID where its name should be, in list views, lookup dialogs, related lists and search results. The Object Reference states it plainly: "for a custom object record to appear in the Salesforce user interface, its name field must be populated. If you use the API to create a custom object record that doesn't have a name, the record's ID is used as its name" (object_reference.txt L3013–3014).

**When it occurs:** On Text name fields only, during API inserts and bulk loads — the UI form makes the name visible enough that people fill it in. It is most common on objects where the name is not a natural business value and nobody decided what should go in it.

**How to avoid:** If the name has no natural business value, choose Auto Number at creation — the platform then always populates it and the failure mode cannot occur. If Text is the right choice, make the mapping mandatory in the load template and add a `Name` completeness check to the post-load reconciliation (`data/data-migration-strategy` territory). Note that the name field's Text-vs-Auto Number type is one of the choices that is fixed at save, so this is a design-time decision, not something to fix after the first bad load.

---

## Gotcha 10: The Object File Is Replaced Whole, and Retrieving It Rewrites Profiles in the Same Package

**What happens:** Two things that both bite during deployment.

First, a partial object file overwrites rather than merges. The guide opens the CustomObject section with "specify all relevant fields when you create or update a custom object. You can't update a single field on the object" (api_meta.txt L41900–41901). A file trimmed down to the two elements someone wanted to change is a full replacement of the object definition with those two elements.

Second, retrieving the object drags access metadata with it: "retrieving a component of this metadata type in a project makes the component appear in any Profile and PermissionSet components that are retrieved in the same package" (api_meta.txt L41920–41921). The same note applies to `CustomTab` (api_meta.txt L47260–47261). A retrieve that includes profiles therefore rewrites those profile files with object and tab entries, and a subsequent deploy of the whole folder pushes access changes nobody reviewed.

**When it occurs:** When an object file is hand-authored from the field table rather than retrieved and edited, and when a manifest lists `CustomObject` or `CustomTab` alongside `Profile` or `PermissionSet`.

**How to avoid:** Always start from a retrieved file and edit it — never assemble an object file from scratch to deploy against an org that already has the object. Keep `Profile` and `PermissionSet` out of the same manifest as objects and tabs unless the access change is the point of the deployment, and diff any profile file the retrieve touched before deploying it. Grant object and tab access through permission sets that you author deliberately (`admin/permission-set-architecture`) rather than through whatever the retrieve produced.

---

## Gotcha 11: `historyRetentionPolicy` on CustomObject Is Reserved, and Turning Tracking Off Does Not Remove History

**What happens:** A team tries to cap history growth by adding `<historyRetentionPolicy>` to the object file. In the CustomObject field table that field is listed as "reserved for future use" (api_meta.txt L42164). The `HistoryRetentionPolicy` component itself is real and documented — `archiveAfterMonths` (minimum 1, maximum 18, default 18), `archiveRetentionYears`, `gracePeriodDays` (0–10, default 1) — but it "is only available to users with the RetainFieldHistory permission", which is the Field Audit Trail add-on (api_meta.txt L44075–44077, L44098–44118). Without that permission the policy is not a lever the org has.

The clean-up assumption fails too. Per the Object Reference, "turning off tracking for a field stops further changes from being recorded, but the history data is not deleted", and separately, "deleting a custom field also permanently deletes the history data for that custom field" (object_reference.txt L110677–110678). So the only way to remove history rows is to destroy the field they belong to.

**When it occurs:** When history volume becomes a performance or storage problem years after tracking was switched on, and someone looks for a retention setting to fix it.

**How to avoid:** Decide field-by-field what actually needs an audit trail before enabling tracking, and keep the tracked set well under the twenty-field ceiling (object_reference.txt L110674). If a compliance requirement genuinely needs long retention, confirm the org has Field Audit Trail — that is a licensing question to answer during design, not a metadata element to add later. Record the audit reason for each tracked field in the object's `description` so a future admin can tell a compliance requirement from a habit.
