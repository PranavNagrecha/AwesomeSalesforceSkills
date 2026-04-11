# FSC Financial Calculations — Work Template

Use this template when implementing custom financial calculation logic in FSC, including rollup recalculation after bulk loads, portfolio performance metrics, custom-object aggregation, or Data Processing Engine recipes.

---

## Scope

**Skill:** `fsc-financial-calculations`

**Request summary:** (describe what the user or project requires — e.g., "Compute monthly TWR for all investment accounts" or "Bulk-load 500K FinancialHolding records without row-lock errors")

---

## Context Gathered

Answer these before writing any code:

- **Rollup engine in use:** Native RBL triggers / DPE / Both / Unknown
- **Objects involved:** (check all that apply)
  - [ ] `FinancialHolding__c` (native FSC)
  - [ ] `AssetsAndLiabilities__c` (native FSC)
  - [ ] `FinancialAccount__c` (native FSC)
  - [ ] Custom financial objects (list names):
  - [ ] External custodian / integration data
- **Data volume estimate:** (FinancialHolding rows per household, total account count)
- **Bulk load involved:** Yes / No
- **Performance metric required:** IRR / TWR / Custom / None
- **Real-time vs. batch accuracy requirement:** Real-time (keep RBL) / Batch/nightly (DPE or custom batch)
- **`WealthAppConfig__c` current state:** (check Enable Rollup Summary and Enable Group Record Rollup field values)

---

## Approach Selected

Reference the decision table in SKILL.md. Record which pattern applies and why:

- [ ] **Bulk load safety protocol** — disable triggers, load, re-enable, run `FinServ.RollupRecalculationBatchable`
- [ ] **Custom Apex performance metric batch** — `Database.Batchable` writing to custom performance object
- [ ] **DPE recipe from scratch** — single writeback node for custom-object aggregation
- [ ] **Hybrid** — describe:

**Justification:** (why this approach over alternatives)

---

## Implementation Notes

### Apex Batch Class (if applicable)

- Class name:
- Target object for output:
- Scope size (records per execute chunk):
- Schedule (cron expression or trigger condition):
- `Database.Stateful` usage: Yes (lightweight counters only) / No

### DPE Recipe (if applicable)

- Recipe name:
- Source objects:
- Aggregate operation (sum / weighted average / custom):
- Target field(s) and object:
- Schedule: (Setup > Data Processing Engine > Schedule)
- Writeback node count: (must be 1)

### Bulk Load Safety Steps

If a bulk load is part of this work, complete these in order:

1. [ ] Disable `Enable_Rollup_Summary__c` on `WealthAppConfig__c` for API user
2. [ ] Disable `Enable_Group_Record_Rollup__c` on `WealthAppConfig__c` for API user
3. [ ] Execute bulk load
4. [ ] Re-enable both settings
5. [ ] Run `Database.executeBatch(new FinServ.RollupRecalculationBatchable(), 200)`
6. [ ] Verify aggregate totals on a sample of affected `FinancialAccount__c` records

---

## Checklist

- [ ] `WealthAppConfig__c` disable/re-enable pattern implemented or documented for all bulk load paths
- [ ] `FinServ.RollupRecalculationBatchable` enqueued after bulk loads and tested in sandbox
- [ ] Custom Apex batch is bulkified — no SOQL or DML inside loops
- [ ] DPE recipes use a single writeback node (not one-to-one converted from RBL)
- [ ] Apex tests cover bulk scenario (200+ records minimum) with rollup value assertions
- [ ] Performance metric calculations are in scheduled batch, not triggers
- [ ] Custom objects / external data have their own separate recalculation path documented
- [ ] `finish()` method logs batch completion; monitoring alert configured for batch failures

---

## Notes

(Record deviations from the standard pattern, org-specific constraints, or decisions made during implementation.)
