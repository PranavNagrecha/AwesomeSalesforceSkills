/**
 * BaseSelector — lightweight selector layer base class.
 *
 * A Selector is the ONLY layer in this architecture that issues SOQL.
 * Every query lives in a selector method named after its intent
 * (e.g. `selectByIdsWithContacts(Set<Id> ids)`), not by its WHERE clause.
 *
 * Selectors default to `WITH USER_MODE` (Summer '23+) so CRUD + FLS + sharing
 * are enforced unless the caller explicitly requests system mode. Never
 * override this silently.
 *
 * Example:
 *
 *     public class AccountsSelector extends BaseSelector {
 *         public List<Account> selectByIds(Set<Id> ids) {
 *             return (List<Account>) Database.queryWithBinds(
 *                 'SELECT Id, Name FROM Account WHERE Id IN :ids',
 *                 new Map<String, Object>{ 'ids' => ids },
 *                 userMode()
 *             );
 *         }
 *     }
 */
public abstract inherited sharing class BaseSelector {

    protected AccessLevel userMode() {
        return AccessLevel.USER_MODE;
    }

    protected AccessLevel systemMode() {
        // Use only when the running user's CRUD/FLS must be bypassed for a
        // documented, reviewed reason. Subclass comment MUST explain why.
        return AccessLevel.SYSTEM_MODE;
    }

    protected String commaSeparated(Set<String> values) {
        List<String> sorted = new List<String>(values);
        sorted.sort();
        return '\'' + String.join(sorted, '\',\'') + '\'';
    }

    protected void assertNotNull(Object value, String argumentName) {
        if (value == null) {
            throw new SelectorException('Argument ' + argumentName + ' must not be null');
        }
    }

    public class SelectorException extends Exception {}
}
