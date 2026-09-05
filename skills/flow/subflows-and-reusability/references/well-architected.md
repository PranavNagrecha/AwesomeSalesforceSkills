# Well-Architected Notes - Subflows And Reusability

## Relevant Pillars

### Operational Excellence

Subflows reduce duplicated maintenance when they encapsulate one clear reusable behavior. Good contracts make change safer and easier to reason about across the automation portfolio.

The platform makes one operational fact unavoidable: a parent binds to the child's *active
version*, because `FlowSubflow.flowName` cannot carry a version suffix. Activating a child
is therefore a release event for every caller, and the only durable record of who those
callers are is what someone wrote in the child's `description` field and the org's *Where
Is This Used?* list.

### Scalability

Reusable flow design helps only when the extracted child logic is also safe under load. Shared logic that is not bulk-safe merely spreads the same scale risk everywhere.

A child is a call inside the parent's transaction, not a new one. Whatever the child spends
from the per-transaction SOQL and DML budget, the parent no longer has. A Get Records
inside a loop is not less expensive for having been moved one file away.

### Reliability

A stable child-flow contract improves predictability, while wide hidden side effects do the opposite. Failure handling at the parent boundary is part of reliability, not an optional add-on.

The constraint that shapes every reliable design here: a Subflow element has no
`faultConnector`. Reliability comes from the child catching its own faults and returning a
status the caller can branch on, never from the caller wrapping the call.

## Architectural Tradeoffs

- **Reuse vs indirection:** extracting common behavior improves consistency, but too much decomposition makes the end-to-end flow harder to follow.
- **Flow reuse vs Apex reuse:** Flow is approachable for declarative shared logic, while complex reusable behavior may need a more structured code boundary.
- **Narrow contracts vs future-proof flexibility:** exposing too many variables for hypothetical callers weakens the design today.
- **`storeOutputAutomatically` vs declared parent variables:** the automatic form is less XML and less to keep in sync; the declared form is the only one where a reviewer can see the caller's half of the contract in the diff.
- **Read-only child vs a child that writes:** a read-only child is safe to add callers to; a writing child re-enters the save order and needs a re-entry guard before the second caller exists.

## Anti-Patterns

1. **Subflow as a hidden side-effect bundle** - the child flow mutates too much state to stay reusable.
2. **Contract sprawl through many generic variables** - callers cannot tell what the child flow really needs.
3. **Reuse used to dodge architectural review** - bulk, error, and transaction problems are merely moved, not solved.
4. **A writing child with no status output** - the caller has no fault path available and cannot detect the failure at all.
5. **Treating child activation as a config change** - it silently repoints every caller in the org.

## Official Sources Used

- Metadata API Developer Guide, `FlowSubflow` / `FlowSubflowInputAssignment` / `FlowSubflowOutputAssignment` — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf (the five-field `FlowSubflow` table with no `faultConnector`; `flowName` cannot carry a version suffix; `assignToReference` names the parent variable while both `name` fields name the child's — `api_meta.txt` L72625-72684)
- Metadata API Developer Guide, `FlowVariable` — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf (`isInput`/`isOutput` semantics, their `False` default for API 25.0+, and Salesforce's own warning that disabling access "can break the functionality of applications and pages that call the flow" — L72846-72933)
- Metadata API Developer Guide, `Flow` — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf (`processType` `AutoLaunchedFlow`; `runInMode` values and their record-access meaning; `status`; the managed-package and active-flow deployment limitations — L68025-68440, L68751-68754)
- Metadata API Developer Guide, `FlowDefinition` and "Upgrade Flow Files to API Version 44.0 or Later" — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf (`activeVersionNumber` overriding deployed `status` fields; a flow with no `status` deploys as `Draft` — L73174-73202, L73920-73945)
- Metadata API Developer Guide, `FlowTest` and subtypes — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf (autolaunched flows are testable before activation; `Start`/`Finish` test points; `InputVariable` parameters from API 66.0; `testType` `WithAssertion`; the `.flowtest` suffix — L73960-74450)
- Apex Developer Guide, "Triggers and Order of Execution" — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf (before-save flows at step 3, after-save at step 14, commit at step 19, and the recursive-save note that steps 9-17 are skipped — `apexdev.txt` L15402-15478)
- Salesforce Developer Limits and Allocations Quick Reference — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_app_limits_cheatsheet.pdf (the per-transaction budget parent and child share: 100 synchronous SOQL queries, 150 DML statements, recursive stack depth 16 — L53-69)
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html (pillar framing for the Operational Excellence / Scalability / Reliability notes above)
- Subflows (Flow Builder reference) — https://help.salesforce.com/s/articleView?id=sf.flow_ref_elements_subflow.htm&type=5 (Flow Builder UI naming for the Subflow element; not fetchable from this environment, retained as the canonical UI-side reference)
