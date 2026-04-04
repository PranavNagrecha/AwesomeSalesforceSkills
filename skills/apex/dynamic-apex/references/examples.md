# Examples — Dynamic Apex

## Example 1: Generic FLS-Checked Update Utility

**Context:** A managed package or shared service layer needs to update any configurable set of fields on an sObject record while respecting the running user's field-level security. The field list comes from custom metadata, not from user input, but FLS must still be enforced because the code is called from an AuraEnabled controller.

**Problem:** Without explicit FLS checks, the DML succeeds even when the current user lacks edit permission on one of the target fields, silently violating the user's permissions profile.

**Solution:**

```apex
public class DynamicUpdateService {

    // Cache describe metadata for the transaction lifetime.
    private static final Map<String, Schema.SObjectType> GLOBAL_DESCRIBE =
        Schema.getGlobalDescribe();
    private static final Map<String, Map<String, Schema.SObjectField>> FIELD_MAP_CACHE =
        new Map<String, Map<String, Schema.SObjectField>>();

    /**
     * Updates allowlisted fields on a single record, enforcing FLS.
     *
     * @param objectApiName  API name of the sObject (e.g. 'Account', 'My_Object__c')
     * @param recordId       Id of the record to update
     * @param fieldValues    Map of field API name -> new value
     * @throws AuraHandledException if the object is inaccessible or a field is not updateable
     */
    @AuraEnabled
    public static void updateRecord(
        String objectApiName,
        Id recordId,
        Map<String, Object> fieldValues
    ) {
        // 1. Validate the object exists and is updateable.
        if (!GLOBAL_DESCRIBE.containsKey(objectApiName.toLowerCase())) {
            throw new AuraHandledException('Unknown object: ' + objectApiName);
        }
        Schema.DescribeSObjectResult objDescribe =
            GLOBAL_DESCRIBE.get(objectApiName.toLowerCase()).getDescribe();
        if (!objDescribe.isUpdateable()) {
            throw new AuraHandledException('Object not updateable: ' + objectApiName);
        }

        // 2. Get field map (cached).
        Map<String, Schema.SObjectField> fieldMap = getFieldMap(objectApiName.toLowerCase());

        // 3. Build the sObject dynamically, checking FLS per field.
        SObject record = objDescribe.getSObjectType().newSObject(recordId);
        for (String fieldName : fieldValues.keySet()) {
            String normalizedField = fieldName.toLowerCase();
            if (!fieldMap.containsKey(normalizedField)) {
                throw new AuraHandledException('Unknown field: ' + fieldName);
            }
            Schema.DescribeFieldResult fdr = fieldMap.get(normalizedField).getDescribe();
            if (!fdr.isUpdateable()) {
                throw new AuraHandledException('Field not updateable: ' + fieldName);
            }
            record.put(fdr.getName(), fieldValues.get(fieldName));
        }

        // 4. Single DML call with fully validated record.
        update record;
    }

    private static Map<String, Schema.SObjectField> getFieldMap(String objectApiName) {
        if (!FIELD_MAP_CACHE.containsKey(objectApiName)) {
            FIELD_MAP_CACHE.put(
                objectApiName,
                GLOBAL_DESCRIBE.get(objectApiName).getDescribe().fields.getMap()
            );
        }
        return FIELD_MAP_CACHE.get(objectApiName);
    }
}
```

**Why it works:** Object and field names come from an allowlisted lookup against live Schema metadata rather than string interpolation. FLS is checked per field via `DescribeFieldResult.isUpdateable()` before `put()` is called. The describe cache avoids repeated `getGlobalDescribe()` calls within the same transaction.

---

## Example 2: Admin-Configurable Dynamic Query Builder

**Context:** A Lightning component lets an admin choose which fields to display in an export table. The field list is stored in a `FieldSet` on the target object. The query must be built at runtime and must include any filter value the user types in a search box.

**Problem:** Naively concatenating Field Set member names without validation and directly embedding the user's search string creates both a brittle query (fields can be deleted) and a SOQL injection vector.

**Solution:**

```apex
public class DynamicQueryBuilder {

    private static final Map<String, Schema.SObjectType> GLOBAL_DESCRIBE =
        Schema.getGlobalDescribe();

    /**
     * Builds and executes a query for an object using a named Field Set.
     * The searchTerm is applied as a LIKE filter on the Name field using a bind variable.
     *
     * @param objectApiName  sObject API name
     * @param fieldSetName   Developer name of the Field Set on that object
     * @param searchTerm     User-supplied search string (bound, not concatenated)
     * @return               Query results, never null
     */
    public static List<SObject> queryWithFieldSet(
        String objectApiName,
        String fieldSetName,
        String searchTerm
    ) {
        // 1. Validate the object.
        String normalizedObj = objectApiName.toLowerCase();
        if (!GLOBAL_DESCRIBE.containsKey(normalizedObj)) {
            throw new IllegalArgumentException('Unknown object: ' + objectApiName);
        }
        Schema.DescribeSObjectResult objDescribe =
            GLOBAL_DESCRIBE.get(normalizedObj).getDescribe();

        // 2. Retrieve and validate Field Set members against the live field map.
        Map<String, Schema.SObjectField> fieldMap = objDescribe.fields.getMap();
        Schema.FieldSet fs = objDescribe.fieldSets.getMap().get(fieldSetName);
        if (fs == null) {
            throw new IllegalArgumentException('Field Set not found: ' + fieldSetName);
        }

        List<String> validatedFields = new List<String>{'Id'};
        for (Schema.FieldSetMember fsm : fs.getFields()) {
            String apiName = fsm.getFieldPath().toLowerCase();
            if (fieldMap.containsKey(apiName)) {
                // Confirm field is accessible.
                if (fieldMap.get(apiName).getDescribe().isAccessible()) {
                    validatedFields.add(fieldMap.get(apiName).getDescribe().getName());
                }
            }
            // Fields not present in the live field map are silently skipped
            // to handle deleted fields gracefully.
        }

        // 3. Build the SELECT clause from validated field names.
        String selectClause = String.join(validatedFields, ', ');

        // 4. Use a bind variable for the user-supplied search term.
        //    The bind variable approach prevents SOQL injection.
        String searchPattern = '%' + searchTerm + '%';
        String query = 'SELECT ' + selectClause
            + ' FROM ' + objDescribe.getName()
            + ' WHERE Name LIKE :searchPattern'
            + ' LIMIT 200';

        return Database.query(query);
    }
}
```

**Why it works:** Field names originate from Schema metadata (Field Set), not user input, and each is validated against the live field map before inclusion. The user's search string is bound via `:searchPattern`, meaning the Apex runtime interpolates it safely — it is never concatenated into the string. Inaccessible fields are filtered out to respect FLS.

---

## Anti-Pattern: Concatenating User Input Directly into Dynamic SOQL

**What practitioners do:** To build a flexible search, developers write:

```apex
// DANGEROUS — do not copy this pattern
String userInput = ApexPages.currentPage().getParameters().get('search');
String q = 'SELECT Id, Name FROM Account WHERE Name = \'' + userInput + '\'';
List<Account> results = Database.query(q);
```

**What goes wrong:** An attacker submits `' OR Name != '` as the search value. The resulting query becomes `WHERE Name = '' OR Name != ''`, which returns every Account the current user can see. More destructive payloads can use `LIMIT 0` variations or cause behavioral changes. This is a textbook SOQL injection.

**Correct approach:** Use a bind variable:

```apex
String userInput = ApexPages.currentPage().getParameters().get('search');
// Bind variable: userInput is never string-interpolated
String q = 'SELECT Id, Name FROM Account WHERE Name = :userInput';
List<Account> results = Database.query(q);
```

The bind variable is evaluated by the Apex runtime at execution time — special characters in `userInput` are treated as literal data, not SOQL syntax.
