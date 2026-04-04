# LLM Anti-Patterns — Person Accounts

Common mistakes AI coding assistants make when generating or advising on Person Accounts.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Accessing Person Account Email via Contact Query Instead of Account

**What the LLM generates:**
```soql
SELECT Id, Email FROM Contact WHERE AccountId = :personAccountId
```
Or in Apex: "To get the email for a Person Account, query the Contact object where AccountId equals the Person Account Id."

**Why it happens:** LLMs conflate "Person Account has a PersonContact" with "therefore query Contact to get person data." The training data contains many patterns of Account+Contact pairs where Contact holds Email, and the LLM generalizes incorrectly to Person Accounts.

**Correct pattern:**
```soql
SELECT Id, Name, PersonEmail, PersonPhone
FROM Account
WHERE IsPersonAccount = true
AND Id = :personAccountId
```
Person-specific fields are accessed directly on the Account object via `Person`-prefixed fields. The Contact object should not be used as the data-access path for Person Account attributes.

**Detection hint:** Look for `FROM Contact WHERE AccountId = :somePersonAccountId` or "query the Contact for a Person Account" in generated code or advice.

---

## Anti-Pattern 2: Creating a Person Account by Inserting a Contact

**What the LLM generates:**
```apex
Contact c = new Contact(
    FirstName = 'Jane',
    LastName = 'Smith',
    Email = 'jane@example.com',
    RecordTypeId = personAccountRtId  // WRONG — no such Contact record type
);
insert c;
```
Or: "To create a Person Account, insert a Contact with the Person Account record type."

**Why it happens:** The LLM confuses the fact that a Person Account "acts like a contact" with the mechanism for creating one. Person Account record types exist on Account, not Contact. Inserting a Contact with a Person Account record type Id will either fail or create a regular Contact (if the Id happens to match a Contact RT).

**Correct pattern:**
```apex
Id personAccountRtId = Schema.SObjectType.Account
    .getRecordTypeInfosByDeveloperName()
    .get('PersonAccount')  // developer name varies by org
    .getRecordTypeId();

Account person = new Account(
    FirstName = 'Jane',
    LastName = 'Smith',
    PersonEmail = 'jane@example.com',
    RecordTypeId = personAccountRtId
);
insert person;
```
Person Accounts are created via the **Account** sObject, not Contact. The `RecordTypeId` must reference an Account record type designated as a Person Account type.

**Detection hint:** `new Contact(... RecordTypeId = personAccountRtId)` or advice to "insert a Contact to create a Person Account."

---

## Anti-Pattern 3: Assuming `IsPersonAccount` Is Safe to Check in `before insert` Triggers

**What the LLM generates:**
```apex
trigger AccountTrigger on Account (before insert, before update) {
    for (Account a : Trigger.new) {
        if (a.IsPersonAccount) {  // WRONG in before insert context
            a.PersonEmail = a.PersonEmail?.toLowerCase();
        }
    }
}
```

**Why it happens:** The LLM sees `IsPersonAccount` used everywhere in Person Account code examples and assumes it is always populated. It does not distinguish trigger contexts where formula fields are not yet resolved.

**Correct pattern:**
```apex
trigger AccountTrigger on Account (before insert, before update) {
    Set<Id> personRtIds = PersonAccountUtils.getPersonAccountRecordTypeIds();
    for (Account a : Trigger.new) {
        // In before insert, IsPersonAccount is null — check RecordTypeId instead
        Boolean isPerson = (Trigger.isInsert)
            ? personRtIds.contains(a.RecordTypeId)
            : a.IsPersonAccount;
        if (isPerson) {
            a.PersonEmail = a.PersonEmail?.toLowerCase();
        }
    }
}
```

**Detection hint:** `IsPersonAccount` used in a `before insert` trigger body without a RecordTypeId fallback.

---

## Anti-Pattern 4: Missing `IsPersonAccount` Filter on Contact Queries in Person Account Orgs

**What the LLM generates:**
```apex
List<Contact> contacts = [
    SELECT Id, FirstName, LastName, Email
    FROM Contact
    WHERE AccountId IN :accountIds
];
// processes all contacts, including PersonContacts
```
Or a batch class that iterates over all Contacts without filtering out PersonContact records.

**Why it happens:** The LLM generates standard Contact queries that are correct in a non-Person-Account org. It does not automatically add Person Account awareness because it does not know whether the target org has Person Accounts enabled.

**Correct pattern:**
```apex
List<Contact> contacts = [
    SELECT Id, FirstName, LastName, Email
    FROM Contact
    WHERE AccountId IN :accountIds
    AND Account.IsPersonAccount = false  // exclude PersonContact records
];
```
Or, if processing both types is required, explicitly branch after querying:
```apex
for (Contact c : contacts) {
    if (c.Account.IsPersonAccount) {
        // handle PersonContact — usually skip or redirect to Account logic
        continue;
    }
    // standard Contact processing
}
```

**Detection hint:** `FROM Contact` with no `IsPersonAccount` filter in code that claims to be Person Account-compatible.

---

## Anti-Pattern 5: Advising That Person Account Enablement Can Be Reversed or Tested Without Consequence

**What the LLM generates:**
"You can enable Person Accounts in your production org to test it, and if it doesn't work for your use case, you can ask Salesforce Support to disable it."

Or: "Enabling Person Accounts is low risk — it just adds a new record type option."

**Why it happens:** LLMs tend to soften irreversibility warnings or are not trained on the specific Salesforce policy that Person Account enablement is permanent. The LLM may also conflate "adding a feature" with "a reversible configuration change."

**Correct pattern:**
Person Account enablement is **permanent and irreversible**. Salesforce Support will not disable Person Accounts once enabled in a production org. The correct guidance is:
1. Enable only in developer sandbox first.
2. Run full test suite and integration tests in sandbox.
3. Make the production enablement decision deliberately, with full stakeholder sign-off.
4. Never enable in production as a trial or experiment.

**Detection hint:** Any statement that suggests Person Account enablement can be "reversed," "rolled back," "undone," or "disabled later."

---

## Anti-Pattern 6: Telling Users to Link a Contact to a Person Account

**What the LLM generates:**
"To associate an individual with a Person Account, create a Contact record and set its AccountId to the Person Account Id — this links the contact as the primary contact for the person."

**Why it happens:** In a standard B2B org, creating a Contact with `AccountId = [Account Id]` is the normal data entry pattern. The LLM generalizes this pattern to Person Accounts without knowing that Person Accounts prohibit child Contacts.

**Correct pattern:**
Person Accounts cannot have child Contact records. Attempting to insert a Contact with `AccountId` pointing to a Person Account causes:
```
FIELD_INTEGRITY_EXCEPTION: You can't link a contact to a Person Account.
```
For individual consumers, the Person Account itself holds all contact information via `PersonEmail`, `PersonPhone`, etc. No separate Contact record should be created. If a new "contact" for a person is needed (e.g., an alternate contact method), consider custom fields on the Person Account or a custom related object — not a child Contact.

**Detection hint:** "create a Contact with AccountId = [Person Account Id]" or "link a contact to a Person Account."
