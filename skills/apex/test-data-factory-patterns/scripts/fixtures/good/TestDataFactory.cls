@IsTest
public class TestDataFactory {
    private static Integer uniqueCounter = 0;

    public static String uniqueSuffix() {
        uniqueCounter++;
        return String.valueOf(DateTime.now().getTime()) + '-' + uniqueCounter;
    }

    public static List<Account> createAccounts(Integer count, Boolean doInsert) {
        List<Account> rows = new List<Account>();
        for (Integer i = 0; i < count; i++) {
            rows.add(new Account(Name = 'Factory Account ' + i, BillingCountry = 'US'));
        }
        if (doInsert) {
            insert rows;
        }
        return rows;
    }

    public static List<Contact> createContacts(List<Account> parents, Integer perAccount, Boolean doInsert) {
        List<Contact> rows = new List<Contact>();
        for (Account parent : parents) {
            for (Integer i = 0; i < perAccount; i++) {
                rows.add(new Contact(AccountId = parent.Id, LastName = 'Factory ' + i));
            }
        }
        if (doInsert) {
            insert rows;
        }
        return rows;
    }

    public static User newUser(String profileName) {
        Profile p = [SELECT Id FROM Profile WHERE Name = :profileName LIMIT 1];
        String suffix = uniqueSuffix();
        return new User(
            Alias = 'fact' + String.valueOf(Math.mod(uniqueCounter, 10000)).leftPad(4, '0'),
            Email = 'factory.' + suffix + '@example.com',
            EmailEncodingKey = 'UTF-8',
            LastName = 'Factory',
            LanguageLocaleKey = 'en_US',
            LocaleSidKey = 'en_US',
            ProfileId = p.Id,
            TimeZoneSidKey = 'America/Los_Angeles',
            UserName = 'factory.' + suffix + '@example.com'
        );
    }

    // UserRole, User-with-role, and PermissionSetAssignment are setup objects.
    // Running their DML inside System.runAs keeps it from colliding with
    // Account or Contact DML earlier in the same test transaction.
    public static User createUserWithAccess(String profileName, String roleName, List<String> permissionSetNames) {
        User u = newUser(profileName);
        System.runAs(new User(Id = UserInfo.getUserId())) {
            if (roleName != null) {
                UserRole role = new UserRole(Name = roleName);
                insert role;
                u.UserRoleId = role.Id;
            }
            insert u;
            if (permissionSetNames != null && !permissionSetNames.isEmpty()) {
                List<PermissionSetAssignment> assignments = new List<PermissionSetAssignment>();
                for (PermissionSet ps : [SELECT Id FROM PermissionSet WHERE Name IN :permissionSetNames]) {
                    assignments.add(new PermissionSetAssignment(AssigneeId = u.Id, PermissionSetId = ps.Id));
                }
                insert assignments;
            }
        }
        return u;
    }
}
