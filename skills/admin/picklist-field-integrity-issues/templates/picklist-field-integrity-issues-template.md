# Picklist Field Integrity Issues — Work Template

Use this template when auditing and remediating picklist data quality issues.

## Scope

**Skill:** `picklist-field-integrity-issues`

**Request summary:** (fill in what the user reported or what triggered this audit)

**Affected object(s):** (e.g., Account, Case, Opportunity)

**Affected field(s):** (e.g., Status__c, Priority__c, Region__c)

## Context Gathered

- **Restricted or unrestricted:** (check Setup > Object Manager > [Field] > Edit)
- **Global Value Set or object-local:** (GVS name if applicable)
- **Record types on the object:** (list all; note which should see which values)
- **Data entry channels:** (UI only / Data Loader / REST API / Bulk API / middleware / Flow)
- **Dependent picklist configured:** (yes/no; if yes, which controlling field)
- **Approximate record count:** (to gauge cleanup effort)

## Integrity Audit Results

### Defined Value Set

List the active picklist values as defined in Setup or metadata:

| # | Value (API Name) | Active | Notes |
|---|---|---|---|
| 1 | (value) | Yes/No | |
| 2 | (value) | Yes/No | |

### Actual Values in Data

Paste the results of the GROUP BY audit query:

```sql
SELECT [Field__c], COUNT(Id) FROM [Object] GROUP BY [Field__c] ORDER BY COUNT(Id) DESC
```

| Value | Record Count | Status |
|---|---|---|
| (value) | (count) | Valid / Orphaned / Invalid |

### Orphaned/Invalid Values Identified

| Invalid Value | Record Count | Recommended Action | Replacement Value |
|---|---|---|---|
| (value) | (count) | Replace / Null / Investigate | (value or null) |

## Dependent Picklist Violations (if applicable)

```sql
SELECT Id, [Controlling__c], [Dependent__c]
FROM [Object]
WHERE [Controlling__c] = '(value)' AND [Dependent__c] NOT IN ('valid1', 'valid2')
```

| Controlling Value | Invalid Dependent Value | Record Count |
|---|---|---|
| (value) | (value) | (count) |

## Record Type Mapping Audit (if applicable)

| Record Type | Field | Values Mapped | Missing Values | Extra Values |
|---|---|---|---|---|
| (RT name) | (field) | (count) | (list) | (list) |

## Remediation Plan

### Step 1: Data Cleanup

- [ ] Run Data Loader / Apex batch to replace orphaned values
- [ ] Verify cleanup with re-run of audit query
- [ ] Confirm zero orphaned values remain

### Step 2: Enforcement

- [ ] Toggle picklist to Restricted (if appropriate)
- [ ] Deploy validation rule for dependent picklist enforcement (if applicable)
- [ ] Update record type picklist mappings (if applicable)

### Step 3: Testing

- [ ] Test valid UI record creation — succeeds
- [ ] Test valid API record creation — succeeds
- [ ] Test invalid API write to restricted picklist — rejected
- [ ] Test invalid dependent combination via API — rejected by validation rule
- [ ] Test record type picklist display — correct values per record type

### Step 4: Monitoring

- [ ] Scheduled report created to flag new orphaned values
- [ ] Deployment checklist updated with record type mapping step
- [ ] Documentation updated with restricted field inventory

## Notes

(Record any deviations from the standard remediation pattern and why.)
