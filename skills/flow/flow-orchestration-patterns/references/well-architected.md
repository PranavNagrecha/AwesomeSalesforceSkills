# Well-Architected Notes — Flow Orchestration Patterns

## Relevant Pillars

- **Reliability** — Orchestrations are persistent across days /
  weeks. The reliability investment is the cancel pathway, the
  fallback for null / inactive assignees, and the evaluation flow
  on each stage exit that re-checks source-record state. Any
  orchestration without these is one organizational change away
  from being stuck.
- **Operational Excellence** — A "stuck Work Item" report — items
  assigned to inactive users, or items aging past N days — is the
  highest-yield ops investment. Without it, stuck orchestrations
  are invisible until someone notices the process didn't complete.

## Architectural Tradeoffs

- **Orchestration vs Approval Process.** Approval Process is older,
  simpler, single-decision. Orchestration is multi-stage,
  multi-human, persistent. For a single-step approval, Approval
  Process wins on simplicity. For anything > 1 stage,
  orchestration is the right tool.
- **Orchestration vs record-triggered flow chain.** Record-triggered
  flow chain runs in transactions; orchestration spans transactions
  with persistence. Use orchestration when human input punctuates
  the work and persistence is required; use record-triggered flow
  when the work is system-only and synchronous.
- **Specific-user vs queue assignment.** Specific user is simpler
  but brittle (deactivation). Queue is more code (queue setup) but
  resilient. For long-running orchestrations, queue is the right
  default.
- **In-flow evaluation vs orchestration evaluation flow.** In-flow
  decisions are evaluated at the moment the flow runs. Orchestration
  evaluation flows run at stage-exit time, which can be days after
  any individual step completed. Re-checking source-record state at
  stage exit is the orchestration-specific pattern.

## Anti-Patterns

1. **Orchestration without a cancel pathway.** Stuck orchestrations
   become operational tickets.
2. **Single-stage single-step orchestration as a Process Builder
   replacement.** Orchestration overhead with no multi-stage
   benefit.
3. **Specific-user assignee on a multi-week step.** User
   deactivation produces stuck Work Items.
4. **Background-step flows without fault paths.** Errors are
   invisible; downstream effects don't fire.
5. **Stage-exit evaluation flows without fault paths.** Unhandled
   faults hold the orchestration.
6. **Mid-orchestration flow definition edits to referenced screen
   flows.** Confused UI or errors at resume time.

## Official Sources Used

- Flow Orchestration overview — https://help.salesforce.com/s/articleView?id=sf.flow_orchestrator.htm&type=5
- Build a Flow Orchestration — https://help.salesforce.com/s/articleView?id=sf.flow_orchestrator_build.htm&type=5
- Stages and Steps in Flow Orchestrator — https://help.salesforce.com/s/articleView?id=sf.flow_orchestrator_concepts.htm&type=5
- Work Items in Flow Orchestration — https://help.salesforce.com/s/articleView?id=sf.flow_orchestrator_workitems.htm&type=5
- Evaluation Flow reference — https://help.salesforce.com/s/articleView?id=sf.flow_concepts_evaluation_flow.htm&type=5
- Sibling skill — `skills/flow/flow-error-notification-patterns/SKILL.md`
- Sibling skill — `skills/flow/flow-time-based-patterns/SKILL.md`
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
