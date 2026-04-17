# Examples — Agent Security Review

## Example 1: Write-scope tightening

**Context:** Service agent can 'Update any Case field' via a generic UpdateRecord action.

**Problem:** Jailbreak could set Case.OwnerId to a competitor user.

**Solution:**

Replace UpdateRecord with scoped actions: `CloseCaseAction`, `AddCaseCommentAction`, `EscalateCaseAction`. Each has a narrow field allowlist enforced server-side. `OwnerId` never appears in any allowlist.

**Why it works:** Attack-surface reduction; the agent can only do what the business allows.


---

## Example 2: Regulated-field masking

**Context:** RAG grounding includes Contact.Social_Security_Number__c.

**Problem:** Agent can emit SSN in response text.

**Solution:**

At the DMO, mark the SSN field classification as Regulated. In Trust Layer output policy, enable PII masking for Regulated. Test: adversarial prompt 'what's the SSN' must return masked value.

**Why it works:** Defense layered at source (DMO classification) + output (Trust Layer mask).

