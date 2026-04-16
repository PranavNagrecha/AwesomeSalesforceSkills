# Data Cloud Query API — Work Template

Use this template when working on tasks that require querying Data Cloud unified profiles, calculated insights, or Data Lake Objects via the Query V2 or Query Connect API.

## Scope

**Skill:** `data-cloud-query-api`

**Request summary:** (fill in: what data needs to be queried and why)

## Context Gathered

- **Data Cloud org provisioned?** [ ] Yes  [ ] No
- **Connected app OAuth scope includes cdp_api?** [ ] Confirmed  [ ] Unknown
- **Target objects (DMO/DLO/CI API names):**
- **Expected result set size:** (rows estimate — determines Query V2 vs Query Connect)
- **Downstream consumer latency tolerance:** (fast = Query V2; slow/large = Query Connect)

## Token Exchange Details

- **Standard SF token endpoint:** `POST {sf_instance}/services/oauth2/token`
- **DC token endpoint:** `POST {sf_instance}/services/a360/token`
- **dcInstanceUrl captured?** [ ] Yes  [ ] No

## Query Draft

```sql
-- Replace with actual DMO/DLO/CI API names from Data Cloud Setup > Data Model Explorer
SELECT
    <field1>,
    <field2>
FROM <ssot__ObjectName__dlm>
WHERE <condition>
LIMIT 1000
```

## Pagination Strategy

- **Using Query V2 (result < 1-hour fetch window)?** [ ] Yes
  - Implement `nextBatchId` loop with < 3-minute inter-batch gap
- **Using Query Connect (large export, > 1-hour window)?** [ ] Yes
  - Implement async poll until status = complete

## Checklist

- [ ] Token exchange uses `/services/a360/token`, NOT `/services/oauth2/token`
- [ ] All API base URLs use `dcInstanceUrl`, NOT `instance_url`
- [ ] SQL uses ANSI syntax, no SOQL operators or bind variables
- [ ] Pagination loop checks for `nextBatchId` and handles cursor expiry
- [ ] Query submits within time window; Query Connect used for large exports
- [ ] Connected app OAuth scope includes `cdp_api`
- [ ] Object names match DMO/DLO API names confirmed in Data Cloud Setup

## Notes

(Record any deviations from the standard pattern and why)
