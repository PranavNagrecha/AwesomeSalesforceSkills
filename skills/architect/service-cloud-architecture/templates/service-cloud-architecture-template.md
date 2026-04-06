# Service Cloud Architecture — Work Template

Use this template when designing a Service Cloud solution architecture.

## Scope

**Skill:** `service-cloud-architecture`

**Request summary:** (fill in what the user asked for)

**Salesforce Edition:** (Enterprise / Unlimited / other)

**Clouds and licenses in scope:** (Service Cloud, Knowledge, Messaging, Service Cloud Voice, etc.)

## Context Gathered

Record the answers to the Before Starting questions from SKILL.md here.

- **Required channels:** (phone, email, chat, messaging, social, self-service portal)
- **Expected case volume:** (monthly volume, peak daily volume, seasonal spikes)
- **Agent count and specialization:** (total agents, skill groups, language requirements)
- **SLA requirements:** (response time, resolution time, by tier)
- **Existing systems:** (current CRM, telephony provider, knowledge tools)
- **Known constraints:** (budget, timeline, licensing limitations)

## Channel Strategy

| Channel | Salesforce Feature | Volume Estimate | Priority | Notes |
|---|---|---|---|---|
| Email | Email-to-Case (On-Demand) | | | |
| Web Form | Web-to-Case | | | |
| Chat/Messaging | Messaging for In-App and Web | | | |
| Phone | Service Cloud Voice / Open CTI | | | |
| Social | Social Customer Service | | | |
| Self-Service | Experience Cloud + Knowledge | | | |

### Channel rationale

(Document why each channel was included or excluded)

## Routing Model

**Selected model:** (Queue-based / Skills-based)

**Rationale:** (Why this model fits the requirements)

### Capacity Model

| Channel | Capacity Units per Agent | Max Concurrent | Notes |
|---|---|---|---|
| Phone/Voice | 1 | 1 | |
| Messaging | | | |
| Email/Case | | | |

### Routing Configurations

| Configuration Name | Priority | Skills/Queue | Timeout | Overflow Behavior |
|---|---|---|---|---|
| | | | | |

## Case Lifecycle

1. **Creation:** (channels, auto-creation rules, web-to-case, email-to-case)
2. **Categorization:** (record types, case reason, auto-classification)
3. **Routing:** (Omni-Channel routing configuration, priority rules)
4. **Assignment:** (agent assignment, capacity consumption)
5. **Work in Progress:** (Console layout, knowledge sidebar, macros)
6. **Resolution:** (closure criteria, customer notification)
7. **Closure:** (auto-close rules, satisfaction survey)

## Entitlement and SLA Design

| Tier | First Response SLA | Resolution SLA | Business Hours | Escalation Path |
|---|---|---|---|---|
| | | | | |

### Milestone Actions

| Milestone | 50% Threshold | 75% Threshold | 100% (Violation) |
|---|---|---|---|
| First Response | | | |
| Resolution | | | |

## Knowledge Strategy

- **Data Category Hierarchy:** (top-level categories and subcategories)
- **Article Record Types:** (FAQ, Troubleshooting, Product Doc, etc.)
- **Authoring Workflow:** (who creates articles, review/approval process)
- **Deflection Targets:** (which case categories to deflect, target deflection rate)
- **Bot/Agentforce Integration:** (which articles surface in bot conversations)

## Integration Architecture

| System | Direction | Method | Purpose |
|---|---|---|---|
| Telephony | Bidirectional | Service Cloud Voice / Open CTI | Voice routing and call data |
| | | | |

### Named Credentials

| Named Credential | Endpoint | Auth Type | Used By |
|---|---|---|---|
| | | | |

## Security Model

- **Case OWD:** (Private / Public Read Only / Public Read Write)
- **Sharing Rules:** (criteria-based sharing for cross-team visibility)
- **Knowledge Data Category Visibility:** (by role: internal, partner, customer)
- **Profile/Permission Set considerations:** (Service Cloud User, Knowledge User)
- **Shield requirements:** (Platform Encryption, Event Monitoring, Field Audit Trail)

## Checklist

Copy from SKILL.md Review Checklist and tick items as you complete them.

- [ ] Channel strategy covers all required customer touchpoints with documented rationale
- [ ] Routing model selected with capacity model showing agent concurrency per channel
- [ ] Case lifecycle documented end-to-end
- [ ] Entitlement processes with milestones designed for all SLA requirements
- [ ] Knowledge taxonomy and article types defined
- [ ] Deflection strategy documented with target rates
- [ ] Integration architecture covers telephony and external systems
- [ ] Service Console layout optimized (fewer than 10 components, 6-8 utility bar items)
- [ ] Security model reviewed (sharing, Knowledge visibility, agent permissions)
- [ ] Licensing confirmed

## Notes

Record any deviations from the standard pattern and why.
