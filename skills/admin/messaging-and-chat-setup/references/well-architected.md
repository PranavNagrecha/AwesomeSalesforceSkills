# Well-Architected Notes — Messaging and Chat Setup

## Relevant Pillars

- **Security** — CORS and CSP Trusted Sites are not optional performance optimizations; they are the browser-enforced security controls that prevent unauthorized domains from accessing the Salesforce API and loading the widget script. Misconfiguration (overly broad wildcards in CORS, or missing CSP entries) either blocks legitimate use or opens the org to cross-origin attacks. Every deployment domain must be explicitly registered and reviewed during security assessments.
- **Reliability** — Fallback queues and off-hours auto-responses protect against routing failures leaving customers in a permanent wait state. An Omni-Channel Flow that has no fault path and no fallback queue is a reliability risk: a single Flow fault drops the session silently. Reliable MIAW deployments define both the happy path and the fallback for every routing scenario.
- **Adaptable** — Separating the Messaging Channel record from the Embedded Service Deployment means routing logic, pre-chat fields, and off-hours behavior can be updated without re-deploying the widget snippet. Similarly, using Omni-Channel Flows for routing (rather than hardcoded queue assignments) means routing rules can be changed without touching the deployment configuration. This separation of concerns follows the Adaptable pillar's principle of change isolation.

## Architectural Tradeoffs

**Queue-Based vs Flow-Based Routing:** Queue-based routing is simple and observable (queue depth is visible in the Omni-Channel supervisor). Flow-based routing is flexible but adds a layer that must be monitored for faults. For organizations with simple routing needs, Flow-based routing adds complexity without benefit. For organizations with multi-skill or business-hours requirements, the queue-only path forces workarounds (multiple channels, manual transfers) that are worse than a well-designed Flow.

**Status-Based vs Tab-Based Capacity:** Status-Based capacity is the architecturally correct model for any org handling asynchronous messaging channels. Tab-Based capacity was designed for synchronous Live Agent chat, where one browser tab equates to one active interaction. Asynchronous messaging breaks this assumption because a session can persist across hours without requiring agent attention. Orgs that defer this decision and keep Tab-Based during MIAW rollout often face agent over-capacity and dropped sessions once asynchronous behavior kicks in.

**Single Channel vs Channel Per Use Case:** A common temptation is to create one Messaging Channel and one Embedded Service Deployment for the entire org. This works initially but becomes brittle when different product lines, regions, or languages need different routing, branding, or pre-chat fields. A better pattern is one Messaging Channel per logical routing domain, with shared queues where possible, and separate Embedded Service Deployments only where branding differs.

## Anti-Patterns

1. **Reusing a Legacy Live Agent Deployment for MIAW** — Creating an Embedded Service Deployment with channel type "Chat" and then attempting to use it for MIAW routes sessions to `LiveChatTranscript` instead of `MessagingSession`. All MIAW-native features are unavailable. A new MIAW-type deployment must be created; the old one cannot be converted.

2. **Configuring Pre-Chat Fields Without a Contact Lookup Automation** — Pre-chat fields collect customer data but do not link a Contact automatically. Deploying pre-chat without a subsequent lookup Flow or trigger leaves every Messaging Session with no Contact association, making case history invisible to agents and breaking any automation that depends on `ContactId` being populated.

3. **Omitting the Fallback Queue on the Messaging Channel** — Deploying a Messaging Channel with an Omni-Channel Flow for routing but no fallback queue configured means a Flow fault silently strands sessions. The fallback queue is the last-resort safety net and must always be set, even when Flow routing is the primary path.

## Official Sources Used

- Messaging for In-App and Web Overview — https://help.salesforce.com/s/articleView?id=sf.miaw_intro_intro.htm
- Configure an Enhanced Web Chat Deployment — https://help.salesforce.com/s/articleView?id=sf.live_agent_create_deployments.htm
- Embedded Chat Developer Guide (Spring '26) — https://developer.salesforce.com/docs/service/messaging-in-app/references
- Route Messaging Sessions with Omni-Channel Flows — https://help.salesforce.com/s/articleView?id=sf.omnichannel_flow_overview.htm
- CORS Trusted Sites — https://help.salesforce.com/s/articleView?id=sf.extend_code_cors.htm
- CSP Trusted Sites — https://help.salesforce.com/s/articleView?id=sf.csp_trusted_sites.htm
- Omni-Channel Capacity Models — https://help.salesforce.com/s/articleView?id=sf.omnichannel_capacity_models.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
