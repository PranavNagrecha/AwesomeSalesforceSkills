# LLM Anti-Patterns — IP Range and Login Flow Strategy

Common mistakes AI coding assistants make when generating or advising on IP Range and Login Flow Strategy.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Suggesting Login Flows Can Hard-Block Login by IP

**What the LLM generates:** "Create a Login Flow that checks the user's IP and, if outside the corporate range, displays an error screen preventing login."

**Why it happens:** LLMs conflate Login Flows (post-authentication conditional screens) with profile Login IP Ranges (network-layer hard deny). The training data often describes both in the same security context without distinguishing their enforcement mechanisms.

**Correct pattern:**

```
Login Flows add friction (extra screens, verification steps) but cannot prevent a determined
user from closing the flow or accessing the org through API login. For hard IP-based login
denial, use Login IP Ranges on the user's profile (Setup > Profiles > Login IP Ranges).
Login Flows are appropriate for conditional verification, not hard blocking.
```

**Detection hint:** Look for Login Flow advice that claims to "block" or "prevent" login. Login Flows can display screens but the enforcement is UI-level, not network-level.

---

## Anti-Pattern 2: Using UserInfo.getUserId() Inside Login Flow Apex

**What the LLM generates:** Apex code that calls `UserInfo.getUserId()` to identify the authenticating user inside a Login Flow Invocable Action.

**Why it happens:** `UserInfo.getUserId()` is the standard Apex pattern for identifying the running user. LLMs default to it because it appears in the majority of Apex training examples. In the Login Flow context, however, this returns the Login Flow User's ID, not the authenticating user's ID.

**Correct pattern:**

```apex
// WRONG — returns Login Flow User ID, not the authenticating user
Id userId = UserInfo.getUserId();

// CORRECT — pass the user's ID from the flow variable $Flow.LoginFlow_UserId
@InvocableMethod
public static List<String> checkUser(List<Id> userIds) {
    Id authenticatingUserId = userIds[0]; // Passed from flow
    // ... use authenticatingUserId for queries and logic
}
```

**Detection hint:** Search for `UserInfo.getUserId()` in any Apex class designed to be called from a Login Flow. Replace with a parameter sourced from `$Flow.LoginFlow_UserId`.

---

## Anti-Pattern 3: Recommending Autolaunched Flow as a Login Flow

**What the LLM generates:** "Create an Autolaunched Flow to run during login that checks the user's IP and updates a field on the User record."

**Why it happens:** LLMs associate "flow that runs automatically" with Autolaunched Flows. Login Flows require Screen Flows because they need to display UI elements during the login process. Autolaunched Flows have no UI and cannot be assigned as Login Flows.

**Correct pattern:**

```
Login Flows must be Screen Flows. Only Screen Flows can be assigned as Login Flows in
Setup > Login Flows. If no screen is needed on the happy path, the Screen Flow can use
Decision elements to skip all screens and proceed directly to the End element — but it
must still be of type Screen Flow.
```

**Detection hint:** Check the flow type recommendation. If the advice says "Autolaunched Flow," "Record-Triggered Flow," or "Scheduled Flow" for a Login Flow use case, it is wrong.

---

## Anti-Pattern 4: Conflating ConnectedAppPlugin with Login Flows

**What the LLM generates:** "Override ConnectedAppPlugin.authorize() to add a custom login screen for all users logging in through the standard Salesforce login page."

**Why it happens:** Training data describes both ConnectedAppPlugin and Login Flows as "login customization" mechanisms. LLMs often recommend ConnectedAppPlugin for standard UI login, when it only applies to Connected App OAuth flows (mobile apps, third-party OAuth integrations).

**Correct pattern:**

```
ConnectedAppPlugin.authorize() runs only when authentication occurs through a Connected App
(OAuth 2.0 flow). It does NOT run during standard username/password login or SSO.

For standard UI login customization: use a Login Flow (Screen Flow assigned to a profile).
For Connected App OAuth customization: use ConnectedAppPlugin.
For both: implement shared logic in a utility class called from both contexts.
```

**Detection hint:** If the advice mentions `ConnectedAppPlugin` for "all users" or "standard login," it is conflating two different mechanisms.

---

## Anti-Pattern 5: Omitting Fault Handling in Login Flow Apex Actions

**What the LLM generates:** A Login Flow design with Apex Actions but no Fault connectors on the Action elements, and no try/catch in the Apex code.

**Why it happens:** LLMs generate "happy path" flow designs by default. In standard flows, an unhandled fault shows an error but the user can navigate away. In Login Flows, an unhandled fault blocks login entirely — the user is stranded on an error page with no way to enter the org.

**Correct pattern:**

```apex
@InvocableMethod
public static List<String> safeIpCheck(List<String> ipAddresses) {
    try {
        // IP detection and range checking logic
        return new List<String>{ result };
    } catch (Exception e) {
        // Log the error for admin visibility
        System.debug(LoggingLevel.ERROR, 'Login Flow IP check failed: ' + e.getMessage());
        // Return a safe default that allows login to proceed
        return new List<String>{ 'UNKNOWN' };
    }
}
```

```
In the flow: add a Fault connector on every Apex Action element. Route the Fault path to
a Screen that says "An error occurred during login verification. You may proceed." with
a Next button leading to the End element. Never let a fault terminate the flow.
```

**Detection hint:** Check whether every Apex Action in the Login Flow has a Fault connector. Check whether the Apex code has try/catch blocks that return safe defaults rather than throwing.

---

## Anti-Pattern 6: Suggesting IP Detection via Flow Formulas Alone

**What the LLM generates:** A flow formula like `IF(LEFT({!sourceIp}, 10) = "203.0.113.", true, false)` for IP range matching inside the Login Flow.

**Why it happens:** LLMs try to minimize code by using declarative formula logic. String-based IP matching is unreliable: it breaks on variable-length octets, does not handle CIDR ranges, and cannot perform numeric range comparison.

**Correct pattern:**

```
Use an Apex Invocable Action for IP detection and range matching. The Invocable should:
1. Get the source IP from Auth.SessionManagement.getCurrentSession()
2. Convert the IP to a numeric value
3. Compare against Custom Metadata IP range records using numeric comparison
4. Return a Boolean to the flow

The flow's Decision element should consume the Boolean, not attempt IP string parsing.
```

**Detection hint:** Look for `LEFT()`, `MID()`, `CONTAINS()`, or string comparison operators applied to IP addresses in flow formulas. These are unreliable for IP range matching.
