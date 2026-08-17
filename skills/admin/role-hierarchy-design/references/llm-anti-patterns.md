# LLM Anti-Patterns — Role Hierarchy Design

Common mistakes AI coding assistants make when generating or advising on role hierarchy design.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Stating a Maximum Number of Hierarchy Levels as a Platform Limit

**What the LLM generates:** "Salesforce supports a maximum of 10 levels in the role hierarchy" or "keep the hierarchy under 10 levels — that is the platform limit."

**Why it happens:** A depth figure circulates widely in blog posts, certification study guides, and forum answers, and the model has absorbed it as though it were a governor limit. The documented ceiling is on the number of *roles*, not the number of *levels*, and the two get conflated because both are "how big can the hierarchy be" questions.

**Correct pattern:**

```
Sourced ceiling — role COUNT:
  Orgs created in Spring '21 or later: up to 5,000 roles.
  Orgs created earlier: 500 by default; contact Salesforce Customer Support to raise it.
  (Spring '21 Release Notes, "Create More Roles")

Sourced guidance — shape, not depth:
  "to improve performance, it's best to set up roles based on data access
   and eliminate any roles that aren't needed."

NOT sourced: any maximum number of LEVELS. Do not assert one.

What to say instead: each level adds indirect members to every Role group
beneath it, and reparenting a role forces Salesforce to do the work of moving
a user for every user in that role and all of their data. Add a level only
when a real access requirement needs an intermediate viewer.
```

**Detection hint:** Grep generated output for `levels` adjacent to a digit, and for the words "maximum" or "limit" within the same sentence as "hierarchy". Any numeric depth claim needs a citation to a fetched Salesforce page or it must be cut.

---

## Anti-Pattern 2: Telling the Admin to Uncheck Grant Access Using Hierarchies on a Standard Object

**What the LLM generates:** "To stop managers from seeing opportunities, go to Sharing Settings and deselect Grant Access Using Hierarchies for Opportunity."

**Why it happens:** The checkbox is visible on the Sharing Settings page in a column that spans all objects, so it reads as universally editable. The model also pattern-matches "turn off inheritance" to the most direct-sounding control.

**Correct pattern:**

```
Editable:     custom objects only, AND only when default access is not
              Controlled by Parent.
Not editable: every standard object. There is no supported way to disable
              hierarchy inheritance for Opportunity, Case, Account, Contact,
              or any other standard object.

To restrict a standard object from a management chain, the options are:
  - restructure the hierarchy so the chain does not sit above the owner
  - do not store the data on that standard object

Restriction rules are NOT the fallback here. The Security Guide scopes them
to "custom objects, external objects, contracts, events, quotes, tasks, time
sheets, and time sheet entries". Account, Opportunity, Case, Contact, Lead
and Order are on none of those lists, so "use a restriction rule instead" is
wrong for exactly the objects this anti-pattern is about.
```

**Detection hint:** Any output pairing "Grant Access Using Hierarchies" with a standard object API name (`Opportunity`, `Case`, `Account`, `Contact`, `Lead`, `Order`) in a deselect/disable instruction is wrong. Custom object names end in `__c`. Flag the second-order version too: offering a restriction rule as the workaround for one of those objects is the same error one step later.

---

## Anti-Pattern 3: Emitting Invented Access-Level Values in Role Metadata

**What the LLM generates:**

```xml
<Role xmlns="http://soap.sforce.com/2006/04/metadata">
    <name>Sales Manager</name>
    <opportunityAccessLevel>ReadWrite</opportunityAccessLevel>
    <caseAccessLevel>Full</caseAccessLevel>
    <contactAccessLevel>ReadOnly</contactAccessLevel>
</Role>
```

**Why it happens:** Salesforce uses several different access-level vocabularies across the platform — `Read`/`Edit`/`None` on roles, `Read`/`Edit`/`All` on `__Share` records, `Private`/`Public Read Only`/`Public Read/Write` on OWD. The model averages them and produces a value from the wrong vocabulary.

**Correct pattern:**

```xml
<!-- force-app/main/default/roles/Sales_Manager.role-meta.xml -->
<?xml version="1.0" encoding="UTF-8"?>
<Role xmlns="http://soap.sforce.com/2006/04/metadata">
    <name>Sales Manager</name>
    <parentRole>Sales_VP</parentRole>
    <caseAccessLevel>Read</caseAccessLevel>
    <contactAccessLevel>Edit</contactAccessLevel>
    <opportunityAccessLevel>Read</opportunityAccessLevel>
    <mayForecastManagerShare>false</mayForecastManagerShare>
</Role>
```

Valid values for all three access-level fields are exactly `Read`, `Edit`, and `None`. The fields are hidden when the corresponding sharing model is Public Read/Write, and `contactAccessLevel` is additionally hidden when the contact model is Controlled by Parent. `parentRole` takes the parent role's `fullName`, so the parent must be in the same deployment or already present in the target org.

**Detection hint:** Regex the generated XML for `<(case|contact|opportunity)AccessLevel>` and assert the inner text is one of `Read|Edit|None`. `scripts/check_role_hierarchy_design.py` performs this check across a roles directory.

---

## Anti-Pattern 4: Proving or Disproving Manager Access With a Share Query

**What the LLM generates:**

```soql
-- "Confirm the manager has access:"
SELECT Id, UserOrGroupId, AccessLevel, RowCause
FROM OpportunityShare
WHERE UserOrGroupId = '005...' AND OpportunityId = '006...'
```

...followed by a conclusion that zero rows means no access.

**Why it happens:** The `__Share` objects are the most discoverable artefact of the sharing model, and the model treats them as a complete access ledger. They are not: they back explicit and implicit grants only.

**Correct pattern:**

```
Access grant types: explicit, group membership, inherited, implicit.
Only explicit and implicit are rows in the Object Sharing table.
Role-hierarchy access is an INHERITED grant, resolved by joining Object
Sharing to the Group Maintenance tables at query time. No row is written.

AccountShare.RowCause is documented as "Valid values include" and
then lists fourteen: Manual, Owner, Team, Rule, GuestRule,
ImplicitParent, GuestParentImplicit, LpuParentImplicit, LpuImplicit,
PortalImplicit, ARImplicit, Territory, Territory2AssociationManual,
TerritoryManual. Older archived versions of that page show only four.
Either way the list is open, so do not argue from it that a hierarchy
row cause is absent. The evidence is the table split, not the picklist.

Two further reasons a row count is not an access count, from the same
page: rows for ImplicitParent / Manual / Owner "are compressed into
one record with the highest level of access", and "for some sharing
mechanisms, such as sharing sets, sharing entries aren't stored at
all".

To verify hierarchy access:
  1. Resolve the role chain:
     SELECT Id, Name, DeveloperName, ParentRoleId FROM UserRole
  2. Confirm the object's OWD is Private or Public Read Only
     (Public Read/Write means grants are irrelevant)
  3. Log in as the user, or open Setup -> Users -> <user> -> Sharing
```

**Detection hint:** Any generated conclusion of the form "the share table has no row, therefore no access" is wrong for a user above the owner in the hierarchy. Flag any `__Share` query presented as a completeness check.

---

## Anti-Pattern 5: Presenting a Role Change as Immediate

**What the LLM generates:** "Change the user's role in Setup and they will immediately see their new team's records." Or a migration script that changes `User.UserRoleId` for 4,000 users in one Bulk API job and then asserts access in the next step.

**Why it happens:** The Setup UI returns instantly, so the operation looks synchronous. The model has no signal that the expensive part happens afterwards.

**Correct pattern:**

```
A role change kicks off asynchronous work. Per Designing Record Access for
Enterprise Scale, moving one user can involve:
  - making everyone above the new role an indirect member of it
  - adding and removing shares when old and new roles have different
    account-child access settings
  - moving the customer/partner account roles off the old role and onto the
    new one for every such account the user owns (Record-Level Access: Under
    the Hood is the source for the 1-3-roles-per-account figure)
  - recalculating every sharing rule naming the old or new role as source

The documented monitoring surface is the Background Jobs page. A completion
email is documented for org-wide-default recalculation; do not promise the
user an email for a role change unless you have confirmed it in that org.

For bulk role reassignment:
  - do it in a window with no deployments, no Apex tests, no data loads
  - implement retry logic for "could not acquire lock" and
    "Group membership operation already in progress"
  - use serial processing if parallel processing produces lock errors
  - verify by login-as AFTER recalculation completes, not immediately
```

**Detection hint:** Look for the words "immediately", "instantly", or "takes effect right away" near a role, group, or OWD change. Also flag any script that asserts access in the same run as the role update.

---

## Anti-Pattern 6: Modelling the Org Chart Instead of the Access Requirements

**What the LLM generates:** A role hierarchy transcribed one-to-one from a reporting structure — CEO, COO, three EVPs, nine VPs, twenty-six directors, eighty managers — presented as a finished design, often with the observation that it "mirrors the organization for clarity."

**Why it happens:** The Salesforce documentation itself describes a role hierarchy as "similar to an organization chart", and generic training data about access control equates hierarchy with reporting line. The model optimises for recognisability rather than for access.

**Correct pattern:**

```
A role earns its place only if some user must see records owned by users
below it, and no shallower placement delivers that.

Intermediate roles that grant nothing:
  - cost indirect-membership rows in the Group Maintenance tables
  - widen the blast radius of every future reparent
  - grant nothing new, because a user two levels up already inherits
    everything a user one level up inherits

Sourced guidance: "to improve performance, it's best to set up roles based
on data access and eliminate any roles that aren't needed."

Ask for each proposed role: which records does this role see that its
parent does not already see? No answer means delete the role.
```

**Detection hint:** If the generated design has a role per manager, or role names that read as job titles rather than access scopes, ask for the access justification per role. Any role whose justification is "reports to X" is an org-chart artefact.

---

## Anti-Pattern 7: Reaching for the Role Hierarchy to Solve Peer or Cross-Branch Access

**What the LLM generates:** "Create a shared parent role above both teams so they can see each other's records", or "add the user to both roles."

**Why it happens:** The model knows the hierarchy is *the* access mechanism in Salesforce and tries to bend it. It also does not encode the constraint that a user holds exactly one role.

**Correct pattern:**

```
Hierarchy access flows UP a single branch. It never flows sideways or down.
A user holds exactly one role; there is no multi-role assignment.

Peer access, same team        -> public group + owner-based sharing rule
Cross-branch access           -> criteria-based sharing rule
Account coverage on several
  axes at once                -> Enterprise Territory Management
One-off, record-specific      -> manual sharing
Rule cannot be expressed
  declaratively               -> Apex managed sharing (__Share rows)

Creating a shared parent role to solve peer access grants that parent
EVERYTHING under both branches. It is almost always over-granting.
```

**Detection hint:** Flag "add a parent role so they can see each other", "assign the user to both roles", and any design where a role exists solely to be a common ancestor.

---

## Anti-Pattern 8: Treating Portal Roles as Ordinary, Editable Roles

**What the LLM generates:** Instructions to "find the partner role in Setup → Roles and update its opportunity access", or a script that updates `UserRole` records for portal roles, or a role-count estimate taken from the Setup Roles page.

**Why it happens:** Portal roles are `UserRole` records like any other in the API, so they look mutable. The model has no signal that they are managed by the platform on behalf of portal-enabled accounts.

**Correct pattern:**

```
Roles for customer and partner users are NOT on the role hierarchy setup page.
For each portal-enabled account, 1-3 roles are appended to the main hierarchy
below the account owner's role.

Object Reference, UserRole: "You can't update any field for a portal role."

Identify them:
  SELECT Id, Name, PortalType, PortalRole, ParentRoleId
  FROM UserRole
  WHERE PortalType != 'None'

  PortalType:  None | CustomerPortal | Partner
  PortalRole:  Executive | Manager | User | PersonAccount

They follow the account owner: moving the owner's role, or changing the
account's owner, reparents them and rewrites the associated shares.

High-volume Experience Cloud site users have NO role, so they cannot be
included in owner-based sharing rules at all.
```

**Detection hint:** Any generated DML or Setup instruction targeting a `UserRole` where `PortalType != 'None'` is invalid. Any role inventory derived from the Setup Roles page undercounts by the number of portal roles.
