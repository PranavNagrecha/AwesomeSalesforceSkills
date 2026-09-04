# Routing Selector — Assignment Rules vs Omni-Channel vs Flow vs Apex vs Territories vs Scoring

`standards/decision-trees/automation-selection.md` decides Flow vs Apex for general logic. It does not cover ownership routing, where the declarative rule engines are usually the right first answer. Use this page when the question is "who should own this record, and what should set that".

## Pick by need

| Need | Use | Why not the others | Skill |
|---|---|---|---|
| Route a new Lead or Case to a user or queue from field values | **Assignment rule** | Zero code, admin-maintained, up to thousands of ordered entries; Flow would re-implement the same criteria table | this skill |
| Same, but on any other object (Account, Opportunity, custom) | **Record-triggered Flow (before-save) setting `OwnerId`**, Apex if the lookup logic needs code | Assignment rules exist only for Lead and Case | `flow/record-triggered-flow-patterns`, `apex/trigger-framework` |
| Distribute work from a queue to whichever agent is available and has capacity | **Omni-Channel** (queue-based or skills-based routing) on top of an assignment rule that lands the record in the queue | Assignment rules pick a queue, never a person inside it; Apex round-robin ignores presence and capacity | `admin/omni-channel-routing-setup` |
| Equal distribution among a fixed rep list, no Omni-Channel licence | **Apex trigger with a counter** (Custom Setting) | Flow counter is unsafe under concurrent inserts; rules have no rotation concept | this skill, Common Patterns |
| Geography or account hierarchy ownership for Accounts and Opportunities | **Enterprise Territory Management** | Assignment rules do not run on Accounts; Flow cannot maintain a territory model | `admin/enterprise-territory-management` |
| Prioritise or tier leads before routing | **Lead scoring writes a score field; the assignment rule routes on it** | Scoring (Sales Cloud or Account Engagement) never sets an owner by itself | `admin/lead-scoring-requirements`, `admin/mcae-lead-scoring-and-grading` |
| Re-route or notify when a Case is unresolved past a time threshold | **Escalation rule** (Case only), or entitlement milestones for SLA tracking | Assignment rules fire once at create; a scheduled Flow re-implements the escalation engine | `admin/escalation-rules`, `admin/entitlements-and-milestones` |
| Control who owns the Account / Contact / Opportunity created on lead convert | **Lead conversion Apex or Flow** | Assignment rules do not run during conversion | `apex/lead-conversion-customization` |
| Third-party routing product (LeanData-style, RevOps tools) owns assignment | **Treat it as an integration** | Two writers of `OwnerId` produce flip-flopping owners; either it passes the assignment header and the rule stays authoritative, or the rule is deactivated and the product is | this skill, gotchas #1 |

## The standard Service Cloud stack

Assignment rule (lands the Case in the right queue) → Omni-Channel (pushes it to an available agent) → Escalation rule or milestones (acts when it sits too long). Each layer answers a different question; skipping the first and pointing Omni-Channel at every Case is the most common way to lose the criteria audit trail.

## Five questions that settle it

1. Is the object Lead or Case? If not, assignment rules are off the table.
2. Is the target a queue or a person? Queues are resilient to staff changes; people are not.
3. Does someone need to be *available* to receive it? Then Omni-Channel, not a rule or Apex.
4. Is the routing key a computed value (score, tier)? Compute it first (Flow or scoring), route on the plain field second.
5. Does anything else write `OwnerId` after save? If yes, decide which writer is authoritative and remove the other (`references/troubleshooting.md`, step 5).
