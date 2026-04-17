# Examples — Session High Assurance Policies

## Example 1: Require HA to view SSN field

**Context:** HR org.

**Problem:** SSN is visible whenever anyone views the Contact.

**Solution:**

Move SSN to a detail page section guarded by a Flow that checks session level; if Standard, route through Verify Identity.

**Why it works:** Single user action, minimal disruption to other workflows.


---

## Example 2: Connected app HA requirement

**Context:** Mobile app used by auditors.

**Problem:** Long-lived refresh tokens bypass MFA.

**Solution:**

Connected App → Session Policy → High Assurance Session Required. Forces MFA on each session.

**Why it works:** Treats the mobile app like a web login for step-up purposes.

