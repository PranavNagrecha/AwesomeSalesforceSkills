/**
 * BaseDomain — lightweight domain layer base class.
 *
 * A Domain class wraps a homogeneous collection of records of one SObject
 * and exposes per-record business rules as methods. It is instantiated by
 * the TriggerHandler subclass once per context and must not issue SOQL.
 *
 * Example:
 *
 *     public class Accounts extends BaseDomain {
 *         public Accounts(List<Account> records) { super(records); }
 *         public void validateNames() {
 *             for (Account a : (List<Account>)records) {
 *                 if (String.isBlank(a.Name)) {
 *                     a.addError('Name is required.');
 *                 }
 *             }
 *         }
 *     }
 *
 * Domains MUST NOT perform DML, callouts, or queries.
 * Domains MUST be bulk-safe (never write loop-based per-record SOQL).
 */
public abstract with sharing class BaseDomain {

    protected List<SObject> records;
    protected Map<Id, SObject> oldMap;

    protected BaseDomain(List<SObject> records) {
        this(records, null);
    }

    protected BaseDomain(List<SObject> records, Map<Id, SObject> oldMap) {
        this.records = records == null ? new List<SObject>() : records;
        this.oldMap = oldMap;
    }

    protected SObject oldVersion(SObject current) {
        return oldMap == null ? null : oldMap.get(current.Id);
    }

    protected Boolean isChanged(SObject current, SObjectField field) {
        if (current == null || field == null) { return false; }
        SObject previous = oldVersion(current);
        if (previous == null) { return false; }
        return current.get(field) != previous.get(field);
    }

    protected Set<Id> recordIds() {
        Set<Id> ids = new Set<Id>();
        for (SObject r : records) {
            if (r.Id != null) { ids.add(r.Id); }
        }
        return ids;
    }
}
