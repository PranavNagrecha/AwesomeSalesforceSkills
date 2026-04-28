# Examples — Apex Dynamic SOQL Binding Safety

Three end-to-end scenarios where dynamic SOQL is required and binding/allowlisting is the difference between safe and exploitable.

## Example 1: Dynamic field-list reporting tool

**Context:** An internal "Quick Report" Lightning page lets users pick an sObject and a list of columns, then renders a tabular report. Both the object name and the field list come from the user.

**Problem:** Naively building `'SELECT ' + String.join(fields, ', ') + ' FROM ' + objectName` lets an attacker inject `Id), (SELECT Username, Password FROM User WHERE 1 = 1` style payloads or pivot to objects they should not see. `escapeSingleQuotes` does nothing here because the attack vector is identifiers, not string literals.

**Solution:**

```apex
public with sharing class QuickReportController {

    @AuraEnabled(cacheable=true)
    public static List<SObject> runReport(String objectApi, List<String> requestedFields) {
        Schema.SObjectType sot = Schema.getGlobalDescribe().get(objectApi);
        if (sot == null) {
            throw new AuraHandledException('Unknown object: ' + objectApi);
        }
        Map<String, Schema.SObjectField> fmap = sot.getDescribe().fields.getMap();

        List<String> safeFields = new List<String>();
        for (String f : requestedFields) {
            Schema.SObjectField sf = fmap.get(f.toLowerCase());
            if (sf == null) {
                throw new AuraHandledException('Unknown field: ' + f);
            }
            safeFields.add(sf.getDescribe().getName());
        }

        String soql = 'SELECT ' + String.join(safeFields, ', ') +
                      ' FROM ' + sot.getDescribe().getName() +
                      ' WITH USER_MODE LIMIT 200';

        return Database.queryWithBinds(
            soql,
            new Map<String, Object>(),
            AccessLevel.USER_MODE
        );
    }
}
```

**Why it works:** Both the object name and every field name are looked up in the Schema describe and replaced with the canonical name returned by the platform. User input never reaches the parsed query — only validated, canonical identifiers do. `AccessLevel.USER_MODE` enforces CRUD/FLS at runtime so a user cannot exfiltrate fields they cannot see, even if they guess a real API name.

---

## Example 2: Search by user-supplied filter

**Context:** A customer support console lets agents search Contacts by name fragment, optional account industry, and a minimum-created-date filter.

**Problem:** Each filter is optional. Building the WHERE clause by concatenation is the fastest path to inserting `' OR Id != null --` somewhere; building it with `String.escapeSingleQuotes` is better but still error-prone if a future field is forgotten.

**Solution:**

```apex
public with sharing class ContactSearchService {

    public List<Contact> search(String nameTerm, String industry, Date sinceCreated) {
        List<String> wheres = new List<String>();
        Map<String, Object> binds = new Map<String, Object>();

        if (String.isNotBlank(nameTerm)) {
            wheres.add('Name LIKE :nameLike');
            binds.put('nameLike', '%' + nameTerm + '%');
        }
        if (String.isNotBlank(industry)) {
            wheres.add('Account.Industry = :industry');
            binds.put('industry', industry);
        }
        if (sinceCreated != null) {
            wheres.add('CreatedDate >= :sinceCreated');
            binds.put('sinceCreated', Datetime.newInstance(sinceCreated, Time.newInstance(0,0,0,0)));
        }

        String soql = 'SELECT Id, Name, Account.Name FROM Contact';
        if (!wheres.isEmpty()) {
            soql += ' WHERE ' + String.join(wheres, ' AND ');
        }
        soql += ' ORDER BY Name LIMIT 200';

        return (List<Contact>) Database.queryWithBinds(
            soql,
            binds,
            AccessLevel.USER_MODE
        );
    }
}
```

**Why it works:** The WHERE-clause skeleton is built from hard-coded literals. Every value is bound. The `binds` map and `wheres` list grow together, so a forgotten bind would manifest as an obvious `Bind variable not found` runtime error — not a silent injection.

---

## Example 3: Sortable list view backed by Apex

**Context:** An LWC datatable on a custom object lets the user click a column header to sort. The column key and direction arrive as `@AuraEnabled` arguments.

**Problem:** Sort field and direction are identifiers, not values. They cannot be bound. A naive `'ORDER BY ' + sortField + ' ' + sortDir` is injectable on both fragments.

**Solution:**

```apex
public with sharing class CaseListController {

    private static final Set<String> ALLOWED_SORTS = new Set<String>{
        'casenumber', 'subject', 'status', 'createddate', 'priority'
    };

    @AuraEnabled(cacheable=true)
    public static List<Case> listCases(String sortField, String sortDir, Integer pageSize) {
        if (sortField == null || !ALLOWED_SORTS.contains(sortField.toLowerCase())) {
            throw new AuraHandledException('Invalid sort field');
        }
        Schema.SObjectField sf =
            Schema.SObjectType.Case.fields.getMap().get(sortField.toLowerCase());
        String safeSort = sf.getDescribe().getName();

        String safeDir = 'DESC'.equalsIgnoreCase(sortDir) ? 'DESC' : 'ASC';
        Integer cap = (pageSize == null) ? 50 : Math.min(Math.max(pageSize, 1), 200);

        String soql = 'SELECT Id, CaseNumber, Subject, Status, Priority, CreatedDate ' +
                      'FROM Case ORDER BY ' + safeSort + ' ' + safeDir + ' LIMIT :cap';

        Map<String, Object> binds = new Map<String, Object>{ 'cap' => cap };
        return (List<Case>) Database.queryWithBinds(soql, binds, AccessLevel.USER_MODE);
    }
}
```

**Why it works:** `sortField` is double-gated — first by an explicit `Set<String>` allowlist, then by Schema describe lookup that returns the canonical name. `sortDir` collapses to two literal values via ternary. `pageSize` is `Integer` and clamped before binding. There is no path for an attacker-controlled string to alter SOQL parsing.

---

## Anti-Pattern: "I escaped the quotes, so it is safe"

**What practitioners do:**

```apex
String fieldName = ApexPages.currentPage().getParameters().get('field');
String safe = String.escapeSingleQuotes(fieldName);
List<SObject> rows = Database.query('SELECT Id, ' + safe + ' FROM Account LIMIT 10');
```

**What goes wrong:** `escapeSingleQuotes` only neutralizes the `'` character. The user can still pass `Id), (SELECT Username FROM User WHERE Username LIKE 'a` — there are no single quotes to escape, and the resulting query is now a multi-select returning user data alongside accounts.

**Correct approach:** Look up `fieldName` in the Schema describe map, use the canonical name returned by `getDescribe().getName()`, and reject anything not present.
