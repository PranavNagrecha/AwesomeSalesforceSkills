public with sharing class NegativeExplicitElevationDescribed {
    public static void seed(List<Case> cases) {
        // the insert runs in system mode, outside runAs(agent)
        TestDataFactory.insertAsSystem(cases);
    }
}
