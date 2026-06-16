# Examples — Apex Execute Anonymous

Two worked scenarios and one anti-pattern showing how to ship an
anonymous Apex script that's safe enough to point at production —
either through the CLI or through the Tooling API REST endpoint.

---

## Example 1: One-shot data correction via `sf apex run -f script.apex`

**Context:** A botched data import set `BillingCountry = 'United States'`
on roughly 8,000 Accounts that should be `'USA'` (the picklist value
your validation rules and routing logic expect). The bad rows have
`Description` containing the import batch ID `IMPORT-2026-04-22-A`,
so they're identifiable. You have ~3 hours before the next nightly
territory rebuild, so you need to fix this in one window — but
without nuking unrelated `BillingCountry` edits a human made after
the import.

**Problem:** Issuing an unguarded `update accs` against 8,000 rows
in a single anonymous block burns through the per-transaction DML
row limit (10,000 — close but not infinite headroom), and any
single bad row (a `BillingState`/`BillingCountry` integrity rule
firing, a Validation Rule blocking the change, a row locked by
another transaction) blows up the whole DML and rolls back every
"correct" change with it. The script then reports "Update failed
on 1 of 8,000" and leaves you guessing which row.

**Solution:** Bound the query with `LIMIT`, batch by ID range,
and use `Database.update(records, false)` so a single bad row
fails *just that row* and the rest commit. Wrap in a savepoint
so you can dry-run end-to-end before you flip the apply flag.

```apex
// scripts/fix-billing-country-IMPORT-2026-04-22-A.apex
Boolean APPLY = false;                          // flip to true to commit
String BATCH_TAG = 'IMPORT-2026-04-22-A';
Integer PAGE_SIZE = 2000;                       // 10k DML row limit / 5 safety

Savepoint sp = Database.setSavepoint();
List<Account> accs = [
    SELECT Id, BillingCountry
    FROM Account
    WHERE BillingCountry = 'United States'
      AND Description LIKE :('%' + BATCH_TAG + '%')
    LIMIT :PAGE_SIZE
];

for (Account a : accs) {
    a.BillingCountry = 'USA';
}

Database.SaveResult[] results = Database.update(accs, false);  // allOrNone=false
Integer ok = 0, failed = 0;
for (Integer i = 0; i < results.size(); i++) {
    if (results[i].isSuccess()) {
        ok++;
    } else {
        failed++;
        System.debug(LoggingLevel.ERROR,
            'Row ' + accs[i].Id + ' failed: ' + results[i].getErrors()[0].getMessage()
        );
    }
}
System.debug('Page size: ' + accs.size() + ' | success: ' + ok + ' | failed: ' + failed);

if (!APPLY) {
    Database.rollback(sp);
    System.debug('DRY RUN — rolled back. Set APPLY=true to commit.');
}
```

**Running it:**

```bash
sf apex run --target-org prod-pranav --file scripts/fix-billing-country-IMPORT-2026-04-22-A.apex
```

The CLI prints the debug log inline. Look for the `USER_DEBUG` lines
to see counts and per-row failure messages. Re-run with `APPLY=true`
once the dry run looks clean. For 8,000 rows you'll loop the script
four times (each pass picks up the next 2,000 because the previous
ones no longer match `BillingCountry = 'United States'`).

**Why it works:**

- `Database.update(records, false)` is the partial-success form —
  failed rows don't roll back successful ones in the same call.
  Read `Database.SaveResult[]` to surface the per-row error so you
  know exactly which IDs to investigate.
- `LIMIT :PAGE_SIZE` keeps the script comfortably inside the
  10,000-DML-row-per-transaction governor cap.
- The `if (!APPLY) Database.rollback(sp)` toggle lets the *exact*
  script you'll commit be tested end-to-end (including failure
  paths) without mutating data.
- `LoggingLevel.ERROR` on the per-row failure log line means it
  survives even when the org's debug-log filter trims `DEBUG`
  output — critical because the failure rows are the part you
  need to keep.

---

## Example 2: Remote execution via Tooling API REST `executeAnonymous`

**Context:** A CI pipeline needs to verify, after every sandbox
refresh, that the data-seeding step ran (e.g., "there are at
least 50 active Users with `Profile.Name = 'Sales User''"). The
pipeline can't install a managed package or deploy a class, and
it has an OAuth access token for the org. The check is a single
SOQL query plus a `System.assert`.

**Problem:** You can't deploy a class as part of the sanity check
(the CI box is read-only against the org by design). The
`/services/data/vXX.0/query/` endpoint can run the SOQL, but
shell-pipelining "did the count exceed 50" logic into a one-liner
is fragile. Anonymous Apex via Tooling REST runs arbitrary Apex
without persisting metadata — perfect for ephemeral checks.

**Solution:** POST the URL-encoded Apex to the Tooling REST
`executeAnonymous` endpoint and parse the JSON response.

```bash
#!/bin/bash
# scripts/verify-sales-users.sh
ORG_URL="https://your-sandbox.my.salesforce.com"
TOKEN="$SF_ACCESS_TOKEN"        # OAuth bearer token

APEX='Integer n = [SELECT COUNT() FROM User WHERE IsActive = true AND Profile.Name = '\''Sales User'\''];
System.assert(n >= 50, '\''Expected >= 50 Sales Users, found '\'' + n);
System.debug('\''Sales User count: '\'' + n);'

# URL-encode the Apex body (jq -sRr @uri is the portable form)
ENCODED=$(printf '%s' "$APEX" | jq -sRr @uri)

curl -s -X GET \
  "${ORG_URL}/services/data/v62.0/tooling/executeAnonymous/?anonymousBody=${ENCODED}" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Accept: application/json" \
  | tee /tmp/exec-result.json
```

A representative successful response:

```json
{
  "line": -1,
  "column": -1,
  "compiled": true,
  "success": true,
  "compileProblem": null,
  "exceptionStackTrace": null,
  "exceptionMessage": null
}
```

A representative failure response (assertion blew up):

```json
{
  "line": 2,
  "column": 1,
  "compiled": true,
  "success": false,
  "compileProblem": null,
  "exceptionStackTrace": "AnonymousBlock: line 2, column 1",
  "exceptionMessage": "System.AssertException: Assertion Failed: Expected >= 50 Sales Users, found 12"
}
```

And a compile failure (syntax error in the Apex body):

```json
{
  "line": 1,
  "column": 47,
  "compiled": false,
  "success": false,
  "compileProblem": "unexpected token: 'WHEREE'",
  "exceptionStackTrace": null,
  "exceptionMessage": null
}
```

**Pipeline gate logic:**

```bash
if jq -e '.compiled == true and .success == true' /tmp/exec-result.json > /dev/null; then
  echo "PASS"
  exit 0
else
  jq -r '
    if .compiled == false then "COMPILE: \(.compileProblem) at line \(.line):\(.column)"
    else "RUNTIME: \(.exceptionMessage)"
    end' /tmp/exec-result.json
  exit 1
fi
```

**Why it works:**

- The HTTP method is `GET` with the Apex source URL-encoded as the
  `anonymousBody` query parameter — surprising but documented; it
  fits the entire script in a URL up to the server's URI length
  cap (~16KB practical limit). Larger scripts should compile
  through `ApexClass` + `MetadataContainer` instead.
- The three Booleans in the response — `compiled`, `success`, and
  the *combination* of the two — distinguish "syntax broke at
  compile" from "ran but threw" from "ran clean." Pipelines need
  the distinction because compile failures point at the script
  itself (developer fix), while runtime failures point at the
  org's data state (different remediation).
- `System.debug` output is NOT in the JSON response. To see
  `System.debug` from a Tooling-API anonymous execution, an
  active `TraceFlag` for the calling user must exist *before* the
  call, and the log is then retrievable via
  `SELECT Id, Body FROM ApexLog ORDER BY StartTime DESC LIMIT 1`
  using the Tooling endpoint. The CI gate above sidesteps this by
  using `System.assert` (which surfaces through `exceptionMessage`).

---

## Anti-Pattern: Anonymous Apex as recurring production maintenance

**What practitioners do:**

A nightly cleanup of "stale draft Cases" — initially "let me run
this once" — becomes a runbook entry: `sf apex run --target-org prod
--file scripts/nightly-stale-case-cleanup.apex`. The script lives in
someone's local repo. The "schedule" is a calendar reminder on the
ops engineer's phone. After a year, three different engineers have
copies of three slightly different versions; the one in prod is
unknown.

```apex
// "nightly" cleanup that became permanent infrastructure
List<Case> stale = [
    SELECT Id FROM Case
    WHERE Status = 'Draft' AND CreatedDate < LAST_N_DAYS:30
    LIMIT 5000
];
delete stale;
```

**What goes wrong:**

- **No audit trail.** Anonymous executions don't show up in
  Setup > Apex Jobs, Setup > Scheduled Jobs, or anywhere a
  Salesforce admin doing a quarterly review would look. The only
  evidence the script ever ran is in debug logs (auto-purged after
  ~7 days) and the executing user's email outbox if they cc'd
  themselves.
- **No source-of-truth.** A scheduled `Schedulable` class is a
  Setup record; you can grep the metadata. The "version of the
  cleanup script we actually run" is whatever is on the engineer's
  laptop — there's no source-of-truth that ties what's authorized
  to what's executing.
- **No failure handling.** A scheduled job that throws lands in
  `AsyncApexJob` and can be alerted on. An anonymous script that
  throws prints to a terminal nobody is watching at 2am.
- **Permissions drift silently.** Anonymous Apex runs as the
  executing user. If the engineer's permissions change (rotated
  off the team, profile tightened, deactivated), the "scheduled"
  cleanup silently stops working. The replacement engineer has
  no idea the job exists.
- **Recurring DML in prod with no change control.** Each anonymous
  invocation is a manual prod change. Most orgs have a change-
  control policy that requires a peer-reviewed deployment for
  prod DML; anonymous executions usually slip the policy.

**Correct approach:**

If a script runs more than once on a schedule, it's not anonymous
Apex anymore. Convert it to a `Schedulable` (for fixed intervals)
or `Database.Batchable` (for volume) class, deploy it through the
normal source-controlled pipeline with tests, and schedule it once
through Setup > Apex Classes > Schedule Apex or `System.schedule`.

For one-off corrections that *might* recur ("looks like the import
job had this bug for three weeks"), still deploy the fix as a class
with `@TestVisible` methods and unit tests, then call it from
anonymous if you need an out-of-band ad-hoc invocation. The class
is the artifact; anonymous is just the trigger.

Reach for Execute Anonymous when:

- The fix is genuinely one-off (data correction, investigation,
  back-fill after a known-bad import).
- You're not in a critical path and the script is reviewable in a
  single page of code.
- The script has a savepoint + dry-run toggle, runs against a
  bounded record set, and has a peer-reviewed version archived in
  `scripts/` in your source repo.

Reach for `Schedulable`/`Batchable`/`Queueable` when:

- The work needs to happen on a schedule, on every save, or in
  response to a recurring event.
- The work needs an audit trail (`AsyncApexJob`,
  `CronTrigger`).
- The work touches >10,000 records in one go (Batch Apex with the
  Database.QueryLocator and explicit batch size).
- Failures need to alert someone (subscribe to
  `BatchApexErrorEvent` Platform Events).
