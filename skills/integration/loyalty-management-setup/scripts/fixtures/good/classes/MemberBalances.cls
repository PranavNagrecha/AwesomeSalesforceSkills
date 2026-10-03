public with sharing class MemberBalances {
    public static List<LoyaltyMemberCurrency> qualifyingBalances(Id memberId) {
        return [
            SELECT Id, PointsBalance, LoyaltyProgramCurrency.Name
            FROM LoyaltyMemberCurrency
            WHERE LoyaltyMemberId = :memberId
            AND LoyaltyProgramCurrency.CurrencyType = 'Qualifying'
            WITH USER_MODE
        ];
    }
}
