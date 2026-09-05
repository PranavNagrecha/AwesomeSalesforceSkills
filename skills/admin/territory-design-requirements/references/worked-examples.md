# Worked Examples — Territory Design Requirements

One B2B SaaS scenario carried end to end: the questionnaire filled in, the hierarchy, the type and
priority table, the assignment-rule matrix, the access decisions, the realignment runbook, the
acceptance tests, and the machine-lintable design file the checker reads.

Copy the shapes; replace the content. The deep metadata reference — the full `Territory2*` XML set,
the manifest, the retrieve/deploy commands — lives in
`skills/admin/enterprise-territory-management/references/metadata-examples.md` and is not repeated
here. What follows is the *design* artefact and just enough grounded XML to show where each design
decision lands.

---

## Scenario

**Northwind Signal**, a B2B SaaS vendor selling an observability platform. 62 quota-carrying
sellers across three regions, two segments and a small public-sector practice:

| Team | Headcount | Today |
|---|---|---|
| AMER Commercial | 21 | Accounts owned ad hoc; "whoever logged it first" |
| AMER Enterprise | 8 | A named list in a spreadsheet |
| EMEA Commercial | 12 | Owned by country, informally |
| EMEA Enterprise | 5 | Named list, overlaps AMER on two global logos |
| APAC (both segments) | 9 | One team, no split |
| Public Sector overlay | 7 | Sit across every region; today they get manual shares |

Account OWD is **Private**. Opportunity OWD is Private. Contact is Controlled By Parent. Case is
Private. Forecast today rolls up by role hierarchy; the CRO wants it by territory from the next
fiscal year. Alignment is re-cut once a year, in the four weeks before the fiscal year starts.

---

## 1. The questionnaire, filled in

The seven questions from `SKILL.md` § Questions to Ask Before Configuring, with the answers that
actually made the design decidable. The third column is what changed in the artefact because of
the answer.

| # | Ask | Answer as given | What it changed |
|---|---|---|---|
| 1 | Which dimensions decide who covers an account, and which are just reporting? | "Region, segment, and the named list. Industry is how we report, not how we cover." | Industry dropped from the rule matrix entirely; three dimensions remain |
| 2 | Name the Account field, API name and population for each dimension | `BillingCountry` 99.2% populated; `Segment__c` picklist (Commercial/Enterprise) 87%; `Named_Account__c` checkbox, maintained by sales ops, 100% | The 13% null `Segment__c` became the sizing case for the catch-all territory, and a data-quality task with an owner before go-live |
| 3 | Can one account be covered by two teams at once — deliberately? | "Yes for public sector. No for geo, and today it happens by accident on the two global logos." | Public Sector becomes an overlay **type** with its own priority; the geo criteria are made mutually exclusive; the two global logos move to the named list |
| 4 | What are the OWDs today? | Account Private, Opportunity Private, Contact Controlled By Parent, Case Private | `accountAccessLevel` may legally be `Read`, `Edit` or `All`; `contactAccessLevel` is **omitted** because the contact model is Controlled By Parent |
| 5 | Does the forecast roll up by territory, and who reads it at each level? | Global: CRO. Region: three RVPs. Region+segment: six segment directors. Named books: one VP. | Four levels, every one with a named reader. A proposed "Sub-region" level had no reader and was cut |
| 6 | How often does this change, and what is the cutover window? | "Once a year, in the four weeks before 1 Feb." | Realignment runbook in §6, with the new model built in `Planning` alongside the live one |
| 7 | Who can change a territory after go-live, and at which node? | "RVPs should be able to move reps inside their own region; nobody else touches the hierarchy." | Three `TerritoryAdminAssignment` rows with `CanManageMembers` true and `CanManageHierarchy` false, at each region node |

Two answers that did **not** survive the questionnaire, and why:

- *"Assign accounts to a renewal territory based on `Contract_End_Date__c`."* A date predicate is
  evaluated when the rule runs, not continuously, so a quarter-boundary account is in the wrong
  territory for most of the quarter. Replaced by `Renewal_Quarter__c`, a picklist maintained by a
  record-triggered Flow. (Whether ETM rejects Date fields outright is UNVERIFIED (2026-09-05) — see
  `references/gotchas.md` Gotcha 1 — but the staleness argument holds either way.)
- *"Give the public-sector team a lower priority number so they win."* Backwards: "The
  account-assigned territory whose territory type priority is highest is then assigned to the
  opportunity" (Metadata API Developer Guide, `Territory2Type` › `priority`).

---

## 2. Territory hierarchy

Four levels, 18 territories, one model. `parent` is the parent territory's **developer name** —
"When you specify the parent territory, use the developer name. Do not use the 'fully qualified'
name" (`Territory2` › `parentTerritory`).

| Level | Territory (developer name) | Parent | Type | Forecast reader |
|---|---|---|---|---|
| 1 | `Global` | — (root) | `Global` | CRO |
| 2 | `AMER` | `Global` | `Geo` | RVP AMER |
| 2 | `EMEA` | `Global` | `Geo` | RVP EMEA |
| 2 | `APAC` | `Global` | `Geo` | RVP APAC |
| 3 | `AMER_Commercial` | `AMER` | `Geo` | Segment Director, AMER Commercial |
| 3 | `AMER_Enterprise` | `AMER` | `Geo` | Segment Director, AMER Enterprise |
| 3 | `EMEA_Commercial` | `EMEA` | `Geo` | Segment Director, EMEA Commercial |
| 3 | `EMEA_Enterprise` | `EMEA` | `Geo` | Segment Director, EMEA Enterprise |
| 3 | `APAC_Commercial` | `APAC` | `Geo` | Segment Director, APAC |
| 3 | `APAC_Enterprise` | `APAC` | `Geo` | Segment Director, APAC |
| 2 | `Named_Accounts` | `Global` | `NamedAccount` | VP Strategic Accounts |
| 3 | `Named_Book_A` … `Named_Book_C` | `Named_Accounts` | `NamedAccount` | VP Strategic Accounts |
| 2 | `Public_Sector` | `Global` | `Overlay` | Director, Public Sector |
| 3 | `Public_Sector_AMER`, `Public_Sector_EMEA` | `Public_Sector` | `Overlay` | Director, Public Sector |
| 2 | `Unassigned` | `Global` | `Geo` | Sales Ops (catch-all, reviewed weekly) |

Ratio check, with the metric defined so it can be recomputed: **territories ÷ active users** =
18 ÷ 62 = **0.29**. The heuristic target (~3, UNVERIFIED (2026-09-05) — see `SKILL.md` §
User-to-Territory Ratio) flags this as low, so the design is tested the other way instead:
**accounts per leaf territory** ranges 310–1,940 and **users per leaf territory** ranges 2–11.
`AMER_Commercial` at 1,940 accounts and 11 users is the one node that fails the coverage-clarity
test and is split next cycle; nothing else is. That is the finding the ratio was a proxy for.

---

## 3. Territory types and priority

Priority is a required unique integer on `Territory2Type`, and the **highest** integer wins
opportunity territory assignment. A tie — two territories of the same type on one account — assigns
**no** territory to the opportunity at all.

| Type (developer name) | Priority | Wins over | Why |
|---|---|---|---|
| `Global` | 10 | — | Root container only; never the winning territory in practice |
| `Geo` | 20 | `Global` | Default coverage |
| `Overlay` | 30 | `Geo` | A public-sector opportunity should forecast in the overlay, not the region |
| `NamedAccount` | 40 | everything | A named logo's opportunity belongs to the strategic rep's forecast |

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Territory2Type xmlns="http://soap.sforce.com/2006/04/metadata">
    <name>Named Account</name>
    <description>Strategic named-account coverage. Highest priority: wins opportunity territory assignment over Overlay (30) and Geo (20).</description>
    <priority>40</priority>
</Territory2Type>
```

The tie the priority table has to prevent: `Named_Book_A` and `Named_Book_B` are both type
`NamedAccount`, so an account on both books assigns no territory to its opportunities. §7's second
acceptance test is the query that catches it.

---

## 4. Assignment-rule matrix

One row per rule. `inherited` is `ruleAssociations.inherited` on the territory: "Rule inheritance
flows from the parent territory where the rule is created to the rule's descendent territories…
A local rule is created within a single territory and affects that territory only."

| Rule (developer name) | Criteria (`field` `operation` `value`) | `booleanFilter` | Items | Territories served | Inherited? |
|---|---|---|---|---|---|
| `AMER_Commercial_Rule` | `BillingCountry` `includes` `US;CA;MX;BR;AR` **and** `Segment__c` `equals` `Commercial` **and** `Named_Account__c` `equals` `false` | `1 AND 2 AND 3` | 3 | `AMER_Commercial` | false (local) |
| `AMER_Enterprise_Rule` | same countries, `Segment__c` `equals` `Enterprise`, `Named_Account__c` `equals` `false` | `1 AND 2 AND 3` | 3 | `AMER_Enterprise` | false |
| `EMEA_Commercial_Rule` | `BillingCountry` `includes` `GB;IE;DE;FR;NL;SE;ES;IT`, `Segment__c` `equals` `Commercial`, `Named_Account__c` `equals` `false` | `1 AND 2 AND 3` | 3 | `EMEA_Commercial` | false |
| `EMEA_Enterprise_Rule` | same countries, `Segment__c` `equals` `Enterprise`, `Named_Account__c` `equals` `false` | `1 AND 2 AND 3` | 3 | `EMEA_Enterprise` | false |
| `APAC_Commercial_Rule` | `BillingCountry` `includes` `AU;NZ;SG;JP;IN`, `Segment__c` `equals` `Commercial`, `Named_Account__c` `equals` `false` | `1 AND 2 AND 3` | 3 | `APAC_Commercial` | false |
| `APAC_Enterprise_Rule` | same countries, `Segment__c` `equals` `Enterprise`, `Named_Account__c` `equals` `false` | `1 AND 2 AND 3` | 3 | `APAC_Enterprise` | false |
| `Public_Sector_Rule` | `Industry` `equals` `Government` **or** `Public_Sector_Flag__c` `equals` `true` | `1 OR 2` | 2 | `Public_Sector_AMER`, `Public_Sector_EMEA` | true, from `Public_Sector` |
| `Unassigned_Rule` | `Segment__c` `equals` `` (blank) **or** `BillingCountry` `equals` `` (blank) | `1 OR 2` | 2 | `Unassigned` | false |
| — (no rule) | `Named_Book_A`, `_B`, `_C`: **manual assignment**, owner = VP Strategic Accounts, reviewed monthly | — | 0 | — | n/a |

Three constraints this matrix is built to respect, all from the Metadata API Developer Guide
(`Territory2Rule`):

- **10 rule items maximum per rule.** The widest rule here uses 3. The version of this design that
  listed 14 countries as 14 separate `equals` items was rejected and rewritten as one `includes`.
- **Item order is positional** — "The sort order of rule items is implicitly derived from the
  position of the rule items in the XML." Reordering the items silently renumbers the
  `booleanFilter`.
- **`booleanFilter` numbering** "must start at 1 and must be contiguous."

The `Named_Account__c equals false` item on every geo rule is what makes the geo and named-account
coverage mutually exclusive at the *primary* layer. The public-sector overlay deliberately does not
carry it — an overlay is supposed to co-assign.

Rule and its association, as they deploy:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Territory2Rule xmlns="http://soap.sforce.com/2006/04/metadata">
    <name>AMER Commercial Rule</name>
    <objectType>Account</objectType>
    <active>true</active>
    <ruleItems>
        <field>Account.BillingCountry</field>
        <operation>includes</operation>
        <value>US;CA;MX;BR;AR</value>
    </ruleItems>
    <ruleItems>
        <field>Account.Segment__c</field>
        <operation>equals</operation>
        <value>Commercial</value>
    </ruleItems>
    <ruleItems>
        <field>Account.Named_Account__c</field>
        <operation>equals</operation>
        <value>false</value>
    </ruleItems>
    <booleanFilter>1 AND 2 AND 3</booleanFilter>
</Territory2Rule>
```

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Territory2 xmlns="http://soap.sforce.com/2006/04/metadata">
    <name>AMER Commercial</name>
    <description>AMER commercial-segment coverage, excluding named accounts.</description>
    <parentTerritory>AMER</parentTerritory>
    <territory2Type>Geo</territory2Type>
    <accountAccessLevel>Edit</accountAccessLevel>
    <opportunityAccessLevel>Edit</opportunityAccessLevel>
    <caseAccessLevel>Read</caseAccessLevel>
    <ruleAssociations>
        <ruleName>AMER_Commercial_Rule</ruleName>
        <inherited>false</inherited>
    </ruleAssociations>
</Territory2>
```

A rule with no `ruleAssociations` entry anywhere deploys cleanly and assigns nothing — which is why
the matrix carries a "Territories served" column rather than leaving it to the builder.

---

## 5. Access-level decisions per object

Decided against Northwind's actual OWDs, in Metadata API spelling. The valid values and the
omission rules are from the Metadata API Developer Guide, `Territory2`.

| Territory | `accountAccessLevel` | `opportunityAccessLevel` | `caseAccessLevel` | `contactAccessLevel` | Why |
|---|---|---|---|---|---|
| `Global` | `Read` | `Read` | `None` | *(omitted)* | CRO needs visibility, not edit rights, across everything |
| `AMER` / `EMEA` / `APAC` | `Read` | `Read` | `Read` | *(omitted)* | RVPs read their branch through `TerritoryAndSubordinates`; edit stays at the leaf |
| `*_Commercial`, `*_Enterprise` | `Edit` | `Edit` | `Read` | *(omitted)* | Sellers work their accounts and opportunities; cases are read-only to them |
| `Named_Book_A/B/C` | `Edit` | `Edit` | `Read` | *(omitted)* | Same working rights as a geo leaf |
| `Public_Sector_*` | `Read` | `Edit` | `None` | *(omitted)* | Overlay co-sells: it owns the opportunity, not the account record |
| `Unassigned` | `Read` | `None` | `None` | *(omitted)* | Sales ops triage only |

Four rules that constrained the table:

- Valid `accountAccessLevel` values are `Read`, `Edit`, `All`. There is no `None` — a territory
  cannot grant *less* than Read on the accounts assigned to it.
- `opportunityAccessLevel`, `caseAccessLevel` and `contactAccessLevel` take `None`, `Read` or `Edit`.
- `contactAccessLevel` is **omitted** everywhere: "Specify no value if your organization's sharing
  model for contacts is Public Read/Write or Controlled By Parent." Northwind's is Controlled By
  Parent.
- Had Account OWD been Public Read/Write, "valid values are only `Edit` and `All`" — the `Read` rows
  above would have been rejected at deploy.

Omitting an element inherits the matching `default*AccessLevel` from `Territory2Settings`, so
"omitted" is a decision to be recorded, not a gap. Note that the same values appear on the
**`Territory2` SOQL object** as different labels — `Read Only` / `Read/Write` / `Owner` for
accounts, `Private` / `Read Only` / `Read/Write` elsewhere (Object Reference, `Territory2`). The
requirements document carries the Metadata API spelling, because that is the one that deploys.

Leads are out of scope for Northwind. If they were in, that is a separate switch:
`Territory2Settings.supportedObjects`, where "The only supported object type is `Lead`", plus
`Territory2.objectAccessLevels` (API 57.0+, values `Read` / `Edit` / `Transfer` / `All`).

---

## 6. Realignment runbook

The model states, from the Object Reference (`Territory2Model.State`): `Planning`, `Activating`,
`Activation Failed`, `Active`, `Archiving`, `Archiving Failed`, `Archived`, `Deleting`,
`Deletion Failed`. What each permits, and what the runbook does in each:

| State | What it permits | Northwind's step |
|---|---|---|
| `Planning` | Initial state of every new model. Deployable. Users without Manage Territories cannot see it | **T-28 days**: `FY27_Alignment` is created and built alongside the live `FY26_Alignment` |
| `Planning` | Rules can be deployed but not run by Metadata API — "Rules can't be run via Metadata API" | **T-21**: a Manage Territories holder runs the rules manually and the output is diffed against FY26 |
| `Activating` / `Activation Failed` | Transient. An audit that tests only for `Active` misreads both as "no active model" | **T-1**: the activation is watched, not assumed |
| `Active` | Live. Only one model at a time. Rules run automatically on record create and edit | **T-0 (1 Feb)**: FY27 activated; FY26 moves out of Active by the same act |
| `Archived` | Read-only, and **one-way** — an archived model cannot be reactivated | **T+30**: FY26 archived only after the first month's forecast has closed cleanly |
| `Deleting` / `Deletion Failed` | `delete()` on a model cascade-deletes its territories, rules and user associations | Not used. Deletion is not the rollback plan |

Two constraints that shape the whole runbook:

- **The rollback position is "do not archive yet."** Archiving is irreversible, and a model with the
  same developer name sitting in `Archived` in the target org blocks a future deploy of that name
  outright — "The `deploy()` operation on production fails because that model's state is `Archived`
  and that state prevents changes to the model." Developer names are therefore fiscal-year-stamped.
- **The deploy assigns nothing.** Rules deploy; the run is user-initiated. The runbook names the
  runner, the window, and reads `Territory2AlignmentLog` for completion rather than assuming it.

Runbook steps, with owners:

| When | Step | Owner | Done when |
|---|---|---|---|
| T-28 | Build `FY27_Alignment` in `Planning` from the linted design file | Salesforce admin | `check_territory_design_requirements.py` clean; source deployed |
| T-21 | Run rules against the Planning model; export `ObjectTerritory2Association` | Admin (Manage Territories) | `Territory2AlignmentLog` shows a finished run |
| T-18 | Diff FY26 vs FY27 assignments; circulate the movers list | Sales ops | RVP sign-off per region |
| T-14 | Load `UserTerritory2Association` for FY27 | Sales ops | Row count matches the design's membership table |
| T-7 | Freeze: no rule edits, no `Named_Account__c` changes | Sales ops | Change log empty |
| T-0 | Activate FY27 | Admin | State reaches `Active`, not `Activation Failed` |
| T-0 +2h | Run §7 acceptance tests | Admin + sales ops | All seven pass |
| T+30 | Archive FY26 | Admin | Only after the first territory forecast closes |

---

## 7. Acceptance tests

Written at design time, run after the rule run finishes. These are the definition of "the build
matches the design" — they belong in the handoff to `admin/enterprise-territory-management`, not
invented afterwards.

```sql
-- 1. The rule run actually finished, and someone owns it.
SELECT Id, Status, StartTime, EndTime, RunAs.Name, Territory2Id
FROM   Territory2AlignmentLog
WHERE  Territory2ModelId = :fy27ModelId
ORDER BY StartTime DESC
LIMIT  5

-- 2. No account sits in two territories of the SAME type.
--    A same-type tie assigns no territory to the opportunity at all.
SELECT ObjectId, COUNT(Id) assignments
FROM   ObjectTerritory2Association
WHERE  SobjectType = 'Account'
AND    Territory2Id IN :namedAccountTerritoryIds
GROUP BY ObjectId
HAVING COUNT(Id) > 1

-- 3. Primary geo coverage is mutually exclusive: no account in two Geo territories.
SELECT ObjectId, COUNT(Id) assignments
FROM   ObjectTerritory2Association
WHERE  SobjectType = 'Account'
AND    Territory2Id IN :geoTerritoryIds
GROUP BY ObjectId
HAVING COUNT(Id) > 1

-- 4. Rule-driven vs manual split matches the design (manual = the three named books only).
SELECT AssociationCause, COUNT(Id) rows
FROM   ObjectTerritory2Association
WHERE  SobjectType = 'Account'
GROUP BY AssociationCause

-- 5. Catch-all is populated but bounded. Design budget: under 1,500 accounts.
SELECT COUNT(Id)
FROM   ObjectTerritory2Association
WHERE  SobjectType = 'Account'
AND    Territory2Id = :unassignedTerritoryId

-- 6. Every territory that is supposed to have members has active members.
SELECT Territory2Id, COUNT(Id) members
FROM   UserTerritory2Association
WHERE  IsActive = true
GROUP BY Territory2Id

-- 7. Territory access actually materialised as shares.
SELECT RowCause, COUNT(Id) shares
FROM   AccountShare
WHERE  RowCause IN ('Territory', 'Territory2AssociationManual')
GROUP BY RowCause
```

Expected results, as the design states them:

| Test | Pass condition | Grounded in |
|---|---|---|
| 1 | A row with an `EndTime` and a terminal `Status` for the FY27 model | `Territory2AlignmentLog` (Object Reference, API 54.0+) |
| 2 | Zero rows | `Territory2Type` › `priority`: a same-type tie assigns no territory |
| 3 | Zero rows | Design decision: geo criteria are mutually exclusive via `Named_Account__c equals false` |
| 4 | `Territory2AssignmentRule` for everything except the named books; `Territory2Manual` for those | `ObjectTerritory2Association.AssociationCause` |
| 5 | Non-zero and under budget | Only accounts with an assignment get a row at all |
| 6 | Every leaf territory present; `Unassigned` may legitimately have none | `UserTerritory2Association.IsActive` |
| 7 | `Territory` rows for rule-driven assignments, `Territory2AssociationManual` for manual ones | `AccountShare.RowCause` (Object Reference): `Territory` = "The territory has access via a territory assignment rule"; `Territory2AssociationManual` replaced `TerritoryManual` in API 45.0 |

One caution on the aggregate queries: `ObjectId` on `ObjectTerritory2Association` is a polymorphic
reference, so keep `SobjectType = 'Account'` in the filter and pass territory Ids as a bind list
rather than traversing to the type through a relationship name the org may not expose.

---

## 8. The design file the checker lints

`templates/territory-design.yaml` filled in for Northwind (abridged to the rows that show every
shape). Lint it with:

```bash
python3 skills/admin/territory-design-requirements/scripts/check_territory_design_requirements.py \
    --manifest-dir docs/design/fy27-territories/
```

```yaml
model: FY27_Alignment
edition: Enterprise
owd:
  account: Private
  opportunity: Private
  contact: ControlledByParent
  case: Private

territory_types:
  - name: Global
    priority: 10
  - name: Geo
    priority: 20
  - name: Overlay
    priority: 30
  - name: NamedAccount
    priority: 40

territories:
  - name: Global
    type: Global
    root: true
    manual_assignment: true
    manual_assignment_owner: "Sales Ops — container territory, never rule-assigned"
    access:
      account: Read
      opportunity: Read
      case: None
    forecast_reader: "CRO"

  - name: AMER
    type: Geo
    parent: Global
    manual_assignment: true
    manual_assignment_owner: "Sales Ops — rollup node, coverage sits at the leaves"
    access:
      account: Read
      opportunity: Read
      case: Read
    forecast_reader: "RVP AMER"

  - name: AMER_Commercial
    type: Geo
    parent: AMER
    access:
      account: Edit
      opportunity: Edit
      case: Read
    forecast_reader: "Segment Director, AMER Commercial"
    rules:
      - name: AMER_Commercial_Rule
        inherited: false
        boolean_filter: "1 AND 2 AND 3"
        items:
          - field: Account.BillingCountry
            operation: includes
            value: "US;CA;MX;BR;AR"
          - field: Account.Segment__c
            operation: equals
            value: Commercial
          - field: Account.Named_Account__c
            operation: equals
            value: "false"

  - name: Named_Accounts
    type: NamedAccount
    parent: Global
    manual_assignment: true
    manual_assignment_owner: "VP Strategic Accounts — rollup node for the three books"
    access:
      account: Read
      opportunity: Read
    forecast_reader: "VP Strategic Accounts"

  - name: Named_Book_A
    type: NamedAccount
    parent: Named_Accounts
    manual_assignment: true
    manual_assignment_owner: "VP Strategic Accounts — list reviewed monthly"
    access:
      account: Edit
      opportunity: Edit
      case: Read
    forecast_reader: "VP Strategic Accounts"

  - name: Public_Sector
    type: Overlay
    parent: Global
    manual_assignment: true
    manual_assignment_owner: "Director, Public Sector — rollup node; the rule is inherited downward"
    access:
      account: Read
      opportunity: Read
    forecast_reader: "Director, Public Sector"

  - name: Public_Sector_AMER
    type: Overlay
    parent: Public_Sector
    access:
      account: Read
      opportunity: Edit
      case: None
    forecast_reader: "Director, Public Sector"
    rules:
      - name: Public_Sector_Rule
        inherited: true
        boolean_filter: "1 OR 2"
        items:
          - field: Account.Industry
            operation: equals
            value: Government
          - field: Account.Public_Sector_Flag__c
            operation: equals
            value: "true"

  - name: Unassigned
    type: Geo
    parent: Global
    access:
      account: Read
      opportunity: None
      case: None
    forecast_reader: "Sales Ops"
    rules:
      - name: Unassigned_Rule
        inherited: false
        boolean_filter: "1 OR 2"
        items:
          - field: Account.Segment__c
            operation: equals
            value: ""
          - field: Account.BillingCountry
            operation: equals
            value: ""

realignment:
  cadence: annual
  cutover_date: "2027-02-01"
  states: "Planning -> Active; FY26 archived at T+30"
  rule_runner: "Salesforce admin holding Manage Territories"
  rollback: "FY26_Alignment is left un-archived until the first FY27 forecast closes"
```

---

## Where each artefact goes next

| Artefact | Consumed by | Path |
|---|---|---|
| `territory-design.yaml` | The ETM build: territory, type and rule XML is transcribed from it | `skills/admin/enterprise-territory-management/references/metadata-examples.md` §2–§5 |
| Access-level decision table (§5) | The same build, plus the OWD conversation it depends on | `skills/admin/sharing-and-visibility/SKILL.md` |
| Realignment runbook (§6) | Release planning for the cutover window | `skills/devops/metadata-api-retrieve-deploy/SKILL.md` |
| Acceptance tests (§7) | Post-activation verification | `skills/admin/enterprise-territory-management/references/metadata-examples.md` §10 |
| Membership table (§2, §6 T-14) | Bulk load of `UserTerritory2Association` | `skills/data/territory-data-alignment/SKILL.md` |
| The questionnaire (§1) | Rolled up into the wider discovery catalogue when territory design is one workstream | `skills/admin/requirements-gathering-for-sf/references/worked-examples.md` |
