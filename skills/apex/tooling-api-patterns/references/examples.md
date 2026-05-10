# Examples — Tooling API Patterns

## Example 1: Single-class compile-and-save (IDE-style flow)

**Context:** A VS Code-style web editor lets a developer edit `MyController.cls` and click *Save*. The save must compile the class against the org and persist the new body, with sub-second feedback on success or per-line errors on failure.

**Problem:** The naive approach is to invoke `sf project deploy start --source-dir <one-file>` from the editor. That works, but every save round-trips through source-tracking comparison, zip packaging, and a full Metadata API deploy job — typically 4–8 seconds. The Tooling API's MetadataContainer flow is the primitive Dev Console and Workbench use; it sidesteps all the deploy ceremony for single-component edits.

**Solution:**

```javascript
// Pseudocode for a save handler. All four POSTs hit /services/data/v59.0/tooling/...
async function saveApexClass(connection, apexClassId, newBody) {
  // 1. Create a session-scoped MetadataContainer
  const container = await connection.tooling.create('MetadataContainer', {
    Name: `ide-save-${Date.now()}`,
  });

  // 2. Stage the new body as an ApexClassMember
  await connection.tooling.create('ApexClassMember', {
    MetadataContainerId: container.id,
    ContentEntityId: apexClassId,   // the existing ApexClass Id
    Body: newBody,
  });

  // 3. Submit for async compile-and-save
  const request = await connection.tooling.create('ContainerAsyncRequest', {
    MetadataContainerId: container.id,
    IsCheckOnly: false,
  });

  // 4. Poll the ContainerAsyncRequest to a terminal state
  let state = 'Queued';
  let backoff = 250;
  while (!['Completed', 'Failed', 'Invalidated', 'Aborted'].includes(state)) {
    await sleep(backoff);
    backoff = Math.min(backoff * 2, 4000);
    const row = await connection.tooling.retrieve('ContainerAsyncRequest', request.id);
    state = row.State;
    if (state === 'Failed') {
      const failures = JSON.parse(row.DeployDetails).componentFailures;
      // Surface failures[i].lineNumber, columnNumber, problem to the editor
      return { ok: false, failures };
    }
  }

  // 5. Cleanup
  await connection.tooling.delete('MetadataContainer', container.id);
  return { ok: true };
}
```

**Why it works:** Each step is a single REST round-trip; Salesforce performs the actual compile asynchronously inside the org. The editor sees the success/failure envelope in the time it takes the platform to compile *one* class — typically 200–800 ms for a non-trivial class. `IsCheckOnly: true` flips the same flow into validation-only mode used by lint-on-save.

---

## Example 2: Code-coverage harvester for a nightly dashboard

**Context:** A nightly CI job runs the full Apex test suite on a dedicated CI sandbox and posts coverage to an internal dashboard for trending. The dashboard needs per-class coverage history, not just the latest snapshot, since the class snapshot is overwritten on every test run.

**Problem:** `sf apex test run --code-coverage --result-format human` prints coverage but doesn't expose individual rows for trending. The CLI is reading exactly the same `ApexCodeCoverageAggregate` rows the Tooling API exposes — querying directly is cleaner for tools.

**Solution:**

```python
# Pseudocode harvesting coverage after a test run completes.
# Uses any HTTP client capable of OAuth-authenticated REST calls.

def harvest_coverage(session, instance_url):
    base = f"{instance_url}/services/data/v59.0/tooling"

    # 1. Trigger the async test run with coverage enabled.
    resp = session.post(
        f"{base}/runTestsAsynchronous/",
        json={"classNames": "MyClass1,MyClass2,MyClass3", "maxFailedTests": -1},
    )
    test_run_id = resp.text.strip('"')

    # 2. Poll AsyncApexJob via the Data API until completion.
    while True:
        job = session.get(
            f"{instance_url}/services/data/v59.0/query/?q="
            f"SELECT+Id,Status,NumberOfErrors+FROM+AsyncApexJob+WHERE+Id='{test_run_id}'"
        ).json()["records"][0]
        if job["Status"] in ("Completed", "Failed", "Aborted"):
            break
        time.sleep(5)

    # 3. Pull aggregate coverage rows.
    aggregate = session.get(
        f"{base}/query/?q="
        f"SELECT+ApexClassOrTrigger.Name,NumLinesCovered,NumLinesUncovered,Coverage+"
        f"FROM+ApexCodeCoverageAggregate"
    ).json()["records"]

    snapshot = {
        "captured_at": datetime.utcnow().isoformat(),
        "rows": [
            {
                "class": r["ApexClassOrTrigger"]["Name"],
                "covered": r["NumLinesCovered"],
                "uncovered": r["NumLinesUncovered"],
                "coverage_lines": r["Coverage"],  # the actual line array
            }
            for r in aggregate
        ],
    }
    persist_to_dashboard(snapshot)
```

**Why it works:** `ApexCodeCoverageAggregate` rows are populated server-side after the async test run finishes. They are *overwritten* on the next test run, so the dashboard's job is to snapshot them externally with a timestamp. The `Coverage` field contains the actual covered/uncovered line array — the dashboard can render line-by-line heatmaps from it.

---

## Example 3: Time-bounded user log capture for a 30-minute incident window

**Context:** A user reports intermittent "record not found" errors. The diagnostic team wants 30 minutes of debug logs while the user reproduces, archived to incident-tracking storage.

**Problem:** Hand-toggling logging in Setup is slow and the operator forgets to turn it off, leaving a TraceFlag active and flooding the org's log buffer. A script-driven capture with a hard ExpirationDate is the right primitive.

**Solution:**

```python
# Pseudocode — capture logs for a user for 30 minutes, then archive.
def capture_user_logs(session, instance_url, user_id, minutes=30):
    base = f"{instance_url}/services/data/v59.0/tooling"

    # 1. Find or create a DebugLevel.
    debug_level = session.get(
        f"{base}/query/?q=SELECT+Id+FROM+DebugLevel+WHERE+DeveloperName='IncidentCapture'"
    ).json()["records"]
    if not debug_level:
        debug_level_id = session.post(f"{base}/sobjects/DebugLevel/", json={
            "DeveloperName": "IncidentCapture",
            "MasterLabel": "Incident Capture",
            "ApexCode": "DEBUG", "Db": "INFO", "Workflow": "INFO",
            "Callout": "INFO", "System": "INFO", "Validation": "INFO",
            "Visualforce": "INFO",
        }).json()["id"]
    else:
        debug_level_id = debug_level[0]["Id"]

    # 2. Insert TraceFlag for the target user, ending in `minutes` from now.
    start = datetime.utcnow().isoformat() + "Z"
    end = (datetime.utcnow() + timedelta(minutes=minutes)).isoformat() + "Z"
    trace_flag_id = session.post(f"{base}/sobjects/TraceFlag/", json={
        "TracedEntityId": user_id,
        "DebugLevelId": debug_level_id,
        "StartDate": start,
        "ExpirationDate": end,
        "LogType": "USER_DEBUG",
    }).json()["id"]

    # 3. Wait for the window (or trigger the user reproduction here).
    time.sleep(minutes * 60)

    # 4. Query logs captured during the window.
    logs = session.get(
        f"{base}/query/?q="
        f"SELECT+Id,LogLength,Operation,StartTime+FROM+ApexLog+"
        f"WHERE+LogUserId='{user_id}'+AND+StartTime>{start}+"
        f"ORDER+BY+StartTime+DESC"
    ).json()["records"]

    # 5. Fetch each log body and archive.
    for row in logs:
        body = session.get(f"{base}/sobjects/ApexLog/{row['Id']}/Body").text
        archive_to_incident_storage(row["Id"], body, row["StartTime"])

    # 6. Cleanup.
    session.delete(f"{base}/sobjects/TraceFlag/{trace_flag_id}")
```

**Why it works:** Setting `ExpirationDate` 30 minutes in the future caps the capture window even if cleanup fails. `LogType = USER_DEBUG` covers both UI and API operations. Body retrieval via `/sobjects/ApexLog/<id>/Body` returns plaintext — no JSON parsing needed. The cleanup deletes the TraceFlag so it doesn't accumulate.

---

## Anti-Pattern: Querying `ApexClass` from the Data API and silently losing `Body`

**What practitioners do:** Write a tool that queries `SELECT Id, Name, Body FROM ApexClass` against the standard Data API endpoint (`/services/data/vXX.0/query/?q=...`). The query returns rows with `Id` and `Name` populated — and `Body` always null or missing.

**What goes wrong:** The Data API exposes a stripped view of `ApexClass` that omits the source body. The query *succeeds* (no `INVALID_TYPE` error) so the bug is silent: every class shows up in the result, but with empty source. Tooling that "kind of works" then ships, and downstream users find their compare/grep features break for some classes (the ones the Data API silently truncated).

**Correct approach:** Hit the Tooling endpoint (`/services/data/vXX.0/tooling/query/?q=...`) for any sObject that represents metadata. The full `ApexClass` row including `Body`, `SymbolTable`, `Status`, and `IsValid` is exposed there. Build an internal helper that defaults to Tooling for known metadata sObjects (the table in *Core Concepts*) and fall through to Data only for known-data sObjects. When unsure, prefer Tooling; the Tooling endpoint serves the cross-cutting sObjects (User, Profile, PermissionSet) too.
