# Metadata Examples — Assignment, Auto-Response and Escalation Rules

Deployable shapes for the three Lead/Case rule types. Field names, enum values, and the skeletons come from the Metadata API Developer Guide (v62 PDF, `AssignmentRules`, `AutoResponseRules`, `EscalationRules` sections); the worked examples below extend the guide's samples to realistic multi-entry rules. Validate the assignment file with:

```bash
python3 skills/admin/assignment-rules/scripts/check_assignment_rules.py --manifest-dir force-app/main/default
```

## Where the files live

| Type | package.xml `<name>` | File in a DX project | API |
|---|---|---|---|
| Assignment rules | `AssignmentRules` for every rule on an object (`<members>Lead</members>`); `AssignmentRule` for one rule (`<members>Lead.Global_Lead_Routing</members>`) | `assignmentRules/Lead.assignmentRules-meta.xml` | 27.0+ |
| Auto-response rules | `AutoResponseRules` / `AutoResponseRule` | `autoResponseRules/Case.autoResponseRules-meta.xml` | 27.0+ |
| Escalation rules | `EscalationRules` / `EscalationRule` | `escalationRules/Case.escalationRules-meta.xml` | 27.0+ |

One file per object holds every rule of that type for the object. Rules are processed in the order they appear in the container, and entries in the order they appear in the rule. All three types accept the `*` wildcard in package.xml.

## Lead assignment rule: three regional entries plus catch-all

```xml
<?xml version="1.0" encoding="UTF-8"?>
<AssignmentRules xmlns="http://soap.sforce.com/2006/04/metadata">
    <assignmentRule>
        <fullName>Global_Lead_Routing</fullName>
        <active>true</active>
        <!-- Entry 1: most specific first -->
        <ruleEntry>
            <assignedTo>EMEA_Lead_Queue</assignedTo>
            <assignedToType>Queue</assignedToType>
            <criteriaItems>
                <field>Lead.Country</field>
                <operation>equals</operation>
                <value>Germany,France,United Kingdom</value>
            </criteriaItems>
            <template>unfiled$public/Lead_Assigned_To_Queue</template>
        </ruleEntry>
        <!-- Entry 2: filter logic across three criteria -->
        <ruleEntry>
            <assignedTo>West_Region_Queue</assignedTo>
            <assignedToType>Queue</assignedToType>
            <booleanFilter>1 AND (2 OR 3)</booleanFilter>
            <criteriaItems>
                <field>Lead.Country</field>
                <operation>equals</operation>
                <value>United States</value>
            </criteriaItems>
            <criteriaItems>
                <field>Lead.State</field>
                <operation>equals</operation>
                <value>CA,OR,WA</value>
            </criteriaItems>
            <criteriaItems>
                <field>Lead.PostalCode</field>
                <operation>startsWith</operation>
                <value>9</value>
            </criteriaItems>
        </ruleEntry>
        <!-- Entry 3: formula instead of criteriaItems (never both) -->
        <ruleEntry>
            <assignedTo>enterprise.desk@acme.example</assignedTo>
            <assignedToType>User</assignedToType>
            <formula>AND(ISPICKVAL(LeadSource, "Partner Referral"), NumberOfEmployees &gt; 1000)</formula>
        </ruleEntry>
        <!-- Entry 4: catch-all, no criteria, always last -->
        <ruleEntry>
            <assignedTo>Unrouted_Leads_Queue</assignedTo>
            <assignedToType>Queue</assignedToType>
        </ruleEntry>
    </assignmentRule>
    <!-- A second, inactive rule kept for after-hours cutover. Only one rule may be active. -->
    <assignmentRule>
        <fullName>After_Hours_Lead_Routing</fullName>
        <active>false</active>
        <ruleEntry>
            <assignedTo>After_Hours_Queue</assignedTo>
            <assignedToType>Queue</assignedToType>
        </ruleEntry>
    </assignmentRule>
</AssignmentRules>
```

How to read it:

- `assignedTo` holds a **username** when `assignedToType` is `User` and the queue's **developer name** when it is `Queue`. The guide's sample uses `testUser@org.com` with `User`.
- `criteriaItems` and `formula` are mutually exclusive on an entry ("Specify either formula or criteriaItems, but not both fields").
- `booleanFilter` numbers the `criteriaItems` in order; without it the items are ANDed.
- `template` is `Folder/Developer_Name`; the guide recommends a Classic template because Lightning templates are not packageable.
- A catch-all entry is an entry with neither `criteriaItems` nor `formula`. The checker script flags an active rule without one.
- Deploying `<active>true</active>` activates that rule and, because only one rule per object can be active, deactivates the one currently active in the target org (`references/migration-and-sandbox.md`).

## Case assignment rule with case team and Cc handling

The three Case-only entry fields: `team` (case team to add), `overrideExistingTeams` (reset vs add), and `notifyCcRecipients` (copy the inbound Cc line onto the auto-response, API 32.0+).

```xml
<?xml version="1.0" encoding="UTF-8"?>
<AssignmentRules xmlns="http://soap.sforce.com/2006/04/metadata">
    <assignmentRule>
        <fullName>Support_Case_Routing</fullName>
        <active>true</active>
        <ruleEntry>
            <assignedTo>Priority_Support_Queue</assignedTo>
            <assignedToType>Queue</assignedToType>
            <booleanFilter>1 AND 2</booleanFilter>
            <criteriaItems>
                <field>Case.Priority</field>
                <operation>equals</operation>
                <value>High</value>
            </criteriaItems>
            <criteriaItems>
                <field>Case.Type</field>
                <operation>equals</operation>
                <value>Problem</value>
            </criteriaItems>
            <team>Tier_2_Escalation_Team</team>
            <overrideExistingTeams>false</overrideExistingTeams>
            <notifyCcRecipients>true</notifyCcRecipients>
            <template>unfiled$public/Case_Assigned_Priority</template>
        </ruleEntry>
        <ruleEntry>
            <assignedTo>General_Support_Queue</assignedTo>
            <assignedToType>Queue</assignedToType>
        </ruleEntry>
    </assignmentRule>
</AssignmentRules>
```

## Case auto-response rule

Auto-response entries carry the sender identity and template; there is no `assignedTo`. The rule is only evaluated when the assignment rule fires (`admin/case-management-setup`), and `senderEmail` must be a verified **OrgWideEmailAddress that is not an Email-to-Case intake address** — a sender equal to a routing address's `emailAddress` creates the loop auto-response → customer reply → routing address → new case → auto-response (`admin/email-to-case-configuration`, `references/metadata-examples.md`, where `support@acme.example` is the routing `emailAddress` this example must not reuse). Provision a dedicated no-reply address for the sender, and confirm it is not, and does not forward into, any routing address.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<AutoResponseRules xmlns="http://soap.sforce.com/2006/04/metadata">
    <autoResponseRule>
        <fullName>Case_Acknowledgement</fullName>
        <active>true</active>
        <!-- senderEmail is a distinct, verified OrgWideEmailAddress that is NOT an
             Email-to-Case routing address (support@acme.example is the routing
             emailAddress in admin/email-to-case-configuration — reusing it here
             loops auto-response replies straight back into a new case). -->
        <ruleEntry>
            <criteriaItems>
                <field>Case.Origin</field>
                <operation>equals</operation>
                <value>Web</value>
            </criteriaItems>
            <senderEmail>support-noreply@acme.example</senderEmail>
            <senderName>Acme Support</senderName>
            <replyToEmail>support-noreply@acme.example</replyToEmail>
            <template>unfiled$public/Case_Web_Acknowledgement</template>
        </ruleEntry>
        <ruleEntry>
            <criteriaItems>
                <field>Case.Origin</field>
                <operation>equals</operation>
                <value>Email</value>
            </criteriaItems>
            <senderEmail>support-noreply@acme.example</senderEmail>
            <senderName>Acme Support</senderName>
            <replyToEmail>support-noreply@acme.example</replyToEmail>
            <template>unfiled$public/Case_Email_Acknowledgement</template>
        </ruleEntry>
    </autoResponseRule>
</AutoResponseRules>
```

The Lead version is identical with `Lead.` fields and lives in `autoResponseRules/Lead.autoResponseRules-meta.xml`. `senderEmail` must be a verified org-wide email address in the target org, and it must not equal — or forward into — any Email-to-Case routing address; validate this with `scripts/check_assignment_rules.py` (rule `AR-LOOP-01`), which cross-references `senderEmail` against every `routingAddresses/emailAddress` it can find under `settings/Case.settings-meta.xml` in the tree.

`support-noreply@acme.example` is also a deploy-time prerequisite in the target org: provision and verify the `OrgWideEmailAddress` in Setup before deploying this rule, or `sf project deploy start` fails validation with `<address> is an invalid From email address.: Email Address` (`references/gotchas.md` #7). `scripts/check_assignment_rules.py` (`AR-SENDER-01`) prints one deduped INFO line naming both `senderEmail` occurrences above as this same prerequisite.

## Case escalation rule: two-stage escalation inside business hours

```xml
<?xml version="1.0" encoding="UTF-8"?>
<EscalationRules xmlns="http://soap.sforce.com/2006/04/metadata">
    <escalationRule>
        <fullName>High_Priority_SLA</fullName>
        <active>true</active>
        <ruleEntry>
            <businessHoursSource>Static</businessHoursSource>
            <businessHours>Support_Business_Hours</businessHours>
            <criteriaItems>
                <field>Case.Priority</field>
                <operation>equals</operation>
                <value>High</value>
            </criteriaItems>
            <escalationStartTime>CaseCreation</escalationStartTime>
            <disableEscalationWhenModified>false</disableEscalationWhenModified>
            <!-- Stage 1 at 2 business hours: notify, no reassignment -->
            <escalationAction>
                <minutesToEscalation>120</minutesToEscalation>
                <notifyCaseOwner>true</notifyCaseOwner>
                <notifyTo>support.manager@acme.example</notifyTo>
                <notifyToTemplate>unfiled$public/Case_Escalation_Warning</notifyToTemplate>
            </escalationAction>
            <!-- Stage 2 at 8 business hours: reassign to Tier 2 and notify -->
            <escalationAction>
                <minutesToEscalation>480</minutesToEscalation>
                <assignedTo>Tier_2_Support_Queue</assignedTo>
                <assignedToType>Queue</assignedToType>
                <assignedToTemplate>unfiled$public/Case_Escalated_To_Tier2</assignedToTemplate>
                <notifyCaseOwner>true</notifyCaseOwner>
                <notifyEmail>sla-breaches@acme.example</notifyEmail>
            </escalationAction>
        </ruleEntry>
        <ruleEntry>
            <businessHoursSource>None</businessHoursSource>
            <escalationStartTime>CaseLastModified</escalationStartTime>
            <disableEscalationWhenModified>true</disableEscalationWhenModified>
            <escalationAction>
                <minutesToEscalation>1440</minutesToEscalation>
                <notifyCaseOwner>true</notifyCaseOwner>
            </escalationAction>
        </ruleEntry>
    </escalationRule>
</EscalationRules>
```

How to read it:

- `businessHoursSource` is `None`, `Case` (use the hours on the Case record), or `Static` (use the named `businessHours`; set it only with `Static`).
- `escalationStartTime` is `CaseCreation` or `CaseLastModified`; `disableEscalationWhenModified` stops the clock when the record is edited.
- Times are **minutes** in metadata although Setup shows hours: 120 = 2 hours, 1440 = 24 hours (the guide's own sample uses 1440).
- An action without `assignedTo` is notification-only. The guide models `escalationAction` as an unbounded list; the commonly quoted five-per-entry ceiling is UNVERIFIED (2026-09-04: not in the Metadata API guide or the App Limits cheat sheet; see `admin/escalation-rules`).
- Every template, queue, and business-hours name must already exist in the target org.

## package.xml and CLI

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Lead</members>
        <members>Case</members>
        <name>AssignmentRules</name>
    </types>
    <types>
        <members>Case</members>
        <name>AutoResponseRules</name>
    </types>
    <types>
        <members>Case</members>
        <name>EscalationRules</name>
    </types>
    <version>62.0</version>
</Package>
```

```bash
# Pull the org's current rules into source before editing
sf project retrieve start --metadata AssignmentRules:Lead AssignmentRules:Case AutoResponseRules:Case EscalationRules:Case --target-org my-sandbox

# Lint, then validate without deploying
python3 skills/admin/assignment-rules/scripts/check_assignment_rules.py --manifest-dir force-app/main/default
sf project deploy validate --source-dir force-app/main/default/assignmentRules --target-org my-sandbox

# Deploy queues and templates first (references/migration-and-sandbox.md), then the rules
sf project deploy start --source-dir force-app/main/default/assignmentRules --target-org my-sandbox
```

For the whole-object retrieve, `AssignmentRules:Lead` returns every Lead rule; to fetch a single rule use the singular type, `AssignmentRule:Lead.Global_Lead_Routing`.
