# Examples — Person Accounts

## Example 1: B2C Retail Org — Creating and Querying Person Accounts via API

**Context:** A retail company migrated from a Contact-only B2C model to Person Accounts. Their integration layer sends customer records from an e-commerce platform to Salesforce. Each customer is an individual person, and the integration previously created a Contact with a dummy Account. After Person Account enablement, the integration needs to create Person Accounts directly.

**Problem:** The integration was creating a generic "Business Account" named after each customer and then creating a Contact linked to it. After Person Account enablement, this created duplicate data — a Business Account + Contact pair per customer, and no Person Account records. Reports showed double the expected customer count.

**Solution:**

```apex
// Step 1: Find the Person Account Record Type Id
// (do this once and cache it, not per record)
Id personAccountRtId = Schema.SObjectType.Account
    .getRecordTypeInfosByDeveloperName()
    .get('PersonAccount')
    .getRecordTypeId();

// Step 2: Create a Person Account via the Account object
Account customer = new Account(
    FirstName = 'Jane',
    LastName = 'Smith',
    PersonEmail = 'jane.smith@example.com',
    PersonPhone = '415-555-0101',
    PersonBirthdate = Date.newInstance(1985, 3, 15),
    RecordTypeId = personAccountRtId
);
insert customer;

// Step 3: Query Person Accounts — always via Account object, not Contact
List<Account> consumers = [
    SELECT Id, Name, PersonEmail, PersonPhone, PersonBirthdate, PersonContactId
    FROM Account
    WHERE IsPersonAccount = true
    AND PersonEmail = 'jane.smith@example.com'
    LIMIT 1
];
```

**Why it works:** Setting `RecordTypeId` to a Person Account record type causes Salesforce to create the Account as a Person Account. The `IsPersonAccount` flag is automatically set to `true` by the platform, and the PersonContact is automatically created and linked via `PersonContactId`. All person-specific fields (`PersonEmail`, `PersonPhone`, etc.) are accessible directly on the Account record.

---

## Example 2: Financial Services Cloud — Associating Financial Records to Individual Clients

**Context:** An FSC org uses Person Accounts to represent individual financial advisory clients. Each client (Person Account) needs associated Financial Account records. A developer is building a Lightning component that displays a client's portfolio summary.

**Problem:** A developer new to FSC queried `Contact` to find the client record and got `PersonContact` records back — then tried to use the Contact Id to query `FinancialAccount__c`. The relationship on `FinancialAccount__c` is to Account (not Contact), so the query returned no results and the component showed an empty portfolio.

**Solution:**

```apex
// Correct: query via Account, use AccountId for Financial Account relationship
public class ClientPortfolioController {

    @AuraEnabled(cacheable=true)
    public static ClientSummary getClientSummary(Id accountId) {

        // Verify this is a Person Account before proceeding
        Account client = [
            SELECT Id, Name, PersonEmail, PersonPhone, IsPersonAccount,
                   PersonBirthdate, PersonContact.OwnerId
            FROM Account
            WHERE Id = :accountId
            AND IsPersonAccount = true
            LIMIT 1
        ];

        if (client == null) {
            throw new AuraHandledException('Record is not a Person Account.');
        }

        // Query Financial Accounts linked to the Person Account via AccountId
        List<FinServ__FinancialAccount__c> accounts = [
            SELECT Id, Name, FinServ__Balance__c, FinServ__FinancialAccountType__c
            FROM FinServ__FinancialAccount__c
            WHERE FinServ__PrimaryOwner__c = :accountId
        ];

        return new ClientSummary(client, accounts);
    }
}
```

**Why it works:** In FSC, `FinancialAccount__c` relates to `Account` via `FinServ__PrimaryOwner__c` — not to Contact. The canonical Person Account identifier is the Account Id. Using the Account Id (not PersonContactId or a Contact Id) correctly retrieves all associated financial records.

---

## Anti-Pattern: Creating a Contact Linked to a Person Account

**What practitioners do:** After enabling Person Accounts, a developer writes a script to create an individual customer by first inserting a Business Account named "John Doe" and then inserting a Contact with `LastName = 'Doe'` and `AccountId = [the Business Account Id]`. When they realize a Person Account should have been used, they try to re-link the Contact to the Person Account instead by updating `AccountId` to the Person Account Id.

**What goes wrong:** Salesforce throws an error when you attempt to save a Contact record with its `AccountId` pointing to a Person Account:
```
FIELD_INTEGRITY_EXCEPTION: You can't link a contact to a Person Account.
```
Person Accounts are individuals — they do not have child Contacts. The attempt fails and leaves an orphan Contact and an incorrectly structured Person Account.

**Correct approach:** Do not create a separate Contact record for a person who should be a Person Account. Instead, create the Account directly with a Person Account record type. If you already have a Business Account + Contact pair representing an individual, you need to migrate — delete or archive the Contact, update the Account's Record Type to a Person Account type (if permitted), and map the Contact fields to the Person-prefixed fields on the Account. This is non-trivial at scale and should be planned as a data migration, not an in-place fix.

---

## Anti-Pattern: Reading Person Email from Contact Instead of Account

**What practitioners do:** An integration queries `SELECT Id, Email FROM Contact WHERE AccountId = :personAccountId` to retrieve the email address for a Person Account customer.

**What goes wrong:** The query may return the PersonContact record with its Email field populated — but this is fragile. In mixed orgs, the AccountId-on-Contact query may unexpectedly return no results if the Contact table behavior differs between API versions, or the result includes PersonContact records that should not be directly consumed. Additionally, some integration platforms cache Contact schema that does not include person account fields.

**Correct approach:** Always access person-specific fields via the Account object using `PersonEmail`, `PersonPhone`, etc.:
```soql
SELECT Id, Name, PersonEmail, PersonPhone FROM Account WHERE IsPersonAccount = true AND Id = :personAccountId
```
This is the platform-endorsed pattern and is consistent across API versions and integration tools.
