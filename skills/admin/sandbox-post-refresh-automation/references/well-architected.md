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

- **Mask emails vs `System emails only` deliverability.** Both
  are mitigations; both are recommended. Email masking protects
  against deliverability misconfiguration; deliverability protects
  against unmasked records (newly-created users in the sandbox).
- **`global class` vs internal helpers.** The interface
  implementation must be `global`, but the helper methods can be
  `private static`. Keep the public surface minimal.
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

## Official Sources Used

- SandboxPostCopy Interface — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_interface_System_SandboxPostCopy.htm
- Test.testSandboxPostCopyScript — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_methods_system_test.htm#apex_System_Test_testSandboxPostCopyScript
- Sandbox Refresh Considerations — https://help.salesforce.com/s/articleView?id=sf.data_sandbox_create.htm&type=5
- Email Deliverability Settings — https://help.salesforce.com/s/articleView?id=sf.emailadmin_deliverability.htm&type=5
- CronTrigger Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_crontrigger.htm
- Sibling skill (sandbox strategy) — `skills/devops/sandbox-strategy-designer/SKILL.md`
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
