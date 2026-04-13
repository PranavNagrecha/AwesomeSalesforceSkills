# Gotchas — Insurance Cloud Architecture

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Module Activation Is Separate from License Provisioning

**What happens:** After purchasing the FSC Insurance Add-On, administrators expect Insurance objects to be immediately available. Each module (Brokerage Management, Claims Management, Policy Administration, Group Benefits) must be explicitly enabled in Setup > Insurance Settings after the license is provisioned. Licensing grants the right to activate; activation must be performed per module.

**When it occurs:** Every new FSC Insurance implementation where a PM or admin assumes the license covers activation. Also occurs during sandbox refreshes where module settings do not carry over automatically.

**How to avoid:** Include a module activation checklist in the environment setup runbook. Verify each required module is enabled in Setup > Insurance Settings and confirm objects appear in Schema Builder before any architecture document is baselined.

---

## Gotcha 2: InsurancePolicyParticipant Uses AccountId, Not ContactId

**What happens:** InsurancePolicyParticipant.PrimaryParticipantAccountId is a lookup to Account — there is no ContactId field on this object. Architects and developers accustomed to standard Contact relationships model participant roles against Contact and write SOQL accordingly. Queries fail silently or return no results.

**When it occurs:** When building SOQL reports, integrations, or OmniScript data actions that reference participant roles (policyholder, named insured, beneficiary). FSC Person Accounts add complexity because a person IS both an Account and a Contact — but the Insurance object model only uses the Account side.

**How to avoid:** All SOQL and integration mappings for InsurancePolicyParticipant must reference Account. Document this explicitly in data architecture diagrams. Confirm with integration teams that their source systems send Account IDs (or values that can be matched to Account, not Contact).

---

## Gotcha 3: InsuranceUnderwritingRule Defaults to Draft and Is Not Evaluated Until Activated

**What happens:** New InsuranceUnderwritingRule records are created in Draft status. Rules in Draft are not evaluated by the Insurance Product Administration APIs during quoting or eligibility checks. Deployments create correct rules but forget to transition them to Active — underwriting returns no decisions silently with no error.

**When it occurs:** Post-deployment testing after a rules migration or new product configuration. The rule record exists in the org but produces no output, making it appear like an API or Integration Procedure bug.

**How to avoid:** Include explicit InsuranceUnderwritingRule status transitions (Draft → Active) in every deployment checklist. Add a post-deployment validation script that queries for `Status = 'Draft'` on rules expected to be active and alerts if any are found.

---

## Gotcha 4: Sandbox Refreshes Do Not Preserve Module Settings

**What happens:** Insurance module settings configured in production are not automatically reflected in refreshed sandboxes. After a full sandbox refresh, administrators must re-enable each Insurance module in the new sandbox's Setup > Insurance Settings before testing can proceed.

**When it occurs:** During each sandbox refresh cycle, particularly for QA and UAT environments. Teams encounter missing Insurance objects and assume a licensing problem when the module was simply not re-enabled post-refresh.

**How to avoid:** Add Insurance module activation to the sandbox post-refresh runbook. Automate verification using a setup health check script that confirms module enablement before handing the sandbox to the QA team.

---

## Gotcha 5: FSC InsurancePolicy and Health Cloud MemberPlan Are Entirely Different Products

**What happens:** Architects with Health Cloud payer experience assume FSC Insurance objects (InsurancePolicy, InsurancePolicyCoverage) share APIs or structure with Health Cloud objects (MemberPlan, CoverageBenefit). They are completely separate licensed products with separate object models, ConnectAPI namespaces, and module activation paths.

**When it occurs:** When the same team has worked on both Health Cloud and FSC Insurance engagements, or when business requirements describe "insurance" without specifying P&C/life (FSC) vs health payer (Health Cloud).

**How to avoid:** At the first architecture meeting, explicitly define which Salesforce product family is in scope. Document the distinction: FSC Insurance Cloud for P&C and life policies vs Health Cloud for health payer (MemberPlan model). This distinction should appear on page one of the solution architecture document.
