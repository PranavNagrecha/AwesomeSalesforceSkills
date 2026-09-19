/** A service that enforces the running user's FLS, so tests must run as a persona. */
public with sharing class OppService {
    public static List<Opportunity> load(Set<Id> ids) {
        return [SELECT Id, Name FROM Opportunity WHERE Id IN :ids WITH USER_MODE];
    }
}
