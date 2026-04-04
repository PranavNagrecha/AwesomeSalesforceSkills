# Well-Architected Notes — Custom Logging and Monitoring

## Relevant Pillars

- **Operational Excellence** — Custom logging is the foundation of production observability. Without persistent logs, diagnosing production incidents requires synchronizing debug log capture with the incident — which is rarely possible. A custom log framework makes the production system self-documenting at all times.
- **Reliability** — Rollback-safe logging via Platform Events ensures that failure events are captured even when the surrounding transaction fails. This is critical for diagnosing repeated failures in batch jobs, integration callbacks, and complex trigger chains.
- **Security** — Log records may capture sensitive data in the Message field. Access to the `Log__c` object should be restricted via permission sets. The log framework should sanitize or mask sensitive field values (credit card numbers, SSNs, tokens) before logging.

## Architectural Tradeoffs

**Direct DML vs. Platform Events:** Direct DML is simpler and has lower latency. Platform Events add a subscription trigger and a small delay but survive transaction rollback. Use PE for ERROR-level logs; use direct DML for INFO/WARN where rollback safety is less critical.

**In-process buffering vs. immediate insert:** Buffering reduces DML statement count (essential for trigger handlers processing bulk records). Immediate insert is simpler but hits governor limits in high-volume contexts. Buffer + flush() is the production-safe pattern.

**Log retention length:** Longer retention = more storage consumed. Shorter retention = less operational history available. Balance by using shorter retention for DEBUG/INFO (days to weeks) and longer retention for ERROR (months) to preserve incident history.

## Anti-Patterns

1. **Per-record DML logging without buffering** — Exceeds DML governor limits in bulk contexts. Always buffer and flush.
2. **Logging sensitive data in Message field** — Log records are accessible to any user with Log__c object read access. Sanitize PII and secrets before logging.
3. **Not scheduling the LogPurger** — Without purge, the Log__c table grows unbounded, consuming data storage and degrading query performance over months.

## Official Sources Used

- Apex Reference Guide — LoggingLevel Enum — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_enum_System_LoggingLevel.htm
- Platform Events Developer Guide — Handling Rollbacks with Platform Events — https://developer.salesforce.com/docs/atlas.en-us.platform_events.meta/platform_events/platform_events_intro.htm
- REST API Developer Guide — EventLogFile — https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/dome_event_log_file_query.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/well-architected/overview
