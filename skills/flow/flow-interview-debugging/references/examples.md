# Examples — Flow Interview Debugging

Worked examples for turning a silent Flow failure into a triageable incident.
Every example shows the Flow metadata **fragment** — the elements under discussion,
named and shaped as the `Flow` metadata type defines them — plus the Setup path
where the configuration lives and what the practitioner actually sees when it
works.

These fragments are excerpts, not deployable documents. A real `Flow` file also
needs `<interviewLabel>`, a `<start>` element (with `<object>` and
`<triggerType>` for anything that references `$Record`), and the variables the
fragment refers to. Paste an excerpt into an existing flow's metadata; do not
expect one to deploy on its own.

---

## Example 1: Route Error Emails Off the Last Modifier

**Context:** An org with 40 active record-triggered flows. The admin who last
touched each flow receives its error email. Two of those admins have left the
company; their emails bounce into nothing. Three production incidents went
unnoticed for a week.

**Problem:** The default recipient for a flow error email is *the user who last
modified the flow* — not the flow's owner, not a queue, not a shared alias.
Rotate staff and error visibility silently rots. Worse, the recipient changes
every time somebody edits the flow, so the on-call rota and the alerting rota
drift apart with no signal.

**Solution:**

Setup → Quick Find `Automation` → **Process Automation Settings** →
**Send Process or Flow Error Email to** → select **Apex Exception Email
Recipients**.

Then populate the recipient list:

Setup → Quick Find `Apex Exception Email` → **Apex Exception Email** → add the
shared alias (for example `salesforce-oncall@example.com`).

```text
Process Automation Settings
  Send Process or Flow Error Email to:
    ( ) User Who Last Modified the Process or Flow      <- default
    (•) Apex Exception Email Recipients                  <- pick this
```

**Why it works:** The recipient list becomes a single, deliberately managed
place instead of a side effect of who last clicked Save. A distribution list or
a shared inbox that feeds a ticket queue survives staff turnover; a named admin
does not.

**Caveat worth knowing before you enable it:** Flow error emails include the
data involved in the interview, including user-entered data. Sending them to a
broad alias widens who can see that payload. If the flow touches regulated data,
route the alias to a restricted group, not to an all-admins list.

---

## Example 2: A Fault Path That Produces a Usable Log Row

**Context:** A record-triggered flow on Case creates a child `Escalation__c`
record. It fails intermittently in production. The error email says an error
occurred at element `Create_Escalation` and nothing else that reproduces.

**Problem:** A fault connector that goes straight to a Screen (or nowhere at
all) throws away the two pieces of context that make triage possible: the
platform's own error text, and the interview identity that ties the failure back
to the log line.

**Solution:**

Wire the DML element's `faultConnector` into a Create Records that writes a
purpose-built log object. The load-bearing fields are `$Flow.FaultMessage` and
`$Flow.InterviewGuid`.

Fragment — the two `<recordCreates>` elements only. It assumes a surrounding flow
whose `<start>` declares `<object>Case</object>` with a record `<triggerType>`,
which is what puts `$Record` in scope, and a `varEscalation` record variable.

```xml
    <recordCreates>
        <name>Create_Escalation</name>
        <label>Create Escalation</label>
        <locationX>264</locationX>
        <locationY>350</locationY>
        <faultConnector>
            <targetReference>Log_Flow_Fault</targetReference>
        </faultConnector>
        <inputReference>varEscalation</inputReference>
    </recordCreates>

    <recordCreates>
        <name>Log_Flow_Fault</name>
        <label>Log Flow Fault</label>
        <locationX>528</locationX>
        <locationY>350</locationY>
        <inputAssignments>
            <field>Flow_API_Name__c</field>
            <value>
                <stringValue>Case_Escalation_Router</stringValue>
            </value>
        </inputAssignments>
        <inputAssignments>
            <field>Failed_Element__c</field>
            <value>
                <stringValue>Create_Escalation</stringValue>
            </value>
        </inputAssignments>
        <inputAssignments>
            <field>Fault_Message__c</field>
            <value>
                <elementReference>$Flow.FaultMessage</elementReference>
            </value>
        </inputAssignments>
        <inputAssignments>
            <field>Interview_Guid__c</field>
            <value>
                <elementReference>$Flow.InterviewGuid</elementReference>
            </value>
        </inputAssignments>
        <inputAssignments>
            <field>Record_Id__c</field>
            <value>
                <elementReference>$Record.Id</elementReference>
            </value>
        </inputAssignments>
        <inputAssignments>
            <field>Running_User__c</field>
            <value>
                <elementReference>$User.Id</elementReference>
            </value>
        </inputAssignments>
        <object>Flow_Error_Log__c</object>
        <storeOutputAutomatically>true</storeOutputAutomatically>
    </recordCreates>
```

**Why it works:** `$Flow.InterviewGuid` is the same identifier Salesforce prints
in the flow error email, so the log row and the email are joinable without
guesswork — you paste the GUID from the email into a report filter and land on
the exact interview. `Failed_Element__c` is hard-coded per fault handler rather
than derived, because Flow has no "which element faulted" global variable; the
element name has to be typed by the author at the point where the fault path is
wired.

**Field types for `Flow_Error_Log__c`:** make `Fault_Message__c` a Long Text
Area (255 characters is not enough for a real `FIELD_CUSTOM_VALIDATION_EXCEPTION`
message) and index `Interview_Guid__c` as an External ID so the join from the
email is a fast lookup rather than a table scan.

---

## Example 3: Wrong vs Right — Fault Path on a Get Records That Returns Nothing

**Wrong:**

```xml
<recordLookups>
    <name>Get_Contract</name>
    <label>Get Contract</label>
    <locationX>176</locationX>
    <locationY>278</locationY>
    <faultConnector>
        <targetReference>Show_No_Contract_Error</targetReference>
    </faultConnector>
    <assignNullValuesIfNoRecordsFound>false</assignNullValuesIfNoRecordsFound>
    <filterLogic>and</filterLogic>
    <filters>
        <field>AccountId</field>
        <operator>EqualTo</operator>
        <value>
            <elementReference>$Record.AccountId</elementReference>
        </value>
    </filters>
    <getFirstRecordOnly>true</getFirstRecordOnly>
    <object>Contract</object>
    <storeOutputAutomatically>true</storeOutputAutomatically>
</recordLookups>
```

The author expects "no contract found" to take the fault path. It never does.
A Get Records that matches zero rows is a **successful** query — it takes the
normal connector with a null result. The fault connector fires only on a real
platform exception (an invalid filter reference, a field the running user cannot
read, a governor breach). The "no contract" branch is dead code, and the flow
silently continues with a null variable until something downstream dereferences
it and throws a much less informative error somewhere else.

**Right:**

```xml
<recordLookups>
    <name>Get_Contract</name>
    <label>Get Contract</label>
    <locationX>176</locationX>
    <locationY>278</locationY>
    <connector>
        <targetReference>Check_Contract_Found</targetReference>
    </connector>
    <faultConnector>
        <targetReference>Log_Flow_Fault</targetReference>
    </faultConnector>
    <assignNullValuesIfNoRecordsFound>true</assignNullValuesIfNoRecordsFound>
    <filterLogic>and</filterLogic>
    <filters>
        <field>AccountId</field>
        <operator>EqualTo</operator>
        <value>
            <elementReference>$Record.AccountId</elementReference>
        </value>
    </filters>
    <getFirstRecordOnly>true</getFirstRecordOnly>
    <object>Contract</object>
    <storeOutputAutomatically>true</storeOutputAutomatically>
</recordLookups>

<decisions>
    <name>Check_Contract_Found</name>
    <label>Check Contract Found</label>
    <locationX>352</locationX>
    <locationY>278</locationY>
    <defaultConnector>
        <targetReference>Handle_No_Contract</targetReference>
    </defaultConnector>
    <defaultConnectorLabel>No Contract Found</defaultConnectorLabel>
    <rules>
        <name>Contract_Found</name>
        <conditionLogic>and</conditionLogic>
        <conditions>
            <leftValueReference>Get_Contract</leftValueReference>
            <operator>IsNull</operator>
            <rightValue>
                <booleanValue>false</booleanValue>
            </rightValue>
        </conditions>
        <connector>
            <targetReference>Continue_Happy_Path</targetReference>
        </connector>
        <label>Contract Found</label>
    </rules>
</decisions>
```

Two changes carry the weight. `assignNullValuesIfNoRecordsFound` set to `true`
guarantees the variable is null (rather than retaining a stale value from an
earlier loop iteration) when nothing matched, which is what makes the `IsNull`
check trustworthy. The Decision — not the fault path — owns the business case.
The fault path is reserved for genuine platform exceptions and routes to the
logger from Example 2.

---

## Example 4: Debugging the Path You Cannot See — Async and Scheduled Paths

**Context:** A record-triggered flow on Opportunity has an immediate path and a
scheduled path set to run one hour after Close Date. The immediate path debugs
cleanly in Flow Builder. The scheduled path fails in production.

**Problem:** The Flow Builder debugger runs the interview you asked for, in your
session, right now. It does not schedule anything, and it does not run as the
user the scheduled path will actually run as. A scheduled path executes later,
in its own transaction, under the Automated Process user unless the flow is
configured otherwise. Every difference between those two contexts — sharing,
field-level security, `$Permission`, `$User.Id`, record state an hour later — is
invisible in the debugger.

**Solution:**

Debug what you can, then observe what you cannot.

1. In Flow Builder, open the flow → **Debug** → in the debug options panel,
   choose the trigger type and, for record-triggered flows, supply a record.
   Leave **roll back changes** on while you iterate so repeated debug runs do
   not litter the org.
2. Turn roll back **off** for the final pass. Rolled-back debug runs do not
   commit, so any downstream automation that would have fired on the committed
   record never fires — and the scheduled path is scheduled off the *committed*
   record change.
3. Observe the scheduled path where it actually lives:
   Setup → Quick Find `Time-Based Workflow` → **Time-Based Workflow** → set the
   filter to the flow's name and Search. Pending scheduled-path entries appear
   here; you can delete a stuck entry from this screen.
4. Watch the interview itself: Setup → Quick Find `Paused` → **Paused And
   Failed Flow Interviews**.
5. Capture failures with the fault-path logger from Example 2. In a scheduled
   path there is no user on screen to see an error — the log row is the only
   durable evidence.

**Why it works:** It stops treating the debugger as a test harness. The debugger
is an authoring aid for the synchronous path; the Time-Based Workflow queue plus
a fault-path log row is the observability stack for everything asynchronous.

**Sandbox rehearsal that actually reproduces:** set the scheduled path offset to
its production value and move the *record data* rather than shortening the
offset. Shortening the offset to "1 minute" for testing changes which batch the
entry lands in and hides ordering bugs that only appear at the real interval.

---

## Example 5: Reading a Flow Error Email Without Guessing

A production flow error email has a predictable shape. Knowing which line
answers which question saves the first ten minutes of every triage.

```text
Subject: Error Occurred During Flow "Case_Escalation_Router": ...

Error element Create_Escalation (FlowRecordCreate).
INSERT --- INSERT FAILED --- ERRORS : (FIELD_CUSTOM_VALIDATION_EXCEPTION)
Escalation reason is required when Priority is High : [Reason__c]

Flow Details
  Flow API Name: Case_Escalation_Router
  Type: Record-Triggered Flow
  Version: 7
  Status: Active
  Flow Interview GUID: 2f1c9a44-...-b7e1
  Org: 00Dxx0000001abc (Acme Production)

Flow Interview Details
  Interview Label: ...
  Current User: Integration User (005xx000001Sv4A)
  Start time: ...
  Duration: 1 seconds

Flow Element Details ...
```

Read it in this order:

| Question | Line that answers it |
|---|---|
| Which element blew up? | `Error element <Name> (<FlowElementType>)` |
| Was it the platform or my data? | The status code — `FIELD_CUSTOM_VALIDATION_EXCEPTION` is data; `UNABLE_TO_LOCK_ROW` is contention; `CANNOT_INSERT_UPDATE_ACTIVATE_ENTITY` is a downstream trigger |
| Which version do I open? | `Version:` — **not** the currently active version, which may already have moved on |
| Which interview do I correlate? | `Flow Interview GUID` — matches `$Flow.InterviewGuid` in the log row |
| Whose permissions applied? | `Current User` — an Automated Process or Integration User here changes the whole diagnosis |

The `Version:` line is the one most often skipped and the one that most often
explains a confusing report. If somebody activated version 8 an hour ago, the
email describing a failure in version 7 is describing code you can no longer see
in Flow Builder's default view. Open the version explicitly from the flow's
detail page before you start reasoning about the element that failed.

---

## Anti-Pattern: A Fault Path That Only Shows a Screen

**What practitioners do:** Wire every fault connector to a Screen element that
displays `{!$Flow.FaultMessage}` and calls it error handling.

**What goes wrong:** It works for screen flows with a human present and is
useless everywhere else. Record-triggered, scheduled, autolaunched, and
platform-event-triggered flows have no screen to render — a Screen element is
not even a valid target in those flow types. And even in a screen flow, the
message is displayed once and then gone: no record, no counter, no way to answer
"how often does this happen?" on Monday morning.

**Correct approach:** The fault path writes a log row first and then, only in
screen flows, displays a message. Two elements, in that order. The log row is
the artifact that survives; the screen is a courtesy to the person standing
there. If you want the user to see something *and* block the save in a
record-triggered flow, that is what the Custom Error element is for — it renders
a message of your choosing and rolls the transaction back.

---

## Anti-Pattern: Debugging With Rollback On and Declaring Victory

**What practitioners do:** Run the flow in Flow Builder with the roll-back
option enabled, watch every element go green, and ship it.

**What goes wrong:** A rolled-back debug run never commits. Every failure mode
that lives at or after commit is invisible: validation rules that only fire on
the committed state, downstream record-triggered flows, Apex triggers on the
records this flow creates, roll-up summary recalculation, scheduled paths that
are enqueued from the commit. The flow passes debug and fails on the first real
save.

**Correct approach:** Iterate with rollback on, then do a final pass with
rollback off in a sandbox with realistic data and realistic downstream
automation active. Treat "green in the debugger" as evidence the element wiring
is right, not as evidence the flow works.

---

## Anti-Pattern: Debugging as Yourself and Shipping to Everyone Else

**What practitioners do:** A System Administrator debugs the flow, sees it work,
and closes the ticket. The flow fails for the support team.

**What goes wrong:** The admin has View All / Modify All and every field visible.
The support agent does not. A Get Records that returns a row for the admin
returns nothing for the agent; an Update Records that succeeds for the admin
throws for the agent on a field their profile cannot write. The error text on the
agent's side ("field is not writeable") names the field but not the reason,
which sends the team looking for a validation rule that does not exist.

**Correct approach:** For screen flows, use the debug option that runs the
interview as another user and pick a real low-privilege persona. For flow types
where that option is unavailable, log in as a test user in a sandbox and run the
flow through its real entry point. Where the flow legitimately needs to exceed
the user's access, set `runInMode` deliberately on the element or the flow rather
than discovering the gap in production — that decision belongs to
`flow/flow-runtime-context-and-sharing`, and the fault-path logger here is what
tells you the decision was wrong.
