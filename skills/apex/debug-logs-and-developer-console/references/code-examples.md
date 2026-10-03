# Code Examples: Debug Logs and Developer Console

Runnable scripts and queries for the debug-log setup in `SKILL.md`. Narrative examples are in `examples.md`.

## Example 1: Script the debug level and trace flags with the sf CLI

**Context:** A platform event trigger on `Order_Event__e` fails intermittently. The developer wants logs from the trigger (which runs as Automated Process) and more detail from one handler class, without clicking through Setup each time.

**Solution:** Create a debug level, an Automated Process trace flag, and a class trace flag through the Tooling API, then pull logs from the CLI.

```bash
#!/usr/bin/env bash
# Run from a Salesforce DX project with a default org set.
set -euo pipefail

# 1. A debug level with Apex Code DEBUG and Database INFO.
DL_ID=$(sf data create record --use-tooling-api --sobject DebugLevel --json \
  --values "DeveloperName=Order_Event_Debug MasterLabel=Order_Event_Debug ApexCode=DEBUG ApexProfiling=INFO Callout=INFO Database=INFO System=INFO Validation=INFO Visualforce=NONE Workflow=INFO" \
  | python3 -c 'import json,sys; print(json.load(sys.stdin)["result"]["id"])')

# 2. A window under 24 hours (ExpirationDate must be < 24h after StartDate).
START=$(date -u +%Y-%m-%dT%H:%M:%S.000+0000)
END=$(date -u -v+30M +%Y-%m-%dT%H:%M:%S.000+0000 2>/dev/null || date -u -d '+30 min' +%Y-%m-%dT%H:%M:%S.000+0000)

# 3. Trace flag on the Automated Process user (look up its Id first; see the SOQL below).
sf data create record --use-tooling-api --sobject TraceFlag \
  --values "TracedEntityId=${AUTOPROC_USER_ID:?set it} DebugLevelId=$DL_ID LogType=USER_DEBUG StartDate=$START ExpirationDate=$END"

# 4. Optional: extra detail for one class. CLASS_TRACING overrides levels but creates no log by itself.
sf data create record --use-tooling-api --sobject TraceFlag \
  --values "TracedEntityId=${HANDLER_CLASS_ID:?set it} DebugLevelId=$DL_ID LogType=CLASS_TRACING StartDate=$START ExpirationDate=$END"

# 5. After reproducing, list and fetch the newest logs.
sf apex list log
sf apex get log --number 2 --output-dir ./logs
```

Look up the IDs with Tooling or standard queries:

```sql
-- Standard SOQL: the Automated Process user
SELECT Id, Name FROM User WHERE Name = 'Automated Process'
-- Tooling API (sf data query --use-tooling-api): the handler class
SELECT Id, Name FROM ApexClass WHERE Name = 'OrderEventHandler'
-- Tooling API: recent logs and their size
SELECT Id, Operation, Status, LogLength, StartTime FROM ApexLog ORDER BY StartTime DESC LIMIT 10
```

**Grounding:** `sf data create record --use-tooling-api --sobject TraceFlag` and `sf apex list log`, `sf apex get log` are from the Salesforce CLI Command Reference (262). `TraceFlag` fields (`TracedEntityId`, `DebugLevelId`, `LogType`, `StartDate`, `ExpirationDate`) and `DebugLevel` fields are from the Tooling API Developer Guide (262). Automated Process for event triggers is from the Platform Events Developer Guide (262). UNVERIFIED (2026-10-03): the `--json` result shape (`result.id`) for your CLI version, and that the Automated Process user is queryable by that name in every org.

**Why it works:** The event trigger's log lands under Automated Process, the class trace flag adds detail for one class only, and the window stays under the 24-hour limit.
