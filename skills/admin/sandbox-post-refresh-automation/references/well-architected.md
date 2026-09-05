# Well-Architected Notes — Sandbox Post-Refresh Automation

## Relevant Pillars

- **Reliability** — Idempotent post-copy means refreshes are safe
  to re-run when something fails mid-step. Non-idempotent code
  (delete-everything, then create) breaks on second invocation.
- **Security** — Email masking, integration-endpoint scrubbing,
  and scheduled-job disable are security controls. Without them,
  sandbox developers can fire real emails, hit production
  endpoints, or trigger production jobs.
- **Operational Excellence** — Codifying the manual checklist as
  Apex makes the post-refresh procedure runbook-as-code. Every
  refresh applies the same recipe; nothing is forgotten because
  someone was on PTO.

## Architectural Tradeoffs

- **Mask emails vs the deliverability Access Level.** Both are mitigations; both are recommended, but
  they are not peers. Masking is Apex, deployable, testable and idempotent. The Access Level has no
  `EmailAdministrationSettings` field (api_meta L114872–114994) and so is a manual Setup action forever.
  Design as though only the automatable half will reliably happen, and treat the manual half as the
  thing that catches users created *after* the mask ran.
- **Automated Process user vs post-activation re-run.** The hook runs before anyone can log in — its
  entire value — but under an identity with partial object access (apexrefguide L228889–228891). A step
  that needs broad permissions has to move to a pipeline stage after activation, which reopens the
  window the hook exists to close. Put the safety steps (mask, abort) in the hook and the
  permission-hungry ones (reseed, config) in the pipeline; do not split them the other way round for
  convenience.
- **Abort everything vs allow-list.** Aborting every live `CronTrigger` is one query and provably
  complete; it also kills the jobs sandbox testing needs. An allow-list is safer for testers and leaks
  whatever nobody thought to name. Prefer abort-all plus an explicit, reviewed re-schedule step — the
  failure mode is then "a tester files a ticket", not "a batch wrote to production".
- **`global class` vs internal helpers.** The interface
  implementation must be `global`, but the helper methods can be
  `private static`. Keep the public surface minimal.
- **Sync mask vs Queueable chain, decided on row count.** The post-copy runs in one synchronous
  transaction, so masking, deactivation and the job sweep share a single set of governor limits. Below a
  few thousand active users the inline loop is right. Above that, the post-copy should enqueue and the
  Queueable should chunk — accepting that the sandbox is briefly unlocked with the work unfinished.
- **Single `runApexClass` vs Queueable chain.** Single is simpler
  but governor-bound. Queueable chain handles long work but adds
  complexity and the post-copy isn't "done" until the chain
  finishes. Use Queueable only when post-copy genuinely exceeds
  sync governors.
- **In-Apex endpoint scrub vs metadata-deploy scrub.** Apex can
  rewrite Custom Settings and Custom Metadata. Named Credentials
  need a metadata deploy. Many orgs combine: Apex post-copy +
  CI pipeline metadata deploy.

## Anti-Patterns

1. **`public` instead of `global` for the class / method.**
   Compiles but interface implementation isn't recognized.
2. **Non-idempotent operations.** Re-runs corrupt state
   (`alice+sandbox+sandbox@...` etc.).
3. **Forgetting to abort scheduled jobs.** Production batches
   fire in sandbox post-refresh.
4. **No fallback when `SandboxContext.sandboxName()` is unknown.**
   Hardcoded if/else with no default; new sandbox names silently
   skip the prep.
5. **No test class.** Deploy fails on org-wide test coverage.
6. **Class deployed only in sandbox, not production.** Refresh
   copies from prod; sandbox-only class is gone post-refresh.
7. **Testing with the 4-arg `testSandboxPostCopyScript`.** Runs as the test initiator, so it cannot
   surface the restricted-user access failures the refresh will hit.
8. **A `CronTrigger` sweep that filters on three states.** `PAUSED`, `BLOCKED` and `PAUSED_BLOCKED`
   are live.
9. **Aborting jobs before scrubbing endpoints.** `abortJob` lets in-flight code run to completion; it
   should complete against mocks, not production.
10. **A checklist with steps but no owner or verification.** The unautomatable steps quietly become
   nobody's, and "we ran the post-copy" replaces "the query returned zero".

## Official Sources Used

- **Apex Reference Guide (v62 PDF), `SandboxPostCopy` Interface, L228876–229016** — the Automated Process
  user execution context and its access restriction (L228889–228891, repeated L228946–228948); the
  mandatory no-arg constructor (L228955–228960); `SandboxContext`'s three accessors (L228933–228935);
  the sample implementation and sample test that this skill's artefacts are shaped from (L228949–229015).
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf
- **Apex Reference Guide, `Test.testSandboxPostCopyScript`, L241140–241228** — the 4-arg signature and
  its "throws a run-time exception if the test install fails" note (L241178), and the recommendation to
  use the 5-arg `RunAsAutoProcUser` overload instead (L241180–241184, L241191–241228). Supports gotcha
  § 13 and `references/metadata-examples.md` § 2.
- **Apex Reference Guide, `System.abortJob`, L238661–238698** — "any code that is in progress will
  continue to execute until it completes" (L238662–238663) and "You can't abort a scheduled Apex job
  using an AsyncApexJob ID" (L238678–238680). Supports gotcha § 14 and the scrub-before-abort ordering.
- **Object Reference (v62 PDF), `CronTrigger`, L86710–86844** — the nine `State` values with their
  verbatim definitions (L86799–86811), supported calls `describeSObjects(), query(), retrieve()` with no
  DML (L86722), and `CronJobDetail.JobType` codes (L86671–86680). Supports gotchas § 12 and § 14 and the
  inventory SOQL in `references/metadata-examples.md` § 4.
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf
- **Object Reference, `Organization.IsSandbox`, L205411–205417** — "Read-only. Indicates whether the
  current organization is a sandbox (true) or production (false) instance. Available in API version 31.0
  or later." Supports the third verification query in `references/metadata-examples.md` § 8.
- **Metadata API Developer Guide (v62 PDF), L2711–2713** — the sandbox `Username` suffix mutation, which
  is the grounding for gotcha § 11 and the Data Loader safety interlock.
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- **Metadata API Developer Guide, `EmailAdministrationSettings`, L114848–115022** — the file suffix
  (`EmailAdminstration.settings`, misspelled in the guide, L114854), version 47.0+ (L114866), and the
  complete 19-field table that contains no deliverability access-level element. Supports gotcha § 5 and
  `references/metadata-examples.md` § 6.
- **Apex Developer Guide (v62 PDF), L13512–13516** — "While custom settings data is included in sandbox
  copies, it is treated as data for the purposes of Apex test isolation. Apex tests must use
  SeeAllData=true..." Supports gotcha § 15.
- **Data Loader Guide (v62 PDF), L351–360** — import batch size limits and Bulk API 2.0 behaviour, for
  the manual masking fallback in `references/metadata-examples.md` § 5.
- **Sibling skill (sandbox strategy)** — `skills/admin/sandbox-strategy/SKILL.md`, for tier and cadence
  decisions this skill deliberately excludes.
- **Salesforce Well-Architected Overview** — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html

Sources deliberately *not* cited, because they could not be verified: Salesforce Help articles on
sandbox refresh behaviour and email deliverability (help.salesforce.com is unfetchable from this
environment), and the Tooling API Developer Guide for `SandboxInfo` / `SandboxProcess` field names. Every
claim resting on those is marked UNVERIFIED (2026-09-05) at the point of use.
