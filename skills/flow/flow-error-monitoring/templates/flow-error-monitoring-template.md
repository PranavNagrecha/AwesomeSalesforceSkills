# Flow Error Monitoring — Design Record

One file per org (or per business unit). It is the durable answer to "who hears about it, how
fast, and how do we know the monitoring itself still works". Fill it in as you work through
`SKILL.md`; the rows marked *(not deployable)* are the ones that will not survive a sandbox
refresh and therefore need a named owner.

## 1. Scope

| Field | Value |
|---|---|
| Org / business unit | |
| Active flows in scope | (from `SELECT COUNT() FROM FlowDefinitionView WHERE IsActive = true`) |
| Flow types present | record-triggered / screen / scheduled / autolaunched / orchestration |
| Central log object | `Application_Log__c` (or: ) |
| Existing external observability | none / Splunk / Datadog / other: |
| Date of this record | |

## 2. Answers to the Questions table in `SKILL.md`

| Question | Answer |
|---|---|
| Who receives flow error email today, and is that deliberate? | |
| Which flow types are in scope, and does anything rely on `FlowInterviewLog`? | |
| Where does the fault-path row go, and does Apex already write there? | |
| Who may resume or delete a paused interview? | |
| What is the response time per severity band, and who is on the hook? | |
| How will we know a *monitoring* flow has itself failed? | |
| How is a new flow prevented from shipping without instrumentation? | |

## 3. Org fences

| Setting | Documented default | This org | Owner | Changed on |
|---|---|---|---|---|
| `enableFlowUseApexExceptionEmail` | `false` (email → last modifier) | | | |
| `enableFlowInterviewSharingEnabled` | `true` | | | |
| `enableFlowDeployAsActiveEnabled` | `false` in production | | | |
| `apexEmailNotifications` recipients | — (replace-on-deploy) | | | |

## 4. Severity bands and SLA

| Severity | `Severity__c` value | Example flow | Channel | Response target | Owner |
|---|---|---|---|---|---|
| Revenue / compliance impacting | `FATAL` | | page | | |
| Operational | `ERROR` | | threshold alert on the log | | |
| Degraded but self-correcting | `WARN` | | scheduled review | | |
| Trace only | `INFOL` / `DEBUGL` | | none | — | — |

## 5. Coverage

| Check | Command / query | Last run | Result |
|---|---|---|---|
| Fault routes reach the sink | `python3 scripts/check_flow_error_monitoring.py --manifest-dir <src> --strict` | | |
| Version drift | `SELECT ApiName, IsActive, IsOutOfDate, VersionNumber FROM FlowDefinitionView WHERE IsActive = true AND IsOutOfDate = true` | | |
| Paused / failed backlog | `SELECT InterviewStatus, CurrentElement, COUNT(Id) FROM FlowInterview WHERE InterviewStatus IN ('Paused','VersionPaused','Error') GROUP BY InterviewStatus, CurrentElement` | | |
| Sink is receiving | forced fault + read the newest `Application_Log__c` row back | | |

## 6. Not deployable — needs an owner

| Item | Owner | Where it is configured | Re-created after a refresh by |
|---|---|---|---|
| Report subscription / scheduled delivery *(not deployable)* | | Setup → Reports | |
| Dashboard refresh schedule *(not deployable)* | | | |
| On-call rota / paging integration *(not deployable)* | | | |

## 7. Open questions and unverified assumptions

Record anything this design depends on that the guides do not state — start with the
`UNVERIFIED` markers in `references/metadata-examples.md` §1 (`$Flow.FaultMessage`,
`$Flow.InterviewGuid`, `$User.Id` as a flow reference) and note what you observed in this org.

| Assumption | How it was checked | Result | Date |
|---|---|---|---|
| `$Flow.FaultMessage` populates `Message__c` | forced fault, read the row | | |
| | | | |

## 8. Deviations from the standard pattern

Anything this org does differently, and why. A deviation with a reason is a decision; a
deviation without one is drift.
