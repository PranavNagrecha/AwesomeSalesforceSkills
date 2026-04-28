# Examples — Acceptance Criteria Given/When/Then

Three worked AC sets showing the shape this skill produces. Each set assumes
the user-story wrapper (As a / I want / So that) has already been written by
`admin/user-story-writing-for-salesforce` — these examples are only the AC
block that pastes inside the story.

---

## Example 1: Opportunity Stage Update Gated by Probability

**Story summary:** A Sales Rep needs to advance an Opportunity from
"Negotiation" to "Closed Won" only when Probability is 100. A Sales Manager
in the same role hierarchy needs to override this for special cases.

**AC block:**

```gherkin
Background:
  Given a user "Alice" in the "Sales_Rep_PSG" permission set group with role "EMEA Sales"
    And a user "Bob"   in the "Sales_Manager_PSG" permission set group with role "EMEA Sales Manager"
    And the Opportunity OWD is "Private"
    And Bob is above Alice in the role hierarchy

Scenario: Sales Rep can move Stage to Closed Won when Probability is 100
  Given an Opportunity owned by Alice
    And the Opportunity StageName is "Negotiation"
    And the Opportunity Probability is 100
   When Alice updates StageName to "Closed Won"
   Then the save succeeds
    And StageName is "Closed Won"
    And CloseDate is unchanged

Scenario: Sales Rep is blocked from Closed Won when Probability is below 100
  Given an Opportunity owned by Alice
    And the Opportunity StageName is "Negotiation"
    And the Opportunity Probability is 50
   When Alice updates StageName to "Closed Won"
   Then the save fails
    And the validation error is "Stage cannot be Closed Won until Probability is 100"
    And StageName remains "Negotiation"

Scenario: Sales Manager can override the Probability gate
  Given an Opportunity owned by Alice
    And the Opportunity Probability is 50
    And Bob is logged in
   When Bob updates StageName to "Closed Won"
   Then the save succeeds
    And StageName is "Closed Won"

Scenario Outline: Stage transitions allowed by Sales Process for a Sales Rep
  Given an Opportunity owned by Alice
    And StageName is "<from_stage>"
    And Probability is <prob>
   When Alice updates StageName to "<to_stage>"
   Then the save <result>

  Examples:
    | from_stage    | prob | to_stage      | result                                          |
    | Prospecting   | 10   | Qualification | succeeds                                        |
    | Qualification | 25   | Negotiation   | succeeds                                        |
    | Negotiation   | 100  | Closed Won    | succeeds                                        |
    | Negotiation   | 50   | Closed Won    | fails with "Probability must be 100"            |
    | Closed Won    | 100  | Prospecting   | fails with "Cannot reopen a Closed Won record"  |

Scenario: Bulk update of 200 Opportunities respects the Probability gate
  Given 200 Opportunities owned by users in "Sales_Rep_PSG"
    And 100 of them have Probability 100 and 100 have Probability 50
   When a Data Loader update sets StageName to "Closed Won" on all 200
   Then the 100 records with Probability 100 succeed
    And the 100 records with Probability 50 fail with "Probability must be 100"
    And no governor-limit error is raised
```

**Why it works:** Three happy-path scenarios are each paired with explicit
deny-cases (negative path, role override is its own scenario). The Outline
collapses what would otherwise be 5 near-duplicate Scenarios. The Bulk
Scenario protects the design from a single-record-only Apex test that
silently breaks at 200.

---

## Example 2: Sharing-Visibility Check on a Custom Object

**Story summary:** A custom object `Deal_Plan__c` is linked to Opportunity.
A Deal Plan should be visible to the Opportunity owner, the Opportunity Team
"Sales Engineer" role, and the user's manager via role hierarchy — and to
no one else.

**AC block:**

```gherkin
Background:
  Given a user "Alice"   in the "Sales_Rep_PSG" with role "EMEA Sales"
    And a user "Bob"     in the "Sales_Manager_PSG" with role "EMEA Sales Manager"
    And a user "Eve"     in the "Sales_Engineer_PSG" with role "EMEA Solutions"
    And a user "Mallory" in the "Sales_Rep_PSG" with role "AMER Sales"
    And the Deal_Plan__c OWD is "Private"
    And Deal_Plan__c is set to "Controlled by Parent" against Opportunity
    And Bob is above Alice in the role hierarchy
    And Bob is NOT above Mallory

Scenario: Owner can read their Deal Plan
  Given an Opportunity owned by Alice
    And a Deal_Plan__c child record on that Opportunity
   When Alice opens the Deal_Plan__c record
   Then the record is visible
    And all fields with FLS "Read" for Sales_Rep_PSG are visible

Scenario: Manager in role hierarchy can read the Deal Plan
  Given the same Deal_Plan__c record from the previous Scenario
   When Bob opens the Deal_Plan__c record
   Then the record is visible

Scenario: Sales Engineer added to Opportunity Team can read the Deal Plan
  Given Eve is added to the Opportunity Team with role "Sales Engineer" and access "Read"
   When Eve opens the same Deal_Plan__c record
   Then the record is visible

Scenario: Peer rep outside the role hierarchy cannot read the Deal Plan
  Given the same Deal_Plan__c record owned by Alice
   When Mallory opens the Deal_Plan__c record
   Then the access is denied
    And the response is the standard "Insufficient Privileges" page

Scenario: Sales Engineer NOT on the Opportunity Team cannot read the Deal Plan
  Given Eve is removed from the Opportunity Team
   When Eve opens the same Deal_Plan__c record
   Then the access is denied

Scenario: Bulk visibility for 1000 Deal Plans respects sharing
  Given 1000 Opportunities owned by Alice
    And one Deal_Plan__c per Opportunity
   When Mallory runs a list-view query "All Deal Plans"
   Then 0 Deal_Plan__c records are returned
    And the query completes without governor-limit error
```

**Why it works:** Permissions and sharing are stated up front (Background)
and never repeated. Every "can see" Scenario is paired with a "cannot see"
Scenario for the symmetric deny-case. The bulk scenario asserts the
sharing-rule recalculation does not blow up at 1k records, which is the
shape `agents/data-loader-pre-flight` will use.

---

## Example 3: Bulk Import of Contacts with Duplicate Emails

**Story summary:** A weekly file of up to 10,000 Contact records is loaded
via Bulk API. Duplicate emails (within the file or against existing records)
must not create new Contacts, but must produce a per-row error report.

**AC block:**

```gherkin
Background:
  Given a user "Loader" in the "Integration_User_PSG" with profile "API Only"
    And a Duplicate Rule "Contact_Email_Dedup" is active for Contact, set to "Block" with allow-bypass off
    And the Bulk API job runs as Loader

Scenario: Single-row clean insert succeeds
  Given a CSV with 1 row
    And the Email is unique within the file and the org
   When Loader runs the Bulk API insert
   Then 1 Contact is created
    And the job's success count is 1
    And the job's error count is 0

Scenario: Single-row duplicate against existing record fails
  Given a Contact already exists with Email "alice@example.com"
    And a CSV with 1 row whose Email is "alice@example.com"
   When Loader runs the Bulk API insert
   Then 0 Contacts are created
    And the job's error count is 1
    And the row error message contains "DUPLICATE_VALUE" and "Contact_Email_Dedup"

Scenario: 1k clean rows succeed
  Given a CSV with 1000 rows, all with unique, non-conflicting Emails
   When Loader runs the Bulk API insert
   Then 1000 Contacts are created
    And the job's success count is 1000
    And the job's error count is 0
    And the job completes within the configured Bulk API timeout

Scenario: 1k rows with 50 internal duplicates produce a partial-success result
  Given a CSV with 1000 rows
    And 50 rows share an Email with another row in the same file
    And the remaining 950 rows have unique, non-conflicting Emails
   When Loader runs the Bulk API insert
   Then 950 Contacts are created (the first occurrence of each Email)
    And 50 rows fail with error "DUPLICATE_VALUE"
    And the per-row error report identifies the duplicate Email value
    And no governor-limit error is raised at the trigger or duplicate-rule layer

Scenario: 1k rows where 100 conflict with existing org records
  Given 100 Contacts already exist in the org with Emails E1..E100
    And a CSV with 1000 rows where 100 rows have Emails E1..E100
    And 900 rows have unique non-conflicting Emails
   When Loader runs the Bulk API insert
   Then 900 Contacts are created
    And 100 rows fail with "DUPLICATE_VALUE"
    And the report names the matching existing Contact Id per failed row

Scenario Outline: Email-blank handling
  Given a CSV with 1 row whose Email is "<value>"
   When Loader runs the Bulk API insert
   Then the row <result>

  Examples:
    | value             | result                                              |
    | (empty)           | succeeds because Email is not required on Contact   |
    | "  "              | fails with "Email cannot be whitespace"             |
    | "not-an-email"    | fails with "Email must be a valid email address"    |
```

**Why it works:** Volumes are explicit (1, 1k, 50, 100). The deny-cases
cover both intra-file and against-org duplicates. The Outline parameterizes
the empty/whitespace edge cases. The Background pins the duplicate-rule
configuration so the AC is unambiguous about whether the rule is "Allow with
alert" vs "Block". This is exactly the shape
`agents/data-loader-pre-flight` consumes when computing the seed shape.

---

## Anti-Pattern: Compound AC With Multiple Whens

**What practitioners do:** Write a single Scenario like:

```
Scenario: Closing the Opportunity
  Given an Opportunity in stage Negotiation
   When the user changes Stage to Closed Won AND saves the record AND the manager approves AND the system sends a confirmation email
   Then everything is updated
```

**What goes wrong:** Four behaviors are wedged into one Scenario. UAT cannot
report which behavior failed. Apex tests written from this AC end up with
multiple oracles in one method and violate single-responsibility. When the
email fails to send but the save succeeds, the Scenario is reported as
"failed" with no signal about which oracle was wrong.

**Correct approach:** Split into four Scenarios — Stage update, save, manager
approval (probably a separate story altogether), email send (likely a
post-commit Scenario with `Then eventually within 60 seconds`).
