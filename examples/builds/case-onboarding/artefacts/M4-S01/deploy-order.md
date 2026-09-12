# Deploy order — M4-S01 (Business Hours and Holidays)

Written by `agents/metadata-builder` on every run, per its AGENT.md Step 7. **Nothing in this build
deploys.** The command at the end is validate-only text for a human to copy; this agent ran no `sf`
command of any kind.

**Note on declaration:** this file is *not* in `plan.json` `steps[M4-S01].outputs[]` — three paths are
declared (`settings/BusinessHours.settings-meta.xml`, `holiday-maintenance-runbook.md`, `package.xml`).
It is written anyway because the human's deploy reads it, which is the same undeclared-`deploy-order.md`
pattern `decisions.md` **O-M3S02-03** records for `M3-S01`, `M3-S02`, `M3-S03` and `M3-S04`. It is
reported again in this run's envelope as an undeclared artefact rather than left for a reader to notice.

---

## 0. Checker status — the checker-policy block is closed

This step was first run at `2026-09-12T06:31:35Z` and ended **blocked** (`checker-policy`): the checker
`plan.json` `steps[M4-S01].acceptance_tests[0]` declares rejected the `Severity 1 24x7` calendar, because
its rule fired on any calendar whose seven days are all `00:00:00.000Z`–`00:00:00.000Z`. That shape was
then, and is now, the only always-open form the skill documents, and `requirement.md` L18 ("Severity 1
outages are 24/7 and never pause") is what asked for it.

**Resolved at the source, not here.** Commit `5b206697a` (`admin/business-hours-and-holidays` v1.0.1)
scopes the rule to the calendar it was always about: the 24/7 shape is an **ERROR** on the org default
(`<default>true</default>`) or on a calendar named literally `Default` — the shipped calendar nobody
edited — and an **INFO** line on any other, deliberately named always-open calendar. INFO never affects
the exit code, including under `--strict`. The same commit added this exact calendar to
`references/examples.md` Example 1, so the shape below is now a documented worked example rather than an
extrapolation from gotcha #1.

**No artefact in this step changed.** The file that was rejected is byte-for-byte the file that now
passes; only the rule moved. Re-run of the declared command, verbatim, from the build directory:

```text
$ python3 skills/admin/business-hours-and-holidays/scripts/check_business_hours_and_holidays.py \
    --manifest-dir artefacts/M4-S01
INFO: BusinessHours.settings-meta.xml / always-open calendar 'Severity 1 24x7': SLA clocks on it never
pause — intended for 24/7 severity tiers; confirm it is not attached to entitlements that expect
business-hour pauses.
EXIT=0
```

### The INFO line asks for one confirmation — here it is

*"confirm it is not attached to entitlements that expect business-hour pauses."*

| Consumer | Reads `Severity 1 24x7`? | Evidence |
|---|---|---|
| `M4-S02` entitlement processes | **no** — the two processes are Premier (240 minutes) and Standard (1 business day), both business-time promises | `plan.json` `steps[M4-S02].inputs` |
| `M4-S03` before-save Flow | **no** — it stamps `Case.BusinessHoursId` from `Account.Region__c` (Q40), which yields `EMEA Support` or `US Support` only | `plan.json` `steps[M4-S03].inputs` |
| `M4-S04` escalation rules | **no** — the Severity 1 entry uses `businessHoursSource = None`, which reads no calendar at all | `plan.json` `steps[M4-S04].inputs.note` |
| Holidays in this file | **none attached to it**, deliberately — a holiday would pause a calendar whose whole purpose is not to | § 1 of `holiday-maintenance-runbook.md` |

So the calendar is presently **unconsumed**: it is the metadata expression of the 24/7 promise that
`M4-S04` carries operationally through `businessHoursSource = None`. That is worth a line at the M4
gate, and it is why the skill's own Decision Guidance names the escalation-entry mechanism first. The
calendar earns its place the moment a Severity 1 **entitlement process** exists, because a milestone has
no `None` source — it reads the process calendar (`gotchas.md` #5). **Anyone adding such a process
points it at this calendar; anyone adding a business-hours process must not.**

### Kept as a record: the two repairs that were rejected while blocked

Neither was written, and neither should be revived now that the rule is scoped.

| Repair | Checker result (verified on scratch copies) | Why it was wrong |
|---|---|---|
| Delete the `Severity 1 24x7` calendar | exit 0 | Deletes something `steps[M4-S01].inputs{}` names and `acceptance_tests[3]` asserts |
| Trim that calendar to Mon–Fri (5 midnight pairs) | exit 0 | **The trap.** Passes the gate while making the never-pausing calendar closed at weekends — the opposite of the requirement, invisible to every downstream check |

A third, writing the days as e.g. `00:00:00.000Z`–`23:59:59.000Z`, was rejected untested: the skill
documents no such value, and it would leave a one-second gap at every midnight.

---

## 1. What this step deploys

| Type | Member | File |
|---|---|---|
| `Settings` | `BusinessHours` | `settings/BusinessHours.settings-meta.xml` |

One member, named explicitly. `SKILL.md` § "Deployable metadata: one settings file": all calendars and
holidays live in **one** file, deployed as `Settings` with member `BusinessHours` (API 29.0+), and the
`package.xml` fragment in `references/examples.md` is the shape copied here. `<version>` is `67.0` per
this build's G3 decision 6, matching `artefacts/M3-S03/package.xml`.

`holiday-maintenance-runbook.md` and this file are build artefacts, not deployable metadata, and are
deliberately not `package.xml` members.

## 2. Order inside the step

There is no intra-step order: one file, one member. The order that matters is **inside** the file, and
it is a deploy-time fact rather than a preference: a `holidays` entry names its calendars by
`<businessHours>` name, so every calendar a holiday names must exist in the same file. All three
`businessHours` entries therefore precede the `holidays` entries, following the retrieved-file layout in
`references/examples.md`.

## 3. Order against the rest of the build

`steps[M4-S01].depends_on` is empty — nothing has to deploy before this. Three later steps depend on it,
and each depends on a **name** in this file, not on an Id:

| Step | What it reads from here | Breaks if |
|---|---|---|
| `M4-S02` (entitlement processes) | `<businessHours>` on each process and milestone must be a `<name>` in this file | a calendar is renamed — `check_entitlements_and_milestones.py` W3 catches it at build scope |
| `M4-S03` (before-save Flow) | looks up `BusinessHours` by `Name` to stamp `Case.BusinessHoursId` (Q40: `Account.Region__c` → EMEA, else US) | the Flow's literal names drift from `US Support` / `EMEA Support` |
| `M4-S04` (escalation rules) | the 8-business-hour entry uses `businessHoursSource = Case`, so it reads whatever `M4-S03` stamped; the Severity 1 entry uses `None` and reads no calendar at all | `Case.BusinessHoursId` is null — then the **org default** (`US Support`) applies (`gotchas.md` #4) |

Deploy this file **before** `M4-S02` and `M4-S04`. A `Settings:BusinessHours` deploy is independent of
the Case object work in M1–M3.

## 4. Grounding — what is copied, and what this build could not confirm

Every element name and enum value written here comes from
`skills/admin/business-hours-and-holidays/references/examples.md` Example 1 (a retrieved
`BusinessHoursSettings` file, extended by commit `5b206697a` with the always-open calendar) and
`SKILL.md` § "Deployable metadata: one settings file". Five things the skill does not settle outright are
marked below rather than guessed; commit `5b206697a` narrowed two of them and closed neither.

**UNVERIFIED — the midnight pair.** `00:00:00.000Z`–`00:00:00.000Z` is written on all seven days of
`Severity 1 24x7`. Three things now stand behind it, and the reading is still not closed:
`references/gotchas.md` #1 (the shipped 24/7 `Default` calendar stores every day that way and *"the same
pair of values means 'open the whole day'"*); `references/examples.md` Example 1, which since commit
`5b206697a` carries this exact calendar as a documented worked example; and the Metadata API Developer
Guide (`api_meta` L111304–111306), which documents `00:00:00.000Z` on the `*EndTime` fields as
**"midnight"** — the value's meaning, not the pair's. **Gotcha #6 is unchanged and still marks the pair
UNVERIFIED**: from the documented shape alone you cannot tell "open 24 hours" from "closed", and the
prescribed resolution is not a document but an org — *"set one day to closed and one to 24 hours in
Setup, retrieve, and compare before hand-writing either."* **Do that before trusting `Severity 1 24x7`**,
and prove it with the clock test in the runbook § 5. This build is `design-only` and has no org, so the
check could not be run here.

**Partly resolved — where `saturday*` / `sunday*` sit in the element sequence.** When this step was
first built, the skill's sample omitted weekend days entirely (it was retrieved from calendars with
weekends closed), so their position was an extrapolation of the sample's week order. Commit `5b206697a`
added the `Severity 1 24x7` block to `references/examples.md` with `saturdayStartTime` … `sundayEndTime`
in exactly the positions written here, so the ordering is now copied from the skill rather than inferred.
It is documented-by-example, **not** confirmed against a retrieve or a `--dry-run` deploy; if the
Metadata API enforces a different sequence for `BusinessHoursSettings` children, this is still the
element a deploy would reject, and nothing else in the file departs from the sample's order.

**Omitted deliberately — `<description>` on a holiday.** `SKILL.md` lists `description` among a
`holidays` entry's fields, but the worked example does not include it, so its position in the sequence
is unstated. Rather than place it by guess, no entry carries one; the holiday names are self-describing
and the runbook § 3 carries the reasoning.

**Omitted deliberately — recurrence frequency.** The skill documents `isRecurring`,
`recurrenceStartDate` and `recurrenceEndDate` but **no element that states how often** a holiday
recurs. Every entry is therefore `isRecurring=false` with an explicit `activityDate`. Runbook § 3
carries the full reasoning and the maintenance cost this creates.

**Business content, not metadata shape — the holiday list itself is UNCONFIRMED.** No clarification
question asked for Acme's holiday dates (Q39 established only that each region has its own set). The 14
entries are a seeded 12-month set whose weekdays were computed, not recalled; they are not Acme's list
until the Q90 owner says so. Runbook § 3 is the table that owner edits.

## 5. Validate-only command for a human

Run against a sandbox, never production, and only after retrieving the target's own file first
(`gotchas.md` #8 — this member is the whole calendar set):

```bash
sf project retrieve start --metadata Settings:BusinessHours --target-org <sandbox-alias>
# merge this build's calendars into the retrieved file, then:
sf project deploy start --manifest .sfskills/builds/case-onboarding/artefacts/M4-S01/package.xml \
  --dry-run --target-org <sandbox-alias>
```

`--dry-run` validates without saving. This agent did not run it and must not.
