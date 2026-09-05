# Chatter Group Governance — Engagement Worksheet

Fill this in as you run workflow steps 1–5 in `SKILL.md`. It is the artefact you hand back; the checker
output pastes straight into sections 2 and 4.

**Skill:** `admin/chatter-group-governance`
**Org / sandbox:** _______________  **Date:** _______________  **Run by:** _______________

---

## 1. Request

**What was asked for (one sentence):**

**Scope** — tick one:

- [ ] Org-wide governance baseline (settings + permissions + policy)
- [ ] Targeted cleanup of an existing group population
- [ ] Offboarding response for a named user or deactivation wave
- [ ] Compliance / discovery request over the group population

---

## 2. Metadata baseline — workflow step 1

```bash
sf project retrieve start --metadata Settings:Chatter,PermissionSet,Profile --target-org <alias>
python3 scripts/check_chatter_group_governance.py --manifest-dir force-app/main/default
```

| Setting | Value found | Action |
|---|---|---|
| `allowChatterGroupArchiving` | | |
| `unlistedGroupsEnabled` | | |
| `allowRecordsInChatterGroup` | | |
| `enableInviteCsnUsers` | | |

| Permission | Granted where (profiles / permission sets) | Holder count | Action |
|---|---|---|---|
| Create and Own New Chatter Groups | | | |
| Manage Unlisted Groups | | | |
| Modify All Data (transfer capability) | | | |

**Blocking findings** (`CGG-UNLISTED-UNGOV`, `CGG-ARCHIVE-OFF`) — paste the checker lines, and what you
did about each:

---

## 3. Answers to the pre-configuration questions

Copy the answers, not just the questions. An unanswered row is a risk you are carrying into step 5.

| Question | Answer | Consequence if wrong |
|---|---|---|
| Who holds Manage Unlisted Groups? | | Group inventory is incomplete and says nothing about what it omitted |
| Is org-wide archiving on? | | Delete becomes the only cleanup lever |
| Which groups are read-mostly rather than post-mostly? | | They auto-archive while genuinely in use |
| Which groups hold files shared elsewhere? | | Deleting the group deletes those files everywhere |
| Who is the transfer target, person or service account? | | Ownership re-orphans on the next departure |
| Is a batch user deactivation in flight? | | Reciprocal follow relationships are hard-deleted, unrecoverable |
| Any group already has `CanHaveGuests = true`? | | The flag cannot be set back to false |

---

## 4. Group population — workflow step 2

```bash
python3 scripts/check_chatter_group_governance.py \
    --manifest-dir force-app/main/default \
    --group-inventory groups.csv \
    --name-prefixes <agreed prefixes> \
    --inactive-days 365
```

| Bucket | Checker code | Count | Disposition |
|---|---|---|---|
| Active, active owner | — | | leave |
| Active, inactive or missing owner | `CGG-INV-ORPHAN` | | transfer (step 4) |
| Active, no feed activity > threshold | `CGG-INV-STALE` | | archive |
| Active, no activity ever, ≤ 1 member | `CGG-INV-EMPTY` | | delete after confirming direct member count |
| Off-convention names | `CGG-INV-NAMING` | | rename or accept as legacy |
| Unlisted groups | `CGG-INV-UNLISTED` | | confirm a permission holder exists |
| Already archived | — | | leave |

**Naming convention agreed for this org:**

**Auto-archive exemptions** — groups getting `IsAutoArchiveDisabled = true`, with the reason each:

| Group | Reason it must not auto-archive |
|---|---|
| | |

---

## 5. Disposition decisions

**Transfer target chosen:** _______________  **Why this target and not a department head:**

**Groups delete-approved** — each row needs a file check before it is executed:

| Group | Member count (direct COUNT, not `MemberCount`) | Files shared elsewhere? | Approved by |
|---|---|---|---|
| | | | |

**Deviations from the standard pattern, and why:**

---

## 6. Post-change verification

- [ ] Checker re-run on the *re-retrieved* metadata tree — clean, or every remaining finding explained
- [ ] `CGG-INV-ORPHAN` count is zero on a fresh export
- [ ] `Chatter.settings` and the permission-set files committed to source control
- [ ] Offboarding runbook updated so ownership transfer precedes deactivation
- [ ] Next quarterly re-measure scheduled, with today's counts recorded as the baseline
