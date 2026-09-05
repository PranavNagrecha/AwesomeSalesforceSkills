# Dashboard Design Template

Complete this before building a dashboard. It forces stakeholder alignment on what the dashboard is
for, who it's for, and how the data is secured. Replace every `<…>` placeholder; the italic text
after each one says what a usable answer looks like. Leave nothing as a placeholder — an unanswered
row is a design decision that will be made by accident later.

---

## Dashboard Overview

| Property | Value |
|----------|-------|
| **Dashboard Title** | `<title>` — *max 80 characters (`Dashboard.Title` limit). Names the audience and the question: "Support Load — Manager View", not "Dashboard 3".* |
| **Dashboard Developer Name** | `<Developer_Name>` — *this is what `package.xml` and the deploy use, not the title. Letters, digits and underscores; starts with a letter; no trailing or doubled underscore.* |
| **Folder (developer name)** | `<Folder_Developer_Name>` — *the folder must exist before the dashboard deploys. `unfiled$public` is the Unfiled Public Reports / Public Reports folder.* |
| **Audience** | `<roles or groups>` — *name the roles or public groups, not individuals. "Support Managers + the Head of Support", not "Priya".* |
| **Business question answered** | `<one sentence>` — *one question, phrased so the answer is a number or a ranking. If it takes two sentences, it is two dashboards.* |
| **Refresh expectation** | `<manual / scheduled / on open>` — *say what the audience believes, then check it against reality. A stale refresh is read as wrong data, not old data.* |
| **Owner (named person)** | `<name>` — *the person who fields "this number looks wrong". Not "the admin team".* |
| **Created / last reviewed** | `<YYYY-MM-DD>` |
| **Review cadence** | `<quarterly / per release / on org change>` — *pair it with the trigger, e.g. "quarterly, and on any change to the Case object".* |
| **Source reports** | `<Folder/Report_Developer_Name>, …` — *list every report this dashboard depends on. This is the blast-radius list when one of them is edited.* |

---

## Running User Configuration

This is the security decision, and it is `dashboardType` in the metadata — not the `runningUser`
element. Pick exactly one.

| `dashboardType` | Selected | What it means | Justification |
|---|:--:|---|---|
| `LoggedInUser` | ☐ | Each viewer sees data at their own access level | *Default. Choose this unless a stated requirement forbids it.* |
| `SpecifiedUser` | ☐ | **All** viewers see one user's data regardless of their own security settings | *Only when every viewer is meant to see that user's full slice.* |
| `MyTeamUser` | ☐ | Managers can view the dashboard from a subordinate's point of view | *For role-hierarchy drill-down, not for standardising numbers.* |

**If `SpecifiedUser`:**

| Question | Answer |
|---|---|
| Running user (username) | `<username>` — *a named service/integration user that will not leave the company, never a human admin.* |
| That user's record access | `<View All Data? object View All? role position? sharing rules?>` — *write what they can actually see; that is what every viewer will see.* |
| Every viewer is entitled to that slice | ☐ Confirmed / ☐ Not confirmed → **stop and redesign** |
| Environment substitution done | ☐ — *`runningUser` is environment-specific. On deploy, an undefined or invalid username is silently replaced with the deploying user's.* |
| Security sign-off | `<name>` / `<YYYY-MM-DD>` |

**Post-deploy verification (do not skip):**

```sql
SELECT DeveloperName, Title, Type, RunningUserId, FolderName
FROM Dashboard WHERE FolderName = '<Folder Name>'
```

Check `Type`. `RunningUserId` is populated even on `LoggedInUser` dashboards, so it proves nothing
on its own.

---

## Dashboard Filters

Maximum 3 filters per dashboard. **A component only responds to a filter if it declares a matching
`dashboardFilterColumns` entry** — fill the last column for every component, not just the first.

| Filter name | Report column code per source report | Components that must respond | Default value |
|---|---|---|---|
| `<Filter label>` | `<CODE per report — e.g. INDUSTRY / ACCOUNT.TYPE>` | `<component numbers>` | `<default, or "none">` |
| `<Filter label>` | `<CODE>` | `<component numbers>` | `<default>` |
| `<Filter label>` | `<CODE>` | `<component numbers>` | `<default>` |

*Column codes differ per report type even for the same business field. Retrieve each source report
and read the code off its XML rather than guessing from the field API name.*

The `between` operator takes two operands and is minimum-inclusive / maximum-exclusive. Every other
dashboard filter operator takes one.

---

## Component Design

One row per component. Aim for 4–6 per dashboard — more creates noise, and every extra component is
another report to keep alive.

### Component 1

| Property | Value |
|----------|-------|
| **Title / header** | `<title>` — *title max 40 characters, header max 80. If the component's scope differs from its neighbours, say so here — that is the only place a reader will see it.* |
| **Source report** | `<Folder_Developer_Name/Report_Developer_Name>` — *developer names, not labels.* |
| **Source report `scope`** | `<organization / MyAccounts / MyTeamsAccounts / …>` — *must match the neighbours or the title must disclose the difference.* |
| **`componentType`** | `<Bar / Column / Donut / Funnel / Gauge / Line / Metric / Pie / Table / FlexTable / Scatter>` — *`Metric` for a single number; `Gauge` needs `gaugeMin`/`gaugeMax`.* |
| **Metric displayed** | `<aggregate + grouping — e.g. Sum of Amount by Stage>` |
| **Decision it enables** | `<what someone does differently after reading it>` — *if the honest answer is "nothing", delete the component.* |
| **Responds to filters** | `<filter names>` → `dashboardFilterColumns` entries needed: `<count>` |
| **Drill behaviour** | ☐ `drillEnabled` (filtered source report) / ☐ `drillToDetailEnabled` (record page) / ☐ `drillDownUrl` → `<url>` / ☐ none — *`drillDownUrl` overrides `drillEnabled`, which overrides `drillToDetailEnabled`. Pick one.* |

### Component 2

| Property | Value |
|----------|-------|
| **Title / header** | `<title>` |
| **Source report** | `<Folder/Report_Developer_Name>` |
| **Source report `scope`** | `<value>` |
| **`componentType`** | `<value>` |
| **Metric displayed** | `<aggregate + grouping>` |
| **Decision it enables** | `<decision>` |
| **Responds to filters** | `<filter names>` |
| **Drill behaviour** | ☐ `drillEnabled` / ☐ `drillToDetailEnabled` / ☐ `drillDownUrl` → `<url>` / ☐ none |

### Component 3

| Property | Value |
|----------|-------|
| **Title / header** | `<title>` |
| **Source report** | `<Folder/Report_Developer_Name>` |
| **Source report `scope`** | `<value>` |
| **`componentType`** | `<value>` |
| **Metric displayed** | `<aggregate + grouping>` |
| **Decision it enables** | `<decision>` |
| **Responds to filters** | `<filter names>` |
| **Drill behaviour** | ☐ `drillEnabled` / ☐ `drillToDetailEnabled` / ☐ `drillDownUrl` → `<url>` / ☐ none |

### Component 4 (copy this block for each additional component)

| Property | Value |
|----------|-------|
| **Title / header** | `<title>` |
| **Source report** | `<Folder/Report_Developer_Name>` |
| **Source report `scope`** | `<value>` |
| **`componentType`** | `<value>` |
| **Metric displayed** | `<aggregate + grouping>` |
| **Decision it enables** | `<decision>` |
| **Responds to filters** | `<filter names>` |
| **Drill behaviour** | ☐ `drillEnabled` / ☐ `drillToDetailEnabled` / ☐ `drillDownUrl` → `<url>` / ☐ none |

---

## Folder and Sharing Settings

Folder access is the right to *open* the dashboard. Which rows appear is still decided by record
sharing and, on a `SpecifiedUser` dashboard, by the running user. These are separate layers.

| Property | Value |
|---|---|
| **Folder `accessType`** | ☐ `Shared` / ☐ `PublicInternal` / ☐ `Public` / ☐ `Hidden` — *`Public` includes portal users. `PublicInternal` is what most orgs mean by "everyone".* |
| **`publicFolderAccess`** | `<ReadOnly / ReadWrite / n-a>` — *only meaningful when `accessType` is `Public`.* |

| `sharedTo` | `sharedToType` | `accessLevel` |
|---|---|---|
| `<role / group / user developer name>` | `<Role / RoleAndSubordinatesInternal / Group / Manager / Organization / User>` | `<View / EditAllContents / Manage>` |
| `<…>` | `<…>` | `<…>` |

| Check | Result |
|---|---|
| Dashboard is **not** in a private folder | ☐ Confirmed |
| Delivery is a direct deploy, not a package install | ☐ Confirmed — *`folderShares` is ignored during package installation; if this ships in a package, plan a post-install step and record it here: `<step>`* |

---

## Subscriptions (if applicable)

A subscription sends the running user's rows to every recipient. It does not re-run per recipient.

| Recipient (role or group) | Frequency | Day / time | Sees rows they could not see themselves? |
|---|---|---|---|
| `<recipient>` | `<daily / weekly / monthly>` | `<day, time>` | ☐ No / ☐ Yes → **do not subscribe** |
| `<recipient>` | `<…>` | `<…>` | ☐ No / ☐ Yes → **do not subscribe** |

| Check | Result |
|---|---|
| Every recipient has access equal to or broader than the running user | ☐ Yes / ☐ No → replace the subscription with per-viewer access to the dashboard |
| No source report is a historical trend report | ☐ Confirmed — *historical trend reports cannot be subscribed to or exported.* |

---

## Testing Checklist

| Test | How to tell it passed | Result |
|------|----------------------|--------|
| Each component displays data | No component shows an error or an empty state on a day with known data | ☐ Pass |
| Every filter moves every component that should respond | Change each filter value and watch the numbers change; a tile that holds still is missing `dashboardFilterColumns` | ☐ Pass |
| Scopes are consistent or disclosed | Compare `<scope>` across the source report XML files; any mismatch is named in a component title | ☐ Pass |
| A low-access user sees only their own slice | Log in as (or simulate) a rep and confirm the numbers shrink as expected | ☐ Pass |
| `Dashboard.Type` in the org matches the design | Run the verification SOQL above | ☐ Pass |
| Drill-through lands where the design says | Click through each component with drill enabled | ☐ Pass |
| Report type is Deployed, not In Development | Setup → Report Types shows the source report types as Deployed | ☐ Pass |
| Checker is clean | `python3 scripts/check_report_inventory.py --manifest-dir force-app/main/default` returns no unaccepted finding | ☐ Pass |
| Mobile view is readable | Only if the audience uses the Salesforce mobile app | ☐ Pass / ☐ N/A |

---

## Approval

| Role | Name | Approved | Date |
|------|------|----------|------|
| Salesforce Admin | `<name>` | ☐ | `<YYYY-MM-DD>` |
| Business owner / audience representative | `<name>` | ☐ | `<YYYY-MM-DD>` |
| Security review (required only for `SpecifiedUser`) | `<name>` | ☐ | `<YYYY-MM-DD>` |
