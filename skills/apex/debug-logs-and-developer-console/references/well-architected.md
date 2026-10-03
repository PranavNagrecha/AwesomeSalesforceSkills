# Well-Architected Notes: Debug Logs And Developer Console

## Relevant Pillars

- **Operational Excellence**: Debug logs and the Developer Console are the primary instruments for diagnosing Apex behavior during development and targeted troubleshooting. Tracing the right entity (user, Automated Process, or an overridden trigger user), short windows, and scripted trace flag setup cut the time to a usable log.

- **Reliability**: Misusing debug tooling introduces risk. More than 1,000 MB of logs in 15 minutes disables trace flags, a trace flag on a frequently accessed class or busy user can make requests fail, and anonymous Apex commits everything once the block succeeds. Knowing these limits prevents incidents caused by debugging itself.

- **Security**: Apex Code at FINEST logs every variable assignment. Keep FINEST away from code that handles passwords, tokens, or personal data, and treat downloaded logs as sensitive files.

## Architectural Tradeoffs

**Debug verbosity vs. log completeness:** Higher verbosity captures more detail but logs over 20 MB lose older lines from any location. Apex Code DEBUG is enough for most work; raise one class with a `CLASS_TRACING` trace flag instead of raising the whole log.

**Developer Console vs. VS Code and the sf CLI:** The Developer Console needs no local tooling and is quick for queries, anonymous Apex, and log review, but its levels apply to all logs while it is open, including deployment logs. VS Code and the CLI give repeatable trace flag scripts (`sf data create record --use-tooling-api`), `sf apex tail log`, and the Replay Debugger.

**Trace flag scope:** A user trace flag logs that user's requests. Automated Process covers platform event triggers, event processes, resumed flow interviews, and publish callbacks. A class or trigger trace flag only changes levels and never creates a log on its own. Combine a narrow entity flag with a class flag for focused detail.

## Anti-Patterns

1. **Leaving FINEST trace flags active across long sessions**: logs grow toward the 20 MB cap and the org toward the 1,000 MB limits that disable or block trace flags. Keep windows short and delete flags and large logs when done.

2. **Using anonymous Apex in production for data fixes without sandbox validation**: it cannot be undone once committed and leaves no deployment record. Test in a sandbox with a dry-run flag, check counts, and make the fix idempotent.

3. **Relying on the Developer Console as the primary IDE**: it has no version control or deployment validation. Use VS Code with Salesforce Extensions for authoring; use the Developer Console for inspection and ad-hoc queries.

## Official Sources Used

- Apex Developer Guide, Summer '26 (262): "Debug Log," "Debug Log Limits," debug log sections and header warning, "Debug Log Categories," "Debug Log Levels," "Debug Event Types," "Setting Debug Log Filters for Apex Classes and Triggers," "Debug Log Order of Precedence," "Anonymous Blocks," sharing implementation details, Per-Transaction Apex Limits. https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf
- Tooling API Developer Guide, Summer '26 (262): "TraceFlag" (`LogType`, `TracedEntityId`, `StartDate`, `ExpirationDate`), "DebugLevel," "ApexLog." https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_tooling.pdf
- Platform Events Developer Guide, Summer '26 (262): "Set Up Debug Logs for Event Subscriptions," Automated Process trace flag steps, publish callback running user. https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/platform_events.pdf
- Salesforce CLI Command Reference, Summer '26 (262): `apex run`, `apex tail log`, `apex get log`, `apex list log`, `data create record --use-tooling-api`. https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/sfdx_cli_reference.pdf

### Earlier references kept from version 1.0.0 (checked 2026-10-03: atlas pages return a script shell, help.salesforce.com returns an app shell, and Well-Architected guide pages redirect to the home page, so no claim in this skill rests on these links)

- Apex Developer Guide (atlas home): https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_dev_guide.htm
- Apex Reference Guide (atlas home): https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_ref_guide.htm (`System.debug`, `LoggingLevel`)
- Salesforce Well-Architected Overview: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html (Well-Architected guide pages redirect to the home page)
