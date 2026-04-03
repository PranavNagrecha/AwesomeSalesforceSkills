# Salesforce Big Objects Implementation Guide
Source: https://developer.salesforce.com/docs/
Downloaded: 2026-04-03

> Version 66.0, Spring '26 | Last updated: March 27, 2026

---

## Overview

A big object stores and manages massive amounts of data on the Salesforce platform. You can archive data from other objects or bring massive datasets from outside systems into a big object to get a full view of your customers. Clients and external systems use a standard set of APIs to access big object data. A big object provides consistent performance, whether you have 1 million records, 100 million, or even 1 billion.

**Available in:** Salesforce Classic and Lightning Experience
**Editions:** Enterprise, Performance, Unlimited, and Developer Editions (up to 1 million records)

### Types of Big Objects

**Standard big objects** — Objects defined by Salesforce and included in Salesforce products. `FieldHistoryArchive` is a standard big object that stores data as part of the Field History Tracking product. Standard big objects are always available and can't be customized.

**Custom big objects** — New objects that you create to store information unique to your org. Custom big objects extend the functionality that Lightning Platform provides.

### Custom Big Object Use Cases

- **360° view of the customer** — Extend your Salesforce data model to include detailed information from loyalty programs, feeds, clicks, billing and provisioning information, and more.
- **Auditing and tracking** — Track and maintain a long-term view of Salesforce or product usage for analysis or compliance purposes.
- **Historical archive** — Maintain access to historical data for analysis or compliance purposes while optimizing the performance of your core CRM or Lightning Platform applications.

### Differences Between Big Objects and Other Objects

| Big Objects | sObjects |
|---|---|
| Horizontally scalable distributed database | Relational database |
| Non-transactional database | Transactional database |
| Hundreds of millions or even billions of records | Millions of records |

**Big object behavioral constraints:**

- Big objects support only object and field permissions, not regular or standard sharing rules.
- Features like triggers, flows, processes, and the Salesforce mobile app aren't supported on big objects.
- When you insert an identical big object record with the same representation multiple times, only a single record is created so that writes can be idempotent. This behavior is different from an sObject, which creates a record for each request.

### API Support for Big Objects

You can process big objects with SOQL, Bulk, Chatter, and SOAP APIs.

> **Note:** These APIs are the only APIs supported for big objects. The REST API, for example, isn't supported.

---

## Big Objects Best Practices

### Considerations When Using Big Objects

- To define a big object or add a field to a custom big object, use either Metadata API or Setup.
- Big objects support custom Lightning and Visualforce components rather than standard UI elements (home pages, detail pages, or list views).
- You can create up to 100 big objects per org. The limits for big object fields are similar to the limits on custom objects and depend on your org's license type.
- You can't use Salesforce Connect external objects to access big objects in another org.
- Big objects don't support encryption. If you archive encrypted data from a standard or custom object, it's stored as clear text on the big object.
- If you're using Salesforce Shield Platform Encryption, standard or custom object field history is encrypted. For field history, data is archived using the Shield field history archive. Big objects respect encryption at rest. Shield Platform Encryption isn't otherwise supported for custom big objects.

### Design with Resiliency in Mind

The big objects database stores billions of records and is a distributed system that favors consistency over availability. The database is designed to ensure row-level consistency.

When working with big data and writing batches of records using APIs or Apex, you can experience a partial batch failure while some records are written and others aren't. In these cases, simply retry until all records are written.

**Key principles:**

- **The best practice when writing to a big object is to have a retry mechanism in place.** Retry the batch until you get a successful result from the API or Apex method.
  - To add logging to a custom object and surface errors to users, use the `addError()` method.
  - To verify that all records are saved, check the `Database.SaveResult` class.
- **Don't try to figure out which records succeeded and which failed.** Retry the entire batch.
- **Big objects don't support transactions.** If attempting to read or write to a big object using a trigger, process, or flow on a sObject, use asynchronous Apex. Use the `Queueable` interface to isolate DML operations on different sObject types and prevent the mixed DML error.
- **Use asynchronous Apex to write to a big object.** By writing asynchronously, you're better equipped to handle database lifecycle events.

---

## Define and Deploy Custom Big Objects

You can define custom big objects with Metadata API or in Setup. After you define and deploy a big object, you can view it or add fields in Setup. After you've deployed a big object, you can't edit or delete the index. To change the index, start over with a new big object.

### Define a Custom Big Object

Define a custom big object through Metadata API by creating XML files that contain its definition, fields, and index.

- **object files** — Create a file for each object to define the custom big object, its fields, and its index.
- **permissionset/profile files** — Create a permission set or profile file to specify permissions for each field. By default, access to a custom big object is restricted.
- **package file** — Create a file for Metadata API to specify the contents of the metadata you want to migrate.

### Naming Conventions for Custom Big Objects

Object names must be unique across all standard objects, custom objects, external objects, and big objects in the org. In the API, the names of custom big objects have a suffix of two underscores immediately followed by a lowercase "b" (`__b`). For example, a big object named "HistoricalInventoryLevels" is seen as `HistoricalInventoryLevels__b`.

### Metadata Reference

#### CustomObject Metadata

| Field Name | Field Type | Description |
|---|---|---|
| deploymentStatus | DeploymentStatus (string enum) | Custom big object's deployment status (`Deployed` for all big objects) |
| fields | CustomField[] | Definition of a field in the big object |
| fullName | string | Unique API name of the big object |
| indexes | Index[] | Definition of the index |
| label | string | Big object's name as displayed in the UI |
| pluralLabel | string | Field plural name as displayed in the UI |

#### CustomField Metadata

| Field Name | Field Type | Description |
|---|---|---|
| fullName | string | Unique API name of a field |
| label | string | Field name as displayed in the UI |
| length | int | Length of a field in characters (Text and LongTextArea fields only). Total characters across all text fields in an index can't exceed 100. **Note:** Email fields are 80 characters. Phone fields are 40 characters. |
| pluralLabel | string | Field plural name as displayed in the UI |
| precision | int | Number of digits for a number value (number fields only) |
| referenceTo | string | Related object type for a lookup field (lookup fields only) |
| relationshipName | string | Name of a relationship as displayed in the UI (lookup fields only) |
| required | boolean | Specifies whether the field is required. All fields that are part of the index must be marked as required. |
| scale | int | Number of digits to the right of the decimal point for a number value (number fields only) |
| type | FieldType | Field type. Supports DateTime, Email, Lookup, Number, Phone, Text, LongTextArea, and URL. **Note:** You can't include LongTextArea and URL fields in the index. Uniqueness isn't supported for custom fields. |

#### Index Metadata

Represents an index defined within a custom big object. Use this metadata type to define the composite primary key (index) for a custom big object.

| Field Name | Field Type | Description |
|---|---|---|
| fields | IndexField[] | The definition of the fields in the index |
| label | string | Required. This name is used to refer to the big object in the user interface. Available in API version 41.0 and later. |

#### IndexField Metadata

Defines which fields make up the index, their order, and sort direction. The order in which the fields are defined determines the order fields are listed in the index.

> **Note:** The total number of characters across all text fields in an index can't exceed 100.

| Field Name | Field Type | Description |
|---|---|---|
| name | string | Required. The API name for the field that's part of the index. This value must match the `fullName` value for the corresponding field in the fields section and be marked as required. **Warning:** If any index field name has a leading or trailing white space, you can't delete the big object record via SOQL+delete API. |
| sortDirection | string | Required. The sort direction of the field in the index. Valid values are `ASC` for ascending order and `DESC` for descending order. |

### Example: Create Metadata Files for Deployment

The following XML creates metadata files for a Customer Interaction object representing customer data from a single session in an online video game. `Account__c`, `Game_Platform__c`, and `Play_Date__c` define the index.

**Customer_Interaction__b.object**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomObject xmlns="http://soap.sforce.com/2006/04/metadata">
  <deploymentStatus>Deployed</deploymentStatus>
  <fields>
    <fullName>In_Game_Purchase__c</fullName>
    <label>In-Game Purchase</label>
    <length>16</length>
    <required>false</required>
    <type>Text</type>
    <unique>false</unique>
  </fields>
  <fields>
    <fullName>Level_Achieved__c</fullName>
    <label>Level Achieved</label>
    <length>16</length>
    <required>false</required>
    <type>Text</type>
    <unique>false</unique>
  </fields>
  <fields>
    <fullName>Lives_This_Game__c</fullName>
    <label>Lives Used This Game</label>
    <length>16</length>
    <required>false</required>
    <type>Text</type>
    <unique>false</unique>
  </fields>
  <fields>
    <fullName>Game_Platform__c</fullName>
    <label>Platform</label>
    <length>16</length>
    <required>true</required>
    <type>Text</type>
    <unique>false</unique>
  </fields>
  <fields>
    <fullName>Score_This_Game__c</fullName>
    <label>Score This Game</label>
    <length>16</length>
    <required>false</required>
    <type>Text</type>
    <unique>false</unique>
  </fields>
  <fields>
    <fullName>Account__c</fullName>
    <label>User Account</label>
    <referenceTo>Account</referenceTo>
    <relationshipName>Game_User_Account</relationshipName>
    <required>true</required>
    <type>Lookup</type>
  </fields>
  <fields>
    <fullName>Play_Date__c</fullName>
    <label>Date of Play</label>
    <required>true</required>
    <type>DateTime</type>
  </fields>
  <fields>
    <fullName>Play_Duration__c</fullName>
    <label>Play Duration</label>
    <required>false</required>
    <type>Number</type>
    <scale>2</scale>
    <precision>18</precision>
  </fields>
  <indexes>
    <fullName>CustomerInteractionsIndex</fullName>
    <label>Customer Interactions Index</label>
    <fields>
      <name>Account__c</name>
      <sortDirection>DESC</sortDirection>
    </fields>
    <fields>
      <name>Game_Platform__c</name>
      <sortDirection>ASC</sortDirection>
    </fields>
    <fields>
      <name>Play_Date__c</name>
      <sortDirection>DESC</sortDirection>
    </fields>
  </indexes>
  <label>Customer Interaction</label>
  <pluralLabel>Customer Interactions</pluralLabel>
</CustomObject>
```

**package.xml**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
  <types>
    <members>*</members>
    <name>CustomObject</name>
  </types>
  <types>
    <members>*</members>
    <name>PermissionSet</name>
  </types>
  <version>41.0</version>
</Package>
```

**Customer_Interaction_BigObject.permissionset**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<PermissionSet xmlns="http://soap.sforce.com/2006/04/metadata">
  <label>Customer Interaction Permission Set</label>
  <fieldPermissions>
    <editable>true</editable>
    <field>Customer_Interaction__b.In_Game_Purchase__c</field>
    <readable>true</readable>
  </fieldPermissions>
  <fieldPermissions>
    <editable>true</editable>
    <field>Customer_Interaction__b.Level_Achieved__c</field>
    <readable>true</readable>
  </fieldPermissions>
  <fieldPermissions>
    <editable>true</editable>
    <field>Customer_Interaction__b.Lives_This_Game__c</field>
    <readable>true</readable>
  </fieldPermissions>
  <fieldPermissions>
    <editable>true</editable>
    <field>Customer_Interaction__b.Play_Duration__c</field>
    <readable>true</readable>
  </fieldPermissions>
  <fieldPermissions>
    <editable>true</editable>
    <field>Customer_Interaction__b.Score_This_Game__c</field>
    <readable>true</readable>
  </fieldPermissions>
</PermissionSet>
```

### Deploy Custom Big Objects Using Metadata API

Use Metadata API and the Ant Migration Tool to deploy. When building files to deploy a custom big object:

- Put the `object` file in a folder called `objects`
- Put the `permissionset` file in a folder called `permissionsets`
- Put the `package.xml` file in the root directory

### View a Custom Big Object in Setup

After deploying, from Setup, enter **Big Objects** in the Quick Find box, then select **Big Objects**. To see its fields and relationships, click the name of a big object.

---

## Deploying and Retrieving Metadata with the Zip File

The `deploy()` and `retrieve()` calls are used to deploy and retrieve a .zip file. Within the .zip file is a project manifest (`package.xml`) that lists what to retrieve or deploy, and one or more XML components organized into folders.

**Limits:**

- You can deploy or retrieve up to 10,000 files at once.
- The maximum size of the deployed or retrieved .zip file is 39 MB.
- If the files are uncompressed in an unzipped folder, the size limit is 600 MB (629,145,600 bytes).
- Managed packages: First-generation managed packages that have passed AppExchange Security Review can contain up to 35,000 files. Second-generation managed packages can contain up to 10,000 files.
- Metadata API base-64 encodes components after compression. The resulting .zip file can't exceed 50 MB.

> **Note:** You can perform a `retrieve()` call for a big object only if its index is defined.

**package.xml elements:**

- `<fullName>` — contains the name of the server-side package. If no `<fullName>` exists, the `package.xml` defines a client-side unpackaged package.
- `<types>` — contains the name of the metadata type and the named members to be retrieved or deployed.
- `<members>` — contains the `fullName` of the component. Use `*` to retrieve all components of a type.
- `<name>` — contains the metadata type (e.g., `CustomObject` or `Profile`).
- `<version>` — the API version number used when the .zip file is deployed or retrieved.

**Sample package.xml:**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
  <types>
    <members>MyCustomObject__c</members>
    <name>CustomObject</name>
  </types>
  <types>
    <members>*</members>
    <name>CustomTab</name>
  </types>
  <types>
    <members>Standard</members>
    <name>Profile</name>
  </types>
  <version></version>
</Package>
```

---

## Populate a Custom Big Object

Use Salesforce APIs to populate a custom big object.

You can use a CSV file to load data into a custom big object via Bulk API 2.0. The first row in the CSV file must contain the field labels used to map the CSV data to the fields in the custom big object during import.

> **Note:** Both Bulk API and Bulk API 2.0 support querying and inserting big objects.

Insertion is idempotent, so inserting data that already exists won't result in duplicates. Reinserting is helpful when uploading millions of records. If an error occurs, the reinsert reuploads the failed uploads without duplicate data.

**Example CSV:**

```
Play Start,In-Game Purchase,Level Achieved,Lives Used,Platform,Play Stop,Score,Account
2015-01-01T23:01:01Z,A12569,57,7,PC,2015-01-02T02:27:01Z,55736,001R000000302D3
2015-01-03T13:22:01Z,B78945,58,7,PC,2015-01-03T15:47:01Z,61209,001R000000302D3
2015-01-04T15:16:01Z,D12156,43,5,iOS,2015-01-04T16:55:01Z,36148,001R000000302D3
```

### Populate a Custom Big Object with Apex

Use the `Database.insertImmediate()` method. DML operations on big objects are considered callouts, so Apex execution governors and limits for callouts apply. However, DML operations on big objects don't count towards Apex DML statement limits.

**Example:** Insert operation assuming an index of `FirstName__c`, `LastName__c`, and `Address__c`.

```apex
// Define the record.
PhoneBook__b pb = new PhoneBook__b();
pb.FirstName__c = 'John';
pb.LastName__c = 'Smith';
pb.Address__c = '1 Market St';
pb.PhoneNumber__c = '555-1212';
database.insertImmediate(pb);
// A single record will be created in the big object.

// Define the record with the same index values but different phone number.
PhoneBook__b pb = new PhoneBook__b();
pb.FirstName__c = 'John';
pb.LastName__c = 'Smith';
pb.Address__c = '1 Market St';
pb.PhoneNumber__c = '415-555-1212';
database.insertImmediate(pb);
// The existing record will be "re-inserted". Only a single record will remain.

// Define the record with different index values.
PhoneBook__b pb = new PhoneBook__b();
pb.FirstName__c = 'John';
pb.LastName__c = 'Smith';
pb.Address__c = 'Salesforce Tower';
pb.PhoneNumber__c = '415-555-1212';
database.insertImmediate(pb);
// A new record will be created leaving two records in the big object.
```

### Considerations for Populating Big Objects with Apex

- Use `String.trim()` to remove leading and trailing white space before inserting values, especially for values in primary key fields.
- When specifying an index field in a SOQL query WHERE clause, SOQL removes any leading or trailing white space before comparing it to the actual field value.
- If you set values to NULL when upserting into a custom big object, the fields aren't updated if they have existing values. To set these values to NULL, delete the field and recreate it.
- Reinserting a record with the same index but different data results in behavior similar to an upsert operation.
- If a record insert fails, `Database.insertImmediate()` doesn't throw an exception. Instead, it returns a `SaveResult` object with a `getErrors()` method.

### Test Populating Big Objects with Apex

- Apex tests that use mixed DML calls (insertion of data into big objects and sObjects within a single transaction) aren't allowed and fail.
- Apex tests are allowed to perform DML on big objects. However, real data is manipulated without any automatic rollback or cleanup. You must manually roll back each test DML operation, or build a mocking framework with the Apex stub API.

---

## Delete Data in a Custom Big Object

Use Apex or SOAP to delete data in a custom big object.

### Apex deleteImmediate()

The Apex method `deleteImmediate()` deletes data in a custom big object. Declare an sObject that contains all the fields in the custom big object's index.

**Constraints:**
- You can specify only fields that are part of the big object's index.
- You must specify all fields in the index.
- You can't include a partially specified index or non-indexed field.
- Wildcards aren't supported.
- The batch limit for big objects using `deleteImmediate()` is **50,000 records at a time**.

If you're deleting all records because of capacity optimization, insert one or two blank records after deletion and wait 24 hours for the new capacity to be recognized.

**Example:**

```apex
// Account__c, Game_Platform__c, and Play_Date__c are part of the custom big object's index.
// Fields must be listed in the order they appear in the index, without any gaps.
List<Customer_Interaction__b> cBO = new List<Customer_Interaction__b>();
cBO.addAll([SELECT Account__c, Game_Platform__c, Play_Date__c FROM Customer_Interaction__b
    WHERE Account__c = '001d000000Ky3xIAB']);

Database.deleteImmediate(cBO);
```

### SOAP deleteByExample()

The SOAP call `deleteByExample()` declares an sObject that contains the fields and values to delete. All rows that match the sObject's fields and values are deleted. All fields in the index must be specified.

**Java example:**

```java
public static void main(String[] args) {
    try {
        Customer_Interaction__b[] sObjectsToDelete = new Customer_Interaction__b[1];
        Customer_Interaction__b customerBO = new Customer_Interaction__b();
        customerBO.setAccount__c("001d000000Ky3xIAB");
        customerBO.setGame_Platform__c("iOS");
        Calendar dt = new GregorianCalendar(2017, 11, 28, 19, 13, 36);
        customerBO.setPlay_Date__c(dt);
        sObjectsToDelete[0] = customerBO;
        DeleteByExampleResult[] result = connection.deleteByExample(sObjectsToDelete);
    } catch (ConnectionException ce) {
        ce.printStackTrace();
    }
}
```

> **Note:** Repeating a successful `deleteByExample()` operation produces a success result, even if the rows were already deleted.

---

## Big Objects Queueable Example

To read or write to a big object using a trigger, process, or flow from a sObject, use asynchronous Apex. This example uses the `Queueable` interface to isolate DML operations on different sObject types and prevent the mixed DML error.

The trigger occurs when a case record is inserted. It calls a method to insert a batch of big object records.

```apex
// CaseTrigger.apxt
trigger CaseTrigger on Case (before insert) {
    if (Trigger.operationType == TriggerOperation.BEFORE_INSERT) {
        // Customer_Interaction__b has three required fields in its row key, in this order:
        // 1) Account__c - lookup to Account
        // 2) Game_Platform__c - Text(18)
        // 3) Play_Date__c - Date/Time
        List<Customer_Interaction__b> interactions = new List<Customer_Interaction__b>();

        for (Case c : Trigger.new) {
            Customer_Interaction__b ci = new Customer_Interaction__b(
                Account__c = c.AccountId,
                Game_Platform__c = c.Game_Platform__c,
                Play_Date__c = Date.today()
            );
            interactions.add(ci);
        }

        CustomerInteractionHandler handler = new CustomerInteractionHandler(interactions);
        System.enqueueJob(handler);
    }
}
```

The Queueable handler:

```apex
// CustomerInteractionHandler.apxc
public class CustomerInteractionHandler implements Queueable {
    private List<Customer_Interaction__b> interactions;

    public CustomerInteractionHandler(List<Customer_Interaction__b> interactions) {
        this.interactions = interactions;
    }

    public void execute(QueueableContext context) {
        List<ExceptionStorage__c> errors = new List<ExceptionStorage__c>();
        try {
            List<Database.SaveResult> srList = Database.insertImmediate(interactions);

            for (Database.SaveResult sr : srList) {
                if (sr.isSuccess()) {
                    System.debug('Successfully inserted Customer Interaction.');
                } else {
                    for (Database.Error err : sr.getErrors()) {
                        System.debug(err.getStatusCode() + ': ' + err.getMessage() +
                            '; Error fields: ' + err.getFields());

                        ExceptionStorage__c es = new ExceptionStorage__c(
                            name = 'Error',
                            ExceptionMessage__c = (err.getMessage()).abbreviate(255),
                            ExceptionType__c = String.valueOf(err.getStatusCode()),
                            ExceptionFields__c = (String.valueOf(err.getFields())).abbreviate(255)
                        );
                        errors.add(es);
                    }
                }
            }
        } catch (Exception e) {
            System.debug('Exception: ' + e.getTypeName() + ', ' + e.getMessage());
            ExceptionStorage__c es = new ExceptionStorage__c(
                name = 'Exception',
                ExceptionMessage__c = e.getMessage(),
                ExceptionType__c = e.getTypeName()
            );
            errors.add(es);
        }

        if (errors.size() > 0) {
            insert errors;
        }
    }
}
```

---

## Big Object Query Examples

### Customer 360 Degree and Filtering

In this use case, administrators load various customer engagement data from external sources into Salesforce big objects and then process the data to enrich customer profiles. The goal is to store customer transactions and interactions in big objects, then process and correlate that data with your core CRM data.

Batch Apex is the best choice for automated processing on a big object or ApiEvent, ReportEvent, or ListViewEvent.

**Run a batch Apex query on a big object and correlate Contact information:**

```apex
public class QueryBigObjectAndContact implements Database.Batchable<sObject> {
    private String key;

    public QueryBigObjectAndContact(String keyParam) {
        key = keyParam;
    }

    public Iterable<SObject> start(Database.BatchableContext BC) {
        return [SELECT Big_Object_Field__c, Account__c FROM Big_Object__b WHERE
            Big_Object_Primary_Key > key LIMIT 50000];
    }

    public void execute(Database.BatchableContext bc, List<Big_Object__b> bos) {
        Map<Id, Big_Object__b> accountIdToBigObjectMap = new Map<Id, Big_Object__b>();
        for (Big_Object__b bigObject : bos) {
            accountIdToBigObjectMap.put(bigObject.Account__c, bigObject);
            key = bigObject.Big_Object_Primariy_Key__c;
        }
        Map<Id, Account> accountMap = new Map<Id, Account>(
            [SELECT Id, Name FROM Account WHERE Id IN :accountIdToBigObjectMap.keySet()]
        );
        for (Id accountId : accountMap.keySet()) {
            Big_Object__b bigObject = accountIdToBigObjectMap.get(accountId);
            Account account = accountMap.get(accountId);
            // perform any actions that integrate the big object and Account
        }
    }

    public void finish(Database.BatchableContext bc) {
        // Daisy chain additional calls using the primary key to get around the 50k governor limit
        QueryBigObjectAndContact nextBatch = new QueryBigObjectAndContact(key);
        Database.executeBatch(nextBatch);
    }
}
```

### Field Audit Trail

Query `FieldHistoryArchive` and analyze results in CSV format.

**Example URI:** `/services/data/vXX.X/jobs/query`

**Example POST Request:**

```json
{
    "operation": "query",
    "query": "SELECT ParentId, FieldHistoryType, Field, Id, NewValue, OldValue FROM FieldHistoryArchive WHERE FieldHistoryType = 'Account' AND CreatedDate > LAST_MONTH"
}
```

**Example CURL Request:**

```bash
curl --include --request GET \
    --header "Authorization: Bearer token" \
    --header "Accept: text/csv" \
    https://instance.salesforce.com/services/data/vXX.X/jobs/query/750R0000000zxr8IAA/results?maxRecords=50000
```

### Real-Time Event Monitoring

With Real-Time Event Monitoring you can track who is accessing confidential and sensitive data in your Salesforce org. The corresponding event objects are `ApiEvent`, `ReportEvent`, and `ListViewEvent`.

**Example: Query and analyze an event big object:**

```apex
public class EventMatchesObject implements Database.Batchable<sObject> {
    private String lastEventDate;

    public EventMatchesObject(String lastEventDateParam) {
        lastEventDate = lastEventDateParam;
    }

    public Iterable<SObject> start(Database.BatchableContext bc) {
        return [SELECT EventDate, EventIdentifier, QueriedEntities, SourceIp, Username,
            UserAgent FROM ApiEvent WHERE EventDate > lastEventDate LIMIT 50000];
    }

    public void execute(Database.BatchableContext bc, List<ApiEvent> events) {
        for (ApiEvent event : events) {
            String objectString = 'Patent__c';
            String eventIdentifier = event.EventIdentifier;
            if (eventIdentifier.contains(objectString)) {
                // Perform actions on the event that contains 'Patent__c'
            }
            lastEventDate = format(event.EventDate);
        }
    }

    public void finish(Database.BatchableContext bc) {
        // Daisy chain additional calls using EventDate to get around the 50k governor limit
        EventMatchesObject nextBatch = new EventMatchesObject(lastEventDate);
        Database.executeBatch(nextBatch);
    }
}
```

### Aggregate Queries

Big objects don't support aggregate functions like `COUNT()`. Use batch Apex as an alternative:

```apex
public class CountBigObjects implements Database.Batchable<sObject> {
    private Integer recordsCounted;
    private String key;

    public CountBigObjects(Integer recordsCountedParam, String keyParam) {
        recordsCounted = recordsCountedParam;
        key = keyParam;
    }

    public Iterable<SObject> start(Database.BatchableContext bc) {
        return [SELECT Custom_Field__c FROM Big_Object__b LIMIT 25000];
    }

    public void execute(Database.BatchableContext bc, List<Big_Object__b> bos) {
        Map<Id, Big_Object__b> accountIdToBigObjectMap = new Map<Id, Big_Object__b>();
        for (Big_Object__b bigObject : bos) {
            accountIdToBigObjectMap.put(bigObject.Account__c, bigObject);
        }
        Map<Id, Account> accountMap = new Map<Id, Account>(
            [SELECT Id, Name FROM Account WHERE Id IN :accountIdToBigObjectMap.keySet()]
        );
        for (Id accountId : accountMap.keySet()) {
            Big_Object__b bigObject = accountIdToBigObjectMap.get(accountId);
            Account account = accountMap.get(accountId);
        }
    }

    public void finish(Database.BatchableContext bc) {
        CountBigObjects nextBatch = new CountBigObjects(recordsCounted, key);
        Database.executeBatch(nextBatch);
    }
}
```

---

## View Big Object Data in Reports and Dashboards

When working with big data and billions of records, it's not practical to build reports or dashboards directly from that data. Instead, use Bulk API to write a query that extracts a smaller, representative subset of the data. Store this working dataset in a custom object and use it in reports, dashboards, or any other Lightning Platform feature.

**Steps:**

1. Identify the big object that contains the data for which you need a report.
2. Create a custom object to hold the working dataset.
   - Under Optional Features, click **Allow Reports**.
   - Add custom fields matching the fields you want to report on from the big object.
3. Create an SOQL query that builds your working dataset by pulling data from your big object into your custom object.
   - **Tip:** Set this job to run nightly to keep the working dataset current.
4. Build a report using the working dataset:
   - From Setup, enter **Report Types** in the Quick Find box, then select **Report Types**.
   - Create a custom report type.
   - For the Primary Object, select the custom object from step 2.
   - Set the report to Deployed.
   - Run the report.
