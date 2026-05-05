# Well-Architected Notes — Flow Error Notification Patterns

## Relevant Pillars

- **Reliability** — Silent failure is the worst Flow failure mode.
  Default-org behavior (no Fault paths, single shared
  exception-recipient inbox) produces silent failures that surface
  weeks later as data drift or customer complaints. The reliability
  investment is "every fault path does *something* observable" —
  even a no-op log is better than a do-nothing branch.
- **Operational Excellence** — Centralizing error handling in a
  single `Flow_Error_Log__c` object + reusable sub-flow pays back
  on every flow you build afterwards. The first flow takes 30 minutes
  to build the infrastructure; flows 2-N take seconds to wire in.

## Architectural Tradeoffs

- **Custom log object vs Platform Event subscriber.** Custom log is
  simpler — every flow inserts a row. Platform Event is more
  flexible — subscriber can route by flow / severity / channel.
  Single-channel orgs use the log. Multi-channel orgs (Slack +
  PagerDuty + email) use the Platform Event.
- **Real-time alert vs daily digest.** Real-time on every error
  trains admins to ignore. Daily digest catches trends but delays
  detection of acute failures. Best practice: digest by default;
  real-time only for the small subset of flows where 30-minute
  detection delay is unacceptable.
- **In-flow suppression vs alert-channel filtering.** Suppressing
  expected-rejection patterns inside the flow (Pattern D) keeps the
  log clean. Alternative: log everything, filter at the alert channel
  (subscriber, report). In-flow is cheaper (no log write); channel
  filtering preserves audit trail.
- **Org-default email recipient as fallback vs disabled.** Leaving
  the default configured catches flows you forgot to wire fault
  paths into. Disabling forces every flow to be audited. Most orgs
  keep it enabled to a fallback inbox; some compliance-heavy orgs
  disable to force coverage.

## Anti-Patterns

1. **"Do-nothing" Fault path.** Silently succeeds the flow; failure
   is invisible.
2. **Fault path that throws away `$Flow.FaultMessage`.** The
   actionable detail is gone; "an error occurred" is what the admin
   sees.
3. **Same Fault path for validation rejections AND programmer
   errors.** Either drowns the admin in noise or hides the validation
   message from the user. Differentiate.
4. **Send Email Action inside a fault path** in a high-volume flow.
   Governor risk; the secondary fault has no further Fault path.
5. **Real-time per-event alerts on every error.** Trains the admin
   to ignore alerts within weeks.
6. **Fault paths on a sub-flow that don't propagate back to the
   parent.** Parent admin's monitoring is blind to sub-flow errors.

## Official Sources Used

- Customize What Happens When a Flow Fails — https://help.salesforce.com/s/articleView?id=sf.flow_build_extend_fault.htm&type=5
- Add a Fault Connector to a Flow Element — https://help.salesforce.com/s/articleView?id=sf.flow_ref_elements_connectors_faults.htm&type=5
- Process Automation Settings (apex exception email recipient) — https://help.salesforce.com/s/articleView?id=sf.process_automation_settings.htm&type=5
- $Flow.FaultMessage Resource — https://help.salesforce.com/s/articleView?id=sf.flow_ref_resources_systemvariables.htm&type=5
- Platform Events overview — https://developer.salesforce.com/docs/atlas.en-us.platform_events.meta/platform_events/
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
