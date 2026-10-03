public with sharing class AccountSearchController {
    private static final Map<String, String> SORTABLE = new Map<String, String>{
        'name' => 'Name',
        'created' => 'CreatedDate',
        'revenue' => 'AnnualRevenue'
    };
    private static final Integer MAX_ROWS = 200;

    @AuraEnabled(cacheable=true)
    public static List<Account> search(String searchTerm, String sortKey, Integer rowLimit) {
        String sortField = SORTABLE.get(sortKey == null ? 'name' : sortKey.toLowerCase());
        if (sortField == null) {
            throw new AuraHandledException('Unsupported sort key.');
        }
        Integer safeLimit = (rowLimit == null || rowLimit < 1 || rowLimit > MAX_ROWS) ? MAX_ROWS : rowLimit;
        Map<String, Object> binds = new Map<String, Object>{
            'pattern' => '%' + (searchTerm == null ? '' : searchTerm) + '%',
            'maxRows' => safeLimit
        };
        // sortField comes only from the SORTABLE allowlist above
        String soql = 'SELECT Id, Name, AnnualRevenue FROM Account WHERE Name LIKE :pattern '
            + 'ORDER BY ' + sortField + ' LIMIT :maxRows'; // allowlisted
        return Database.queryWithBinds(soql, binds, AccessLevel.USER_MODE);
    }
}
