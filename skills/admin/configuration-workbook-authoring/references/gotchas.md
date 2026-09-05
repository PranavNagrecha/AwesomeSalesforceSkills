# Gotchas — Configuration Workbook Authoring

Non-obvious failure modes that turn a workbook from a delivery instrument
into a graveyard.

---

## Gotcha 1: The workbook becomes a wiki nobody maintains

**What happens:** The workbook gets authored at sprint kickoff, lives in
Notion or a Confluence page, and is never updated again. By mid-sprint the
admin team is working off Slack threads and the workbook is stale.

**When it occurs:** Whenever the workbook is treated as a *one-time*
deliverable rather than the canonical sprint instrument.

**How to avoid:** Version-lock the workbook in the repo at sprint commit
(`docs/workbooks/<release>/cwb.md`). After commit, every change is a *new*
row, not an edit-in-place. CI runs `python3 scripts/check_workbook.py` on
every PR that touches the file.

---

## Gotcha 2: Rows that span multiple sections

**What happens:** A single row reads "Add Account Plan object, give the SDR
PSG access, and trigger a notification flow on insert." That row touches
three sections (Objects+Fields, Permission Sets+PSGs, Automation) and would
need to be addressed by three different agents.

**When it occurs:** When the row author thinks in features rather than in
configurable artifacts.

**How to avoid:** Enforce **one row, one agent, one section**. If a row's
content needs more than one `recommended_agent`, split it. The split rows
share the same `source_story_id` and `source_req_id`; cross-row dependencies
go in `notes`.

---

## Gotcha 3: Missing `source_req_id` produces orphan rows

**What happens:** A row appears in the workbook with no fit-gap reference. By
the time release notes are written, nobody can explain why the field exists.

**When it occurs:** When the admin team adds "obvious" rows during build
without going back to the BA. Or when the BA forgot to open a fit-gap row.

**How to avoid:** Hard rule — every row must carry both `source_req_id` and
`source_story_id`. Reviewers reject orphan rows; `check_workbook.py` flags
them. If a real configurable change has no fit-gap row, the workflow stops
and the BA opens one before the workbook row is written.

---

## Gotcha 4: The workbook drifts from org reality (no version-lock)

**What happens:** The team re-runs the workbook generator midway through the
sprint, picking up new rows and silently losing rows that were already
deployed. The post-sprint audit finds metadata in the org with no
corresponding workbook row.

**When it occurs:** When the workbook is regenerated rather than amended, or
when authors edit existing rows in place after sprint commit.

**How to avoid:** The committed workbook is **immutable**. Mid-sprint change
requests open new rows with `status: change-requested` and reference the
superseded row in `notes`. Old rows stay; their `target_value` is preserved
as historical record. Tag the file at sprint commit so reverts are possible.

---

## Gotcha 5: The workbook is "just notes" with no schema

**What happens:** Someone authors a freeform document with prose like "We
need a few new fields on Opportunity, plus the SDR PSG, plus probably a
Flow." There are no rows, no IDs, no owners, no agents.

**When it occurs:** When a project skips the schema because it feels like
overkill for a small feature.

**How to avoid:** Even a one-row workbook uses the canonical row schema. The
overhead is trivial; the audit value is enormous. Generic templates live in
`templates/config-workbook.md` — copy and fill, never freestyle.

---

## Gotcha 6: The Integrations section is omitted

**What happens:** The team writes the first 9 sections, deploys, and then
discovers a fit-gap row required a new Named Credential and Connected App.
The integration team is angry; the workbook silently dropped their work.

**When it occurs:** When the workbook author treats Integrations as
"something the integration team owns separately."

**How to avoid:** The Integrations section is **always present**. If the
release truly has no integration work, the section carries a single row
labeled `not-in-scope-this-release` with that as `target_value` and the
release manager as owner. An empty section is information; a missing one is
a gap.

---

## Gotcha 7: Inline credentials in `target_value`

**What happens:** A row's `target_value` reads "Connect to API at
https://api.example.com with key sk_live_…". The workbook is committed to
git. Now the secret is in version control forever.

**When it occurs:** When an author copies the integration spec verbatim and
forgets to substitute Named Credential aliases for raw secrets.

**How to avoid:** Workbook rows reference Named Credentials by alias only
(e.g. `target_value: "Use Named Credential alias 'AcmeBilling_API'"`). The
checker greps for raw secret patterns; reviewers reject any row with an
inline secret regardless of how the row got committed.

---

## Gotcha 8: `recommended_agent` references an invented or deprecated agent

**What happens:** A row's `recommended_agent` says `data-loader-agent`, which
isn't a real agent in the runtime roster. The hand-off step silently fails or
gets routed to a human who doesn't know what to do.

**When it occurs:** When the author writes the agent name from memory rather
than checking `agents/_shared/SKILL_MAP.md`.

**How to avoid:** `check_workbook.py` validates every `recommended_agent`
value against the live runtime roster (read from `agents/_shared/SKILL_MAP.md`
plus the `agents/<name>/AGENT.md` directory listing). Deprecated agents (e.g.
`validation-rule-auditor` superseded by `audit-router --domain
validation_rule`) are flagged with a hint pointing to the replacement.

---

## Gotcha 9: `target_value` names the Setup screen instead of the component

**What happens:** A row reads `Setup → Object Manager → Lead → Fields & Relationships → New`. It looks like an instruction and reviews cleanly, but nothing downstream can use it. The executing agent cannot tell whether the field is Number or Picklist; the deployment manifest cannot be built from it at all, because `package.xml` addresses components by `fullName` inside a `<members>` element — `Lead.Qualification_Score__c`, never a click-path. The row survives to sprint commit and turns into a conversation.

**When it occurs:** When the row is transcribed from a demo, a screen recording, or a training doc — all of which describe navigation because that is what a human watching needs.

**How to avoid:** `target_value` states the component and its settable values: type, length, required, default, restricted, the value set it draws from. `check_workbook.py` flags cells matching `Setup →`, `Object Manager →`, "go to Setup" and "navigate to". A useful self-test: if the cell cannot become a `<members>` line, it is not a row yet.

---

## Gotcha 10: A row names two agents, so neither picks it up

**What happens:** `recommended_agent` reads `object-designer, flow-builder` or `permission-set-architect / audit-router`. Both agents read the workbook, both see a row addressed half to them, and the row is executed twice with different assumptions or not at all. This is distinct from Gotcha 2 — the row can sit inside a single section and still name two agents, because the author was describing *the work* rather than *the artefact*.

**When it occurs:** When one configurable artefact genuinely needs a second agent to be useful (a field plus the Flow that populates it), and the author records the dependency in the routing column instead of in `notes`.

**How to avoid:** One row, one agent. The dependency belongs in `notes` as a `row_id` reference (`Depends on CWB-OBJ-101`). `check_workbook.py` splits the cell on `,` `;` `/` `+` `and` `or` `then` and reports the row when more than one fragment resolves to a real agent — while leaving `audit-router --domain=sharing` alone, since everything after the first space is invocation argument, not a second agent.

---

## Gotcha 11: A `recommended_skills` citation that does not resolve

**What happens:** A row cites `admin/lead-sharing-rules`. It reads correctly, matches the repo's naming convention, and does not exist. The executing agent reads its Mandatory Reads, finds nothing at that path, and either proceeds ungrounded or stops. Plausible-slug citations are the single most common defect in machine-authored workbooks precisely because they are indistinguishable from real ones by eye.

**When it occurs:** When the author writes the skill id from memory rather than from `agents/_shared/SKILL_MAP.md` — whose own opening paragraph states that every skill id it lists has been verified to exist and that a new citation must be verified before it is committed.

**How to avoid:** `check_workbook.py` resolves every entry against disk and prints the exact path it looked for: `recommended_skills entry \`admin/lead-sharing-rules\` does not resolve — skills/admin/lead-sharing-rules/SKILL.md does not exist`. It handles all three accepted shapes — `<domain>/<slug>`, `<domain>/<slug> → references/<file>.md`, and repo-relative `templates/…` or `standards/…` paths — so a correct citation never has to be rewritten to satisfy the checker.

---

## Gotcha 12: A Section 6 row with no decision-tree branch

**What happens:** A row says "build a Flow" and nothing else. Nobody can tell whether Flow was chosen or defaulted to. Six months later the row is the only record of the decision, the Flow has grown a callout and a loop, and the review that would have caught it never happened because there was nothing to disagree with.

**When it occurs:** When the tool was obvious to the author at the time. Obvious-at-the-time is exactly the decision that goes unrecorded.

**How to avoid:** Every Section 6 row cites `standards/decision-trees/automation-selection.md` **and the branch that resolved it** — the tree labels its branches `Q1`…`Q12`, so `automation-selection.md Q2` plus a clause of reason. `check_workbook.py` reports the missing citation and, separately, a citation with no `Q<n>` branch. When the tree genuinely does not cover the decision — ownership routing on Lead or Case, for instance, which `admin/assignment-rules` → `references/routing-selector.md` states in its own opening is outside `automation-selection.md`'s scope — say which branch you reached, say the tree stops there, and name what did resolve it.

---

## Gotcha 13: A Section 4 row whose artefact is not a sharing rule

**What happens:** A row in Sharing Settings reads "OWD for Lead = Private". It is routed to the sharing auditor, which finds no such component. The org-wide default is the `sharingModel` field on the `CustomObject` metadata type — it deploys inside the object file that Section 1 owns, not in the `SharingRules` container that Section 4 owns, and the Metadata API Developer Guide notes it became settable through the API for internal users only in version 30.0 and later. The two sections have separate files, separate deploy positions, and separate reviewers.

**When it occurs:** Whenever "sharing" is read as a topic rather than as a metadata container. Manual shares make it worse: the guide states outright that manual sharing rules cannot be retrieved, deleted or deployed, so a Section 4 row describing one has no deployable artefact at all and must be recorded as a runbook step somewhere else.

**How to avoid:** Section 4 holds `SharingRules` components — criteria-based, owner-based, territory-based and guest-user rules, all of which live in one `<Object>.sharingRules` file. OWD goes in Section 1 with the object. Restriction rules and manual-share procedure go in `notes` with an explicit "not deployable" flag. Every Section 4 row cites `standards/decision-trees/sharing-selection.md` and its `Q<n>` branch; `check_workbook.py` enforces both halves.

---

## Gotcha 14: Sprint commit without the version lock

**What happens:** The team declares the workbook committed in stand-up, sets the statuses, and keeps editing the file. There is no tag and no snapshot, so "what was committed" is whatever `git log` happens to say later. When a deployed field turns out to differ from its row, nobody can prove whether the row changed or the build did.

**When it occurs:** When `status: committed` is treated as the version lock. It is not — it is a per-row label that an in-place edit can silently rewrite. The lock is the snapshot.

**How to avoid:** Version-locking is two actions, both required: set every in-scope row to `committed`, **and** snapshot the file at `docs/workbooks/<release>/cwb.md` and tag it. From that point the file is append-only — mid-sprint change requests open new rows with `status: change-requested` referencing the superseded `row_id` in `notes`. Run `check_workbook.py` immediately before the tag, not after; and do not pass `--allow-empty-section` at commit time, because that flag turns off exactly the check (Gotcha 6) that catches the section someone forgot.

---

## Gotcha 15: Profiles listed as the grant target when permission sets are the model

**What happens:** A Section 3 row reads "grant edit FLS on the new field to the Sales Ops Profile". It deploys, and then the row cannot be verified from what comes back. Two documented Metadata API behaviours make it unreviewable rather than merely unfashionable. First, the content of a profile returned by Metadata API depends on what else was requested in the same `RetrieveRequest` — profiles only include field-level security for fields included in custom objects returned alongside them — so a retrieve driven by a different manifest silently omits the very permission the row claims. Second, profile deployment is designed to *overlay* the existing settings in the target org: disabled permissions are not exported, so a row that intends to remove access does nothing unless the file explicitly carries `<value>false</value>`. A permission set row has neither property.

**When it occurs:** When the org still assigns most access by profile and the row records the current mechanism rather than the target one. It also occurs when the author knows profiles are legacy but has no rule for the residue and so keeps everything together.

**How to avoid:** Grants go on permission sets, which the Section 3 row names and `permission-set-architect` executes. A Profile row is correct for exactly one thing: the residue with no `PermissionSet` equivalent — `loginHours`, `loginIpRanges`, `layoutAssignments`, `categoryGroupVisibilities`, `loginFlows`, the `default` app inside `applicationVisibilities` and the `default` record type inside `recordTypeVisibilities`. `check_workbook.py` reports a Section 3 row that pairs a grant verb with "Profile" unless the cell names one of those elements. `admin/permission-sets-vs-profiles` owns the decomposition itself; note also that editing standard objects on standard profiles has been disabled since API version 50.0, so a row targeting one will not deploy at all.
