# Examples — OmniStudio vs Standard Decision

## Example 1: FSC-Licensed Bank — Multi-Step New Account Opening UI

**Context:** A regional bank runs on Financial Services Cloud (FSC). The product team wants a new account opening experience that guides bankers through collecting applicant information (Account, Contact), running an external credit bureau check via REST API, and creating a Financial Account record upon approval. The flow spans 6 screens with conditional branching based on credit score.

**Problem:** Without a structured decision process, developers default to a Screen Flow with multiple Get Records elements and a custom Apex action for the external callout. This works for a prototype but becomes expensive to maintain: the Screen Flow grows to 40+ elements, the Apex callout class requires its own test coverage and error handling, and the cross-object data model makes Screen Flow debugging difficult. The team is also unaware that their FSC license already includes OmniStudio.

**Solution:**

The correct architecture is OmniStudio:

1. Build an **Integration Procedure** (`AccountOpening_GetApplicantData`) that retrieves Account and Contact data in parallel branches and calls the external credit bureau via an HTTP Action element. The Integration Procedure handles response mapping and caching.
2. Build an **OmniScript** (`NewAccountOpening`) with 6 steps, each step bound to the Integration Procedure's output. Conditional branching uses OmniScript's native Set Values and Conditional View elements — no Apex required.
3. Surface a **FlexCard** on the Account record page with a Launch OmniScript action, giving bankers a one-click entry point.
4. Map the OmniScript's final step to a DataRaptor Transform that creates the Financial Account record.

No Apex is required. The external callout, data assembly, and conditional UI are all declarative.

**Why it works:** FSC includes the OmniStudio license, the use case spans 3+ objects plus an external callout, and the declarative Integration Procedure handles multi-source data assembly more efficiently than equivalent Apex code. The team's FSC implementation already included OmniStudio training, so ramp time is not a factor.

---

## Example 2: Service Cloud Org — Guided Troubleshooting Flow

**Context:** A telecom company runs on Service Cloud (no Industries license). Support agents need a guided troubleshooting wizard that walks through 4 steps: verify account status, identify device model, run a network check script (pre-defined Apex), and log a case note. All data is on the Account and Case objects.

**Problem:** An architect familiar with OmniStudio from a previous FSC engagement recommends OmniScript. The org does not have an Industries license. OmniStudio components are deployed from a managed package in a sandbox but fail silently in the production org when the license check runs, causing the wizard to render as a blank page with no error message surfaced to the agent.

**Solution:**

Standard tooling is the correct choice here:

1. Build a **Screen Flow** with 4 screens: Account lookup (Get Records), Device picklist (Choice element), Network check (Apex Action invoking the existing Apex class), and Case Note (Update Records).
2. Add a **custom LWC** on the Device screen if the standard picklist display is insufficient.
3. Embed the Screen Flow in a **Lightning App Builder page** using the Flow component.

```xml
<!-- Illustrative: Screen Flow metadata element for Apex action step -->
<actionCalls>
    <name>Run_Network_Check</name>
    <actionName>NetworkCheckController</actionName>
    <actionType>apex</actionType>
    <inputParameters>
        <name>accountId</name>
        <value>
            <elementReference>accountRecord.Id</elementReference>
        </value>
    </inputParameters>
</actionCalls>
```

**Why it works:** The org is not licensed for OmniStudio. Screen Flow handles single-object and two-object guided processes adequately. The Apex class already exists, making the Screen Flow Apex Action element a low-effort integration. The solution is maintainable by admins without OmniStudio expertise.

---

## Anti-Pattern: Recommending OmniStudio Without Checking the License

**What practitioners do:** An architect sees a multi-step guided UI requirement and immediately recommends OmniStudio based on the pattern fit, without verifying the org's license.

**What goes wrong:** OmniStudio components are deployed to the org (potentially via managed package), pass sandbox testing where a developer edition or trial license may be active, and then fail silently or visibly in production when the license check enforces restrictions. This results in blank pages, broken Lightning components, or runtime errors that are difficult to trace to the root cause.

**Correct approach:** Always confirm the org's installed licenses in Setup > Company Information > Licenses before recommending OmniStudio. If the license is not present, recommend standard tooling regardless of capability fit. If the license is borderline (e.g., a limited Nonprofit license tier), confirm with the Salesforce Account Executive or contract documentation before designing against OmniStudio features.
