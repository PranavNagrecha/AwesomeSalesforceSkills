/**
 * TestUserFactory — creates users with specific Profile + PermissionSets for
 * use inside `System.runAs()` blocks.
 *
 *     User salesRep = TestUserFactory.createUser(
 *         'Standard User',
 *         new List<String>{ 'Sales_App_Access', 'Shared_Queue_Member' }
 *     );
 *     System.runAs(salesRep) {
 *         // Test what the record looks like through this user's sharing + FLS.
 *     }
 *
 * Rules:
 *  - Always bulk-insert users when making more than one.
 *  - Unique username prefix prevents conflicts across parallel test runs.
 */
@IsTest
public class TestUserFactory {

    private static Integer seq = 0;

    public static User createUser(String profileName, List<String> permissionSetNames) {
        User u = buildUser(profileName);
        insert u;
        assignPermissionSets(u.Id, permissionSetNames);
        return u;
    }

    public static List<User> createUsers(Integer count, String profileName, List<String> permissionSetNames) {
        List<User> out = new List<User>();
        for (Integer i = 0; i < count; i++) {
            out.add(buildUser(profileName));
        }
        insert out;
        Set<Id> ids = new Set<Id>();
        for (User u : out) { ids.add(u.Id); }
        assignPermissionSets(ids, permissionSetNames);
        return out;
    }

    private static User buildUser(String profileName) {
        Profile p = [SELECT Id FROM Profile WHERE Name = :profileName LIMIT 1];
        seq += 1;
        String uniq = String.valueOf(Crypto.getRandomLong()).right(6) + seq;
        return new User(
            FirstName = 'Test',
            LastName  = 'User ' + uniq,
            Alias     = ('tu' + uniq).left(8),
            Username  = 'test.user.' + uniq + '@skills.repo.test',
            Email     = 'test.user.' + uniq + '@example.com',
            ProfileId = p.Id,
            TimeZoneSidKey     = 'America/Los_Angeles',
            LocaleSidKey       = 'en_US',
            EmailEncodingKey   = 'UTF-8',
            LanguageLocaleKey  = 'en_US'
        );
    }

    private static void assignPermissionSets(Id userId, List<String> names) {
        assignPermissionSets(new Set<Id>{userId}, names);
    }

    private static void assignPermissionSets(Set<Id> userIds, List<String> names) {
        if (names == null || names.isEmpty() || userIds.isEmpty()) { return; }
        List<PermissionSet> sets = [SELECT Id, Name FROM PermissionSet WHERE Name IN :names];
        List<PermissionSetAssignment> psas = new List<PermissionSetAssignment>();
        for (Id uid : userIds) {
            for (PermissionSet ps : sets) {
                psas.add(new PermissionSetAssignment(AssigneeId = uid, PermissionSetId = ps.Id));
            }
        }
        insert psas;
    }
}
