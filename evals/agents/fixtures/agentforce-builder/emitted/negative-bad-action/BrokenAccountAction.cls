/**
 * BrokenAccountAction — intentionally malformed for negative fixture.
 * Missing: @InvocableMethod annotation, inner Request class,
 * inner Response class, @InvocableVariable decorators.
 * Gate C static check MUST reject this.
 */
public with sharing class BrokenAccountAction {
    public static String summarize(Id accountId) {
        Account a = [SELECT Name FROM Account WHERE Id = :accountId LIMIT 1];
        return a.Name;
    }
}
