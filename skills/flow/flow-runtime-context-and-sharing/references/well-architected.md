# Well-Architected Notes — Flow Runtime Context And Sharing

## Relevant Pillars

This skill is the canonical **Security** entry point in the `flow/` domain. The other pillars are touched only as second-order consequences of security decisions.

- **Security (primary)** — Run mode is the platform's first-class control over sharing-rule, FLS, and CRUD enforcement inside Flow. A wrong default here is a data-leak primitive: every record-triggered flow that defaults to System Context Without Sharing without justification is a latent CVE waiting for a curious analyst. The whole skill exists to make this control explicit, audited, and least-privileged.
- **Reliability (secondary)** — Flows that escalate to System Context can succeed where User Context would fail closed, but they also succeed in ways the user wouldn't expect. Reliability here means *predictable behavior under all personas* — not just "doesn't crash."
- **Operational Excellence (secondary)** — Audit findings on run mode are inevitable in any org with > 50 active flows. The skill bakes in a repeatable audit script (see `examples.md` Example 2) so ops teams can produce a defensible inventory on demand.
- **Performance** — Out of scope. Run mode does not materially affect query performance; sharing-rule enforcement adds a sharing-row join but it's typically optimized.
- **Scalability** — Out of scope.

## Architectural Tradeoffs

### Tradeoff 1 — Default-Safe vs Default-Convenient

The Salesforce platform default for record-triggered flows is convenient (System Context Without Sharing) — automation just works without sharing rules getting in the way. It is not safe — sharing-rule violations are silent.

This skill recommends inverting the default at the org-policy level: every flow must explicitly set `<runInMode>`, and the recommended default is `SystemModeWithSharing` for record-triggered flows that don't have a documented bypass requirement. The cost is friction at flow authoring time (every flow needs a thought-out run-mode decision). The benefit is no surprise data-leak findings in audit.

### Tradeoff 2 — Per-Element Override vs Subflow Boundary

When a User Context flow needs to escalate one operation, there are two patterns:
- **Per-element `runInMode` override** — minimal change, scoped to one element, easy to audit grep.
- **System Context Subflow** — cleaner separation of concerns, easier to test in isolation, but introduces a flow boundary that adds debugging complexity.

Use per-element override when the escalation is a single read of one specific record. Use the subflow pattern when the escalation involves multiple writes or when the escalated logic is reused across multiple parent flows.

### Tradeoff 3 — Without-Sharing + Audit vs With-Sharing + Granular Shares

For bulk reparenting and similar maintenance work, the choices are:
- **System Context Without Sharing + audit log** — operationally simple; compensating control is the audit log; trust model is "the flow is reviewed code."
- **System Context With Sharing + Apex-managed shares** — operationally complex (must grant explicit shares ahead of every run); trust model is "sharing rules are the source of truth."

For large orgs with active sharing-rule governance, the latter is sounder but heavier. Most orgs settle on the former with a strong audit-log convention.

### Tradeoff 4 — Implicit Default vs Explicit Pinning

Letting flows inherit the API-version default is convenient — one less line of XML per flow. It is also a foot-gun: any later Save in Flow Builder bumps the API version and silently changes behavior. The skill mandates explicit pinning despite the verbosity, because the failure mode of implicit defaults (silent security regression on save) is the worst possible outcome.

## Anti-Patterns

1. **"It worked in my dev org" without persona testing** — Devs run flows as sysadmin. Sysadmin sees everything. The flow appears to work; in production with a real low-privileged user, it fails or (worse) escalates silently. Always test with the lowest-privileged persona who could trigger the flow.
2. **Using `$Permission` as a security boundary** — `$Permission` is a feature-toggle merge field, not a security control. It only resolves correctly for human users, can be bypassed by changing the user's permission set, and gives a false sense of safety. The actual security boundary is `<runInMode>`.
3. **Flipping the entire flow to Without Sharing to make one Get Records work** — collateral damage to every other element. Use per-element override (Pattern 1 in `examples.md`) instead.
4. **No audit log on without-sharing writes** — without an audit log, a privileged write is indistinguishable from a malicious one. Auditors will require this control retroactively; cheaper to add it upfront.
5. **Trusting subflow inheritance of run mode** — there is none. Set `<runInMode>` on every subflow.

## Architectural Principle: Least Privilege as Default

The skill's core stance: every flow runs in the **least permissive** mode that can complete its work. Escalations are explicit, justified, and audited. The default is User Context for screens, System Context With Sharing for record-triggered, and only Without Sharing with a written justification.

This inverts the platform default — and that is the point. The platform optimizes for "ship a flow that works." A security posture optimizes for "ship a flow whose blast radius is bounded." The skill provides the discipline to do the second without sacrificing too much of the first.

## Architectural Principle: Separation of Concerns Between UI and Data Layer

Screen Flows are the UI layer. They should run in User Context — what the user sees on screen reflects what they're entitled to see. Privileged writes happen in subflows configured as System Context. The screen passes the minimum input (record Id, the new value) to the subflow; the subflow does the privileged work and returns a success/failure flag.

This is the same separation as `with sharing` Apex controllers calling `without sharing` service classes — the platform pattern, expressed in Flow.

## Architectural Principle: Audit Trail for Run-Mode Escalations

Every System Context Without Sharing flow writes to an audit log per record affected. The log captures:
- Source flow name and version
- Affected record Id
- Triggering user Id (passed as input where the running user is Automated Process)
- Timestamp
- The specific values changed

This is the compensating control for the bypass. Without it, a without-sharing flow is indistinguishable from an attacker exploiting a privilege escalation.

## Official Sources Used

- Salesforce Help — Configure Flow Run Behavior: https://help.salesforce.com/s/articleView?id=platform.flow_distribute_run_user.htm
- Salesforce Help — Run-Mode Considerations for Flows: https://help.salesforce.com/s/articleView?id=platform.flow_considerations_run_user.htm
- Salesforce Help — How Does Flow Security Work?: https://help.salesforce.com/s/articleView?id=sf.flow_distribute_security.htm
- Salesforce Spring '21 Release Notes — Default Run Mode for Record-Triggered Flows changed.
- Salesforce Architects — Well-Architected Trusted (Security): https://architect.salesforce.com/well-architected/trusted/secure
- Salesforce Architects — Least Privilege Principle: https://architect.salesforce.com/
- Salesforce Developer — Apex Sharing Keywords: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_classes_keywords_sharing.htm
