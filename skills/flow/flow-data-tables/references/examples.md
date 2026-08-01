# Examples — Flow Data Tables

## Example 1: Select a contact when logging a case

**Context:** an agent opens a screen flow from an Account and must pick the contact the
case is for.

**Problem:** the first build used a custom screen component — a bundle of roughly two
hundred lines with its own `@api` output and change-event dispatch — for what is
display-and-select. It also fetched every contact in the org and left the empty case
unhandled, so an account with no active contacts produced a screen with headers and
nothing else.

**Solution:** bound query, explicit empty-state branch, single-select table.

```xml
<recordLookups>
    <name>Get_Account_Contacts</name>
    <label>Get Account Contacts</label>
    <object>Contact</object>
    <filterLogic>and</filterLogic>
    <filters>
        <field>AccountId</field>
        <operator>EqualTo</operator>
        <value><elementReference>recordId</elementReference></value>
    </filters>
    <filters>
        <field>IsActive__c</field>
        <operator>EqualTo</operator>
        <value><booleanValue>true</booleanValue></value>
    </filters>
    <queriedFields>Id</queriedFields>
    <queriedFields>Name</queriedFields>
    <queriedFields>Email</queriedFields>
    <queriedFields>Title</queriedFields>
    <sortField>LastName</sortField>
    <sortOrder>Asc</sortOrder>
    <getFirstRecordOnly>false</getFirstRecordOnly>
    <storeOutputAutomatically>true</storeOutputAutomatically>
    <connector><targetReference>Has_Contacts</targetReference></connector>
</recordLookups>

<decisions>
    <name>Has_Contacts</name>
    <label>Has Contacts?</label>
    <defaultConnector>
        <targetReference>Screen_No_Contacts</targetReference>
    </defaultConnector>
    <defaultConnectorLabel>None found</defaultConnectorLabel>
    <rules>
        <name>Found</name>
        <conditionLogic>and</conditionLogic>
        <conditions>
            <leftValueReference>Get_Account_Contacts</leftValueReference>
            <operator>IsNull</operator>
            <rightValue><booleanValue>false</booleanValue></rightValue>
        </conditions>
        <connector><targetReference>Screen_Pick_Contact</targetReference></connector>
    </rules>
</decisions>
```

Downstream, single selection yields one record, so the Create Records element consumes it
directly — no Loop:

```text
Screen_Pick_Contact
  └── Data Table  (API name: ContactTable)
        Source Collection : {!Get_Account_Contacts}
        Selection Mode    : Single
        Columns           : Name (Text) | Title (Text) | Email (Email)
        Required          : true

Create_Case
  ContactId  = {!ContactTable.firstSelectedRow.Id}
  AccountId  = {!recordId}
  Subject    = {!Screen_Pick_Contact.Case_Subject}
```

**Why it works:** the query is bounded by the account and by an active flag, so the
screen's cost tracks the decision the user is making rather than the size of the object.
Marking the table required removes a whole class of downstream null handling. The Decision
before the screen is what turns "no active contacts" from a screen that looks broken into
a message that explains itself — and that is the case the flow will never be demonstrated
with.

---

## Example 2: Multi-select for a bulk update

**Context:** a supervisor picks several open cases and reassigns them in one pass.

**Problem:** the flow was originally built single-select. When the requirement changed to
multiple, every downstream reference broke, because multiple selection returns a record
collection where single returns a record — the Update Records element could not consume
it, and the fault path still pointed at the old element.

**Solution:** with multiple selection, iterate the collection and build a single update.

```text
Screen_Pick_Cases
  └── Data Table  (API name: CaseTable)
        Source Collection : {!Get_Open_Cases}
        Selection Mode    : Multiple
        Columns           : CaseNumber (Text) | Subject (Text)
                            Priority (Text)   | CreatedDate (Date/Time)
        Required          : true

Loop_Selected  over  {!CaseTable.selectedRows}
  └── Assignment  Add_To_Update
        {!varCaseToUpdate.Id}       = {!Loop_Selected.Id}
        {!varCaseToUpdate.OwnerId}  = {!Screen_Pick_Cases.New_Owner}
        {!varCasesToUpdate}   Add   {!varCaseToUpdate}

Update_Records  Update_Cases
  Record Collection : {!varCasesToUpdate}
  Fault connector   -> Screen_Update_Failed
```

Two configuration details that are easy to get wrong:

- `CreatedDate` needs its column type set to Date/Time explicitly. Left to inference it
  can render in a form that is not what a supervisor scanning the list expects, and
  because nothing errors it survives review.
- The update happens **after** the loop, against the assembled collection. Putting an
  Update Records element inside the loop issues one DML statement per selected row and
  walks straight into the per-transaction limit of 150 DML statements — a fault that only
  appears once someone selects enough rows, which is to say in production.

**Why it works:** one DML statement regardless of how many rows were selected, and a fault
connector on it so a validation-rule failure produces a screen the supervisor can act on
rather than an unhandled flow error. See `templates/flow/FaultPath_Template.md` for the
canonical fault-path shape rather than inventing one per flow.
