# Deploy order — M3-S05

Build: `northwind-sales` · Milestone: M3 (Approval, the panel and the page) · Step type: `ui` · API version 62.0

This note is written by `agents/metadata-builder` Step 7 and is text for a human. Nothing in it is
executed by this agent or by any acceptance test. The validate-only command in § 6 is for a person to
copy; this agent never runs it, and `scripts/mock_deploy.py` hard-codes `--dry-run`.

Sourced from `skills/admin/lightning-record-page-configuration/SKILL.md` ("Before Starting",
"Assignment: Three Rungs and a Fallback", "Activation Is Assignment", "Pattern: Moving a Page and Its
Assignment Between Orgs", "Recommended Workflow" steps 5–7, "Review Checklist"),
`skills/admin/lightning-record-page-configuration/references/examples.md` Example 1 and Example 3,
`skills/admin/lightning-record-page-configuration/references/gotchas.md` #1, #2, #3, #4, #5 and #6,
`skills/admin/lightning-record-page-configuration/templates/lightning-record-page-configuration-template.md`
(§ 2, the assignment matrix reproduced below),
`skills/admin/path-and-guidance/references/metadata-examples.md` § 4 and § 6,
`.sfskills/builds/northwind-sales/artefacts/M2-S05/deploy-order.md` § 3, and the upstream bundle
`artefacts/M3-S04/lwc/discountApprovalPanel/discountApprovalPanel.js-meta.xml`.

## 0. Why API version 62.0

`plan.json` carries no top-level `api_version` key and this step's `inputs{}` carry none either, so
`agents/metadata-builder/AGENT.md` ("Inputs") falls back to its documented default, `62.0`. Every
other `package.xml` under `artefacts/` in this build declares `<version>62.0</version>`, and the
M3-S04 bundle this page hosts is pinned at 62.0 in its own `.js-meta.xml`, so
`scripts/mock_deploy.py`'s highest-version scan sees one version for the whole build.

Two version floors in this step, both cleared by 62.0:

| Element | Floor | Source |
|---|---|---|
| `itemInstances` (replacing the removed `componentInstances`), `fieldInstance` | API 49.0 | `gotchas.md` #5 |
| `identifier`, **required** on every `componentInstance` and `fieldInstance`, max 120 characters | API 53.0 | `gotchas.md` #5; SKILL.md "Regions, Facets, and the 100-Component Cap" |

The `identifier` floor is the one that bites. The FlexiPage fence this page's structure is copied from
— `path-and-guidance/references/metadata-examples.md` § 4 — **omits `identifier` on all three of its
`componentInstance` blocks**. A page built from it verbatim raised three ERRORs at exit 1 from
`check_lightning_record_page_configuration.py` in this plan's own fixture run (plan decision **D10**).
All three identifiers were added here.

## 1. Order inside this step

Two components, and the order between them is not free.

| # | Component | Because |
|---|---|---|
| 1 | `FlexiPage:Opportunity_Enterprise_Record_Page` | The page must exist before anything can point at it. The `ActionOverride` in step 2 names it by developer name in `<content>`; deploy the object file first and the override references a page the org does not have. |
| 2 | `CustomObject:Opportunity` (the two `actionOverrides` blocks) | This is the activation. "Saving a page creates the `FlexiPage`; activating it writes an override" (SKILL.md, "Activation Is Assignment — There Is No Separate Active Flag"). |

Both members are in the single `package.xml` beside this note, so **one manifest deploy satisfies the
ordering by itself** — the platform resolves intra-request references. A split-source deploy must run
`flexipages/` then `objects/`.

## 2. Dependencies on components outside this step

Everything below must already exist in the target org, or ship in the same request, before this page
renders as designed. None of it is in this step's manifest.

| Needed | From | What breaks without it |
|---|---|---|
| `LightningComponentBundle:discountApprovalPanel` | **M3-S04** | `<componentName>c:discountApprovalPanel</componentName>` resolves to nothing. The bundle declares no `package.xml` of its own (`agents/apex-builder` / `lwc-builder` contracts name none); **M4-S04** is the build-level manifest step that carries its member. |
| `ApexClass:OpportunityApprovalController` (+ its service and test) | **M3-S03** | The bundle imports the controller; the LWC deploys but its Submit button has no server. Same manifest story: M4-S04 carries the `ApexClass` members. |
| `PathAssistant:Enterprise_Opportunity_Path`, `Settings:PathAssistant` | **M2-S05** | The `subheader` region renders the component and the component finds no active path for the record type, so the chevron is empty. **This page names no path.** `runtime_sales_pathassistant:pathAssistant` resolves the active path for the record's record type at run time — which is exactly why M2-S05 § 3 item 3 says a green M2 deploy proves nothing about the page, and why this step proves nothing about the path. |
| `RecordType:Opportunity.Enterprise`, `Opportunity.Discount__c`, `Opportunity.Approval_Status__c` | **M1-S01** | The record type is what makes this the *Enterprise* page (§ 3 below); the two fields are what the M3-S04 bundle reads. |
| `ApprovalProcess:Opportunity.Discount_Approval` | **M3-S02** | The panel's Submit path has no process to enter. |

**Nothing outside this step depends on this step**, except the build-level manifest in M4-S04 and the
M4 cutover runbook.

## 3. What a green deploy of this step does *not* prove

This is the section `skills/admin/lightning-record-page-configuration` exists to force. Three
statements, all of them assignment-shaped, and none of them visible in a deploy result.

### 3.1 An app with its own Opportunity record page wins over this org default, and must be re-pointed in Setup if Northwind runs one

The org default written by this step is **Rung 3 — the lowest rung** (SKILL.md, "Assignment: Three
Rungs and a Fallback"). Two rungs outrank it, and both live in `CustomApplication` metadata, not on
the object and not on the page:

| Rung | Setup label | Metadata home | Element |
|---|---|---|---|
| 1 (wins) | App, Record Type, and Profile | `CustomApplication` | `<profileActionOverrides>` |
| 2 | App Default | `CustomApplication` | `<actionOverrides>` |
| **3 (this step)** | **Org Default** | **`CustomObject`** | **`<actionOverrides>`** |
| 4 | none | — | Salesforce's system default record page |

The Metadata API reference states the precedence without hedging: *"When a user invokes the custom
app, a matching ProfileActionOverride assignment takes precedence over existing overrides for the
record page specified in ActionOverride"* (quoted in SKILL.md and `gotchas.md` #2).

**This is assumption A38, and it is a medium-risk open item, not a closed one.** No clarification
asked which Lightning apps expose Opportunity at Northwind, and this build writes no
`applications/*.app-meta.xml`. So: if Northwind runs a Lightning app that carries its own Opportunity
record page — a sales console beside the standard app is the classic pair — **that app's assignment
wins for every user working inside it, and this step changes nothing for them. It must be re-pointed
in Setup (or in the app's metadata) by hand.** `examples.md` Example 3 is this failure in full: an
org-default change that half the org never saw, because a two-year-old `profileActionOverrides` entry
inside one app still matched and still won.

Enumerate before the M3 gate rather than after a rep reports the wrong page:

```bash
sf project retrieve start --metadata "CustomApplication" --target-org <alias>
grep -l -E "actionOverrides|profileActionOverrides" force-app/main/default/applications/*.app-meta.xml
grep -B 2 -A 8 "Opportunity" force-app/main/default/applications/*.app-meta.xml
```

For each hit, decide per `examples.md` Example 3 step 2: **delete** the entry so the org default takes
over, or **re-point** its `<content>` at `Opportunity_Enterprise_Record_Page`. Re-pointing is safer
when the assignment was deliberate; deleting is right when nobody can say why it exists. Whichever you
choose, that is a `CustomApplication` deploy this build does not contain.

If a `profileActionOverrides` entry has to be *written*, read `gotchas.md` #2 first: the
`pageOrSobjectType` value in that block is the one element in this domain the published reference
contradicts itself about, and the gotcha's instruction is explicit — take the value from a file
retrieved out of the target org, *"and never let an agent generate this element from memory."* This
agent did not, and neither should the next one.

### 3.2 Only the Enterprise page is built. The Renewal record type falls through, and nothing in this build asserts what it falls through to

This step builds **one** page, per the plan. Q50's proposed default allowed one page; assumption
**A15** records building new rather than editing whatever the org has; and the step's own `notes` in
`plan.json` state it: *"Only the Enterprise page is built… the Renewal record type falls through to
the org's existing Opportunity page, and that is recorded rather than silently assumed."*

Two consequences a reader should not have to infer:

1. **The org default is not record-type-scoped.** `ActionOverride` on `CustomObject` has no
   `recordType` field — SKILL.md's Rung 1 row is the only rung that carries one, and it lives in
   `CustomApplication`. So the two overrides this step writes make
   `Opportunity_Enterprise_Record_Page` the default for **every** Opportunity record type in the org,
   Renewal included, unless a higher rung says otherwise. The page is named for the Enterprise process
   and is the page the Enterprise path renders on; it is not fenced off from Renewal by anything in
   this step. If Renewal genuinely needs a different page, that is a Rung 1 row per app — and Rung 1
   *requires* `recordType` whenever `actionName` is `View` (SKILL.md) — or a second page, and neither
   is in this build.
2. **`Renewal_Opportunity_Path` renders only if the page a renewal rep lands on carries the
   component.** This is finding **O-M2S05-04**, recorded in `artefacts/M2-S05/deploy-order.md` § 3:
   *"So `Renewal_Opportunity_Path` renders only if Northwind's current Opportunity record page already
   carries `runtime_sales_pathassistant:pathAssistant`. Nothing in this build asserts that it does."*
   That finding is **not closed by this step.** What this step does close is the Enterprise half:
   `check_path_and_guidance.py` run at build scope over `artefacts/` (advisory — the step does not
   declare it) now indexes this page and reports no Check 6c note for either path. Read that result
   carefully: the checker indexes FlexiPage components **by `sobjectType`**, not by record type, so
   one Opportunity page carrying the component silences the note for *both* paths. It cannot tell that
   the Renewal record type may resolve to a different page entirely.

```bash
sf project retrieve start --metadata "FlexiPage" --target-org <alias>
grep -rl "runtime_sales_pathassistant:pathAssistant" force-app/main/default/flexipages/
```

### 3.3 Two shapes in this page are not grounded in any cited skill, and only the org can settle them

Both are marked `UNVERIFIED (2026-09-19):` inline in the flexipage file. The checker cannot see either
one — it validates identifiers, region capacity, operators and assignment, not region names against a
template's real slot set, and not a component namespace against the org's component list.

| Unverified | What was written | How to settle it |
|---|---|---|
| That `flexipage:recordHomeWithSubheaderTemplateDesktop` provides a region named **`sidebar`** | `<name>sidebar</name>` on the third region, as `plan.json steps[M3-S05].inputs.components.sidebar` declares. SKILL.md names `header` / `main` / `sidebar` as the slots a template defines, but neither cited skill fences *this* template's region set; the fence it is copied from shows only `subheader` and `main`. | Open the template in Lightning App Builder, or retrieve any page already built on it and read its `<flexiPageRegions><name>` values. If the region is named something else, only that one `<name>` element changes. A region name the template does not define is a deploy-time failure. |
| The **`c:`** namespace prefix on a custom LWC in a `componentInstance` | `<componentName>c:discountApprovalPanel</componentName>`. The bundle name is exact — it comes from the upstream artefact. The prefix is documented in this library at `skills/admin/service-console-configuration/references/metadata-examples.md` (`c:consoleTelephonyListener`), which is **not** one of this step's cited skills; none of the three cited skills fences a custom LWC on a page. | The dry run in § 6 settles it: an unresolvable `componentName` fails validation. Confirm also that the bundle deploys *first* — "App Builder only lists components whose `isExposed` is `true` and whose `targets` include the page type" (`lwc-base-component-recipes/references/code-examples.md`), and this bundle declares both. |

## 4. Assignment matrix

The shape is `templates/lightning-record-page-configuration-template.md` § 2. The platform never
renders this in one place; this table is where it exists for Northwind.

**Object:** `Opportunity` · **Page type:** `RecordPage` · **Date:** 2026-09-19 · **Org:** production (design-only build; no org was read)

| Rung | App | Record type | Profile | Form factor | Page | Metadata home |
|---|---|---|---|---|---|---|
| 3 — Org Default | (all) | (all) | (all) | `Large` | `Opportunity_Enterprise_Record_Page` | `objects/Opportunity/Opportunity.object-meta.xml` ← **this step** |
| 3 — Org Default | (all) | (all) | (all) | `Small` | `Opportunity_Enterprise_Record_Page` | `objects/Opportunity/Opportunity.object-meta.xml` ← **this step** |
| 2 — App Default | *unknown — see § 3.1* | — | — | — | — | `applications/<App>.app-meta.xml` (**not in this build**) |
| 1 — App + RT + Profile | *unknown — see § 3.1* | — | — | — | — | `applications/<App>.app-meta.xml` (**not in this build**) |

**Form factor coverage.** `Large` is Lightning Experience desktop; `Small` is the Salesforce mobile
app; an absent `formFactor` on a `CustomObject` override means **Salesforce Classic**, not "all of
them" (`gotchas.md` #3, quoting the `ActionOverride` reference). Mobile is in scope — assumption
**A17** (Q51's default) puts this build on desktop and the mobile app, and the M3-S04 bundle declares
`supportedFormFactors` `Large` and `Small` to match — so **both rows above are written explicitly**.
"Covering both is literally two overrides that differ in one element."

Worth knowing rather than discovering: **no override is written for Classic.** Nothing in this build
targets it, and Path and LWCs do not render there.

**Overrides being deleted by this step: none.** This step adds two and removes nothing. Anything
already pointing at an Opportunity page in an app survives it — which is § 3.1.

## 5. Manifest member forms used

| Type | Member form | Source |
|---|---|---|
| `FlexiPage` | `Opportunity_Enterprise_Record_Page` — the file-name stem | `examples.md` Example 1 step 4 |
| `CustomObject` | `Opportunity` — the object API name, unqualified | `examples.md` Example 1 step 4; SKILL.md "Pattern: Moving a Page and Its Assignment Between Orgs" |

Both are named explicitly rather than with `*`, so the manifest and the files on disk agree in both
directions — every file covered by a member, every member backed by a file. That is what the step's
`manifest` acceptance test asserts.

**`CustomApplication` is the third type SKILL.md's manifest pattern names, and it is deliberately
absent.** This build writes no application file, so there is no app-level override to ship. Read that
as "nothing to deploy", never as "nothing to check" — § 3.1 is the check.

**A manifest naming only `FlexiPage` is "incomplete by definition"** (`gotchas.md` #1). The
`CustomObject` member is not optional decoration: it is the entire activation. Deploying the
flexipages folder alone is green, changes nothing any user sees, and produces no error to investigate.
Change sets have the same trap under a friendlier name — adding the Lightning page component does not
add the object.

## 6. The validate-only command a human may run

Text for a person to copy. This agent does not run it.

```bash
sf project deploy start \
  --manifest .sfskills/builds/northwind-sales/artefacts/M3-S05/package.xml \
  --dry-run \
  --target-org <alias>
```

Two notes before running it:

- The M3-S04 bundle and the M3-S03 classes must already be in the target org, or the
  `componentName` reference in § 3.3 fails validation for the right reason and the wrong one at the
  same time. Prefer the layer's own form, which assembles the whole milestone and is already
  `--dry-run` by construction: `python3 scripts/mock_deploy.py <plan.json> --org-alias <alias>
  --milestone M3 --mode manifest`.
- A green dry run still proves none of § 3. It proves the XML is deployable, not that the right users
  land on the page.

## 7. Post-deploy steps the deploy does not perform

- **Verify as a user, not as a deploy result.** SKILL.md "Recommended Workflow" step 6 and the Review
  Checklist are unambiguous: log in as one Enterprise rep and one manager, open an Enterprise
  Opportunity, and confirm the chevron, the detail panel and the discount panel are all present —
  *"The dialog shows what you set, not what resolves"* (`examples.md` Example 3). Then open a Renewal
  Opportunity and confirm what it renders (§ 3.2).
- **Check the mobile form factor separately.** A desktop check says nothing about `Small`
  (`gotchas.md` #3).
- **Re-check § 3.1 after any future app is added.** A new Lightning app over Opportunity is a new
  Rung 2 surface, and this org default loses to it silently.
- **Do not hand-edit this page after retrieving it at a different API version.** `gotchas.md` #5:
  retrieve fresh at the project's current version, diff, and edit the fresh copy. A round trip
  through a pre-53.0 retrieve drops every `identifier` and the file stops deploying.
- **`sobjectType` is a one-way door.** It is `Opportunity` and cannot be repointed
  (`gotchas.md` #4). Recovery is clone-and-rebuild, and the clone starts with zero overrides pointing
  at it — straight back into `gotchas.md` #1.
