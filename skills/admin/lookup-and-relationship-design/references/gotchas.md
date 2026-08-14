# Gotchas — Lookup and Relationship Design

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: A Detail-Side Object Cannot Be Put in a Queue, Shared Manually, or Given a Sharing Rule

**What happens:** The moment an object sits on the detail side of a master-detail relationship, three capabilities disappear from Setup with no migration path: sharing rules, manual sharing, and queues. The Object Reference states it plainly — "Custom objects on the detail side of a master-detail relationship can't have sharing rules, manual sharing, or queues, because these elements require the Owner field." The root cause is that "The Owner field on the detail object isn't available and is automatically set to the owner of its associated master record."

**When it occurs:** Discovered late, usually when someone tries to route detail records through Omni-Channel, assignment rules, or a "Work Queue" list view — all of which require a Queue, which requires OwnerId. Also hits Apex written against the object: `detailRecord.OwnerId` fails to compile because the field is not on the sObject at all.

**How to avoid:** Decide ownership before the relationship type. If detail records will ever need their own owner, their own queue, or their own sharing rule, the relationship must be Lookup. If you need cascade delete on a Lookup, set `deleteConstraint` to `Cascade` (see Gotcha 2) rather than converting to master-detail. Converting an object off the detail side later means rebuilding every roll-up summary that points at it.

---

## Gotcha 2: `deleteConstraint` Defaults to `SetNull` — Parent Deletion Silently Blanks the Child

**What happens:** A Lookup field deployed without an explicit `deleteConstraint` gets `SetNull`. Deleting the parent succeeds, the child record survives, and the lookup field is quietly emptied. There is no error, no warning, and no record of the former parent Id anywhere except the recycle bin. Reports filtered on the lookup lose those rows overnight.

**When it occurs:** Any parent delete — including bulk deletes, merge operations that delete the losing record, and cascade deletes propagating from a grandparent. Most common after a data-cleanup job removes "duplicate" Accounts.

**How to avoid:** Set the constraint deliberately in the `CustomField` metadata. Metadata API defines exactly three values: "Cascade—Deletes the lookup record as well as associated lookup fields. Restrict—Prevents the record from being deleted if it's in a lookup relationship. SetNull—This value is the default." Use `Restrict` when the child is meaningless without its parent and you would rather block the delete than lose the link. Note that `Restrict` surfaces to the user as a delete failure, so pair it with a clear field-level Help Text explaining why the parent cannot be removed.

---

## Gotcha 3: The Two Master-Details on a Junction Object Are Not Interchangeable

**What happens:** On a junction object, `relationshipOrder` decides which parent is primary. The Metadata API `CustomField` reference notes it "is valid for all master-detail relationships, but the value is only non-zero for junction objects" — `0` is primary, `1` is secondary. The primary parent determines the junction record's owner and the look-and-feel it inherits. Deploy the two fields in the wrong order and every junction record is owned by the wrong side of the model, which changes who can see it.

**When it occurs:** Silently, at deploy time. Retrieving the object from another org and re-deploying can also reorder the fields if the source org had a different designation.

**How to avoid:** Set `relationshipOrder` explicitly on both master-detail fields in source control rather than relying on creation order in the UI. Assert the intended primary in the deployment review checklist, and after deploy, spot-check the OwnerId of a sample junction record against the intended master.

---

## Gotcha 4: SOQL Caps Relationship Traversal Long Before Your Data Model Does

**What happens:** A data model can nest ten levels deep; a query cannot follow it. The SOQL reference sets four separate ceilings: "In each specified relationship, no more than five levels can be specified in a child-to-parent relationship," "No more than 55 child-to-parent relationships can be specified in a query," and "No more than 20 parent-to-child relationships can be specified in a query." For parent-to-child depth, "In API version 58.0 and later, up to five levels of parent-to-child relationship can be queried via REST, SOAP, and Apex query calls for standard and custom objects."

**When it occurs:** Usually in a report or an LWC that needs a grandparent's grandparent's field. The design passes review because nothing in Setup blocks a six-deep chain; only the query fails.

**How to avoid:** Cap the intended read path at five child-to-parent hops when you draw the model, not when you write the query. Where the model genuinely needs to be deeper, flatten with a cross-object formula field at the midpoint — that formula becomes a one-hop field for every downstream query. The same doc notes "A custom object allows up to 40 relationships, so you can reference all the child-to-parent relationships for a custom object in one query," which is the practical budget per object.

---

## Gotcha 5: `CHILD_SHARE_FAILS_PARENT` on Ownership Changes You Did Not Expect to Touch the Parent

**What happens:** A reparent or owner-change DML fails with the API status code `CHILD_SHARE_FAILS_PARENT`. The SOAP API status-code reference explains the rule: "if you don't have appropriate permissions on a parent record, you can't change the owner of or define sharing rules for a child record." The running user has full access to the record being edited and still cannot save it, which reads as a permissions bug rather than a data-model consequence.

**When it occurs:** Most often in an integration user or a Flow running in user context that reassigns child records in bulk, where the parent sits outside that user's role-hierarchy branch or is owned by a private-OWD peer.

**How to avoid:** When a relationship implies inherited access, the automation touching the child needs read/edit on the parent too. Grant that through a permission set on the integration user, or move the operation to `without sharing` Apex only when the elevated access is a documented, reviewed decision. Do not "fix" it by opening the parent object's OWD — that changes visibility for every user, not just the one failing.
