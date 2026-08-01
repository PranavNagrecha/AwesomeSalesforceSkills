# Well-Architected Notes — OmniStudio Asynchronous Data Operations

**Scalability, but only for the right cause:** asynchrony is the correct answer when the
latency is one genuinely slow external system and the wrong answer when it is N calls that
could be one, a repeated lookup, or a transform in the wrong layer. Moving those costs across
a transaction boundary preserves every one of them and adds a status object, a polling loop
and a failure mode that reaches nobody. Measure before restructuring: the fastest
asynchronous procedure is still slower than the synchronous one you no longer need.

**Scalability, the limit that actually binds:** an Integration Procedure's HTTP actions run
inside an Apex transaction, so the numbers that govern them are Apex callout limits — a
default 10-second timeout, a per-callout maximum of 120,000 milliseconds, a cumulative
120-second allowance across all callouts in the transaction, and a maximum of 100 callouts.
The cumulative figure is additive, which is why raising individual timeouts moves a failure
later rather than removing it, and why concurrency does not create allowance that was not
there.

**Reliability:** the moment a step leaves the caller's transaction, its failure leaves the
caller's error path. The caller has already returned successfully, so nothing propagates to
the user, to the OmniScript's error branch, or to any alert wired to the synchronous flow.
Asynchronous work needs its own durable failure record and its own alerting, and the status
endpoint has to be able to answer "failed" — a poll that can only say "not yet" turns every
failure into an infinite spinner.

**User Experience:** the response contract changes, and skipping that is what makes an async
migration look like a regression. The synchronous response no longer carries the value the
step produced, so any consumer still reading that path now reads nothing. "Not computed yet"
and "empty" have to be distinguishable states, or every slow request presents to the user as
a data defect.

**Performance, and the cost of getting caching wrong:** caching is the cheapest available
latency fix, and its failure mode is a stale read immediately after a successful write —
which the user interprets as their change not saving, so they repeat it. The safe candidates
are values no user can change in-session; for anything both expensive and volatile, narrowing
what is cached beats shortening how long it lives.

**Observability:** once work spans transactions, "did that step run" is not answerable from
the user's session, and it will be asked after the session has ended. A correlation id
generated at the synchronous entry point and carried through every chained step and the status
record costs one field and one parameter, and it is the difference between reconstructing a
failure and guessing at it.

## Official Sources Used

- Callout Limits and Limitations — the 10-second default, 120,000 ms per-callout maximum, cumulative 120-second transaction allowance and 100-callout ceiling that bound an Integration Procedure's HTTP actions — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_callouts_timeouts.htm
- Settings for Long-Running Integration Procedures — the configuration surface for procedures that exceed a synchronous budget — https://help.salesforce.com/s/articleView?id=sf.os_settings_for_long_running_integration_procedures_56206.htm&type=5
- Invoke a Chainable Integration Procedure with REST Calls — the chaining mechanism and what the caller receives — https://help.salesforce.com/s/articleView?id=sf.os_invoke_a_chainable_integration_procedure_with_rest_calls_56330.htm&type=5
- Cache for Omnistudio Data Mappers and Integration Procedures — the caching surface and what it applies to — https://help.salesforce.com/s/articleView?id=sf.os_cache_for_dataraptors_and_integration_procedures_48057.htm&type=5
- Integration Procedure Actions — the action types, and the blocks used for conditional execution, caching, list processing and error handling — https://help.salesforce.com/s/articleView?id=sf.os_integration_procedure_actions_50165.htm&type=5
- Common Integration Procedure Action Properties — the per-action properties that govern execution — https://help.salesforce.com/s/articleView?id=sf.os_common_integration_procedure_action_properties_50188.htm&type=5
