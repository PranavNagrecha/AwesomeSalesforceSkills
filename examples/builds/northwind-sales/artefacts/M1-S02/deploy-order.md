# Deploy order — M1-S02

Build: `northwind-sales` · Milestone: M1 (Enterprise and Renewal data model) · Step type: `ui` · API version 62.0 (defaulted — `plan.json` carries no `api_version`)

This note is written by `metadata-builder` and is text for a human. Nothing here is executed by this
agent or by any acceptance test.

Two `Layout` components ship in this step:

| Component | File |
|---|---|
| `Opportunity-Opportunity Enterprise Layout` | `layouts/Opportunity-Opportunity Enterprise Layout.layout-meta.xml` |
| `Opportunity-Opportunity Renewal Layout` | `layouts/Opportunity-Opportunity Renewal Layout.layout-meta.xml` |

---

## 0. Before anything else — the two layouts are incomplete by design (BLOCKING for the related list)

Both files ship with **no `relatedLists` block at all**, so neither layout shows Opportunity
Products when it is deployed as it stands. Requirement item 2 ("reps add products from our price
book to every Enterprise opportunity") is not satisfied by this step's artefacts alone. Close the
gap by retrieving the string from the org rather than by typing it:

```bash
sf project retrieve start --metadata "Layout:Opportunity-Opportunity Layout" --target-org <alias>
```

Then **copy the Opportunity Products `relatedLists` block verbatim** out of the layout that retrieve
emits — the whole `<relatedLists>…</relatedLists>` element, `<relatedList>` name and every `<fields>`
alias inside it — and paste it into both files in this step before deploying.

**Hand-authoring the related-list name is exactly what this instruction exists to prevent.** The
Opportunity Products related-list API name appears in no skill in this library: a grep across
`skills/` and `templates/` returns `RelatedOpportunityTeamList`, `RelatedNoteList` and
`RelatedActivityList` and nothing else, and every one of those is documented as an *example*, not as
a catalogue. `admin/opportunity-management/references/metadata-examples.md` §4 marks
`RelatedOpportunityTeamList` and its three `fields` entries `UNVERIFIED (2026-09-04)` — "the guide
documents the element, not the catalogue of related-list names" — and instructs: retrieve the layout
from an org where the related list is already placed and copy the exact strings the retrieve emits
before deploying the block. `admin/record-types-and-page-layouts/references/metadata-examples.md`
adds the reason a plausible guess fails silently rather than loudly: related-list `fields` for
standard fields are **retrieval aliases, not API names** — Fax, Mobile and Home Phone come back as
`Phone2`, `Phone3`, `Phone4` (api_meta.txt:83121–83124) — so a hand-written API name round-trips
wrong even when it deploys. This is assumption **A26**, risk `medium`, and it is carried here
because a `design-only` build has no org connection to run the retrieve.

Until that block is pasted in, treat the two layouts as field layouts only.

---

## 1. Order within this step

The two layouts are independent of each other. One `sf project deploy start` resolves both, and
their only ordering constraint points **backwards**, at M1-S01:

| # | Component | Must come after | Why |
|---|---|---|---|
| 1 | `CustomField` `Opportunity.Discount__c`, `Opportunity.Approval_Status__c` | — (**M1-S01**) | Both layouts carry a `layoutItems/field` entry naming each of them. A layout item naming a field the org does not hold fails the deploy on the cross-reference. `admin/change-management-and-deployment/references/llm-anti-patterns.md` Anti-Pattern 4 puts objects and fields first and everything that references them after. |
| 2 | `Layout` `Opportunity-Opportunity Enterprise Layout`, `Opportunity-Opportunity Renewal Layout` | 1 | This step. Nothing inside it orders one layout before the other. |

The layouts do **not** depend on the two record types deploying first. A `Layout` file carries no
reference to a record type; the binding between them lives in `Profile.layoutAssignments`, which is
M2-S02's (see §2). Deploying M1-S01 and M1-S02 in one request is the simplest correct order, and it
is the order `scripts/mock_deploy.py --milestone M1` assembles.

---

## 2. Dependencies on components outside this step

| Outside component | Step | Direction |
|---|---|---|
| `Opportunity.Discount__c`, `Opportunity.Approval_Status__c` | **M1-S01** (`documented`) | Deploy **before** this step. See §1. |
| `RecordType` `Opportunity.Enterprise`, `Opportunity.Renewal` | **M1-S01** (`documented`) | No ordering constraint against the layouts themselves, but both must exist before M2-S02 can assign a layout to a record type. |
| `Profile` `Sales User` — `layoutAssignments` + `recordTypeVisibilities` | **M2-S02** (human-gated) | Deploy **after** this step. `layoutAssignments/layout` names the layout in its **file-name form** — `Opportunity-Opportunity Enterprise Layout`, object, hyphen, layout name — and a character-for-character mismatch with the file names above is an `INVALID_CROSS_REFERENCE_KEY`, not a missing-assignment warning. **Until M2-S02 ships, both layouts are deployed metadata that nobody is assigned to**: a permission set can grant record-type visibility only; the page-layout assignment and the default record type exist solely on `Profile` (`admin/record-types-and-page-layouts/references/metadata-examples.md`, "Making the record type visible and assigning the page"). |
| `PathAssistant` `Enterprise_Opportunity_Path`, `Renewal_Opportunity_Path` | **M2-S05** | Independent of the layouts — a Path binds to a record type, not to a layout. Ordered after M1-S01 for the record types. |
| `FlexiPage` `Opportunity_Enterprise_Record_Page` | **M3-S05** | Deploy **after** this step. The Lightning record page is what an Enterprise rep actually opens; this layout supplies the field set its Record Detail region renders and it stays the layout of record for Salesforce Mobile and for any user the FlexiPage assignment does not reach. Changing the field set here without re-reading M3-S05 is how the two drift apart. |
| The build-level `package.xml` | **M4-S04** | Aggregates both `Layout` members from this step's manifest. |

---

## 3. Manual steps no deploy performs

1. **Paste in the Opportunity Products related-list block** (§0). A green deploy of these two files
   is not evidence that a rep can add a product line — it is evidence that the field sections
   deployed.
2. **Discover the platform's layout-required standard fields for Opportunity, one per run.**
   The set of standard fields the platform requires *on an Opportunity layout* is **unverified** and
   is not asserted anywhere in these two files. Only the **Case** set is verified in this library
   (`ContactId`, `Description`, `SuppliedEmail` present, and `Status` at
   `<behavior>Required</behavior>` — `sf project deploy start --dry-run` against a Summer '26
   developer org on 2026-09-05, `examples/builds/case-onboarding/reports/MOCK-DEPLOY-M1.md` runs
   1–5), and `admin/record-types-and-page-layouts/references/metadata-examples.md` says in bold that
   the membership does **not** generalise: *"Do not extrapolate a per-object list — the shape of the
   rule generalises, the membership does not."* `references/gotchas.md` #13 names this build's exact
   temptation and forbids it: *"Do not generalise `Status` to `StageName` on Opportunity … without a
   dry run against the target org."* So no field on either layout carries
   `<behavior>Required</behavior>`.

   Discover the set by iterating the dry run, **one field per run** — the deploy reports a single
   missing field at a time, so a layout three fields short costs three round trips before it even
   reaches the `must be Required` message:

   ```bash
   python3 scripts/mock_deploy.py .sfskills/builds/northwind-sales/plan.json \
     --org-alias <alias> --step M1-S02
   ```

   That script is validation-only: it assembles the step's artefacts into a source tree and runs
   `sf project deploy start --dry-run` (`checkOnly`) against the org. There is no flag to disable
   the dry run and no deploy option, which is why assumption A25 writes it as
   "`scripts/mock_deploy.py --dry-run`" — the `--dry-run` is the behaviour, not a flag you pass.
   Two messages, two different fixes, both in the `Layout` file:

   | Message | Fix |
   |---|---|
   | `Layout must contain an item for required layout field: <Field>` | add a `layoutItems` entry naming that field, any `behavior` |
   | `Field:<Field> must be Required` | set that item's `<behavior>Required</behavior>` |

   Repeat until the layout validates, then apply the same items to **both** files. This is
   assumption **A25**, risk `medium`, and it is the reason this step's artefacts must not be
   described as "deploy-ready" on the strength of a static check
   (`references/llm-anti-patterns.md` Anti-Pattern 6: say "validated by `--dry-run` against \<org\>"
   or say nothing).
3. **Confirm nothing was added to the SMB layout** (Q14). This is satisfied structurally rather than
   by a check: no SMB layout file exists anywhere in this build's outputs, so no deploy in this
   build can touch it. Confirm the same at the M1 gate by reading the build-level manifest
   (M4-S04) rather than by opening the org.
4. **Decide whether two identical layouts are wanted.** The Enterprise and Renewal files are
   byte-for-byte identical; they differ only in file name. That follows from decision **D2** (two
   record types, therefore two layouts and two Paths) and from the one-Path-per-record-type
   constraint, not from any field difference anyone asked for. `admin/record-types-and-page-layouts`
   lists "record type with an identical page layout to another record type" as a merge candidate to
   surface proactively. Keeping both is a defensible choice — it leaves room for the two motions to
   diverge without a later record-type change — but it should be a choice someone made, not a
   by-product.

---

## 4. Verify after deploy

Layouts have no useful SOQL verification of their own. Two checks instead:

- Setup → Object Manager → Opportunity → Page Layouts — both layouts present under those exact
  names.
- Setup → Object Manager → Opportunity → Page Layouts → **Page Layout Assignment** — after M2-S02
  ships, the Sales User row shows the Enterprise layout against the Enterprise record type and the
  Renewal layout against the Renewal record type. Before M2-S02, every cell still points at the
  org's existing Opportunity layout, and that is the expected reading, not a failure.

Then open a new Opportunity of each record type **as a rep, not as System Administrator** — the
admin profile will not reproduce a missing assignment.

---

## 5. Validate-only command for the human

Run this yourself. **This agent does not run it, and no acceptance test invokes it.**

```bash
sf project deploy start \
  --manifest .sfskills/builds/northwind-sales/artefacts/M1-S02/package.xml \
  --target-org <alias> \
  --dry-run
```

`--dry-run` validates without saving to the org. Use `sf project deploy validate` instead only
against a **production** org: it requires Apex tests and returns a job ID for a later
`sf project deploy quick`.

Note that this manifest carries the two `Layout` members only. Validating it on its own against an
org that does not yet hold `Discount__c` and `Approval_Status__c` fails on the field cross-reference
(§1) — validate M1-S01 and M1-S02 together, which is what
`python3 scripts/mock_deploy.py … --milestone M1` assembles.

---

## 6. Repair after run 1

`reports/MOCK-DEPLOY-M1.md` run 1 (`python3 scripts/mock_deploy.py plan.json --org-alias
sfskills-dev --mode manifest --milestone M1`, 2026-09-18T13:34Z) returned **N3-F-02 (HIGH)** against
both layouts: *"Layout must contain an item for required layout field: Probability."* This is the §3
item 2 discovery procedure firing for the first time — the dry run named one missing field, which
§3 item 2 says to expect one field at a time.

Fix applied: both files now carry a `layoutItems` entry for `Probability` in the Opportunity
Information section, immediately after `Amount`, with `<behavior>Required</behavior>` — not `Edit`.
Per `admin/record-types-and-page-layouts/references/gotchas.md` #13 and
`references/metadata-examples.md`'s `behavior` table, a field the *platform* requires on the layout
is not the layout-required-item table's "any behavior" case; it is the same shape as `Status` on
Case (gotcha #13): `Required` is a deploy precondition there, not the analyst's design choice, and
setting it to `Edit` risks the second-round message `Field:Probability must be Required` on the next
dry run. Writing `Required` now, on the strength of the deploy message the org already returned,
skips that avoidable second round trip.

**Assumption A25 is now partially discharged, not closed.** The dry run confirmed `Probability` is
layout-required for Opportunity — the platform-required membership question §3 item 2 raised is
answered for this one field. It is not answered in general: `sf project deploy start --dry-run`
reports one missing-`layoutItems` field per run (§3 item 2, `gotchas.md` #12), so run 1 stopped at
the first missing field, `Probability`, without saying whether it is the only one. A further
required field may still surface on the next dry run against these two files. **Keep the
iterate-the-dry-run note in §3 item 2 standing** — do not read this repair as having closed A25, and
budget for at least one more `scripts/mock_deploy.py` round before treating either layout's
required-field set as complete.

**Org finding carried here for the record:** N3-F-02 (HIGH), `reports/MOCK-DEPLOY-M1.md` run 1 —
*"Layout must contain an item for required layout field: Probability"* on both
`Opportunity-Opportunity Enterprise Layout` and `Opportunity-Opportunity Renewal Layout`. Re-run
evidence: this step's declared checker (`check_record_type_layouts.py --manifest-dir artefacts`) and
`check-outputs` re-ran clean after the fix — see the envelope for this run's checker results section.

### Second discovery (run 2)

`reports/MOCK-DEPLOY-M1.md` run 2 (2026-09-18T13:43Z, after both M1-S01's and this step's run-1
repairs landed) returned **N3-F-03 (HIGH)** against both layouts: *"Field:Name must be Required."*
This is §3 item 2's discovery procedure firing a second time, exactly as flagged above: the first
run named `Probability` as a missing `layoutItems` entry; this run reports that a field already
present — `Name`, carried at `behavior=Edit` since D2/Q11 — must instead be `behavior=Required`. The
two deploy messages are the two distinct failure shapes §3 item 2's table already names (`Layout must
contain an item for required layout field: <F>` vs. `Field:<F> must be Required`); this one is the
second shape, not a new field the layout was missing.

Fix applied: both files now set `Name`'s `layoutItems` entry to `<behavior>Required</behavior>`
(previously `Edit`). Same reasoning as the `Probability` fix above and per `gotchas.md` #13: on
Opportunity, `Name` is now confirmed platform-required on the layout, so its behavior is a deploy
precondition rather than the `Edit`/`Required` choice Q11 otherwise leaves to the requirement (Q11's
answer — enforcement lives in the M2-S03/M2-S04 validation rules, not on the layout — is unaffected
for every other field; it was never in tension with a platform-required item, per gotcha #13's own
distinction). Nothing else in either file changed.

**Assumption A25 is now confirmed for two fields (`Probability`, `Name`), still not closed.** The
Opportunity layout-required set is a two-item list at minimum; §3 item 2's iterate-the-dry-run
procedure and `gotchas.md` #12's one-field-per-run behavior both still apply verbatim — a third field
may surface on the next dry run against either file, and nothing here rules that out. Keep budgeting
`scripts/mock_deploy.py` rounds until a run returns no further `Layout must contain…` or
`Field:… must be Required` message for either layout.

**Org finding carried here for the record:** N3-F-03 (HIGH), `reports/MOCK-DEPLOY-M1.md` run 2 —
*"Field:Name must be Required"* on both `Opportunity-Opportunity Enterprise Layout` and
`Opportunity-Opportunity Renewal Layout`. Re-run evidence: this step's declared checker and
`check-outputs` re-ran clean after this fix — see the envelope for this run's checker results
section.

### Third discovery (run 3) — StageName confirmed, CloseDate inferred

`reports/MOCK-DEPLOY-M1.md` run 3 (2026-09-18T13:52Z, after the `Name` repair landed) closed N3-F-03
(`Name` accepted as `Required`) and returned **N3-F-04 (HIGH)** against both layouts:
*"Field:StageName must be Required."* This is §3 item 2's discovery procedure firing a third time,
same shape as N3-F-03: an existing item (`StageName`, at `behavior=Edit` since Q11/D2) must instead
be `Required`.

**`StageName` — org-confirmed (run 3).** Fix applied: both files now set `StageName`'s `layoutItems`
entry to `<behavior>Required</behavior>` (previously `Edit`). Same `gotchas.md` #13 reasoning as
`Probability` and `Name`: `StageName` is confirmed platform-required on the Opportunity layout by
N3-F-04 itself.

**`CloseDate` — UNVERIFIED (2026-09-18): inference, not yet org-confirmed.** This run also sets
`CloseDate`'s `layoutItems` entry to `<behavior>Required</behavior>` (previously `Edit`), one dry-run
round ahead of the org naming it. The basis is a pattern, not a deploy message against this build:
`Name`, `StageName`, and `CloseDate` are the three fields Salesforce marks `nillable="false"` (required
at the field level, independent of any layout) on Opportunity, and the three org findings so far —
N3-F-02 (`Probability`, a layout-only requirement), N3-F-03 (`Name`), N3-F-04 (`StageName`) — are
consistent with every field-level-required standard field also being layout-required, which would
make `CloseDate` the fourth. **This is inferred from the pattern across N3-F-02 through N3-F-04, not
confirmed by a deploy message naming `CloseDate` for this build.** `references/metadata-examples.md`
still says, in bold, not to extrapolate a per-object required set from another object or from theory,
and `gotchas.md` #13 exists precisely to stop this class of one-step-too-far reasoning; setting
`CloseDate` ahead of confirmation is a deliberate bet to save a round trip, made explicit here rather
than passed off as verified. **Read this paragraph before treating `CloseDate`'s `Required` behavior
as established** — if run 4 does not confirm it (i.e., a dry run against both files with `CloseDate`
already `Required` returns a message about a different field, or none at all, without ever having
independently named `CloseDate`), downgrade this line and record why in the next repair pass; if run 4
instead reports `CloseDate` was accepted or is silent on it, replace `UNVERIFIED (2026-09-18)` with a
confirmed citation to that run.

**Assumption A25 is now confirmed for three fields (`Probability`, `Name`, `StageName`) with a fourth
(`CloseDate`) written ahead of confirmation.** Still not closed. Keep budgeting
`scripts/mock_deploy.py` rounds — run 4 either passes (all four fields sufficient) or names a fifth
field the field-level-required pattern above did not predict.

**Org finding carried here for the record:** N3-F-04 (HIGH), `reports/MOCK-DEPLOY-M1.md` run 3 —
*"Field:StageName must be Required"* on both `Opportunity-Opportunity Enterprise Layout` and
`Opportunity-Opportunity Renewal Layout`. Re-run evidence: this step's declared checker and
`check-outputs` re-ran clean after this fix — see the envelope for this run's checker results
section.
