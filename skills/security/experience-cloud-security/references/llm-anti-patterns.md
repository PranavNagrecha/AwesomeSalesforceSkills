# LLM Anti-Patterns — Experience Cloud Security

Common mistakes AI coding assistants make when generating or advising on Experience Cloud Security.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending Internal OWD Changes to Fix Portal Access

**What the LLM generates:** When a portal user cannot see records, the LLM suggests changing the internal OWD to "Public Read Only" to give portal users access.

**Why it happens:** Training data bias — many OWD explanations conflate internal and external OWD. LLMs learn that "OWD controls who can see records" and apply it to portal users without distinguishing the external OWD concept.

**Correct pattern:**
```
External users' record access is controlled by External OWD (separate from internal OWD) and Sharing Sets.
To grant portal users access to records:
1. Set External OWD for the object to the desired access level (cannot be more permissive than internal OWD)
2. Create a Sharing Set with an access mapping from the portal user's Contact/Account to the target records
```

**Detection hint:** Any suggestion to change internal OWD to grant portal or community user access. Internal OWD changes affect all internal users — a separate external OWD and Sharing Set is the correct approach.

---

## Anti-Pattern 2: Suggesting Guest Users Can Be Added to Sharing Sets

**What the LLM generates:** Instructions to add a guest user profile to a Sharing Set or create a Sharing Set for the guest user to access records.

**Why it happens:** LLMs conflate guest users with other external user types (Customer Community, Partner). The distinction that Sharing Sets apply only to authenticated licensed portal users and explicitly exclude guest users is a nuance not widely represented in training data.

**Correct pattern:**
```
Guest users cannot be included in Sharing Sets. Guest user record access must be granted via:
- Guest sharing rules (limited to objects and conditions)
- Apex sharing (insert ObjectName__Share record) triggered by an automated process
- Profile-level "View All" for specific objects (only if the risk is acceptable)
```

**Detection hint:** Any instruction to add a guest profile or guest user to a Sharing Set configuration.

---

## Anti-Pattern 3: Assuming External OWD Can Be Set More Permissive Than Internal OWD

**What the LLM generates:** Instructions to set external OWD to "Public Read/Write" while internal OWD is "Private" to give portal users broad access without affecting internal users.

**Why it happens:** LLMs reason that external and internal OWD are independent settings that can be configured independently in any combination. The constraint that external OWD can never exceed internal OWD permissiveness is a platform-specific restriction.

**Correct pattern:**
```
External OWD can be equal to or more restrictive than internal OWD — never more permissive.
If internal OWD is Private, external OWD can also only be Private.
To give portal users broader access than what internal OWD allows, use Sharing Sets, not OWD.
```

**Detection hint:** Any configuration recommendation where external OWD is set to a more permissive value than the corresponding internal OWD for the same object.

---

## Anti-Pattern 4: Using "without sharing" in Apex Accessible to Guest Profile

**What the LLM generates:** Apex classes for Experience Cloud pages or REST endpoints marked `global without sharing`, often citing performance reasons or the need to access system-level data.

**Why it happens:** LLMs are trained on many Apex examples that use `without sharing` for utility classes and controllers. They apply this pattern broadly without flagging the security implication for guest user contexts.

**Correct pattern:**
```apex
// For any Apex accessible to guest or portal users:
public with sharing class GuestDataController {
    @AuraEnabled
    public static List<Case> getOpenCases() {
        // with sharing enforces the guest profile's record access
        return [SELECT Id, Subject FROM Case WHERE Status = 'Open'];
    }
}
```

**Detection hint:** Any Apex class intended for use in an Experience Cloud site or guest profile context that uses `without sharing` or lacks a sharing keyword.

---

## Anti-Pattern 5: Recommending "View All" Profile Permission for Portal Users

**What the LLM generates:** To give portal users broad access, the LLM suggests granting "View All" permission on the object to the portal user profile as a simpler alternative to Sharing Sets.

**Why it happens:** LLMs know that profile-level "View All" grants broad read access. They suggest it as a simple solution without considering the overly permissive nature — a portal user with View All can read ALL records of that object, not just records related to their account.

**Correct pattern:**
```
"View All" on a portal user profile grants access to ALL records of that object regardless of account relationship.
Use Sharing Sets with a specific lookup mapping to restrict access to only related records.
"View All" is only appropriate for objects where the portal user legitimately needs to see all records (e.g., public Knowledge articles).
```

**Detection hint:** Any recommendation to grant "View All" or "Modify All" permission to a Customer Community or Partner Community profile as a solution to record visibility issues.
