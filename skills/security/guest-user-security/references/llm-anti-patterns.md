# LLM Anti-Patterns — Guest User Security

## 1. Suggesting `without sharing` for Guest-Accessible Apex

**What the LLM generates wrong:** When asked to build an @AuraEnabled controller for an Experience Cloud page, the LLM marks the class `without sharing` because "guest users don't have a user context so sharing enforcement doesn't apply."

**Why it happens:** `without sharing` is often recommended for integration classes or system-context operations. The LLM incorrectly generalizes this to guest user scenarios.

**Correct pattern:** Use `with sharing` for all guest-facing Apex. This enforces the sharing model (Public OWD records are visible; Private OWD records are not). Combine with `WITH USER_MODE` in SOQL for field-level enforcement.

**Detection hint:** Any `without sharing` class that is annotated `@AuraEnabled` or `@RestResource` and is reachable from an Experience Cloud page.

---

## 2. Forgetting `WITH USER_MODE` in Guest SOQL

**What the LLM generates wrong:** The LLM generates a SOQL query in a `with sharing` class without `WITH USER_MODE`, assuming `with sharing` handles both record and field visibility.

**Why it happens:** `with sharing` and field-level security are distinct concepts. The LLM conflates them because "with sharing = security enforcement."

**Correct pattern:** `with sharing` only enforces record visibility. `WITH USER_MODE` in SOQL enforces both sharing AND field-level security. For guest-facing classes, use both: class-level `with sharing` + query-level `WITH USER_MODE`.

**Detection hint:** Any SOQL in a guest-context class that lacks `WITH USER_MODE` and returns more than the Id field.

---

## 3. Recommending Guest Sharing Rules to Access Private OWD Records

**What the LLM generates wrong:** When a developer asks "how can guest users see specific Account records on my Experience Cloud site?", the LLM suggests creating guest sharing rules.

**Why it happens:** Sharing rules are the standard mechanism for extending record access in Salesforce. The LLM applies this pattern without knowing the Spring '21 change that removed guest sharing rule access to Private OWD records.

**Correct pattern:** Since Spring '21, guest sharing rules cannot grant access to Private OWD records. The only way to give guest users access to records is to set the OWD to Public Read Only. Use Apex filtering to control which of those public records the guest actually sees.

**Detection hint:** Any guidance suggesting "create a sharing rule for the guest user to access [Object] records" where that object has Private OWD.

---

## 4. Hardcoding Guest User ID Assumptions

**What the LLM generates wrong:** The LLM generates code that checks `UserInfo.getUserId() == '005000000000000'` or similar hardcoded guest user ID patterns to detect guest context.

**Why it happens:** Older Salesforce patterns used the all-zeros guest user ID. The LLM has seen this in training data.

**Correct pattern:** Guest user IDs are org-specific and site-specific. Never hardcode a guest user ID. To detect guest context in Apex, check `UserInfo.getUserType() == 'Guest'`. To detect it in LWC, use `@wire(getUser)` and check the user's profile type.

**Detection hint:** Any hardcoded User ID comparison or references to `'005000000000000'` for guest detection.

---

## 5. Not Auditing Per-Site Guest Profiles After Site Addition

**What the LLM generates wrong:** The LLM provides a guest user hardening guide that assumes there is one guest profile to configure, without mentioning that each Experience Cloud site has a separate profile.

**Why it happens:** The LLM generalizes from single-site examples in documentation.

**Correct pattern:** Every Experience Cloud site generates its own guest user and guest user profile. Any hardening checklist must enumerate all sites in the org and apply the review to each site's guest profile independently. Reference: `SELECT Id, Name, GuestUser.Profile.Name FROM Network` in Tooling API.

**Detection hint:** Any guest profile hardening advice that does not mention querying or auditing multiple sites.
