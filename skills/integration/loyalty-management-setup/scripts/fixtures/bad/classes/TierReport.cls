public with sharing class TierReport {
    public static List<LoyaltyMemberCurrency> rewards(Id memberId) {
        return [SELECT Id, PointsBalance FROM LoyaltyMemberCurrency WHERE LoyaltyMemberId = :memberId AND CurrencyType = 'Non-Qualifying'];
    }
    public static List<LoyaltyProgramCurrency> currencies() {
        return [SELECT Id FROM LoyaltyProgramCurrency WHERE CurrencyType = 'Non-Qualifying'];
    }
}
