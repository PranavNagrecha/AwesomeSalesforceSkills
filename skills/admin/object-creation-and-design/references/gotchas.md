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
