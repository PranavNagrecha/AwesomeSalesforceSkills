# Opportunity Management — Design Record

Fill this in before building. It is the input to `references/metadata-examples.md` and the
evidence a reviewer reads. Delete rows that do not apply; do not delete headings.

**Skill:** `opportunity-management`
**Org / sandbox:** `<alias>`
**Author / date:** `<name>` / `<YYYY-MM-DD>`
**Request summary:** `<what was asked for, in one sentence>`

---

## 1. Motions and record types

One row per distinct sales motion. Each motion needs its own `BusinessProcess`, and — because a
record type binds exactly one process, and only one Path can exist per record type — its own
record type if it needs its own stage subset or its own guidance.

| Motion | `BusinessProcess` `fullName` (bare) | Record type `fullName` | Path needed? | Default for which profiles? |
|---|---|---|---|---|
| New business | `New Business` | `New_Business` | yes | |
| Renewal | | | | |

## 2. Stage ladder

The single source of truth for the `standardValueSet` deploy. Use the **metadata** vocabulary in
the `forecastCategory` column: `Pipeline`, `BestCase`, `Forecast` (= UI "Commit"), `Closed`,
`Omitted`. Mark which motions expose each stage.

| Order | Stage `fullName` | `probability` | `forecastCategory` (metadata) | UI category | `won` | `closed` | In motions |
|---|---|---|---|---|---|---|---|
| 1 | Prospecting | 10 | `Pipeline` | Pipeline | false | false | all |
| … | | | | | | | |
| n | Closed Won | 100 | `Closed` | Closed | true | true | all |
| n+1 | Closed Lost | 0 | `Omitted` | Omitted | false | true | all |

Checks to tick off on this table:

- [ ] Every motion's process contains at least one `won` stage and at least one `closed`-not-`won` stage
- [ ] `Closed Lost` maps to `Omitted`, not `Closed`
- [ ] Probabilities are monotonic within each motion
- [ ] No stage is being **deleted**; retirements are deactivations, with the audit in `references/examples.md` run first

## 3. Existing-data impact

Complete before editing anything. Query 1 in the anti-pattern section of `references/examples.md`.

| Stage being changed or retired | Open records | Closed records | Migration target | Owner of the migration |
|---|---|---|---|---|
| | | | | |

## 4. Path design

One block per record type. `picklistValueName` must be a stage that record type's process exposes.

| Record type | Stage (`picklistValueName`) | Key fields (`fieldNames`) | Guidance summary |
|---|---|---|---|
| | | | |

- [ ] Confirmed only one Path exists per record type (platform ceiling)
- [ ] No existing Path's `entityName` / `fieldName` / `recordTypeName` is being edited — those need delete-and-recreate
- [ ] Path component placement on the Lightning record page is in the runbook, since no deploy carries it

## 5. Enforcement

Path guides; validation rules enforce. List every progression rule the business asked for and where
it actually lives.

| Requirement | Mechanism (validation rule / Flow / none) | API name | Tested? |
|---|---|---|---|
| | | | |

## 6. Teams and splits

- Team selling required? `yes / no` → `enableOpportunityTeam` in `settings/Opportunity.settings-meta.xml`
- Access level per team role:

  | Team role | `OpportunityAccessLevel` (`Read` / `Edit` / `All`) | Justification vs OWD |
  |---|---|---|
  | | | |

- Splits required? `yes / no`. If yes, record the decision and who signed it — splits cannot be disabled
  once data exists, and split types cannot be created or deleted through any API.

  | Split type label | `IsTotalValidated` (fixed at creation) | Which forecast type consumes it |
  |---|---|---|
  | | | |

- Who may set `IsPrivate`, and is the field on the layout? `<answer>` — setting it removes teams, splits
  and sharing from that record.

## 7. Manual-Setup register

The states no deploy can carry. Someone performs these by hand in every org; list them here so the
runbook can.

| Step | Org(s) | Owner | Done |
|---|---|---|---|
| Enable Opportunity Splits in Setup | | | [ ] |
| Create split type(s) with the exact labels in §6 | | | [ ] |
| Place the Path component on the Lightning record page | | | [ ] |
| Confirm field history tracking on the stage field | | | [ ] |

## 8. Verification evidence

Paste the results, not a claim that they passed.

| Check | Where | Result |
|---|---|---|
| `check_opportunity_management.py --manifest-dir …` | | |
| Query 8a — stage ladder | `references/metadata-examples.md` §8 | |
| Query 8b — pipeline by stage and category | §8 | |
| Query 8d — validated splits total 100 (expect zero rows) | §8 | |
| Setup check 8e — splits, split types, Path placement | §8 | |

## 9. Deviations

Anything done differently from the patterns in `SKILL.md`, and why. An empty section means the
standard pattern was followed exactly — say so rather than leaving it blank.
