# Examples — Experience Cloud Member Management

## Example 1: Customer Portal Self-Registration with ConfigurableSelfRegHandler

**Context:** A B2C e-commerce company wants customers to self-register on their Experience Cloud site. Standard registration fields (name, email, password) are sufficient, but each new user must be assigned to a shared "Customer Community Users" account. The site uses a Customer Community license.

**Problem:** Without a custom handler or correctly configured default account, self-registration either fails silently (no default account) or assigns users to the wrong account, breaking case visibility and sharing rules.

**Solution:**

Step 1 — Create the catch-all account in Setup and note its ID.

Step 2 — In Setup > Digital Experiences > [site] > Administration > Registration:
- Enable Self-Registration
- Default New User Account: "Customer Community Users" (the catch-all account)
- Default Profile: "Customer Community User" (external profile tied to CC license)
- Leave the Self-Registration Handler field blank to use the declarative Configurable Self-Registration page.

For sites that need custom post-registration logic (e.g., assign users to different accounts based on email domain), implement a handler class:

```apex
public class CustomerSelfRegHandler implements Auth.ConfigurableSelfRegHandler {

    private static final String DEFAULT_ACCOUNT_ID = '001000000000001AAA'; // replace with real ID

    public User registerUser(Auth.SelfRegistrationContext context) {
        User u = new User();
        u.Username     = context.email;
        u.Email        = context.email;
        u.FirstName    = context.firstName;
        u.LastName     = context.lastName;
        u.Alias        = context.email.substring(0, Math.min(8, context.email.indexOf('@')));
        u.CommunityNickname = u.Alias + String.valueOf(Math.random()).substring(2, 7);
        u.TimeZoneSidKey    = 'America/Los_Angeles';
        u.LocaleSidKey      = 'en_US';
        u.EmailEncodingKey  = 'UTF-8';
        u.LanguageLocaleKey = 'en_US';
        u.ProfileId         = [SELECT Id FROM Profile
                                WHERE Name = 'Customer Community User' LIMIT 1].Id;
        // Link to the catch-all account via Contact — platform handles Contact creation
        // AccountId is set on the Contact, not the User directly in self-reg context
        return u;
    }
}
```

Then set this class name in the Self-Registration Handler field in the Registration settings.

**Why it works:** `Auth.ConfigurableSelfRegHandler.registerUser` gives full control over the User record returned to the platform. The platform creates the associated Contact and links it to the account specified in the Default New User Account setting (or one set programmatically if the handler overrides it). Returning `null` from `registerUser` cancels the registration, which is useful for domain-based allow/deny lists.

---

## Example 2: Partner User Onboarding via Manual Addition

**Context:** A manufacturing company has 15 regional distributors. Each distributor has 1–3 users who need access to a Partner Community site to view deals and submit leads. Every user must be vetted by the channel manager before gaining access.

**Problem:** Enabling self-registration would let anyone register. Profile-based membership would grant access to everyone with that profile without individual review. Neither is appropriate here.

**Solution:**

Step 1 — Confirm the distributor's Account record exists and has the correct Account record type (e.g., "Partner Account").

Step 2 — Open the distributor's Contact record in Salesforce. In the action menu, click **Enable Partner User**. A new User record creation dialog appears.

Step 3 — Fill in the User record:
- Profile: "Partner Community User" (external profile tied to Partner Community license)
- Username: must be unique globally (often `firstname.lastname@partnerdomain.com.sfpartner`)
- Email: distributor's work email

Step 4 — Confirm the site's Members list (Administration > Members) includes the "Partner Community User" profile. The new user automatically gets site access because their profile is in the Members list.

Step 5 — Save. The user receives a welcome email with a login link and temporary password.

```
// No Apex required. All steps above are declarative.
// Automation can be added via Flow or Process Builder to trigger the
// "Enable Partner User" action when a Contact's Partner_Vetting_Status__c = 'Approved'.
```

**Why it works:** The "Enable Partner User" action creates a User record linked to the Contact and Account. Because the profile is pre-added to the site's Members list, no further site-level configuration is needed. The vetting gate is enforced by withholding the "Enable Partner User" action until the channel manager approves the Contact.

---

## Anti-Pattern: Reusing an Internal Profile for External Users

**What practitioners do:** To save time, some admins clone an existing internal "Standard User" profile and assign it to a portal user, expecting it to work with the Experience Cloud site.

**What goes wrong:** Internal profiles (tied to the Salesforce license) cannot be added to the site's Members list. Even if the user record is created, the user cannot log in to the Experience Cloud site because internal profiles are blocked from external-facing sites by the platform. The admin sees the user in Setup > All Users but the user sees an "Insufficient Privileges" error on login.

**Correct approach:** Always create or use a profile tied to an external license (Customer Community, Customer Community Plus, Partner Community, or External Identity). Clone from an existing external profile of the correct license type, never from an internal profile.
