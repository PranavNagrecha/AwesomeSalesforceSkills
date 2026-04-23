# Flow Versioning — Examples

## Example 1: Non-Breaking Bump

Flow `CustomerOnboarding` — v12 active. Change: add optional variable
`partnerAccountId`.

- Create v13, default partnerAccountId = null.
- Activate v13.
- v12 inactive, paused interviews resume on v12.
- 30 days after last paused interview on v12 drains, delete v12.

## Example 2: Breaking Change → New Flow

Flow `CustomerOnboarding` — v13 active. Change: rename
`customerId` to `accountId` everywhere. This is contract-breaking for
paused interviews and callers.

- Do NOT bump to v14.
- Create new flow `CustomerOnboarding2`.
- Point new traffic to new flow via caller switch.
- Drain v13 paused interviews (30-90 days depending on max pause).
- Retire `CustomerOnboarding` entirely.

## Example 3: Cleanup Job (SOQL)

```sql
SELECT DefinitionId, VersionNumber, Status, LastModifiedDate
FROM Flow
WHERE Status = 'Obsolete'
  AND LastModifiedDate < LAST_N_DAYS:30
```

Feed into a removal script reviewed by the owning team.

## Example 4: Paused Interview Report

```sql
SELECT FlowDefinitionDeveloperName, CurrentElement, PauseLabel,
       CreatedDate, InterviewLabel
FROM FlowInterview
WHERE IsPaused = true
ORDER BY CreatedDate ASC
```

Oldest paused interviews indicate drain progress.

## Example 5: PR-Embedded Changelog

```text
### Flow: QuoteApproval
- From: v7 (active)
- To:   v8 (this PR)
- Diff: split "Qualify" decision into two branches
- Breaking? NO — output shape unchanged.
- Rollback: activate v7.
- Retire v6: after v8 active 30 days.
```

## Example 6: Activation Checklist

- [ ] Diff vs active, breaking-change list reviewed.
- [ ] Callers inventoried.
- [ ] Tests updated.
- [ ] Paused interview drain plan documented.
- [ ] Rollback plan = activate prior version (no redeploy).
