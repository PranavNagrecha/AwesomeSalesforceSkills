# Metadata Examples — Escalation Rules (Operational)

Field names, enum values, and the skeleton come from the Metadata API Developer Guide `EscalationRules` section (v62 PDF, `RuleEntry` / `EscalationAction` field tables and the guide's own sample definition). The examples below extend that sample into the shapes you actually deploy and operate.

**The base shape lives next door.** `admin/assignment-rules` `references/metadata-examples.md` already carries a minimal two-stage Case escalation rule alongside the Assignment and Auto-Response files, and the "where the files live" table for all three types. Read that first if you need the bare skeleton. This file covers what happens after: mixed clocks, a rule staged for cutover, monitoring, and the parallel run.

Validate anything you write here with:

```bash
python3 skills/admin/escalation-rules/scripts/check_escalation_rules.py --manifest-dir force-app/main/default
```

## Where the file lives

| Property | Value |
|---|---|
| DX path | `force-app/main/default/escalationRules/Case.escalationRules-meta.xml` |
| Suffix / folder | `.escalationRules` in the `escalationRules` folder |
| package.xml type (all rules for an object) | `EscalationRules`, member `Case` |
| package.xml type (one named rule) | `EscalationRule`, member `Case.Support_SLA_Escalation` |
| Wildcard | `*` is supported for `EscalationRules` |
| API version | 27.0 and later |

One file holds **every** escalation rule for the object, active and inactive. Retrieving `EscalationRules:Case` and deploying it back overwrites the whole file, so never hand-write a partial file over a retrieved one.

## Three-tier escalation with mixed clocks, plus a rule staged for cutover

Three entries in one rule, each with a different clock, and a second rule deployed inactive for the parallel run. Note the tiers escalate **inside** an entry via repeated `escalationAction`, not across entries — a case matches one entry only.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<EscalationRules xmlns="http://soap.sforce.com/2006/04/metadata">
    <!-- The live rule. Exactly one rule in this file should be active. -->
    <escalationRule>
        <fullName>Support_SLA_Escalation</fullName>
        <active>true</active>

        <!-- Entry 1: Sev-1 runs 24/7. businessHoursSource None ignores every calendar,
             including any calendar on the Case itself. -->
        <ruleEntry>
            <businessHoursSource>None</businessHoursSource>
            <booleanFilter>1 AND 2</booleanFilter>
            <criteriaItems>
                <field>Case.Priority</field>
                <operation>equals</operation>
                <value>Sev-1</value>
            </criteriaItems>
            <criteriaItems>
                <field>Case.Status</field>
                <operation>notEqual</operation>
                <value>Closed</value>
            </criteriaItems>
            <escalationStartTime>CaseCreation</escalationStartTime>
            <disableEscalationWhenModified>false</disableEscalationWhenModified>
            <!-- Stage 1 at 15 wall-clock minutes: notify only, owner keeps the case. -->
            <escalationAction>
                <minutesToEscalation>15</minutesToEscalation>
                <notifyCaseOwner>true</notifyCaseOwner>
                <notifyTo>duty.manager@acme.example</notifyTo>
                <notifyToTemplate>unfiled$public/Sev1_Escalation_Warning</notifyToTemplate>
            </escalationAction>
            <!-- Stage 2 at 60 wall-clock minutes: change of owner. This writes OwnerId. -->
            <escalationAction>
                <minutesToEscalation>60</minutesToEscalation>
                <assignedTo>Sev1_Bridge_Queue</assignedTo>
                <assignedToType>Queue</assignedToType>
                <assignedToTemplate>unfiled$public/Sev1_Handover</assignedToTemplate>
                <notifyCaseOwner>true</notifyCaseOwner>
                <notifyEmail>incident-bridge@acme.example</notifyEmail>
            </escalationAction>
        </ruleEntry>

        <!-- Entry 2: High priority follows the calendar named on the Case record. -->
        <ruleEntry>
            <businessHoursSource>Case</businessHoursSource>
            <criteriaItems>
                <field>Case.Priority</field>
                <operation>equals</operation>
                <value>High</value>
            </criteriaItems>
            <escalationStartTime>CaseLastModified</escalationStartTime>
            <disableEscalationWhenModified>false</disableEscalationWhenModified>
            <!-- 4 business hours = 240 minutes. Notify-only: no assignedTo. -->
            <escalationAction>
                <minutesToEscalation>240</minutesToEscalation>
                <notifyCaseOwner>true</notifyCaseOwner>
                <notifyTo>support.manager@acme.example</notifyTo>
                <notifyToTemplate>unfiled$public/Case_Escalation_Warning</notifyToTemplate>
            </escalationAction>
            <!-- 8 business hours = 480 minutes: reassign to Tier 2. -->
            <escalationAction>
                <minutesToEscalation>480</minutesToEscalation>
                <assignedTo>Tier_2_Support_Queue</assignedTo>
                <assignedToType>Queue</assignedToType>
                <assignedToTemplate>unfiled$public/Case_Escalated_To_Tier2</assignedToTemplate>
                <notifyEmail>sla-breaches@acme.example</notifyEmail>
            </escalationAction>
        </ruleEntry>

        <!-- Entry 3: everything else, on one fixed calendar regardless of the Case field.
             businessHours is legal here only because the source is Static. -->
        <ruleEntry>
            <businessHoursSource>Static</businessHoursSource>
            <businessHours>Global_Support_Hours</businessHours>
            <formula>AND(NOT(IsClosed), NOT(ISPICKVAL(Priority, "Sev-1")), NOT(ISPICKVAL(Priority, "High")))</formula>
            <escalationStartTime>CaseLastModified</escalationStartTime>
            <!-- Any edit disables escalation for this tier: touching the case is the SLA. -->
            <disableEscalationWhenModified>true</disableEscalationWhenModified>
            <!-- 24 business hours = 1440 minutes, the value used in the guide's own sample. -->
            <escalationAction>
                <minutesToEscalation>1440</minutesToEscalation>
                <notifyCaseOwner>true</notifyCaseOwner>
                <notifyTo>support.manager@acme.example</notifyTo>
            </escalationAction>
        </ruleEntry>
    </escalationRule>

    <!-- The replacement, deployed INACTIVE so production behaviour does not change.
         Activation is a separate, one-line deploy: see "Parallel run and cutover" below. -->
    <escalationRule>
        <fullName>Support_SLA_Escalation_2026H2</fullName>
        <active>false</active>
        <ruleEntry>
            <businessHoursSource>Static</businessHoursSource>
            <businessHours>Global_Support_Hours</businessHours>
            <criteriaItems>
                <field>Case.Priority</field>
                <operation>equals</operation>
                <value>Sev-1,High</value>
            </criteriaItems>
            <escalationStartTime>CaseCreation</escalationStartTime>
            <disableEscalationWhenModified>false</disableEscalationWhenModified>
            <escalationAction>
                <minutesToEscalation>120</minutesToEscalation>
                <notifyCaseOwner>true</notifyCaseOwner>
                <notifyTo>support.manager@acme.example</notifyTo>
            </escalationAction>
        </ruleEntry>
    </escalationRule>
</EscalationRules>
```

How to read it:

- **`businessHoursSource` is per entry, and it is the whole clock decision.** `None` = wall clock; `Case` = the calendar on `Case.BusinessHoursId`; `Static` = the calendar named in `businessHours`. The guide is explicit that `businessHours` is specified "only if businessHoursSource is set to Static".
- **`minutesToEscalation` is minutes.** 15, 60, 240, 480, 1440 above are 15 min, 1 h, 4 h, 8 h, 24 h. Setup shows hours; the metadata does not.
- **Stages live inside one entry.** Entry 1 has two actions at 15 and 60 minutes. Adding a second entry with the same criteria would be dead configuration — the first match wins.
- **Notify-only vs reassign** is decided by the presence of `assignedTo`. `assignedToType` (`User` or `Queue`) is meaningless without it, and a reassigning action writes `OwnerId`.
- **`criteriaItems` and `formula` are mutually exclusive** on an entry: "Specify either formula or criteriaItems, but not both fields." Entry 3 uses `formula`; entries 1 and 2 use `criteriaItems`.
- **`booleanFilter` numbers the `criteriaItems` in document order.** Without it they are ANDed.
- **`escalationStartTime` and `disableEscalationWhenModified` are different levers.** `CaseLastModified` *restarts* the clock on an edit; `disableEscalationWhenModified` *stops* escalation on an edit. Entry 3 uses both, so any touch ends escalation for that case.
- **Templates must be Classic** — the guide notes Lightning email templates are not packageable and recommends Classic for `assignedToTemplate`.
- Every queue, user, calendar, and template named here must already exist in the target org, or the deploy fails on the reference, not on the rule.

### Adding one entry to a retrieved file

Rule entries are positional — order in the file is evaluation order. To insert a new most-specific tier, put it **first** inside the existing `escalationRule`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- Excerpt: the new entry only, shown inside its real root so it parses standalone.
     In practice you paste the <ruleEntry> block as the FIRST child of the existing
     <escalationRule> in Case.escalationRules-meta.xml. -->
<EscalationRules xmlns="http://soap.sforce.com/2006/04/metadata">
    <escalationRule>
        <fullName>Support_SLA_Escalation</fullName>
        <active>true</active>
        <ruleEntry>
            <businessHoursSource>None</businessHoursSource>
            <criteriaItems>
                <field>Case.Type</field>
                <operation>equals</operation>
                <value>Security Incident</value>
            </criteriaItems>
            <escalationStartTime>CaseCreation</escalationStartTime>
            <escalationAction>
                <minutesToEscalation>10</minutesToEscalation>
                <notifyEmail>secops@acme.example</notifyEmail>
                <notifyCaseOwner>true</notifyCaseOwner>
            </escalationAction>
        </ruleEntry>
    </escalationRule>
</EscalationRules>
```

## package.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Case</members>
        <name>EscalationRules</name>
    </types>
    <version>62.0</version>
</Package>
```

`EscalationRules` accepts the `*` wildcard for every object's rules. To move a single named rule instead of the whole file, use the singular type:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Case.Support_SLA_Escalation</members>
        <name>EscalationRule</name>
    </types>
    <version>62.0</version>
</Package>
```

## Retrieve, lint, deploy

```bash
# 1. Pull the org's current rules BEFORE editing — the file is whole-file overwrite
sf project retrieve start --metadata EscalationRules:Case --target-org my-sandbox

# 2. Lint the folder
python3 skills/admin/escalation-rules/scripts/check_escalation_rules.py \
  --manifest-dir force-app/main/default

# 3. Validate without deploying (queues, calendars and templates must already exist)
sf project deploy validate --source-dir force-app/main/default/escalationRules \
  --target-org my-sandbox

# 4. Deploy
sf project deploy start --source-dir force-app/main/default/escalationRules \
  --target-org my-sandbox
```

Deploy order: business-hours calendars (`Settings:BusinessHours`), then queues and Classic email templates, then the escalation rules that name them.

## Parallel run and cutover

Activation is a behaviour change for every open case, not an addition. Run it as a cutover:

| Step | Action | What it proves |
|---|---|---|
| 1 | Deploy the replacement rule with `<active>false</active>` alongside the incumbent | The XML deploys; every queue, calendar, and template resolves in the target org |
| 2 | Diff the two rules' entry criteria against a sample of live cases (query below) | Which cases change tier, and which fall out of scope entirely |
| 3 | Take the escalated-case baseline (query below) immediately before switching | You can tell a wave from normal volume afterwards |
| 4 | Deploy **only** the `active` flip, in a staffed window | The blast radius of the change is one field |
| 5 | Re-run the baseline query hourly for the first SLA period | Confirms fired-vs-expected, and catches the reactivation wave early |
| 6 | Delete the retired rule from the file in a later deploy | The file stops carrying dead configuration |

Cases already past the new threshold at step 4 escalate on the engine's first pass after activation. That is expected; the reason for step 3 is to be able to say so.

## Verification and monitoring

Baseline and monitoring query — escalated cases still open, by owner:

```sql
SELECT OwnerId, COUNT(Id) escalatedOpen
FROM Case
WHERE IsEscalated = true AND IsClosed = false
GROUP BY OwnerId
ORDER BY COUNT(Id) DESC
```

The case-level list, for spotting a wave or a tier that never fires:

```sql
SELECT Id, CaseNumber, Priority, Status, OwnerId, BusinessHoursId,
       CreatedDate, LastModifiedDate
FROM Case
WHERE IsEscalated = true AND IsClosed = false
  AND CreatedDate = LAST_N_DAYS:7
ORDER BY CreatedDate
```

`Case.IsEscalated` is a plain boolean with `Create`, `Update`, `Filter`, `Group` and `Sort` in the Object Reference — meaning it reports and filters well, but also that anything with update access can set it. Treat a spike as a question, not a fact.

Standing report definition to hand over with the rule:

| Report property | Value |
|---|---|
| Report type | Cases |
| Filters | `Escalated = True` AND `Closed = False` AND `Date/Time Opened = LAST 30 DAYS` |
| Grouping | Case Owner, then Priority |
| Columns | Case Number, Priority, Status, Date/Time Opened, Last Modified Date, Business Hours |
| Schedule | Weekly to the support manager named in step 3 of `SKILL.md`'s workflow |

Setup check after activation: **Setup > Escalation Rules** shows exactly one rule with Active checked, and it is the new one. Open it and confirm each entry's business hours selection survived the deploy.

Clock test: do **not** re-derive it here. Use the after-hours clock test in `admin/business-hours-and-holidays` `references/examples.md` (Example 4) — create a case just before the calendar closes, then confirm the escalation lands in the next open window rather than overnight. It is the same test for escalation entries and milestone timers because both read the same calendar.
