# Examples — Scoping Rules

## Example 1: Contacts Default to the Viewing User's Department

**Context:** A 900-seat services org runs a shared Contact database. Every consultant can legitimately see every contact — that is deliberate, because staffing decisions cross practice lines. The complaint is not access, it is that the default Contacts list view returns 400,000 rows and a consultant in the Data practice has to filter every single time. Contact carries a `Department` field; User carries `Department`; the values are already aligned because both are fed from the HR system.

**Problem:** The obvious fixes are all wrong. Tightening the Contact OWD takes away access the business wants people to have. A per-user personal list view does not scale to 900 people and cannot be governed. A shared list view with a hardcoded department filter needs one view per department and does not follow a consultant who moves practice.

**Solution:**

Step 1 — build the rule. This criterion is a plain comparison, so Object Manager is the faster path:

```text
Setup → Object Manager → Contact → Scoping Rules → New

  Label:           SR for Department A contacts
  Description:     View contacts from Department A.
  Record criteria: Department=$User.Department
  User criteria:   $User.UserRoleId = '00Exxxxxxxxxxxx'
  Active:          leave unchecked until deployed
```

The equivalent deployable file, for a source-tracked org:

```xml
<!-- force-app/main/default/restrictionRules/SR_Department_A_Contacts.rule-meta.xml -->
<?xml version="1.0" encoding="UTF-8"?>
<RestrictionRule xmlns="http://soap.sforce.com/2006/04/metadata">
    <active>true</active>
    <description>View contacts from Department A.</description>
    <enforcementType>Scoping</enforcementType>
    <masterLabel>SR for Department A contacts</masterLabel>
    <recordFilter>Department=$User.Department</recordFilter>
    <targetEntity>Contact</targetEntity>
    <userCriteria>$User.UserRoleId = '00Exxxxxxxxxxxx'</userCriteria>
    <version>1</version>
</RestrictionRule>
```

Step 2 — remap the role ID. `00Exxxxxxxxxxxx` is the sandbox consulting role. Query the destination org for the production value before deploying:

```soql
SELECT Id, Name, DeveloperName FROM UserRole WHERE DeveloperName = 'Consulting_Staff'
```

Step 3 — deploy and activate:

```bash
sf project deploy start --metadata RestrictionRule:SR_Department_A_Contacts
```

Step 4 — wire the surfaces. This is the step that makes the rule visible; without it nothing changes for any user. Set `filterScope` on the Contact list view the consultants land on:

```xml
<!-- force-app/main/default/objects/Contact/listViews/All_Active_Contacts.listView-meta.xml -->
<?xml version="1.0" encoding="UTF-8"?>
<ListView xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>All_Active_Contacts</fullName>
    <columns>NAME</columns>
    <columns>ACCOUNT.NAME</columns>
    <columns>CONTACT.DEPARTMENT</columns>
    <columns>CONTACT.TITLE</columns>
    <filterScope>ScopingRule</filterScope>
    <label>Contacts (My Department)</label>
</ListView>
```

Step 5 — verify as an affected user, and prove access is intact:

```soql
-- As a Data-practice consultant. Returns only Data-practice contacts.
SELECT COUNT() FROM Contact

-- Same user, same session. Returns the full 400,000.
SELECT COUNT() FROM Contact USING SCOPE everything
```

**Why it works:** `$User.Department` is evaluated per running user, so one rule covers every practice and follows a consultant who transfers — no per-department artefact exists to maintain. The two counts in step 5 are the proof that this is a focus control and not an access control: the same user, in the same session, reaches all 400,000 records by asking for them. That is the intended behaviour, and it is why this design would be unacceptable if the requirement had been confidentiality.

**Source:** `recordFilter` and `userCriteria` strings are the documented Contact-department example; the `filterScope` value `ScopingRule` and its Lightning-only, opt-in behaviour are from the ListView metadata type reference. See `well-architected.md` for URLs.

---

## Example 2: Accounts Default to the Banker's Current Branch (SOQL Operator)

**Context:** A retail bank runs Financial Services Cloud. Bankers are assigned to a branch through `Banker.CurrentBranchId`, and accounts are linked to branches through the `BranchUnitCustomer` junction. A banker covering the Leeds branch should open Salesforce and see Leeds accounts, but must retain access to every account in the region for cover and escalation.

**Problem:** There is no field on Account holding the branch, so `Field = $User.Field` cannot express this. The relationship is two hops: User → Banker → BranchUnit → BranchUnitCustomer → Account. Object Manager cannot build this criterion at all.

**Solution:**

Step 1 — write and time the subquery standalone, logged in as a banker, before it ever becomes a rule:

```soql
SELECT AccountId FROM BranchUnitCustomer
WHERE BranchUnitId IN (SELECT CurrentBranchId FROM Banker WHERE UserOrContactId = '005xxxxxxxxxxxxxxx')
```

If this is slow here it will be slow on every list view render, and an inefficient rule is one Salesforce reserves the right to disable.

Step 2 — wrap it in the SOQL operator. What follows is Salesforce's published rule, reproduced exactly — and note that its nested `SELECT` does *not* carry `USING SCOPE EVERYTHING`, even though the same guide states that nested `SELECT` statements must. Deploy the compliant form (the clause on both) unless you have verified the documented form works in your org; see `gotchas.md` Gotcha 5:

```xml
<!-- force-app/main/default/restrictionRules/BranchRuleOnAccount.rule-meta.xml -->
<?xml version="1.0" encoding="UTF-8"?>
<RestrictionRule xmlns="http://soap.sforce.com/2006/04/metadata">
  <active>true</active>
  <description>Scoping rule where users can scope account records by the user's current branch</description>
  <enforcementType>Scoping</enforcementType>
  <masterLabel>BranchRuleOnAccount</masterLabel>
  <recordFilter>SOQL(Id, SELECT AccountId FROM BranchUnitCustomer USING SCOPE EVERYTHING WHERE BranchUnitId IN(SELECT CurrentBranchId From Banker WHERE UserOrContactId = $User.Id))</recordFilter>
  <targetEntity>Account</targetEntity>
  <userCriteria>$User.IsActive = true</userCriteria>
  <version>1</version>
</RestrictionRule>
```

Step 3 — deploy through Metadata API. There is no Setup path for this rule:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
  <types>
    <members>*</members>
    <name>RestrictionRule</name>
  </types>
  <version>67.0</version>
</Package>
```

```text
myPackage/package.xml
myPackage/restrictionRules/BranchRuleOnAccount.rule
```

Step 4 — give bankers a way to move. A banker covering two branches for the week needs to switch without an admin. Build a Screen Flow that writes `Banker.CurrentBranchId`, and surface it in the Lightning Utility Bar; the rule reads the new value on the next query and never changes.

**Why it works:** `$User.Id` is the one dynamic user variable the SOQL operator accepts, and it is enough — everything else is reached by joining. The junction object in the subquery (`BranchUnitCustomer`) is deliberately not the target entity (`Account`), satisfying the constraint that the SOQL query object and the target entity cannot be the same. Because the rule is parameterised on a mutable user attribute rather than a literal branch, one rule serves every branch in the bank, which matters given the low per-object active-rule cap.

**Source:** the `recordFilter`, `userCriteria`, `package.xml` and directory layout are the documented branch-management quick start; the utility-bar Flow pattern is Salesforce's documented approach to letting users set their own scope. See `well-architected.md` for URLs.

---

## Example 3: Scoping Multiple Values, and the Quoting Trap

**Context:** A specialist team owns a named book of relationship managers rather than a single department. The scope must cover records whose owner reports to either of two managers, and a second rule must match a set of literal names, one of which contains a comma.

**Problem:** The criteria language uses the comma as its value delimiter, so a name like `Torres, Jia` silently splits into two values and the rule matches records nobody intended. There is no error — the deploy succeeds and the wrong record set appears.

**Solution:**

```text
-- Two manager IDs, comma-separated on the right-hand side:
recordFilter:  Agent__c.Owner:User.ManagerId=001xx000003HNy7, 001xx000003HNut
userCriteria:  $User.IsActive=true

-- Literal names, one containing a comma, protected by double quotes:
recordFilter:  Name__c='Tom, Anita, "Torres, Jia"'
userCriteria:  $User.IsActive=true
```

Salesforce's rule is that "double-quotes specify that the value inside the quotes isn't considered a delimiter". Without them the second filter matches four values (`Tom`, `Anita`, `Torres`, `Jia`) instead of three.

Note `Owner:User` in the first filter. `Owner` is polymorphic — Salesforce's example is that an event's Owner "can contain a user or a queue, but queues aren't supported in scoping rules" — so the reference must be typed to User. `Agent__c.Owner.ManagerId` is not valid; `Agent__c.Owner:User.ManagerId` is. The path also sits at the one-level dot-notation limit ("one lookup level from the `targetEntity`").

What you cannot do here is add a second condition. Outside the SOQL operator, "scoping rules support only the EQUALS operator. The AND and OR operators aren't supported" — the comma list is multi-value equality on one field, not a way to combine fields. A requirement spanning two fields needs a precomputed field to match against, or the API path.

**Why it works:** Both filters stay inside the supported data types (reference and string) and inside the one-level lookup limit, and the quoting makes the delimiter explicit rather than relying on the parser to guess.

**Source:** both criteria strings are the documented multiple-values examples; the `Owner:User` typing requirement and the one-level dot-notation limit are from the Considerations page. See `well-architected.md` for URLs.

---

## Failure Example: A Scoping Rule Shipped as a Compliance Control

**Context:** An insurance org has a claims team and a special investigations unit. Legal asks that ordinary claims handlers not see claims flagged for investigation. An admin, told to "restrict what handlers see on Claim", finds Scoping Rules in Object Manager on the custom `Claim__c` object, builds `Under_Investigation__c = false` as the record criterion with the claims-handler role as the user criterion, activates it, sets `filterScope` on the team list view, and reports the control as delivered. The list view now shows no investigated claims. It demos correctly.

**What goes wrong:** Nothing, for about a month. Then a handler receives an email with a claim link, clicks it, and opens an investigated claim. Another handler builds a personal report without selecting **Filter by scope** and gets the full set. A third runs a global search and finds every investigated claim, because Search does not appear in the scoping surface table at all — it appears in the *restriction* rule surface list ("Links, List Views, Lookups, Records, Related Lists, Reports, Search, SOQL, SOSL"), which is a different feature. Nothing was breached in the platform's terms: the sharing model always granted these users access, and the documentation says so explicitly — scoping rules "don't restrict the access that your users have to records. Your users can still open and report on all the records that they can access according to your org's sharing settings." The control was never a control. The audit finding lands on the admin.

**How to recover:**

1. Do not disable the scoping rule first. "To disable a scoping rule, first delete the list views and reports that have **Filter by scope** selected. After a scoping rule is disabled, the list views and reports aren't functional nor modifiable." Deal with the surfaces while they are still editable.
2. Classify the requirement correctly. "Must not see" is an access requirement, so the answer is the sharing model and `admin/restriction-rules`. Confirm `Claim__c` is a custom object, which is on the restriction-supported list.
3. Expect the criteria to be less expressive on the way over: "restriction rules support only the EQUALS operator", formulas are not supported, and null or blank values in criteria are not supported. A scoping criterion may not translate one-for-one.
4. Know the remaining holes before you promise enforcement: restriction rules "aren't applied for code executed in System Mode", and users with View All Records or View All Data see everything regardless. Neither is a reason to keep the scoping rule; both are things Legal needs to hear.
5. Record the classification decision in writing so the next person does not repeat it.

**The generalisable lesson:** the two features share a metadata type, a Setup neighbourhood and most of a vocabulary, and exactly one of them is a security control. If a stakeholder would be upset that a user *could* see a record, a scoping rule is the wrong artefact no matter how convincing the list view looks.
