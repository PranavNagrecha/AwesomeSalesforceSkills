/**
 * BaseService — lightweight service layer base class.
 *
 * A Service is the unit of business work. It orchestrates Domain + Selector
 * classes, performs DML, emits platform events, and is the ONLY layer that
 * should begin a savepoint, catch exceptions for logging, or call out.
 *
 * Services are stateless: put mutable state in the request object passed to
 * each method, not in instance fields.
 *
 * Example:
 *
 *     public class AccountMergeService extends BaseService {
 *         public void merge(Id masterId, List<Id> duplicateIds) {
 *             Savepoint sp = beginTransaction();
 *             try {
 *                 ...
 *                 commitTransaction();
 *             } catch (Exception e) {
 *                 rollbackTransaction(sp);
 *                 logAndRethrow('AccountMergeService.merge', e);
 *             }
 *         }
 *     }
 */
public abstract with sharing class BaseService {

    protected Savepoint beginTransaction() {
        return Database.setSavepoint();
    }

    protected void rollbackTransaction(Savepoint sp) {
        if (sp != null) {
            Database.rollback(sp);
        }
    }

    protected void commitTransaction() {
        // Reserved hook — today commit is implicit at transaction end.
        // Override if you need post-commit hooks (e.g. publishing Platform Events
        // via EventBus.TriggerContext) so subclasses have one extension point.
    }

    protected void logAndRethrow(String source, Exception e) {
        ApplicationLogger.error(source, e);
        throw new ServiceException(e.getMessage(), e);
    }

    protected void logAndSwallow(String source, Exception e) {
        ApplicationLogger.error(source, e);
    }

    public class ServiceException extends Exception {}
}
