# Gotchas — Sandbox Post-Refresh Automation

Non-obvious behaviors of the SandboxPostCopy lifecycle. Guide references are line numbers in the v62
PDFs: `apexrefguide` = Apex Reference Guide, `object_reference` = Object Reference, `api_meta` =
Metadata API Developer Guide.

---

## Gotcha 1: `SandboxPostCopy` implementations are written `global`, class and method both

**What happens.** Class declared `public class MyPrep implements SandboxPostCopy`. It compiles. Whether
the post-copy framework will then invoke it is the part nobody can confirm from a failed refresh, because
the failure is silent — the sandbox unlocks either way.

**When it occurs.** Standard Apex habit: `public` is the default reflex, and nothing in the compiler
pushes back.

**How to avoid.** `global class MyPrep implements SandboxPostCopy`, `global void runApexClass(...)`.
Every Salesforce-authored sample uses `global` for both: apexrefguide L228952 (`global class
PrepareMySandbox implements SandboxPostCopy`), L228955 (`global PrepareMySandbox()`), L228975
(`global void runApexClass(SandboxContext context)`).

> UNVERIFIED (2026-09-05): the Apex Reference Guide never states in prose that a `public` implementation
> is rejected, and its member-signature line for the interface method actually reads `public void
> runApexClass(System.SandboxContext context)` (L228926) — documentation convention for describing an
> interface member. `global` is what the working samples use and what this skill recommends; "`public`
> won't satisfy the contract" is inference from those samples, not a sourced statement.

---

## Gotcha 2: `runApexClass` runs ONCE; mid-execution failure leaves sandbox half-prepared

**What happens.** Post-copy class's first method (mask emails) succeeds. Second method (deactivate users)
hits a governor limit. Class throws. Sandbox is unlocked anyway, but only emails are masked; users still
active.

**When it occurs.** Long post-copy classes that exceed sync CPU.

**How to avoid.**
- Make every step idempotent so re-running cleans up.
- Wrap each step in its own try/catch so one failure costs one step, not the whole run.
- For very long work, queue follow-up work via Queueable / Batch. The post-copy class enqueues; the
  queueable does the long work.
- Document the manual re-run. The guide gives it as the intended recovery: "If the script fails, run the
  script after sandbox activation as a user with appropriate permissions" (apexrefguide L228891).

---

## Gotcha 3: Scheduled jobs DO copy from prod to sandbox

**What happens.** Production has a scheduled batch that synchronizes data with an external system every
hour. Sandbox is refreshed; the batch copies. After sandbox unlock, the batch fires — sending
sandbox-side data to the production-pointing integration.

**When it occurs.** Every refresh that doesn't include explicit job-disable in post-copy.

**How to avoid.** `System.abortJob` for every live `CronTrigger` in post-copy (all six live states — see
§ 12). Or selectively for jobs that mutate external state. Verify by re-querying `CronTrigger` after the
sandbox is up; a count of zero is the assertion, not a glance at the Scheduled Jobs page.

> UNVERIFIED (2026-09-05): none of the guides checked for this skill (Apex Reference, Apex Developer,
> Object Reference, Metadata API, App Limits) contains a sentence stating that scheduled jobs are copied
> into a refreshed sandbox. It is a widely-reported behaviour documented on Salesforce Help, which cannot
> be fetched. The *mitigation* — querying `CronTrigger` and calling `System.abortJob` — is fully grounded;
> the copy behaviour itself is not. If your org's refresh produces zero `CronTrigger` rows, this gotcha
> costs you one query and nothing else.

---

## Gotcha 4: Named Credential URLs are not Apex-mutable directly

**What happens.** Post-copy class tries to update a Named Credential's URL via DML; the write does not
take.

**When it occurs.** Implementing endpoint scrubbing in pure Apex.

**How to avoid.** Pre-deploy sandbox-pointing Named Credential metadata as a SEPARATE metadata-deploy
step that runs after the sandbox is unlocked (CI pipeline orchestrates: refresh → wait → deploy NC
metadata → re-run post-copy if needed). Or accept that NCs need manual re-pointing post-refresh. Custom
Settings and Custom Metadata are the mutable alternatives and are what the sample class in
`references/metadata-examples.md` § 1 scrubs.

> UNVERIFIED (2026-09-05): no statement about `NamedCredential` URL write-access appears in the guides
> checked for this skill. The recommendation stands on the deployment shape (Named Credentials are a
> metadata type, and metadata is deployed, not DML'd), not on a quoted sentence.

---

## Gotcha 5: The deliverability Access Level has no Metadata API surface

**What happens.** A team decides to make "System email only" part of the automated post-refresh package,
goes looking for the element in `EmailAdministrationSettings`, and does not find it. The step quietly
becomes "someone will do it in Setup", and then nobody does.

**When it occurs.** Any attempt to put mitigation A (org-wide deliverability restriction) into a deploy
or into the post-copy Apex.

**How to avoid.** Record it as a `manual` step with an owner — the checklist JSON in
`references/metadata-examples.md` § 7 has an `owner` field precisely so this cannot masquerade as
automated. Then do not rely on it alone: email masking is the control you *can* automate, which is why
this skill treats the two as belt-and-suspenders rather than alternatives.

> UNVERIFIED (2026-09-05): the `EmailAdministrationSettings` metadata type's complete field list
> (api_meta L114872–114994) is 19 boolean fields, none of them an access-level enum, and the strings
> "System emails only" / "All email" / "No access" appear nowhere in `api_meta` or `object_reference`.
> Whether Salesforce resets deliverability on refresh — the original form of this gotcha — is likewise
> unsourced in this corpus. Verify the post-refresh value in your own org rather than assuming either way.

---

## Gotcha 6: `SandboxContext.sandboxName()` returns the human-given name

**What happens.** Post-copy logic branches on `context.sandboxName() == 'Dev'`. Admin renames the sandbox
to "Development". Branching breaks silently.

**When it occurs.** Sandbox renames; or org acquisitions where naming conventions differ.

**How to avoid.** Document the names your post-copy class branches on. Add an explicit fallback for
unknown names, and keep the safety steps (mask, abort) **outside** the branch entirely so an unrecognised
name cannot skip them. `SandboxContext` exposes exactly three accessors — `organizationId()`,
`sandboxId()`, `sandboxName()` (apexrefguide L228933–228935) — and `sandboxId()` is the stable one of the
three, though it changes when the sandbox is deleted and recreated rather than refreshed.

---

## Gotcha 7: The post-copy class must already be deployed in production

**What happens.** Admin writes the post-copy class in a sandbox. Refresh runs; the class doesn't exist in
the refreshed sandbox because it was never in prod.

**When it occurs.** First-time deployment of the post-copy infrastructure.

**How to avoid.** Deploy the post-copy class to PRODUCTION first. The sandbox copies it from prod on
refresh. Then bind it to each sandbox — the class is named on the sandbox's own configuration, not
inherited automatically by every sandbox in the org.

---

## Gotcha 8: Test coverage for post-copy classes

**What happens.** SandboxPostCopy class deploys to production but has zero test coverage; deploy fails on
the org-wide 75% threshold.

**When it occurs.** First-time deployment without a test class.

**How to avoid.** Use `Test.testSandboxPostCopyScript` in a test class that invokes the post-copy logic
and asserts each method's side effects. The method has no return value — "This method throws a run-time
exception if the test install fails" (apexrefguide L241178) — so the assertions have to be on state you
query back, not on anything the call hands you.

---

## Gotcha 9: Single-execution semantics — no retry on failure

**What happens.** Post-copy class throws an unhandled exception. The sandbox is unlocked anyway; the
post-copy doesn't re-run automatically. Somebody has to invoke the work manually afterwards.

**When it occurs.** Any unhandled exception during post-copy.

**How to avoid.** Wrap each method in try-catch; log and continue rather than throwing. Document the
re-run procedure in the runbook, and note that the re-run happens under a *different* identity than the
original — see § 10, which is the reason a re-run can succeed where the refresh-time run failed.

---

## Gotcha 10: The script runs as a restricted Automated Process user, not as an admin

**What happens.** The post-copy class queries or updates an object the running identity cannot reach. It
throws, mid-run, on a line that works perfectly when the same admin runs it in anonymous Apex an hour
later. Nothing in the sandbox says why.

**When it occurs.** Any step touching an object or feature outside the Automated Process user's access —
and there is no published list of what that covers, so the first honest signal is a failed refresh.

**How to avoid.** The guide is explicit, and states it twice (apexrefguide L228889–228891, repeated
verbatim at L228946–228948):

> "The SandboxPostCopy Apex class is executed at the end of the sandbox copy using a special Automated
> Process user that isn't visible within the org. This user doesn't have access to all object and
> features; therefore, the Apex script cannot access all objects and features. If the script fails, run
> the script after sandbox activation as a user with appropriate permissions."

Three consequences worth designing for:

1. **Test under that identity, not yours.** Use the 5-arg `Test.testSandboxPostCopyScript` overload with
   `RunAsAutoProcUser = true` (§ 13). A 4-arg test proves nothing about this failure mode.
2. **Guard each step separately** so an access failure on step 2 does not cost you steps 3–6.
3. **Keep the post-activation re-run in the runbook as a first-class path**, not an embarrassment — the
   guide names it as the intended recovery, because the re-run runs as a real user with real permissions.

The user is not visible in Setup, so you cannot inspect or grant its permissions. Design around the
constraint; you cannot configure your way out of it.

---

## Gotcha 11: The copy rewrites Username automatically — Email it leaves alone

**What happens.** Someone reasons that since sandbox usernames come out as `alice@acme.com.uat`,
Salesforce must be sanitising user identity generally, and treats email masking as belt-and-braces.
It is not. `Username` is mutated by the platform; `Email` is copied through verbatim, still routable,
still pointing at a real person.

**When it occurs.** Every refresh, silently. The two fields sit next to each other on the User record and
look like they were treated the same way.

**How to avoid.** Know which half the platform does. api_meta L2711–2713:

> "For example, when you copy data to a sandbox, the fields containing usernames from the production
> organization are altered to include the sandbox name. In a sandbox named `test`, the username
> `user@acme.com` becomes `user@acme.com.test`."

`Email` gets no equivalent treatment, which is the entire reason `maskUserEmail()` exists. Two things
fall out of this:

- **Derive masked emails from `Email`, never from `Username`.** `Username` already carries the sandbox
  suffix; reusing it double-suffixes the address and breaks the reverse mapping you masked *for*.
- **Use the suffix as a safety interlock.** A script about to mask emails or abort jobs can assert that
  the running user's `Username` ends in the expected sandbox suffix. If it does not, you are connected to
  production. This is cheaper than `Organization.IsSandbox` in a Data Loader context, where you have the
  exported usernames in front of you and no Apex.

---

## Gotcha 12: The three-state `CronTrigger` filter misses three more live states

**What happens.** The post-copy aborts everything in `WAITING`, `ACQUIRED`, `EXECUTING` — the three
states everyone knows — and reports success. A job that happened to be `BLOCKED` at that moment survives,
and fires as soon as the instance blocking it finishes.

**When it occurs.** Whenever a second instance of a job was attempted while the first was running
(`BLOCKED`), or when the refresh lands near a Salesforce release window (`PAUSED`, `PAUSED_BLOCKED`).
Release windows are exactly when refreshes get scheduled, so this is not a rare alignment.

**How to avoid.** `CronTrigger.State` has nine documented values (object_reference L86799–86811). Six
mean the job will still run:

| Still live | Documented meaning |
|---|---|
| `WAITING` | "The job is waiting for execution." |
| `ACQUIRED` | "The job has been picked up by the system and is about to execute." |
| `EXECUTING` | "The job is executing." |
| `PAUSED` | "A job can have this state during patch and major releases. After the release has finished, the job state is automatically set to WAITING or another state." |
| `BLOCKED` | "Execution of a second instance of the job is attempted while one instance is running. This state lasts until the first job instance is completed." |
| `PAUSED_BLOCKED` | "A job has this state due to a release occurring. When the release has finished and no other instance of the job is running, the job's status is set to another state." |

`COMPLETE`, `ERROR` and `DELETED` are the only terminal three. `PAUSED` is the trap that reads safe:
the guide says the state resolves back to `WAITING` on its own once the release finishes.

---

## Gotcha 13: The 4-arg `testSandboxPostCopyScript` tests the wrong permissions

**What happens.** The post-copy test passes in CI, deploys, and the refresh fails anyway — on an object
access error the test could never have produced, because the test ran as whoever launched it.

**When it occurs.** Any test written against the 4-arg overload, which is the one most code samples and
most generated code reach for.

**How to avoid.** Use the 5-arg overload. apexrefguide L241180–241184:

> "Salesforce recommends that you use the `testSandboxPostCopyScript(script, organizationId, sandboxId,
> sandboxName, isRunAsAutoProcUser)` overload instead of this method. When `isRunAsAutoProcUser` is true,
> the SandboxPostCopy script is tested with the same user access permissions as used by post-copy tasks
> during sandbox creation."

The guide's own sample test passes `true` (apexrefguide L229004–229006). Combined with § 10, the 4-arg
form is not merely less thorough — it systematically cannot reproduce the single most likely refresh-time
failure. The 5-arg overload is documented at L241191–241228; the parameter is `RunAsAutoProcUser`, and
"when false, the test runs as the test initiator".

---

## Gotcha 14: `abortJob` needs a CronTrigger Id, and does not stop code already running

**What happens.** Two separate surprises from one method. First: the job disappears from the schedule but
its current run keeps going, finishes, and writes to the external system anyway. Second: code that
collected `AsyncApexJob` Ids (the natural thing to query when thinking about "running jobs") fails to
abort scheduled Apex at all.

**When it occurs.** The first every time a job is caught mid-execution — likely, since a refresh unlocks
into a window where hourly jobs are due. The second whenever the job inventory is built from
`AsyncApexJob` rather than `CronTrigger`.

**How to avoid.** Three grounded facts, and one design consequence:

- "The specified job is stopped, but any code that is in progress will continue to execute until it
  completes" (apexrefguide L238662–238663). Aborting is not killing. Assume one more run of anything that
  was `EXECUTING`, and make sure the endpoint scrub (§ 4) has already happened when it lands.
- "The `jobId` is the ID associated with an AsyncApexJob ID for batch or future Apex jobs, or a
  CronTrigger ID for scheduled Apex jobs. You can't abort a scheduled Apex job using an AsyncApexJob ID"
  (apexrefguide L238678–238680).
- `CronTrigger` supports only `describeSObjects()`, `query()`, `retrieve()` (object_reference L86722).
  There is no create, update or delete — so DML against the record is not a fallback when `abortJob`
  throws. `abortJob` is the only write path there is.
- **Order the post-copy steps accordingly.** Scrub endpoints *before* aborting jobs, not after. An
  in-flight job that survives the abort by seconds should find mock endpoints already in place.

---

## Gotcha 15: Custom Settings survive the copy but are invisible to your tests

**What happens.** The post-copy scrubs `Integration_Config__c` correctly. The test written to prove it
sees nothing, asserts against an empty org-default row, and passes for the wrong reason — or fails
confusingly on a `null`.

**When it occurs.** Testing any post-copy step that rewrites Custom Settings data, which is the main
Apex-mutable endpoint-scrub path (§ 4).

**How to avoid.** Apex Developer Guide L13514–13516: "While custom settings data is included in sandbox
copies, it is treated as data for the purposes of Apex test isolation. Apex tests must use
`SeeAllData=true` to see existing custom settings data in the organization." So either annotate the test
`@IsTest(SeeAllData=true)`, or — better — have the test insert its own org-default row in setup and
assert the scrub overwrote *that*. The second keeps the test hermetic and still exercises the branch.

Note the asymmetry this creates: the setting's data reaches the sandbox by copy, but no test you write
under default isolation can observe the copied value. The scrub is verified by the post-refresh query in
`references/metadata-examples.md` § 8, not by the test class.
