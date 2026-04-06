# Territory API and Assignment — Work Template

Use this template when working on tasks in this area.

## Scope

**Skill:** `territory-api-and-assignment`

**Request summary:** (fill in what the user asked for)

## Context Gathered

Record the answers to the Before Starting questions from SKILL.md here.

- ETM enabled and Territory2Model in Active state? (verify with `SELECT Id, State FROM Territory2Model WHERE State = 'Active'`)
- Territory2 IDs resolved: (list territory names → IDs)
- Operation type: [ ] UserTerritory2Association DML  [ ] ObjectTerritory2Association DML  [ ] SOAP Rule Evaluation
- Is this synchronous or async context? (If async, SOAP callout must be deferred)
- Estimated record volume: (determines sync vs. batch approach)

## Approach

Which pattern from SKILL.md applies? Why?

- [ ] Pattern 1: Bulk User Territory Assignment
- [ ] Pattern 2: Manual Account-Territory Pin (ObjectTerritory2Association)
- [ ] Pattern 3: SOAP-Based Assignment Rule Evaluation

## Pre-DML Check

Before writing any DML:

- [ ] Queried existing `UserTerritory2Association` or `ObjectTerritory2Association` to identify net-new records
- [ ] Confirmed `AssociationCause` will be set to `'Territory'` (not `'Territory2RuleAssociation'`)
- [ ] Confirmed DML uses `Database.insert(list, false)` with `SaveResult` inspection

## Callout Guard (if rule evaluation needed)

- [ ] Confirmed execution context is synchronous (not Batch, Queueable, Scheduled, or @future)
- [ ] `UserInfo.getSessionId()` will return non-null in this context
- [ ] Account IDs chunked into groups of ≤200
- [ ] Endpoint URL built from `URL.getOrgDomainUrl().toExternalForm()`

## Checklist

Copy the review checklist from SKILL.md and tick items as you complete them.

- [ ] ETM is enabled and at least one Territory2Model is in Active state in the target org
- [ ] All DML uses `Database.insert(list, false)` and inspects `SaveResult`
- [ ] No Apex triggers relied upon to fire on `ObjectTerritory2Association` DML
- [ ] SOAP callout for rule evaluation is not called from async Apex
- [ ] SOAP requests chunked to ≤200 account IDs per call
- [ ] `AssociationCause` explicitly set to `'Territory'` for managed associations
- [ ] Deletion paths exist to clean up stale associations
- [ ] Session ID availability verified before SOAP callout path is invoked

## Notes

Record any deviations from the standard pattern and why. For example:
- If SOAP callout could not be used synchronously, document the Platform Event bridge approach
- If `AssociationCause` needed to be preserved from a migration source, document the override
