public class CleanIdRouting {
    public static String classify(Id recordId) {
        Schema.SObjectType sot = recordId.getSObjectType();
        if (sot == Account.SObjectType) { return 'Account'; }
        if (sot == Contact.SObjectType) { return 'Contact'; }
        return 'Unknown';
    }
}
