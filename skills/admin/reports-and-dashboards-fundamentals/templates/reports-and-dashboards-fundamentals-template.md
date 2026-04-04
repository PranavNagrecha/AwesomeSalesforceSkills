# Reports and Dashboards Fundamentals — Work Template

Use this template when designing or documenting a report or dashboard in Salesforce. Fill in each section before building.

---

## Scope

**Skill:** `reports-and-dashboards-fundamentals`

**Request summary:** (Describe what the stakeholder asked for in one sentence)

**Delivery date:** (When does this need to be ready?)

---

## Business Question

(State the specific question this report or dashboard must answer. Be precise.)

> Example: "Which accounts in the Eastern region have had no activity in the last 60 days, and who owns them?"

---

## Audience

| Field | Value |
|-------|-------|
| Primary audience | (e.g., Sales Managers, VP of Sales, Support Team) |
| Viewing frequency | (e.g., Daily, Weekly, One-time) |
| Delivery method | (On-demand dashboard / Report subscription / Export) |
| Access level | (What records should each viewer see? Their own? Their team's? All?) |

---

## Data Design

### Primary Object

(Which Salesforce object drives this report?)

### Related Objects

| Object | Relationship | Join Type |
|--------|-------------|-----------|
| (e.g., Contacts) | (e.g., Lookup from Account) | (Outer — show Accounts without Contacts / Inner — only Accounts with Contacts) |

### Report Type

- [ ] Standard report type — name: _______________
- [ ] Custom Report Type — to be created: _______________
- [ ] Justification for CRT (if applicable): _______________

### Report Format

- [ ] Tabular (flat list / export)
- [ ] Summary (grouped by one dimension)
- [ ] Matrix (rows AND columns grouped)
- [ ] Joined (multiple blocks — list blocks and their report types below)

**Joined blocks (if applicable):**

| Block | Report Type | Filters | Group By |
|-------|------------|---------|---------|
| Block 1 | | | |
| Block 2 | | | |

---

## Filters

| Filter Field | Operator | Value | Notes |
|-------------|----------|-------|-------|
| (e.g., Close Date) | (e.g., equals) | (e.g., Current FQ) | (Use relative dates — avoid hard-coded dates) |
| | | | |
| | | | |

**Cross-filters (if applicable):**

| Parent Object | Direction | Child Object | Sub-filter |
|--------------|-----------|-------------|-----------|
| (e.g., Accounts) | WITHOUT | (e.g., Activities) | (e.g., Activity Date > LAST 60 DAYS) |

---

## Groupings and Columns

### Row Groupings (Summary/Matrix)

| Order | Field | Sort | Subtotal |
|-------|-------|------|---------|
| 1st | | (Asc/Desc) | (Yes/No) |
| 2nd | | | |

### Column Groupings (Matrix only)

| Order | Field |
|-------|-------|
| 1st | |

### Key Columns

| Column | Field | Type | Notes |
|--------|-------|------|-------|
| | | (Standard/Formula/Bucket) | |

### Bucket Fields

| Field | Bucket Name | Ranges |
|-------|------------|--------|
| (e.g., Amount) | Deal Size | Small: 0–10k / Mid: 10k–100k / Enterprise: 100k+ |

### Summary Formulas

| Name | Formula | Format | Level |
|------|---------|--------|-------|
| (e.g., Win Rate) | (e.g., CLOSED_WON_COUNT / RowCount) | Percent | All summary levels |

---

## Dashboard Design

(Complete this section only if the output includes a dashboard)

### Dashboard Configuration

| Setting | Value |
|---------|-------|
| Dashboard name | |
| Running user type | (Run as logged-in user / Run as specified user: ___) |
| Edition required | (Enterprise for dynamic / Professional for static) |
| Refresh schedule | (Auto 24h / On demand only for dynamic) |
| Folder | |

### Components

| # | Component Type | Source Report | Metric/Chart Config | Notes |
|---|---------------|--------------|-------------------|-------|
| 1 | (Metric/Chart/Table/Gauge) | | (Field for value, chart axis, etc.) | |
| 2 | | | | |
| 3 | | | | |
| 4 | | | | |
| 5 | | | | |

### Dashboard Filters

| Filter Name | Mapped Field | Affected Components |
|------------|-------------|-------------------|
| | | |

---

## Access and Delivery

### Folder Permissions

| Folder | Who Has Access | Permission Level |
|--------|---------------|-----------------|
| Report folder | (Role, Profile, or Public Group) | (View / Edit) |
| Dashboard folder | | |

### Report Subscription (if applicable)

| Setting | Value |
|---------|-------|
| Frequency | (Daily / Weekly / Monthly) |
| Recipients | (List names or roles — confirm all are active employees) |
| Running user | (Who owns the report — whose data do recipients receive?) |
| Condition | (Send always / Send when condition is met: ___) |

---

## Validation

Run through these before marking complete:

- [ ] Row counts verified against a known control (SOQL or list view)
- [ ] All date filters use relative ranges (no hard-coded year or month-day)
- [ ] CRT join semantics match business intent (outer vs inner confirmed)
- [ ] Dashboard running user configuration reviewed and documented
- [ ] Dashboard filters tested against all components — confirmed which are and are not affected
- [ ] Report and dashboard assigned to a shared folder (not private)
- [ ] Subscription recipients are current, active employees
- [ ] No tabular report driving a Metric or Chart dashboard component without a row limit
- [ ] Joined report block count is ≤ 5 and row count per block is ≤ 2,000
- [ ] Bucket field "Other" category reviewed — blank values accounted for
- [ ] Dashboard does not exceed 20 source report components

---

## Notes and Deviations

(Record any departures from the standard patterns documented in SKILL.md, and explain why.)
