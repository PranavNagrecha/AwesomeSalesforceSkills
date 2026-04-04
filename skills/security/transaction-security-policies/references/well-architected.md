# Well-Architected Notes — Transaction Security Policies

## Relevant Pillars

- **Security** — Transaction Security Policies are a first-class Security pillar capability. They provide the platform's native real-time enforcement layer: the ability to block, challenge, notify, or terminate sessions based on user behavior events as they occur. Every org handling sensitive data should have an inventory of active policies covering at minimum login anomalies and high-volume data export.

- **Operational Excellence** — Policy lifecycle management (Monitor mode, match-log review, promotion to Active, periodic audit of execution users and recipients) is an operational discipline. Well-architected orgs treat Transaction Security Policies the same as other automation: version-controlled via Metadata API, validated in sandboxes, and audited on a defined schedule.

- **Reliability** — Over-aggressive policies (broad conditions, Block enforcement, no Monitor period) risk blocking legitimate users and degrading service reliability. Under-permissive policies (sitting in Monitor mode indefinitely, broken execution users, unsupported event types) create false assurance. Both failure modes reduce org reliability. The reliability tradeoff must be acknowledged when selecting enforcement actions.

## Architectural Tradeoffs

**Block vs. MFA vs. Notify:** Block actions are the most disruptive — they prevent the operation entirely and always carry a risk of false-positive user impact. MFA step-up is less disruptive and appropriate when the user is likely legitimate but identity re-verification adds value. Notification-only is non-disruptive and best for initial rollout or low-severity signals. Start with Notification, graduate to MFA, escalate to Block only when confidence in the condition logic is high.

**Enhanced Condition Builder vs. Legacy Apex PolicyCondition:** Enhanced Condition Builder requires no Apex and is the preferred approach for any condition expressible in its UI. It has no Apex compile dependency, is maintainable by admins, and deploys cleanly via Metadata API. Legacy Apex policies offer full programmatic flexibility but introduce code-maintenance burden, "Author Apex" permission dependency, and silent failure modes on compile errors. Choose Enhanced unless the condition genuinely requires logic the Condition Builder cannot express.

**Breadth of coverage vs. alert fatigue:** A policy that matches too broadly (e.g., Notify on every API call) generates noise that causes the security team to ignore alerts. A policy that matches too narrowly (e.g., only a specific report name) misses close variants. Design conditions to be as specific as the threat model requires and validate match rates in Monitor mode before activating.

**Scope: org-wide vs. profile/user-targeted:** Most policy conditions can include a `UserId` or `ProfileId` filter to narrow the scope. Org-wide policies (no user filter) apply to all users and carry higher false-positive risk. Profile-targeted policies are easier to tune and lower-risk during rollout. Start scoped, expand to org-wide after validation.

## Anti-Patterns

1. **Deploying Active enforcement policies without Monitor mode validation** — Moving a new policy directly to Active skips the observation phase. Broad or misconfigured conditions (wrong field format, overly inclusive substrings) immediately block legitimate users, causing incident-level disruptions. Always start in Monitor mode and review match logs before enabling enforcement.

2. **Treating Transaction Security Policies as the only security control** — Transaction Security Policies are a behavioral enforcement layer, not a replacement for login IP ranges, session security settings, permission model hygiene, or Shield Platform Encryption. Over-relying on policies without baseline security hardening creates a false sense of security. Policies supplement other controls; they do not substitute for them.

3. **Setting execution users and notification recipients to individual employee accounts** — Tying policy execution context and notification delivery to specific employees creates fragility. When those employees leave and their accounts are deactivated, policies silently stop working. Use dedicated service accounts or distribution groups for these roles, and include policy health in offboarding checklists.

4. **Ignoring the policy-supported event type list** — Configuring policies on unsupported event types (e.g., `IdentityVerificationEvent`) provides no enforcement while creating a false impression that a control is in place. This is a latent security gap — the org believes a protection exists, but it never fires. Always validate event type support before building a policy.

## Official Sources Used

- Salesforce Security Guide — Transaction Security Policies overview, enforcement actions, and setup navigation: https://help.salesforce.com/s/articleView?id=sf.transaction_security_policy_overview.htm&type=5
- Salesforce Help: Create Transaction Security Policies — condition builder, event types, action configuration: https://help.salesforce.com/s/articleView?id=sf.transaction_security_create_policies.htm&type=5
- Platform Events Developer Guide — RTEM event types, policy-support flags, field references for LoginEvent, ReportEvent, ApiEvent: https://developer.salesforce.com/docs/atlas.en-us.platform_events.meta/platform_events/platform_events_intro_emp.htm
- Salesforce Well-Architected Overview — Security pillar framing, behavioral enforcement patterns: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Metadata API Developer Guide — TransactionSecurityPolicy metadata type reference: https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm
