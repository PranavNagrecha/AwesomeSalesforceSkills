/**
 * SecurityUtils — CRUD/FLS + sharing enforcement helpers.
 *
 * Prefer calling these at the edge of a service method rather than inside
 * loops. They throw `SecurityException` on failure, which surfaces in LWC
 * as an AuraHandledException and in REST as a 403.
 *
 * For queries, prefer `WITH USER_MODE` in SOQL (Summer '23+) and
 * `Security.stripInaccessible` for DML prep.
 */
public inherited sharing class SecurityUtils {

    public class SecurityException extends Exception {}

    public static List<SObject> stripInaccessibleForUpdate(List<SObject> records) {
        return stripInaccessible(AccessType.UPDATABLE, records);
    }

    public static List<SObject> stripInaccessibleForInsert(List<SObject> records) {
        return stripInaccessible(AccessType.CREATABLE, records);
    }

    public static List<SObject> stripInaccessible(AccessType action, List<SObject> records) {
        if (records == null || records.isEmpty()) { return records; }
        SObjectAccessDecision decision = Security.stripInaccessible(action, records);
        if (!decision.getRemovedFields().isEmpty()) {
            ApplicationLogger.warn(
                'SecurityUtils.stripInaccessible',
                'Stripped fields: ' + JSON.serialize(decision.getRemovedFields())
            );
        }
        return decision.getRecords();
    }

    public static void requireReadable(Schema.SObjectType token) {
        require(token, 'isAccessible');
    }

    public static void requireCreatable(Schema.SObjectType token) {
        require(token, 'isCreateable');
    }

    public static void requireUpdatable(Schema.SObjectType token) {
        require(token, 'isUpdateable');
    }

    public static void requireDeletable(Schema.SObjectType token) {
        require(token, 'isDeletable');
    }

    private static void require(Schema.SObjectType token, String verb) {
        if (token == null) {
            throw new SecurityException('SObjectType is null');
        }
        Schema.DescribeSObjectResult describe = token.getDescribe();
        Boolean ok = false;
        if (verb == 'isAccessible') { ok = describe.isAccessible(); }
        else if (verb == 'isCreateable') { ok = describe.isCreateable(); }
        else if (verb == 'isUpdateable') { ok = describe.isUpdateable(); }
        else if (verb == 'isDeletable')  { ok = describe.isDeletable();  }
        if (!ok) {
            throw new SecurityException(
                'User ' + UserInfo.getUserName() + ' lacks ' + verb
                + ' on ' + describe.getName()
            );
        }
    }
}
