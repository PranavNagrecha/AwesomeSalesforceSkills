/**
 * ApplicationLogger — standard façade over `Application_Log__c`.
 *
 * Replaces `System.debug` for any code path that must be queryable in
 * production. Reads `Logger_Setting__mdt.Minimum_Severity__c` so verbosity
 * is configurable per org without redeployment.
 *
 * Usage:
 *
 *     ApplicationLogger.error('AccountMergeService.merge', e);
 *     ApplicationLogger.warn('OrderSync', 'Stale price book version for order ' + order.Id);
 *     ApplicationLogger.info('NightlyRefresh', 'Processed ' + n + ' records');
 *     ApplicationLogger.flush();   // call in finally{} blocks for long-running work
 */
public with sharing class ApplicationLogger {

    public enum Severity { DEBUGL, INFOL, WARN, ERROR, FATAL }

    @TestVisible private static List<Application_Log__c> buffer = new List<Application_Log__c>();
    @TestVisible private static Severity minimumSeverity;

    public static void debugL(String source, String message)       { log(Severity.DEBUGL, source, message, null); }
    public static void info(String source, String message)         { log(Severity.INFOL,  source, message, null); }
    public static void warn(String source, String message)         { log(Severity.WARN,   source, message, null); }
    public static void error(String source, String message)        { log(Severity.ERROR,  source, message, null); }
    public static void error(String source, Exception e)           { log(Severity.ERROR,  source, e == null ? 'null exception' : e.getMessage(), e); }
    public static void fatal(String source, String message)        { log(Severity.FATAL,  source, message, null); }

    public static void log(Severity severity, String source, String message, Exception cause) {
        if (severity.ordinal() < getMinimumSeverity().ordinal()) {
            return;
        }
        Application_Log__c entry = new Application_Log__c(
            Severity__c     = severity.name(),
            Source__c       = source == null ? 'Unknown' : source.left(255),
            Message__c      = (message == null ? '' : message).left(32768),
            Stack_Trace__c  = cause == null ? null : cause.getStackTraceString().left(32768),
            Exception_Type__c = cause == null ? null : cause.getTypeName(),
            Quiddity__c     = String.valueOf(System.Request.getCurrent().getQuiddity()),
            Request_Id__c   = System.Request.getCurrent().getRequestId(),
            Running_User__c = UserInfo.getUserId()
        );
        buffer.add(entry);
        if (severity.ordinal() >= Severity.ERROR.ordinal()) {
            flush();
        }
    }

    public static void flush() {
        if (buffer.isEmpty()) { return; }
        try {
            insert buffer;
        } catch (DmlException e) {
            System.debug(LoggingLevel.ERROR, 'ApplicationLogger.flush failed: ' + e.getMessage());
        } finally {
            buffer.clear();
        }
    }

    @TestVisible
    private static Severity getMinimumSeverity() {
        if (minimumSeverity != null) { return minimumSeverity; }
        Logger_Setting__mdt setting = Logger_Setting__mdt.getInstance('Default');
        if (setting == null || String.isBlank(setting.Minimum_Severity__c)) {
            minimumSeverity = Severity.INFOL;
        } else {
            try {
                minimumSeverity = Severity.valueOf(setting.Minimum_Severity__c.toUpperCase());
            } catch (Exception e) {
                minimumSeverity = Severity.INFOL;
            }
        }
        return minimumSeverity;
    }
}
