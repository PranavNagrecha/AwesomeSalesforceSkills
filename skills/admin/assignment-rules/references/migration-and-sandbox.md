# Migration and Sandbox Notes — Assignment, Auto-Response and Escalation Rules

What breaks when rules move between orgs, and what a sandbox refresh does to them.

## Rules reference things by name, not Id

Everything inside a rule file resolves by developer name or username in the **target** org, so the target must already contain:

| Reference in the rule | Resolved against | Deploy it first as |
|---|---|---|
| `assignedTo` with `assignedToType` `Queue` | Queue developer name, and the queue must list the object in its supported objects | `Queue` metadata (`queues/<Name>.queue-meta.xml`) — `admin/queues-and-public-groups` |
| `assignedTo` with `assignedToType` `User` | Username | Nothing deployable — the user must exist with that exact username |
| `template` / `assignedToTemplate` / `notifyToTemplate` | `Folder/Template_Developer_Name`; Classic templates only — the Metadata API guide notes Lightning email templates are not packageable | `EmailTemplate` plus its `EmailFolder` — `admin/email-templates-and-alerts` |
| `businessHours` (escalation, `businessHoursSource` = `Static`) | Business hours name | `BusinessHoursEntry` in `BusinessHoursSettings` — see the Business Hours section of `admin/escalation-rules` |
| `criteriaItems` `field` | Field API name on the object | Fields, record types, picklist values |

A rule that references a missing queue or template fails deploy validation; a rule that references a missing user fails the same way. Deploy in this order: fields → queues → templates → business hours → rules.

## Usernames are different in every org

Usernames are globally unique, and a sandbox copies production users with the sandbox name appended to each username (`devops/sandbox-refresh-and-templates`). So a rule entry retrieved from a sandbox that targets `jane@acme.com.uat` cannot deploy to production, and the production version cannot deploy to the sandbox. Consequences:

- Prefer queue targets. A queue's developer name is the same in every org; membership is maintained per org without touching the rule.
- If a user target is unavoidable, keep the rule file production-shaped in source control and accept that sandbox validation of that entry needs a per-org edit.

## Activation travels with the file

`<active>true</active>` in a deployed rule activates it, and since only one rule per object can be active, the previously active rule in the target org is deactivated by that deploy without any warning. Retrieve before you deploy so the file you push contains every rule for the object with the activation state you intend, and treat a deploy that flips `active` as a change-management event, exactly like clicking Active in Setup.

## Sandbox refresh overwrites the sandbox copy

A refresh replaces the sandbox's rules with production's. Rules built only in a sandbox are gone after the refresh unless they were retrieved to source control. Commit the three rule files (`assignmentRules/`, `autoResponseRules/`, `escalationRules/`) whenever they change.

## Ids are not portable

- Data Loader's `sfdc.assignmentRule` and the Bulk API assignment rule setting take an **Id**, which differs per org. Look it up in each org: `SELECT Id FROM AssignmentRule WHERE Name = 'Global Lead Routing' AND SobjectType = 'Lead'`.
- REST `Sforce-Auto-Assign: true` and Apex `useDefaultRule = true` avoid the Id entirely; prefer them where the integration supports it.

## Post-deploy checklist

- [ ] `python3 skills/admin/assignment-rules/scripts/check_assignment_rules.py` passes on the deployed folder (one active rule, catch-all present, no empty active rule)
- [ ] `SELECT COUNT() FROM AssignmentRule WHERE SobjectType = 'Case' AND Active = true` returns 1 in the target org
- [ ] Every queue named in the file appears in `SELECT Queue.DeveloperName FROM QueueSobject WHERE SobjectType = 'Case'`
- [ ] Auto-response sender addresses exist as verified org-wide email addresses in the target org
- [ ] In a sandbox, email deliverability is raised from system-only before testing auto-response
- [ ] One record per channel created and its owner recorded (`references/testing.md`)
- [ ] Integration teams re-confirmed the header or rule Id for the target org
