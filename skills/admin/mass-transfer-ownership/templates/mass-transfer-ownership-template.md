# Mass Transfer Ownership — Run Sheet

One run sheet per transfer event. Fill it in before the first row is written; the completed
sheet plus the rollback CSV plus the job result files are the audit trail.

**Skill:** `mass-transfer-ownership`
**Event:** _(e.g. "Jamie Reyes departure, 2026-09-08" / "Q4 territory cut, 30 → 18")_
**Requested by / approver:**
**Window:** _(date, time, time zone — and whether it is inside business hours)_

---

## 1. Answers to the pre-configuration questions

Copy the answers from the `Questions to Ask Before Configuring` table in SKILL.md. An
unanswered row here is a decision the tool will make for you.

| Question | Answer |
|---|---|
| Scope: which owners, which objects, open records only or everything? | |
| Cascade: which child objects must follow the parent, and in what order? | |
| Teams: do Account or Opportunity team members have to survive the move? | |
| Notification: must the new owner be emailed? | |
| Assignment rules: should they fire, or must they be suppressed? | |
| Reversal: what is the rollback trigger, and who decides? | |
| Volume: per-object row counts from the §1 impact queries. | |

## 2. Volume inventory

Counts from `references/metadata-examples.md` §1. Fill in every in-scope object, including the
ones you expect to be zero — a zero you checked is different from a zero you assumed.

| Object | Source owner(s) | Rows in scope | Open / closed split | Queue-owned rows | Team rows |
|---|---|---|---|---|---|
| Account | | | n/a | | |
| Opportunity | | | | | |
| Case | | | | | |
| Contact | | | n/a | | |
| _custom object_ | | | | | |

## 3. Tool decision

| Object | Tool | Why this one, from the SKILL.md decision table |
|---|---|---|
| | | |

Settings that must be explicit for each tool run:

- [ ] Assignment rule: **cleared** in Data Loader Settings / `assignmentRuleId` **omitted** from
      the Bulk API job body / `assignmentRuleHeader` **unset** in Apex — or, if rules must fire,
      the rule id recorded here: ______
- [ ] New-owner email: not sent on the Bulk API or Data Loader path. If the business requires
      it, the run moves to Apex with `EmailHeader.triggerUserEmail = true`. Decision: ______
- [ ] Serial vs. parallel (Data Loader) and batch size: ______
- [ ] Keep Account Teams: on/off. If on, confirm the file has one old owner and one new owner.

## 4. Sharing recalculation plan

- Org-wide default for each in-scope object: ______
- Deferral needed? _(rule of thumb in SKILL.md; the feature needs a Salesforce Support case
  before it can be used at all)_
- Support case raised on: ______  Enabled on: ______
- `Sharing.settings` retrieved to source control before the change: [ ]
- Resume scheduled for: ______ _(the resume, not the transfer, is the long half)_

## 5. Rollback artefacts captured before execution

- [ ] Plan CSV with `Id,OwnerId,Old_OwnerId` exported: path ______
- [ ] Linted clean: `python3 scripts/check_mass_transfer_ownership.py --plan <file>`
- [ ] `AccountTeamMember` / `OpportunityTeamMember` snapshot exported: path ______
- [ ] Pre-transfer counts recorded in §2 above

## 6. Execution log

| # | Object | Tool | Job / batch id | Start | End | Success | Errors |
|---|---|---|---|---|---|---|---|
| 1 | | | | | | | |
| 2 | | | | | | | |

- [ ] Bulk API result files (`successfulResults`, `failedResults`, `unprocessedRecords`) pulled
      the same day — they are deleted after seven days
- [ ] Data Loader `success.csv` and `error.csv` archived

## 7. Validation

Run the §6 query set in `references/metadata-examples.md` and record the result of each.

| Check | Expected | Actual |
|---|---|---|
| Source owners hold nothing in scope | 0 | |
| Target owner count matches §2 | | |
| Child ownership matches the cascade decision | | |
| No records landed on an inactive user | 0 | |
| Team row counts vs. the §5 snapshot | | |
| `UserRecordAccess` sample: new owner has read/edit | all true | |

- [ ] Background Jobs shows no remaining *Sharing Rule Recalculation* rows
- [ ] Deferral flags returned to `false` and the resume confirmed complete

## 8. Deviations and follow-ups

Record anything that differed from the plan and why, plus any side effect that rollback would
not undo (team members lost, emails sent, downstream automation fired). These are the notes the
next transfer reads.

| Deviation | Reason | Follow-up owner |
|---|---|---|
| | | |
