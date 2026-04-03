# Examples — Data Skew and Sharing Performance

## Example 1: Integration User Ownership Skew Causing Role Change Failures

**Context:** A mid-market B2B org runs a nightly marketing integration that imports Leads owned by a single service user ("Marketing Import User"). Over three years, this user accumulates 120,000 Lead records. The org uses Private OWD on Leads and has a role hierarchy-based sharing rule.

**Problem:** During Q4 territory realignment, an admin tries to move the Marketing Import User to a new role. The operation runs for 90+ minutes, triggers "Group membership operation already in progress" errors for concurrent role changes, and ultimately leaves some Lead sharing in an inconsistent state. The recalculation fan-out from 120,000 owned records is the cause.

**Solution:**

Remove the user from the role hierarchy and remove them from all public groups that source sharing rules:

1. Navigate to Setup → Users → [Marketing Import User] → Edit.
2. Set Role to "None" and save.
3. Verify the user is not a member of any public group that is the source group for an active sharing rule (Setup → Sharing Settings → Sharing Rules → check Source).
4. For future imports, distribute Leads across a pool of queues — keep each queue's Lead count under 10,000.

**Why it works:** A user with no role cannot trigger role-hierarchy-based sharing recalculations. Per the *Designing Record Access for Enterprise Scale* guide, placing skew-prone users outside the role hierarchy is the documented mitigation when ownership redistribution is not feasible.

---

## Example 2: Catch-All Account Causing Implicit Sharing Scan Slowness

**Context:** A marketing team loaded 400,000 contacts purchased from a data vendor under a single Account called "Unassigned Contacts" because the contacts had no known business relationship. Six months later, any single Contact ownership change takes 30+ seconds.

**Problem:** Every time any user gains or loses access to a Contact under this account, Salesforce must scan all 399,999 sibling contacts to determine whether the implicit parent share on the Account should be retained. This is parent-child data skew. The scan is not limited to bulk loads — a single record update triggers it.

**Solution:**

Identify and remediate with SOQL, then re-parent in batches:

```sql
-- Identify accounts with >10,000 children (run in Developer Console)
SELECT AccountId, COUNT(Id) cnt
FROM Contact
GROUP BY AccountId
HAVING COUNT(Id) > 10000
ORDER BY cnt DESC
```

After identifying the skewed account:
1. Create 40 segmentation accounts ("Unassigned Contacts - Batch 001" through "- Batch 040").
2. Re-parent contacts in batches of ~10,000 using Data Loader (serial mode, off-peak hours).
3. Evaluate setting Contact OWD to "Controlled by Parent" — this disables implicit sharing entirely, eliminating future scans at the cost of independent child record shares.

**Why it works:** With fewer than 10,000 children per parent, the implicit sharing scan completes quickly. Salesforce's documented guideline is to keep parent-child cardinality below 10,000 to avoid implicit sharing performance degradation.

---

## Anti-Pattern: Accumulating Records in a Single Queue Without Cleanup

**What practitioners do:** Route new records to a single "holding" queue for manual assignment. Never implement a cleanup process. After 18 months the queue holds 45,000 open records.

**What goes wrong:** Adding any new member to the queue triggers sharing recalculation for all 45,000 records. If a sharing rule is sourced from this queue, every membership change fans out across all records. End-of-quarter operations that involve adding new reps to queues fail with lock errors.

**Correct approach:** Implement a nightly batch process or scheduled Flow that auto-assigns records sitting in the holding queue for more than N business days. Keep each queue's live record count below 10,000. If multiple geographic or segment queues are needed, create them in advance rather than letting a single queue accumulate.
