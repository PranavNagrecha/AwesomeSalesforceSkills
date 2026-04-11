# Examples — Compliant Data Sharing Setup

## Example 1: Isolating Retail Banking from Wealth Management Teams

**Context:** A mid-sized FSC org has two business lines — retail banking and wealth management — using the same Salesforce instance. Both lines share Account and Opportunity objects. Retail relationship managers were inadvertently able to see wealth management client accounts because the OWD was Public Read/Write and the role hierarchy placed both lines under a shared regional manager.

**Problem:** With standard sharing, any regional manager can see all accounts owned by users below them in the hierarchy. There is no way to enforce a hard boundary between retail and wealth teams without Compliant Data Sharing. Sharing rules cannot remove access granted via role hierarchy.

**Solution:**

```text
Admin steps:
1. Setup > Sharing Settings
   - Account OWD: change to Private
   - Opportunity OWD: change to Private
   (Schedule during maintenance window — triggers recalculation)

2. Setup > Industries Settings
   - enableCompliantDataSharingForAccount = true
   - enableCompliantDataSharingForOpportunity = true

3. Create Participant Roles:
   - "Retail RM"         AccessLevel: Edit
   - "Retail Co-RM"      AccessLevel: Read
   - "Wealth Advisor"    AccessLevel: Edit
   - "Wealth Associate"  AccessLevel: Read

4. Assign permission sets:
   - CDS Manager → all CDS administrators
   - CDS User → all retail RMs, wealth advisors, and their managers

5. For each Account owned by a retail RM:
   - Add Participant Role assignment: retail RM → "Retail RM"
   (Do NOT add wealth advisor participants to retail accounts,
    and vice versa, to enforce the ethical wall)

6. Validate: log in as a wealth advisor and confirm retail banking 
   accounts are not visible in list views or search.
```

**Why it works:** CDS disables role-hierarchy inheritance on Account and Opportunity. The regional manager who sits above both lines no longer automatically sees either line's records. Access is granted only through explicit Participant Role assignments, so the ethical wall is maintained at the platform level regardless of hierarchy changes.

---

## Example 2: Assigning Participant Roles to a Financial Deal Record

**Context:** An investment banking deal team is using Financial Deal records to manage an M&A transaction. The deal lead, a co-advisor, and a compliance officer all need access to the Financial Deal record, but each at a different permission level. No one outside the deal team should be able to see it.

**Problem:** With standard OWD alone, the Financial Deal record is visible to the owner's management chain. Without CDS, there is no way to limit visibility to the named deal team only. The compliance officer is in a completely different role hierarchy branch and would have no access at all under normal sharing.

**Solution:**

```text
Prerequisites:
- Deal Management must be enabled (Setup > Financial Deal Settings)
- IndustriesSettings: enableCompliantDataSharingForFinancialDeal = true
- Financial Deal Participants related list added to Financial Deal page layout
- Participant Roles created:
    "Deal Lead"          AccessLevel: Edit
    "Deal Co-Advisor"    AccessLevel: Edit
    "Compliance Review"  AccessLevel: Read

Admin workflow for a specific Financial Deal record:
1. Open the Financial Deal record.
2. Navigate to the Financial Deal Participants related list.
3. Click New Participant.
   - User: [Deal Lead user]
   - Participant Role: Deal Lead
4. Click New Participant.
   - User: [Co-Advisor user]
   - Participant Role: Deal Co-Advisor
5. Click New Participant.
   - User: [Compliance Officer user]
   - Participant Role: Compliance Review

Verification:
- Log in as the compliance officer and confirm the Financial Deal record 
  appears with read-only access.
- Log in as a user outside the deal team and confirm the record is not 
  visible (OWD is Private, no participant assignment exists for them).
```

**Why it works:** Each Participant Role assignment triggers the CDS engine to write a `RowCause = 'CompliantDataSharing'` share row for that user on that record. The compliance officer gains Read access via the "Compliance Review" role even though they are in a completely different org hierarchy branch. The deal remains invisible to everyone not listed as a participant.

---

## Anti-Pattern: Leaving Standard Sharing Rules in Place When CDS Is Enabled

**What practitioners do:** An admin enables CDS for Account but does not audit or remove existing Account sharing rules (e.g., "Share all accounts in the Retail Banking public group with the Wealth Management public group"). The sharing rules were created before CDS and were intended to be replaced by the ethical wall.

**What goes wrong:** Standard sharing rules produce `RowCause = 'ManualShare'` or criteria-based share rows that are completely independent of CDS. CDS does not remove or override them. Wealth management users continue to see retail banking accounts via the sharing rule even though CDS is active. The ethical wall is incomplete and the compliance team reports the separation as failed.

**Correct approach:** Before enabling CDS, audit all Account and Opportunity sharing rules. Delete or disable any rules that would grant cross-line access. CDS replaces role-hierarchy inheritance; it does not replace sharing rules. Both mechanisms can be active simultaneously and both must be managed deliberately.
