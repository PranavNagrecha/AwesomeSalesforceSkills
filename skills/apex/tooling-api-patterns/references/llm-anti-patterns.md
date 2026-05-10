# LLM Anti-Patterns — Tooling API Patterns

Common mistakes AI coding assistants make when generating or advising on Tooling API tooling. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Routing Tooling-only sObject queries through the Data API endpoint

**What the LLM generates:** Code that queries `ApexClass`, `FlowDefinition`, `ValidationRule`, or `EntityDefinition` against `/services/data/vXX.0/query/?q=...` without recognizing these are Tooling-only.

**Why it happens:** Training data contains many Salesforce REST examples for the Data API. The LLM treats "Salesforce REST query" as a single endpoint and substitutes any sObject name into the same path. The Data endpoint *accepts* `ApexClass` queries (returns Id/Name) but silently strips `Body`, so the bug looks like working code.

**Correct pattern:**

```text
# CORRECT — Tooling endpoint
GET /services/data/v59.0/tooling/query/?q=SELECT+Id,Name,Body+FROM+ApexClass

# WRONG — Data endpoint silently truncates Body
GET /services/data/v59.0/query/?q=SELECT+Id,Name,Body+FROM+ApexClass
```

**Detection hint:** Grep for `/query/?q=` followed by `ApexClass`, `ApexTrigger`, `ApexCodeCoverage`, `ApexLog`, `TraceFlag`, `DebugLevel`, `FlowDefinition`, `Flow`, `ValidationRule`, `EntityDefinition`, `FieldDefinition`, `MetadataContainer`, `ContainerAsyncRequest`, `ApexExecutionOverlay`. Any match where the path lacks `/tooling/` is a bug. Also flag any code that selects `Body` from `ApexClass` and the URL doesn't contain `tooling`.

---

## Anti-Pattern 2: Treating `ContainerAsyncRequest.DeployDetails` as a structured object

**What the LLM generates:** `errors = container_request.DeployDetails.componentFailures` or `for failure in row['DeployDetails']['componentFailures']`.

**Why it happens:** The field name "DeployDetails" sounds structured. LLMs default to dot-or-bracket access on JSON-like fields, missing that this specific field is a JSON-encoded *string*.

**Correct pattern:**

```python
# CORRECT — parse the string first
import json
row = retrieve('ContainerAsyncRequest', request_id)
if row['State'] == 'Failed':
    details = json.loads(row['DeployDetails'])
    for failure in details['componentFailures']:
        print(failure['lineNumber'], failure['problem'])
```

**Detection hint:** Any code accessing `.componentFailures` or `.componentSuccesses` on a `DeployDetails` field without a preceding `JSON.parse` / `json.loads` is broken.

---

## Anti-Pattern 3: Inserting a TraceFlag without checking for an existing active one

**What the LLM generates:** Direct `POST` of a new TraceFlag for the user without first querying — sometimes wrapped in a function called something like `enable_logging_for_user(user_id)`.

**Why it happens:** "Enable logging" sounds like a stateless toggle. The LLM generates the imperative shape ("create a TraceFlag") without modeling the per-(user, LogType) uniqueness constraint.

**Correct pattern:**

```python
# CORRECT — query first, reuse or replace
existing = query(
    f"SELECT Id FROM TraceFlag WHERE TracedEntityId='{user_id}' "
    f"AND LogType='USER_DEBUG' AND ExpirationDate > {now()}"
)
if existing:
    update('TraceFlag', existing[0]['Id'], {'ExpirationDate': new_end})
else:
    insert('TraceFlag', {...})
```

**Detection hint:** Any code path that POSTs to `/sobjects/TraceFlag/` without a preceding query against `TraceFlag` filtered by `TracedEntityId` and `LogType` is at risk of `DUPLICATE_VALUE`. Look for `create('TraceFlag'` or `POST .../TraceFlag/` without a sibling query.

---

## Anti-Pattern 4: Polling forever without a max-wait ceiling

**What the LLM generates:** A `while True:` loop or `while state != 'Completed':` that polls a `ContainerAsyncRequest` or `AsyncApexJob` indefinitely.

**Why it happens:** The happy path always completes quickly in tests; the LLM doesn't generate the failure-mode handling because it doesn't surface in the example traces it learned from.

**Correct pattern:**

```python
# CORRECT — bounded polling with backoff and timeout
deadline = time.monotonic() + 60   # 60 second cap for compile
backoff = 0.25
while time.monotonic() < deadline:
    row = retrieve('ContainerAsyncRequest', request_id)
    if row['State'] in ('Completed', 'Failed', 'Invalidated', 'Aborted'):
        break
    time.sleep(backoff)
    backoff = min(backoff * 2, 4.0)
else:
    raise TimeoutError(f"Compile did not complete in 60s, last state {row['State']}")
```

**Detection hint:** Any `while True` or `while not done` polling loop without a clock-based deadline check. Also flag missing handling for the `Invalidated` and `Aborted` states (LLMs often only check `Completed` and `Failed`).

---

## Anti-Pattern 5: Forgetting to delete `MetadataContainer` / `TraceFlag` / `ApexExecutionOverlayAction` after use

**What the LLM generates:** Save flow that creates a MetadataContainer, submits the request, polls to terminal state, returns the result — and never deletes the container. Same omission for TraceFlags and overlay actions.

**Why it happens:** "Cleanup" is a non-functional concern that doesn't show up in the happy-path narrative. The LLM ends the function at the success return, missing the orphan-resource consequence.

**Correct pattern:**

```python
# CORRECT — try/finally cleanup, runs on success and failure
container_id = create('MetadataContainer', {...})['id']
try:
    create('ApexClassMember', {...})
    request_id = create('ContainerAsyncRequest', {...})['id']
    state = poll_to_terminal(request_id)
    return state
finally:
    delete('MetadataContainer', container_id)
```

**Detection hint:** Any code that creates a `MetadataContainer`, `TraceFlag`, or `ApexExecutionOverlayAction` and lacks a corresponding `delete` call (ideally inside `finally`/`try-with-resources`/`defer`). For `TraceFlag`, an explicit `ExpirationDate` cap is a partial mitigation but not a substitute for cleanup — orphan rows still accumulate.

---

## Anti-Pattern 6: Assuming anonymous Apex via Tooling REST runs as a system superuser

**What the LLM generates:** Code that runs `executeAnonymous` to perform a privileged operation (e.g., delete records across all owners, modify protected metadata) without checking the calling principal's permissions.

**Why it happens:** The word "anonymous" connotes "no user context" / "elevated privilege" in many programming environments. In Salesforce, anonymous Apex via Tooling REST runs in the *caller's* context.

**Correct pattern:** Either (a) ensure the calling principal has the required permissions explicitly (document a permission set the integration user must have), or (b) wrap the privileged logic in a compiled `without sharing` Apex helper and invoke it from the anonymous body. Never assume the call has elevated privilege by virtue of being "anonymous."

**Detection hint:** Any `executeAnonymous` body that performs `Database.delete`, sets `OwnerId` across users, modifies `User`/`Profile`/`PermissionSet`, or queries with `WITH SYSTEM_MODE` should be reviewed for the calling principal's permission posture. The bug surfaces only at runtime in production with a real integration user.
