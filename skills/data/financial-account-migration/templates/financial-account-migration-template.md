# Financial Account Migration — Work Template

Use this template when planning or executing a bulk migration of FSC financial account data.

## Scope

**Skill:** `data/financial-account-migration`

**Request summary:** (fill in what the user asked for — e.g., "migrate 400k holdings and 2M transactions from Fidelity export into Production FSC org")

---

## 1. Deployment Model Confirmation

| Question | Answer |
|---|---|
| Is the target org managed-package FSC (`FinServ__` namespace)? | [ ] Yes / [ ] No |
| Is the target org Core FSC (API v61.0+, Spring '25+)? | [ ] Yes / [ ] No |
| Core FSC version confirmed via: `sf sobject describe --sobject FinancialAccountTransaction` | (paste output or note result) |

---

## 2. Pre-Load Configuration

| Step | Status | Notes |
|---|---|---|
| RBL current value queried: `FinServ__EnableRollupSummary__c` | [ ] Done | Current value: _______ |
| RBL disabled for ETL user via Wealth Application Config | [ ] Done | Confirmed false: [ ] |
| DPE recalculation job identified (Core FSC only) | [ ] N/A / [ ] Done | Job name: _______ |
| FinancialSecurity records pre-loaded or confirmed present | [ ] Done | Count in target: _______ |

---

## 3. Insert Order Checklist

Execute jobs in this sequence. Record record counts at each step.

| # | Object | Source File | External ID Field | Target Count | Status |
|---|---|---|---|---|---|
| 1 | Account / PersonAccount | | | | [ ] Done |
| 2 | FinancialSecurity | | | | [ ] Done |
| 3 | FinancialAccount | | | | [ ] Done |
| 4 | FinancialAccountRole (Primary Owner first) | | | | [ ] Done |
| 5 | FinancialHolding | | | | [ ] Done |
| 6 | FinancialAccountTransaction | | | | [ ] Done |

---

## 4. Balance History Strategy

**Deployment model:** (managed package / Core FSC)

**Strategy chosen:**

- [ ] **Managed-package:** Write current balance to `FinServ__Balance__c` on FinancialAccount during step 3 above. No separate balance history load required.
- [ ] **Core FSC:** Load `FinancialAccountBalance` child records after FinancialAccount (step 3) and before or after FinancialHolding.

| FinancialAccountBalance load details (Core FSC only) | Value |
|---|---|
| Historical periods to migrate | _______ months |
| Total FinancialAccountBalance rows | _______ |
| Sort order of CSV | Ascending by BalanceDate: [ ] Confirmed |
| Load status | [ ] Done |

---

## 5. Post-Load Recalculation

| Step | Status | Notes |
|---|---|---|
| Re-enabled `FinServ__EnableRollupSummary__c` for ETL user | [ ] Done | |
| Invoked `FinServ.RollupRecalculationBatchable` (managed package) | [ ] N/A / [ ] Done | Batch job ID: _______ |
| Triggered DPE recalculation job (Core FSC) | [ ] N/A / [ ] Done | Job name: _______ |
| Recalculation job completed without errors | [ ] Done | |

---

## 6. Reconciliation and Validation

| Check | Expected | Actual | Pass? |
|---|---|---|---|
| FinancialAccount count matches source | | | [ ] |
| FinancialHolding count matches source | | | [ ] |
| FinancialAccountTransaction count matches source | | | [ ] |
| FinancialAccountBalance count matches source (Core FSC) | | | [ ] |
| Sample account holding balance matches source | | | [ ] |
| Household-level rollup total is non-zero | | | [ ] |
| No UNABLE_TO_LOCK_ROW errors in load logs | | | [ ] |

---

## 7. Notes and Deviations

(Record any deviations from the standard pattern, partial loads, retry decisions, or scope changes here.)

---

## 8. Sign-Off

| Role | Name | Date |
|---|---|---|
| Migration Lead | | |
| Org Admin / Salesforce Owner | | |
| QA Reviewer | | |
