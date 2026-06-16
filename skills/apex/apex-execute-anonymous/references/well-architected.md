# Well-Architected Notes — Apex Execute Anonymous

## Relevant Pillars

Execute Anonymous is the rare Salesforce tool whose architectural
fitness is almost entirely a question of **Operational Excellence**.
The mechanics (a one-shot script that compiles, runs, returns) are
trivial; the discipline question is *whether reaching for it is a
healthy signal or a smell* given what the work actually is.

- **Operational Excellence** — Anonymous Apex is the right tool when
  the work is genuinely one-off and the alternative is heavier
  (deploying a class for a fix that will never run again). It is
  the wrong tool when the work is recurring, large-volume, or
  needs an audit trail. The architectural failure mode is "the
  permanent script" — an anonymous block that, by being convenient,
  becomes load-bearing infrastructure no one inspects. Healthy
  practice: a `scripts/` directory in the source repo, peer review
  for prod runs, savepoint + dry-run discipline by default.
- **Reliability** — Anonymous executions don't surface in
  `AsyncApexJob`, `CronTrigger`, or any Setup screen an admin would
  audit. A script that silently fails (governor limit, permission
  error, locked row) doesn't alert anyone unless the engineer
  watching the CLI catches it. Reliability comes from explicit
  partial-success handling (`Database.update(records, false)` plus
  per-row `SaveResult` inspection) and from refusing to use anonymous
  for anything that needs to "just run" without a human present.
- **Security** — Anonymous runs as the executing user with full
  sharing/CRUD/FLS enforcement, which is *good* — the platform
  doesn't give you a way to escalate from inside a script. The
  security concern is the inverse: scripts written by an admin
  often assume admin-level permissions and break (silently, via
  zero-row SOQL results) when run by a different user. Audit who
  has the License + Permission to run Anonymous Apex in prod
  (typically the "Author Apex" perm) — it's a powerful gate that
  many orgs leave open to too many users.
- **Performance** — Per-execution governor limits apply identically
  to anonymous and to triggers. There is no "script mode" with extra
  headroom. Performance discipline = bulkification (build collections,
  DML once outside the loop) and bounded SOQL (`LIMIT` on every
  query). Beyond ~10,000 records of work, anonymous is the wrong
  tool — Batch Apex is.

## Architectural Tradeoffs

The defining choice is **which tool to use for the kind of work in
front of you**. The five live options have meaningfully different
profiles:

| Dimension                | Execute Anonymous            | Scheduled Apex (`Schedulable`)        | Batch Apex (`Database.Batchable`)     | LWC Quick Action / Custom Button       | Workbench / Data Loader                 |
|--------------------------|------------------------------|----------------------------------------|----------------------------------------|----------------------------------------|------------------------------------------|
| Recurrence               | One-off only                 | Cron-scheduled                         | One run, but volume-tolerant           | User-invoked, recurring                | One-off bulk, user-invoked               |
| Audit trail              | Debug log (7-day) only       | `CronTrigger`, `AsyncApexJob`          | `AsyncApexJob`, optional `BatchApexErrorEvent` | UI action history, FieldHistory     | Loader log files + Bulk API job status   |
| Volume ceiling           | ~10k records/transaction     | Per-tx limits per execution            | Effectively unbounded (chunked)        | Per-tx limits per click                | Hundreds of thousands (Bulk API)         |
| Code review path         | `scripts/` PR (if disciplined) | Standard class deploy + tests          | Standard class deploy + tests          | LWC/Apex deploy + tests                | Field-mapping doc + sandbox dry-run      |
| User-invocable           | Engineer with Author Apex    | Triggered by cron, not user            | Triggered by cron or call              | Any user with button access            | Admin / data steward                     |
| Failure visibility       | Debug log only               | `AsyncApexJob.NumberOfErrors`          | `AsyncApexJob` + `BatchApexErrorEvent` | Toast + page reload                    | CSV error file, row-level                |
| Time-to-build            | Minutes                      | Hours (class + test + schedule)        | Hours (class + test + schedule)        | Hours-to-days (UI + class + test)      | Minutes (mapping)                        |
| Right when               | True one-off correction      | Recurring on a clock                   | Recurring at volume                    | Recurring user-initiated workflow      | Bulk insert/update of external data      |
| Wrong when               | Anything recurring           | Tiny volume, very rare run             | Single small batch                     | Background / scheduled work            | Logic-heavy transformations              |

Two boundary cases are worth flagging:

- **Anonymous Apex vs LWC quick action with Apex backing.** If the
  fix needs to be re-runnable by non-developers (e.g., "support reps
  click a button to merge duplicate customer records"), the
  one-time cost of building an LWC + invocable Apex pays back in
  audit trail and self-service. Anonymous Apex is the wrong stopping
  point for "this might recur."
- **Anonymous Apex vs Workbench/Data Loader bulk update.** For pure
  field-value changes with no logic ("set every Closed-Won Opportunity
  with ARR > $100k to a new Tier"), exporting a CSV → editing in
  Excel → Data Loader upsert is often safer than an anonymous script,
  because the staged CSV is human-reviewable and the Bulk API surfaces
  per-row errors in a structured way. Use anonymous when the *logic*
  is more complex than a value substitution.

## Anti-Patterns

1. **The "permanent one-off."** A script that runs on a calendar
   reminder because converting it to `Schedulable` "isn't worth the
   effort." It accumulates engineer-specific dependencies (whose
   laptop has the latest version, whose token authenticates which
   org) and silently breaks when the engineer rotates off the team.
   Convert anything that runs more than twice on a cadence to a
   deployed `Schedulable` or `Batchable`.
2. **Unbounded SOQL + DML in production.** `SELECT Id FROM Account
   WHERE Industry = 'Tech'` with no `LIMIT`, followed by an update.
   On any sufficiently large org, this either hits the 50,000-row
   query cap (some rows silently ignored) or the 10,000-DML-row cap
   (partial-commit then rollback at row 10,001). Always bound, and
   always page through deliberately.
3. **DML without a savepoint or dry-run toggle.** Anonymous commits
   on success — there is no "are you sure?" prompt. A typo in the
   filter clause is one click away from updating every record in
   the org. Default posture: `Boolean APPLY = false;` at the top,
   `if (APPLY) update records;` at the bottom, plus a
   `Database.setSavepoint` / `Database.rollback` pair around the
   whole block.
4. **Treating successful enqueue as successful execution.**
   `Database.executeBatch(...)` or `System.enqueueJob(...)` inside
   anonymous returns the job ID, and the script exits with
   `success: true`. The async work has not yet started, let alone
   completed. Pipelines that need to confirm the work finished must
   poll `AsyncApexJob` separately or subscribe to a completion
   Platform Event the batch publishes.
5. **Running scripts directly against the default org.** `sf apex run
   --file fix.apex` (no `--target-org`) uses whatever org happens to
   be the default — which on a typical engineer's laptop alternates
   between three sandboxes and prod over the course of a day. Make
   `--target-org <alias>` mandatory for any script with DML, and add
   a confirmation prompt in the script itself for prod aliases.

## Official Sources Used

- Apex Developer Guide — Anonymous Blocks:
  https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_anonymous_block.htm
- Apex Developer Guide — Execute Anonymous Apex:
  https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_execute_anonymous.htm
- Salesforce DX Developer Guide — Execute Anonymous Apex:
  https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_develop_apex_run_anon.htm
- Salesforce CLI Command Reference — `sf apex` commands:
  https://developer.salesforce.com/docs/atlas.en-us.sfdx_cli_reference.meta/sfdx_cli_reference/cli_reference_apex_commands_unified.htm
- Tooling API Developer Guide — REST Resources (includes
  `executeAnonymous`):
  https://developer.salesforce.com/docs/atlas.en-us.api_tooling.meta/api_tooling/intro_rest_resources.htm
- Tooling API Developer Guide — Introducing Tooling API:
  https://developer.salesforce.com/docs/atlas.en-us.api_tooling.meta/api_tooling/sforce_api_tooling.htm
- SOAP API Developer Guide — `ExecuteAnonymousResult` (response
  shape mirrored by the REST endpoint):
  https://developer.salesforce.com/docs/atlas.en-us.api.meta/api/sforce_api_calls_executeanonymous_result.htm
- Salesforce Well-Architected — Operationally Excellent:
  https://architect.salesforce.com/well-architected/trusted/well-managed
