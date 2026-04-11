# Examples — FSC Architecture Patterns

## Example 1: Greenfield FSC Implementation — Choosing Between Data Models

**Context:** A regional wealth management firm is implementing FSC for the first time. They have no existing Salesforce org. Implementation starts in Q1 2025 on a new Developer sandbox. The technical architect must decide whether to install the `FinServ__` managed package or configure platform-native FSC.

**Problem:** The team defaults to installing the managed package because most FSC documentation and AppExchange listings they have encountered reference `FinServ__` objects. They do not realize the managed-package model creates a namespace dependency that will complicate every CI/CD pipeline, integration field mapping, and Metadata API retrieve they do them for the entire life of the implementation.

**Solution:**

The architect checks the Salesforce FSC Data Model Gallery on architect.salesforce.com to confirm that the platform-native model ships `FinancialAccount`, `FinancialHolding`, and `FinancialGoal` as standard objects with full Metadata API support. Since the org is a blank sandbox with no legacy data, the architect documents the following decision:

```
Architecture Decision: FSC Data Model Selection
Decision: Platform-native FSC (no managed package)
Rationale:
  - New org — no migration cost
  - Standard objects = no FinServ__ namespace in all metadata, SOQL, and API calls
  - CI/CD pipelines (Salesforce DX) retrieve and deploy without package-version coordination
  - Core banking integration field mappings do not need namespace translation
  - Aligned with Salesforce long-term FSC investment
Constraint: Do NOT install the Financial Services Cloud managed package in this org
          or any connected sandbox. Installation creates irrecoverable namespace conflicts.
```

All integration developers are briefed: the core banking connector maps to `FinancialAccount.Name`, `FinancialAccount.FinancialAccountNumber`, and `FinancialAccount.Balance__c`, not `FinServ__FinancialAccount__c.FinServ__FinancialAccountNumber__c`.

**Why it works:** Platform-native FSC eliminates namespace friction without losing any functional capability that matters for this implementation. The decision is made once, documented in the ADR, and enforced at the sandbox management level by prohibiting managed-package installation.

---

## Example 2: Designing Compliant Data Sharing for a Multi-Team Financial Services Org

**Context:** A large bank uses FSC for both its Wealth Management division and its Retail Banking division. Advisors in Wealth Management must not see Retail Banking clients' financial accounts (and vice versa) unless a formal advisor relationship has been established. Compliance requires an audit trail of who has access to which financial accounts and why.

**Problem:** The initial implementation used criteria-based sharing rules to attempt isolation. Rules were defined as "share Financial Accounts where RecordType = Wealth Management to Wealth Management Role." This approach does not align access with actual advisor relationships. When an advisor transfers between teams or a client relationship ends, the criteria-based rules do not automatically revoke access. Compliance audits flag this as a gap.

**Solution:**

The architect redesigns the sharing model using Compliant Data Sharing:

```
Step 1: Set OWD for FinancialAccount to Private
        (without this, CDS share sets have no enforcement power)

Step 2: Enable Compliant Data Sharing in FSC Settings > Sharing Settings

Step 3: Create FinancialAccountRole records to link advisors to specific financial accounts
        Each FinancialAccountRole record = one advisor + one FinancialAccount + role type
        Role types: Primary Advisor, Co-Advisor, Relationship Manager

Step 4: Configure CDS Share Set:
        Object: FinancialAccount
        Share To: Users who hold an active FinancialAccountRole on this FinancialAccount
        Access: Read/Write for Primary Advisor, Read for Co-Advisor

Step 5: Remove all legacy criteria-based sharing rules that conflict with CDS

Step 6: Validate:
        - Advisor A (Wealth Management) cannot see Retail client accounts
        - Advisor A CAN see Wealth Management accounts where they hold a FinancialAccountRole
        - When Advisor A's FinancialAccountRole is deactivated, access is revoked within the
          next sharing recalculation cycle
```

**Why it works:** CDS ties access directly to the formal advisor-client relationship recorded in `FinancialAccountRole`. When the relationship ends, deactivating the role record revokes access. Compliance auditors can query `FinancialAccountRole` to see exactly which advisors have access to which accounts and when each relationship was created or ended. This is not achievable with criteria-based sharing rules.

---

## Anti-Pattern: Designing Standard Sharing Rules Instead of CDS for FSC Financial Record Access

**What practitioners do:** Architects familiar with standard Salesforce sharing model design criteria-based sharing rules (e.g., share `FinancialAccount` records where `OwnerId = current user` or where `BranchId__c = current user's branch`) to control access to financial account records in FSC. They treat FSC like any other Salesforce org and skip the CDS configuration steps.

**What goes wrong:**

1. Criteria-based sharing rules do not track the advisor-client relationship as a first-class entity. When an advisor moves to a different team, their access does not change automatically — an admin must manually update the sharing rule or the OWD, which is error-prone and does not produce an audit trail.

2. Branch-level criteria sharing (all users at Branch X see all clients at Branch X) over-shares financial account data. Compliance audits flag this as granting access beyond the "need to know" principle required by FINRA Rule 4370 and similar regulations.

3. Standard sharing rules cannot model role-based access to financial accounts (Primary Advisor vs. Co-Advisor vs. View-Only) without building a parallel custom object to track these relationships — which re-invents `FinancialAccountRole`.

**Correct approach:** Enable Compliant Data Sharing. Set `FinancialAccount` OWD to Private. Configure `FinancialAccountRole` records as the relationship-tracking mechanism. Define CDS share sets that grant access exclusively to users holding active `FinancialAccountRole` records for the specific financial account. This is the FSC-native solution for exactly this compliance pattern.
