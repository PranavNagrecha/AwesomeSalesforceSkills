# LLM Anti-Patterns — Flow Runtime Context And Sharing

Common mistakes AI coding assistants make when generating or advising on Flow run-mode and sharing.
These patterns help the consuming agent self-check its own output.

---

## Anti-Pattern 1: Defaulting to `SystemModeWithoutSharing` Without Justification

**What the LLM generates:**

```xml
<Flow xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>62.0</apiVersion>
    <runInMode>SystemModeWithoutSharing</runInMode>
    <processType>Flow</processType>
    <!-- ... -->
</Flow>
```

For a Screen Flow that lets reps update their own Opportunities — no escalation needed.

**Why it happens:** LLMs see "Salesforce + Flow + automation" and pattern-match to the platform default. Training data includes many examples of `SystemModeWithoutSharing` because it's the default in code samples; the model doesn't learn that "default" doesn't mean "recommended."

**Correct pattern:**

```xml
<Flow xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>62.0</apiVersion>
    <runInMode>DefaultMode</runInMode>
    <!-- DefaultMode in a Screen Flow = User Context = least privilege -->
    <processType>Flow</processType>
    <!-- ... -->
</Flow>
```

For Screen Flows, the right answer is User Context (DefaultMode for screen flows). For record-triggered flows that don't need to bypass sharing, the right answer is `SystemModeWithSharing`.

**Detection hint:** Grep generated XML for `<runInMode>SystemModeWithoutSharing</runInMode>` and require an inline justification in the flow `<description>` field. Reject any output where the rationale is missing.

---

## Anti-Pattern 2: Recommending Without-Sharing for Screen Flows to "Make the Records Show Up"

**What the LLM generates:** When the user reports "my Screen Flow's Get Records returns nothing" the LLM suggests:

> "Set the flow's Run Mode to System Context Without Sharing — that will let it bypass sharing and the records will appear."

**Why it happens:** The LLM is trained on troubleshooting threads where "without sharing" is the most common quick-fix answer. It optimizes for "make the symptom go away" without considering the security blast radius.

**Correct pattern:**

```
1. Diagnose WHY the records are missing — sharing rule? FLS? CRUD? Wrong filter?
2. If sharing: confirm the user SHOULD have access. If yes, fix the sharing rule.
   If no, the flow is doing the right thing by failing closed.
3. Only if the user genuinely shouldn't see the record but the flow needs to read it
   on their behalf, add a per-element runInMode override on JUST that Get Records
   (preferably SystemModeWithSharing, not Without).
4. If multiple writes need to escalate, refactor into a System Context Subflow.
```

**Detection hint:** Reject any LLM output that suggests changing flow-wide run mode as the first response to "Get Records returned nothing" without first asking "should the user have access at the sharing-rule level?"

---

## Anti-Pattern 3: Ignoring FLS Implications When Generating Get Records Elements

**What the LLM generates:**

```xml
<recordLookups>
    <name>Get_Account_For_Display</name>
    <object>Account</object>
    <queriedFields>Name</queriedFields>
    <queriedFields>AnnualRevenue</queriedFields>
    <queriedFields>Compensation_Bracket__c</queriedFields>
    <queriedFields>Strategic_Notes__c</queriedFields>
    <!-- ... 30 more fields ... -->
</recordLookups>
```

In a User Context Screen Flow — the LLM queries every field on the object, assuming "more data = better."

**Why it happens:** LLMs default to permissive queries. They don't reason about which fields the running user is entitled to see. In User Context, FLS is enforced — fields the user lacks access to come back null, but the field is still listed in the query.

**Correct pattern:**

```xml
<recordLookups>
    <name>Get_Account_For_Display</name>
    <object>Account</object>
    <!-- Only the fields displayed to the user. Audit FLS for the running user's profile. -->
    <queriedFields>Name</queriedFields>
    <queriedFields>Industry</queriedFields>
</recordLookups>
```

Query only the fields actually displayed or used. For sensitive fields (`Compensation_*`, `SSN__c`, etc.), confirm FLS for the running user's profile before adding them.

**Detection hint:** Flag any Get Records element with > 10 queried fields on a sensitive object. Require the LLM to justify each field against the screen's display set.

---

## Anti-Pattern 4: Treating Before-Save and After-Save the Same for Run Mode

**What the LLM generates:** When asked to add a security comment to a flow, the LLM writes:

> "Configured for User Context to enforce sharing rules on record reads."

Without checking whether the flow is before-save or after-save. Before-save flows ignore the run-mode setting entirely.

**Why it happens:** LLMs treat "Flow" as a single concept and don't distinguish trigger sub-types. The before-save vs after-save distinction is platform-specific and often missed in summary documentation.

**Correct pattern:**

```
For before-save flows:
   "This is a before-save record-triggered flow. Run mode setting is platform-ignored;
    the flow always executes in System Context as part of the triggering DML."

For after-save flows:
   "Configured for SystemModeWithSharing so sharing rules apply to related-record
    reads even when triggered by a sysadmin DML."
```

**Detection hint:** Cross-reference `<triggerType>` and the run-mode comment. If `triggerType` is `RecordBeforeSave` and the comment claims a non-System run mode is in effect, the comment is wrong.

---

## Anti-Pattern 5: Suggesting `$Permission` Checks as a Substitute for Run-Mode Decisions

**What the LLM generates:** When asked to "make sure only authorized users can run the privileged branch":

```
Decision: User Is Authorized
   condition: {!$Permission.Manage_Sensitive_Data} = true
   true path: [privileged update]
   false path: [end]
```

In a flow whose run mode is System Context Without Sharing — and worse, the flow is scheduled (running as Automated Process).

**Why it happens:** LLMs treat `$Permission` as a security primitive because the name contains "Permission." It is actually a feature-flag merge field that resolves against the running user's permission sets. It is not a security boundary; the actual boundary is `<runInMode>`.

**Correct pattern:**

```
Approach 1 — Use run mode as the actual control:
   - Set the flow to User Context.
   - Only users with the platform-level permission to perform the operation can trigger it.
   - The Decision element is unnecessary.

Approach 2 — If feature-flagging is desired separately from security:
   - Keep $Permission as a feature flag (gates "show the new UI" not "allow privileged write").
   - Combine with a User Context run mode for actual security.
   - Never use $Permission in a flow whose running user is Automated Process — it always
     resolves to false there.
```

**Detection hint:** Flag any flow that uses `$Permission` in a Decision and is also configured as System Context Without Sharing. The combination is almost always confused-deputy security thinking.

---

## Anti-Pattern 6: Hand-Waving the Spring '21 Default Change

**What the LLM generates:**

> "Record-triggered flows run in User Context by default."

This was true before Spring '21 (API 51.0). It is false for any flow at API 52.0 or higher.

**Why it happens:** LLM training cutoffs include pre-Spring-'21 documentation. The change isn't always reflected in derivative content (Stack Overflow answers, blog posts) the model trained on.

**Correct pattern:**

```
Record-triggered flows default to:
   - User Context if apiVersion <= 51.0 (Winter '21 and earlier)
   - System Context Without Sharing if apiVersion >= 52.0 (Spring '21 and later)

Always set <runInMode> explicitly to avoid ambiguity. Never rely on the default.
```

**Detection hint:** Reject any LLM statement about Flow defaults that doesn't condition on apiVersion. Statements of the form "Flows run as X by default" without the version qualifier are stale.

---

## Anti-Pattern 7: Assuming Subflow Inherits Parent's Run Mode

**What the LLM generates:** When asked about a parent-subflow chain:

> "The subflow inherits the System Context Without Sharing setting from the parent flow."

Wrong. Each flow's `runInMode` is independent.

**Why it happens:** Inheritance is a familiar pattern from OOP and from Apex (where `inherited sharing` exists as an explicit keyword). LLMs project the pattern onto Flow without checking whether Flow has the same semantics. It does not.

**Correct pattern:**

```
Each flow's <runInMode> is independent. There is no inheritance.
A subflow with <runInMode>DefaultMode</runInMode> uses the default for its own flow type
(auto-launched = SystemModeWithoutSharing post-Spring-'21; screen = User Context).
A subflow with <runInMode>SystemModeWithSharing</runInMode> runs with sharing
regardless of the caller. Always set <runInMode> explicitly on every subflow.
```

**Detection hint:** Search LLM output for the word "inherit" near "subflow" — flag for review.

---

## Anti-Pattern 8: Recommending `SystemModeWithoutSharing` for Screen Flows on Experience Cloud

**What the LLM generates:** When asked to make an Experience Cloud (community / portal) form work for guest users:

> "Set the flow to System Context Without Sharing so it can read and write the records the form needs."

In an Experience Cloud guest-user flow — this is a data-leak primitive.

**Why it happens:** The LLM optimizes for "make the form work" and applies the same fix it suggests for internal Screen Flows. Guest-user context is special: minimal permissions are part of the threat model.

**Correct pattern:**

```
Experience Cloud guest flows MUST run in User Context.
Use the guest user profile + sharing sets to grant the minimum record access required.
If the form needs to write a record the guest can't see (e.g., a new Lead), use the
guest user profile's Create permission on Lead — do not bypass via run mode.
For lookups the guest legitimately can't see, use a per-element override on a single
Get Records, never the entire flow.
```

**Detection hint:** Cross-reference any flow recommended for Experience Cloud with its `<runInMode>` setting. P0 alert on any combination of Experience Cloud profile + `SystemModeWithoutSharing`.

---

## Anti-Pattern 9: Using `$User.Email` in a Scheduled Flow's Email Action

**What the LLM generates:**

```
Send Email Alert:
  recipient: {!$User.Email}
  subject: "Daily Sales Report"
```

In a scheduled flow.

**Why it happens:** LLMs default to `$User.Email` as the most common recipient pattern. They don't recognize that scheduled flows run as Automated Process, which has no email address — the merge field returns blank, the email fails or sends to no one.

**Correct pattern:**

```
For scheduled flows, hardcode recipients via Custom Metadata Type or Custom Setting:

Get Records: Email_Recipients_Setting__mdt
  filter: Purpose__c = 'Daily_Sales_Report'

Loop: each recipient
  Send Email Alert
    recipient: {!loopRecipient.Email__c}
    subject: "Daily Sales Report"
```

**Detection hint:** Flag any scheduled, PE-triggered, or CDC-triggered flow that uses `$User`, `$Profile`, or `$UserRole` merge fields.

---

## Anti-Pattern 10: Skipping the Audit-Log Step on Without-Sharing Writes

**What the LLM generates:** A System Context Without Sharing flow with a Create or Update Records element — and no corresponding audit-log write.

**Why it happens:** LLMs optimize for the minimum viable flow. Audit logs feel like "extra work" that's not strictly required for the functional spec.

**Correct pattern:**

```
Every System Context Without Sharing DML element must be followed by:

Create Records: Privileged_Action_Log__c
  Source_Flow__c = "Account_Last_Touch_Bump"
  Affected_Record_Id__c = {!recordId}
  Triggering_User_Id__c = {!triggeringUserId}  // passed in from User Context parent
  Operation__c = "UPDATE"
  Field_Changes__c = {!changeSummary}
  Timestamp__c = {!$Flow.CurrentDateTime}
```

**Detection hint:** Any flow with `<runInMode>SystemModeWithoutSharing</runInMode>` and no Create Records element targeting a `*_Log__c` or audit-table object should be flagged for review.

---

## Anti-Pattern 11: Confusing `with sharing` Apex with Flow Run Mode

**What the LLM generates:** When asked "does this flow respect sharing?":

> "Yes — the underlying Apex actions are declared `with sharing`, so the flow respects sharing rules end-to-end."

Wrong on two levels: (1) `with sharing` on Apex actions doesn't propagate to the flow's own DML elements; (2) the flow's own run mode is the binding control for the flow's own elements.

**Why it happens:** LLMs blur the boundary between Flow and Apex. Apex sharing keywords are well-documented; Flow run mode is comparatively obscure. The LLM falls back on what it knows.

**Correct pattern:**

```
Two separate enforcement boundaries:
  1. Flow's own Get/Create/Update/Delete elements — controlled by <runInMode>.
  2. Apex actions called from the flow — controlled by the Apex class's
     own `with sharing` / `without sharing` declaration.

Both must be reviewed independently. A `with sharing` Apex action called from a
SystemModeWithoutSharing flow does NOT make the flow's other elements sharing-aware.
```

**Detection hint:** Reject any LLM statement that conflates flow-level run mode with Apex sharing keywords for the called class.
