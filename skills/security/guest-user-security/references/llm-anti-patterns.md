# LLM Anti-Patterns — Guest User Security

## 1. Suggesting `without sharing` for Guest-Accessible Apex

**What the LLM generates wrong:** When asked to build an @AuraEnabled controller for an Experience Cloud page, the LLM marks the class `without sharing` because "guest users don't have a user context so sharing enforcement doesn't apply."

**Why it happens:** `without sharing` is often recommended for integration classes or system-context operations. The LLM incorrectly generalizes this to guest user scenarios.

**Correct pattern:** Use `with sharing` for all guest-facing Apex. This enforces the sharing model — for a guest that means only records reached by a guest user sharing rule are visible, since guest org-wide defaults are Private on every object. Combine with `WITH USER_MODE` in SOQL for field-level enforcement.

**Detection hint:** Any `without sharing` class that is annotated `@AuraEnabled` or `@RestResource` and is reachable from an Experience Cloud page.

---

## 2. Forgetting `WITH USER_MODE` in Guest SOQL

**What the LLM generates wrong:** The LLM generates a SOQL query in a `with sharing` class without `WITH USER_MODE`, assuming `with sharing` handles both record and field visibility.

**Why it happens:** `with sharing` and field-level security are distinct concepts. The LLM conflates them because "with sharing = security enforcement."

**Correct pattern:** `with sharing` only enforces record visibility. `WITH USER_MODE` in SOQL enforces both sharing AND field-level security. For guest-facing classes, use both: class-level `with sharing` + query-level `WITH USER_MODE`.

**Detection hint:** Any SOQL in a guest-context class that lacks `WITH USER_MODE` and returns more than the Id field.

---

## 3. Telling Someone to Loosen OWD So Guest Users Can See Records

**What the LLM generates wrong:** Asked "how can guest users see specific Account records on my Experience Cloud site?", the model answers "set the Account org-wide default to Public Read Only — guests can only see records where OWD is Public Read Only or Public Read/Write; Private OWD hides everything from them." Variants add "and Spring '21 removed guest sharing rules' ability to reach Private records," which inverts the mechanism a second time.

**Why it happens:** For every *other* user type, OWD really is the floor and sharing rules layer on top — so the model applies the general Salesforce sharing model to guests, where it does not hold. The Winter '21 guest policy is recent enough and narrow enough that older blog posts, Stack Exchange answers, and pre-2021 implementation guides dominate the training signal. The wrong answer is also *actionable*: an admin can follow it, the OWD change succeeds, and nothing errors — the guest simply still can't see the record, while every authenticated user in the org now can.

**Correct pattern:** Guest org-wide defaults are **Private for every object, including objects not shown on the Sharing Settings page, and that access level can't be changed.** "Secure guest user record access" is enabled in all orgs with Experience Cloud sites and can't be disabled. Record access is granted **exclusively** through **guest user sharing rules** — a special criteria-based sharing rule type that grants Read Only and counts toward the 50 criteria-based rules per object. Guests also can't be added to public groups or queues, can't receive manual or Apex managed shares, and can't own records. So: write a narrow guest user sharing rule; never touch OWD.

**Why this one is dangerous:** it fails in the exposure direction. The recommended remedy does nothing for the stated goal and silently widens record access across the entire authenticated org.

**Detection hint:** in prose, the strings `Public Read Only` or `Public Read/Write` within ~200 characters of `guest`; any sentence pairing `guest` with `set the OWD` / `change the org-wide default`; any claim that guest sharing rules *cannot* reach Private records. In metadata, a `.sharingRules-meta.xml` change proposed alongside a guest remediation, or an `objectPermissions` diff on a Guest profile paired with an OWD edit in the same change set.

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
