/** Minimal stub so template-class-not-shipped stays silent in this fixture dir. */
public class TestDataFactory {
    public static List<Case> createCases(Integer count, Id accountId, Map<String, Object> overrides) {
        List<Case> out = new List<Case>();
        for (Integer i = 0; i < count; i++) {
            out.add(new Case(Subject = 'Fixture ' + i, Origin = 'Web'));
        }
        return out;
    }

    public static Database.SaveResult[] insertAsSystem(List<SObject> records) {
        return Database.insert(records, AccessLevel.SYSTEM_MODE);
    }
}
