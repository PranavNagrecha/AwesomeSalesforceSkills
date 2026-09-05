# Gotchas: Sharing and Visibility

---

## `View All` and `Modify All` Bypass Everything You Thought You Designed

**What happens:** An admin insists the object is private. A user still sees every record. The reason is not the sharing rule - it is an object-level bypass permission.

**When it occurs:** Legacy profiles, copied permission sets, admin-lite personas.

**How to avoid:** Audit object `View All` / `Modify All` and system `View All Data` / `Modify All Data` before debugging sharing rules.

**Example:**
```text
Object OWD = Private
Permission Set = Opportunity View All
Result = user sees every Opportunity anyway
```

---

## Manual Sharing Becomes Invisible Technical Debt

**What happens:** Access works today because admins shared a few records manually months ago. Nobody remembers that, so future debugging gets misdirected.

**When it occurs:** Escalations, executive exceptions, and one-off customer access requests.

**How to avoid:** Treat manual sharing as temporary. Report on it, review it, and replace recurring patterns with a declarative model.

**Example:**
```text
Recurring support request: "Share this Account with the partner team."
Fix: public group + owner-based or criteria-based rule
```

---

## Role Hierarchy Does Not Solve Cross-Team Access

**What happens:** Business users expect peers in another function to see the same records because they collaborate. The hierarchy does not grant that access.

**When it occurs:** Sales-to-service, service-to-legal, or region-to-region collaboration models.

**How to avoid:** Use public groups and sharing rules for sideways access. Keep the hierarchy aligned to reporting structure, not every collaboration scenario.

**Example:**
```text
Manager access = automatic through hierarchy
Peer-team access = requires sharing rule or team membership
```

---

## Criteria-Based Sharing at Volume Has a Cost

**What happens:** A rule based on fields like region, status, and business unit looks elegant until large data changes cause sharing recalculation pain.

**When it occurs:** Mass updates, ownership changes, and large backfills.

**How to avoid:** Keep criteria selective, reduce unnecessary rules, and test recalculation impact before major data events.

**Example:**
```text
Mass update 500,000 records
Criteria-based rule depends on Status__c
Result: recalculation becomes part of the operational risk
```

---

## View All Data as the Sharing Model Leaves Private Children Orphaned

**What happens:** OWD on the primary object is Private, but every internal user has **View All Data** (or object View All). Sharing rules were never built. Tasks/Events stay Private and owned by people who left. Reports on "my team's activities" are empty; everyone can still see every Account.

**When it occurs:** Reporting-heavy, automation-light orgs; "we just gave everyone admin-lite."

**How to avoid:** VAD is a bypass, not a model. If the real model is "everyone sees Accounts," set OWD accordingly and **do not** hide behind VAD. Activity OWD is independent — inactive owners plus Private Tasks means the activity graph is dark even when the parent is wide open. Reassign or open activity access **before** celebrating Account visibility.

---

## A Grant At Or Below the OWD Adds Nothing

**What happens:** A share row must be strictly more permissive than the object's org-wide default. The Apex Developer Guide's own managed-sharing sample handles the failure inline — "Access level must be more permissive than the object's default" — and catches a `StatusCode.FIELD_FILTER_VALIDATION_EXCEPTION` whose message contains `AccessLevel`. The consequence for declarative work: raise an object's OWD from Private to `Read` (Public Read Only) and a `Read` grant on that object stops adding anything. UNVERIFIED (2026-09-04): the quoted requirement is documented for share rows inserted by Apex; the v62 PDFs do not restate it for declaratively created sharing rules or manual shares, so verify the exact failure mode in a scratch org before quoting it as a platform error.

**When it occurs:** Someone widens an OWD "temporarily" to unblock a report, or a package raises an OWD in a target org where Read-level rules already exist. The rules stay visible in Setup, so nobody looks there.

**How to avoid:** Treat OWD as the floor that every grant is measured against, and re-audit the rule set whenever the OWD moves. Under OWD `Read`, only `Edit` is a meaningful grant; under `ReadWrite`, no sharing rule adds anything at all. `references/metadata-examples.md` step 1 shows the enumeration and where it is set.

---

## A Deployed Public Group Arrives Empty

**What happens:** The Metadata API guide states it in one line on the `Group` type: "Members of the public group aren't migrated when you deploy the group type." The group, the sharing rules that name it, and the deployment all succeed. Zero users gain access, because the group has zero members in the target org.

**When it occurs:** Every sandbox-to-production promotion of a new sharing model, and every scratch-org rebuild. It looks like a sharing bug because Setup shows the rule as active.

**How to avoid:** Make group membership an explicit post-deploy step with a named owner, not an assumption. Verify with `UserRecordAccess` for a real user in the target org before closing the change (`references/metadata-examples.md` step 7), not by reading the rule list.

---

## `doesIncludeBosses` Widens Every Grant a Group Ever Receives

**What happens:** `Group` carries a required `doesIncludeBosses` flag that "indicates whether records shared with users in this group are also shared with users higher in the role hierarchy," corresponding to the **Grant Access Using Hierarchies** checkbox on the group's detail page. It is set once on the group and applies retroactively to every rule that ever targets it. `Queue` gained the same field in API version 67.0. This is a different switch from the object-level Grant Access Using Hierarchies setting, and the two are routinely confused.

**When it occurs:** A group is created for a narrow, confidential population; a year later someone asks why the whole management chain above those users can read the records.

**How to avoid:** Set `doesIncludeBosses` deliberately in the group's XML and record the choice next to the group in the sharing model document. For a confidential population it is almost always `false`.

---

## Master-Detail Children Have No Share Table and No Rules to Write

**What happens:** The Object Reference draws the line at the relationship, not at the OWD: "Custom objects on the detail side of a master-detail relationship can't have sharing rules, manual sharing, or queues, because these elements require the Owner field," and "A sharing rule object is created for each custom object that doesn't have a master-detail relationship to another object." So on a detail object there is no `Child__Share` to query, no rule to deploy, and no Apex managed sharing to write — the record "inherits the sharing and security settings of its master record."

**When it occurs:** Late in a design, when someone asks for an exception on the child that the parent's model does not grant. The answer is a data-model change, not a sharing change.

**How to avoid:** Decide master-detail versus lookup with the access model in hand, not only the rollup and cascade-delete requirements. If the child needs its own access story, it needs its own owner, which means a lookup.

---

## An Empty Share Table Does Not Prove There Is No Access

**What happens:** Two documented cases put real access outside the share tables. The Object Reference says of `AccountShare`: "For some sharing mechanisms, such as sharing sets, sharing entries aren't stored at all" — so Experience Cloud access granted by a sharing set is invisible to a `__Share` query. And once faster account sharing recalculation is enabled, implicit parent-child shares are no longer materialised: "Sharing entries that have a value of `ImplicitChild` in the `RowCause` field aren't returned when you query this object. Instead, the system dynamically determines whether users can access child case records when they try to access them." The same note appears on `CaseShare`, `ContactShare`, and `OpportunityShare`.

**When it occurs:** Any audit or Apex assertion built on "count the share rows." It reports clean while a partner user is reading the record.

**How to avoid:** Use `UserRecordAccess` as the authority on *whether* access exists and the share table only to explain *why*. The guide adds a standing warning: "don't create customizations that rely on the availability of these sharing entries."

---

## `UserRecordAccess` Answers a Narrower Question Than It Appears To

**What happens:** Three constraints sit on the diagnostic tool people reach for first. "This object doesn't consider whether a user's access is blocked by a restriction rule," so it reports pre-restriction access and can say `HasReadAccess = true` for a record the user cannot open. "Up to 200 record IDs can be queried." And the SELECT clause is dictated by the WHERE clause: filtering by `UserId` and `RecordId` allows `SELECT RecordId` plus access-level fields and `MaxAccessLevel`, but adding an access-level field to the filter forces `SELECT RecordId` **only** — any other field in the SELECT is a query error, not a warning.

**When it occurs:** Bulk access audits over more than 200 records, and any org using restriction rules (custom objects, external objects, contracts, events, quotes, tasks, time sheets, time sheet entries).

**How to avoid:** Chunk record ids in 200s. When the query and the user disagree, check restriction rules before checking sharing — the guide says so directly: "If a user's access is blocked even though query results state that they should have access, check to see if a restriction rule on the object prevents the user's access." Routing between these mechanisms is `standards/decision-trees/sharing-selection.md` Q8; the mechanics are `admin/restriction-rules`.

---

## The Previous Owner Keeps Access, and API and UI Disagree About How Much

**What happens:** On Opportunity, ownership transfer does not simply remove the old owner. The Object Reference: "when you change the owner of an opportunity using the API, the previous owner's access becomes Read Only or the access specified in your organization-wide default for opportunities, whichever is greater. However, performing this same action in the user interface allows you to select the access level for the previous owner when the previous owner is on an opportunity team." Two paths, two outcomes, from the same business action.

**When it occurs:** Territory realignments and mass reassignments run through Data Loader, in orgs with team selling enabled. Access that an admin believed was revoked in bulk is still granted, sourced from a `Team` row rather than `Owner`.

**How to avoid:** After any scripted transfer on an object with teams, query the share table filtered on `RowCause = 'Team'` for the departing owners and clear team membership explicitly. Do not infer the API's behaviour from what the transfer screen offered.
