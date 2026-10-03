# Metadata Examples: NPSP Household Accounts

Household naming settings (`npsp__Household_Naming_Settings__c`) and Households Settings (`npo02__Households_Settings__c`) are custom settings, so their values are data. The one deployable artifact in this domain is a custom naming class. Build it only when the token syntax cannot express the rule. The interface and settings come from the NPSP source (`SalesforceFoundation/NPSP`): `HH_INaming` is declared `global Interface HH_INaming`, and `Household_Naming_Settings__c.Implementing_Class__c` holds the class name.

## 1. Custom naming class

Rule implemented: a household whose members share one last name is "The Smith Family". Mixed last names fall back to "Smith and Jones Household". Greetings list each member.

```apex
// force-app/main/default/classes/FamilyHouseholdNaming.cls
global with sharing class FamilyHouseholdNaming implements npsp.HH_INaming {

    // NPSP removes excluded members before calling these methods
    // (see the method comments on npsp.HH_INaming).

    global String getHouseholdName(List<Contact> listCon) {
        if (listCon == null || listCon.isEmpty()) {
            return 'Anonymous Household';
        }
        List<String> lastNames = distinctLastNames(listCon);
        if (lastNames.size() == 1) {
            return 'The ' + lastNames[0] + ' Family';
        }
        return joinWithAnd(lastNames) + ' Household';
    }

    global String getHouseholdFormalGreeting(List<Contact> listCon) {
        if (listCon == null || listCon.isEmpty()) {
            return 'Friend';
        }
        List<String> parts = new List<String>();
        for (Contact c : listCon) {
            String part = String.isBlank(c.Salutation) ? '' : c.Salutation + ' ';
            part += String.isBlank(c.FirstName) ? '' : c.FirstName + ' ';
            parts.add((part + c.LastName).trim());
        }
        return joinWithAnd(parts);
    }

    global String getHouseholdInformalGreeting(List<Contact> listCon) {
        if (listCon == null || listCon.isEmpty()) {
            return 'Friend';
        }
        List<String> firstNames = new List<String>();
        for (Contact c : listCon) {
            firstNames.add(String.isBlank(c.FirstName) ? c.LastName : c.FirstName);
        }
        return joinWithAnd(firstNames);
    }

    global String getExampleName(npsp__Household_Naming_Settings__c hns, String strField, List<Contact> listCon) {
        if (strField == 'npsp__Formal_Greeting_Format__c' || strField == 'Formal_Greeting_Format__c') {
            return getHouseholdFormalGreeting(listCon);
        }
        if (strField == 'npsp__Informal_Greeting_Format__c' || strField == 'Informal_Greeting_Format__c') {
            return getHouseholdInformalGreeting(listCon);
        }
        return getHouseholdName(listCon);
    }

    global Set<String> setHouseholdNameFieldsOnContact() {
        // Tells NPSP which Contact fields to query before calling this class.
        return new Set<String>{ 'Salutation', 'FirstName', 'LastName' };
    }

    private static List<String> distinctLastNames(List<Contact> listCon) {
        List<String> result = new List<String>();
        Set<String> seen = new Set<String>();
        for (Contact c : listCon) {
            if (!seen.contains(c.LastName)) {
                seen.add(c.LastName);
                result.add(c.LastName);
            }
        }
        return result;
    }

    private static String joinWithAnd(List<String> items) {
        if (items.size() == 1) {
            return items[0];
        }
        List<String> head = new List<String>();
        for (Integer i = 0; i < items.size() - 1; i++) {
            head.add(items[i]);
        }
        return String.join(head, ', ') + ' and ' + items[items.size() - 1];
    }
}
```

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- force-app/main/default/classes/FamilyHouseholdNaming.cls-meta.xml -->
<ApexClass xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>67.0</apiVersion>
    <status>Active</status>
</ApexClass>
```

## 2. Test class

The methods take in-memory Contacts, so the test needs no DML and no NPSP settings records. The input order mirrors the order NPSP passes members in (naming order, then primary contact, then CreatedDate, per `ContactSelector`).

```apex
// force-app/main/default/classes/FamilyHouseholdNamingTest.cls
@IsTest
private class FamilyHouseholdNamingTest {

    @IsTest
    static void sharedLastNameBecomesFamily() {
        List<Contact> members = new List<Contact>{
            new Contact(Salutation = 'Ms.', FirstName = 'Jane', LastName = 'Smith'),
            new Contact(Salutation = 'Mr.', FirstName = 'John', LastName = 'Smith')
        };
        FamilyHouseholdNaming naming = new FamilyHouseholdNaming();
        Assert.areEqual('The Smith Family', naming.getHouseholdName(members));
        Assert.areEqual('Ms. Jane Smith and Mr. John Smith', naming.getHouseholdFormalGreeting(members));
        Assert.areEqual('Jane and John', naming.getHouseholdInformalGreeting(members));
    }

    @IsTest
    static void mixedLastNamesFallBackToHousehold() {
        List<Contact> members = new List<Contact>{
            new Contact(FirstName = 'Jane', LastName = 'Smith'),
            new Contact(FirstName = 'John', LastName = 'Jones'),
            new Contact(FirstName = 'Ava', LastName = 'Lee')
        };
        Assert.areEqual('Smith, Jones and Lee Household', new FamilyHouseholdNaming().getHouseholdName(members));
    }

    @IsTest
    static void emptyHouseholdUsesAnonymousText() {
        FamilyHouseholdNaming naming = new FamilyHouseholdNaming();
        Assert.areEqual('Anonymous Household', naming.getHouseholdName(new List<Contact>()));
        Assert.areEqual('Friend', naming.getHouseholdInformalGreeting(new List<Contact>()));
    }

    @IsTest
    static void declaresTheContactFieldsItReads() {
        Set<String> fields = new FamilyHouseholdNaming().setHouseholdNameFieldsOnContact();
        Assert.isTrue(fields.containsAll(new Set<String>{ 'Salutation', 'FirstName', 'LastName' }));
    }
}
```

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- force-app/main/default/classes/FamilyHouseholdNamingTest.cls-meta.xml -->
<ApexClass xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>67.0</apiVersion>
    <status>Active</status>
</ApexClass>
```

## 3. package.xml member form

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- manifest/package.xml -->
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>FamilyHouseholdNaming</members>
        <members>FamilyHouseholdNamingTest</members>
        <name>ApexClass</name>
    </types>
    <version>67.0</version>
</Package>
```

## 4. Register the class and refresh

1. Deploy: `sf project deploy start --manifest manifest/package.xml --test-level RunSpecifiedTests --tests FamilyHouseholdNamingTest`.
2. In NPSP Settings > People > Households, set Implementing Class to `FamilyHouseholdNaming` and save. NPSP's `HH_HouseholdNamingSettingValidator` resolves the name with `Type.forName(className)` and rejects classes that are not `HH_INaming` instances.
3. Click Refresh Household Names, then spot-check households with shared and mixed last names.

UNVERIFIED (2026-10-03): the Apex Reference Guide (Type Class, `forName(fullyQualifiedName)`) says that when a managed package calls the single-argument form for a local type in an org with no namespace, the method returns null. NPSP's validator uses that form. Validate step 2 in a sandbox before production; if the settings page reports an invalid class, the class cannot be resolved from the package in that org.

## 5. Audit queries

```sql
-- Households with any user-controlled naming field (';' alone means none)
SELECT Id, Name, npo02__Formal_Greeting__c, npo02__Informal_Greeting__c,
       npo02__SYSTEM_CUSTOM_NAMING__c
FROM Account
WHERE RecordType.DeveloperName = 'HH_Account'
  AND npo02__SYSTEM_CUSTOM_NAMING__c != null
```

```sql
-- Member order NPSP will use when it builds names
SELECT AccountId, Id, FirstName, LastName, npo02__Household_Naming_Order__c,
       npsp__Primary_Contact__c, CreatedDate
FROM Contact
WHERE AccountId = :householdId
ORDER BY npo02__Household_Naming_Order__c ASC NULLS LAST,
         npsp__Primary_Contact__c DESC, CreatedDate
```
