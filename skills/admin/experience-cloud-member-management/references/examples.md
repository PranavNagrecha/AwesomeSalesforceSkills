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
global class CustomerSelfRegHandler implements Auth.ConfigurableSelfRegHandler {

    private static final String PARTNER_ACCOUNT_ID = '001000000000001AAA'; // replace with real ID

    // The ONLY method on Auth.ConfigurableSelfRegHandler.
    // It returns the Id of the User it created — not a User sObject.
    global Id createUser(Id accountId,
                         Id profileId,
                         Map<SObjectField, String> registrationAttributes,
                         String password) {

        User u = new User();
        u.ProfileId = profileId;

        // registrationAttributes is keyed by SObjectField, not by String.
        for (SObjectField field : registrationAttributes.keySet()) {
            u.put(field, registrationAttributes.get(field));
        }

        // Domain-based account routing: override the account the platform passed in.
        Id targetAccountId = accountId;
        String email = registrationAttributes.get(User.Email);
        if (String.isNotBlank(email) && email.endsWithIgnoreCase('@partner.example.com')) {
            targetAccountId = PARTNER_ACCOUNT_ID;
        }

        u.CommunityNickname  = generateNickname(email);
        u.TimeZoneSidKey     = UserInfo.getTimeZone().getID();
        u.LocaleSidKey       = UserInfo.getLocale();
        u.LanguageLocaleKey  = UserInfo.getLocale();
        u.EmailEncodingKey   = 'UTF-8';

        if (String.isBlank(password)) {
            password = generateRandomPassword();
        }
        Site.validatePassword(u, password, password);

        // Site.createExternalUser creates the Contact under targetAccountId,
        // creates the User, and returns the new User Id.
        return Site.createExternalUser(u, targetAccountId, password);
    }

    private String generateNickname(String email) { /* ... */ return null; }
    private String generateRandomPassword()       { /* ... */ return null; }
}
```

Then set this class name in the Self-Registration Handler field in the Registration settings.

**Why it works:** `Auth.ConfigurableSelfRegHandler.createUser` receives the account and profile configured in the Registration settings, plus the form values as a `Map<SObjectField, String>`, and hands back the Id of the user it created. `Site.createExternalUser(user, accountId, password)` does the Contact creation and account linkage in one call, which is why the handler can route users to different accounts by passing a different `accountId`. Returning `null` — or throwing — fails the registration, which is how a domain-based allow/deny list is implemented.

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

## Anti-Pattern: Reusing an Internal Profile for a Contact-Based External User

**What practitioners do:** To save time, an admin clones an internal "Standard User" profile, assigns it to a portal user record, and expects that user to reach the Experience Cloud site the way the external members do.

**What goes wrong:** Not what most write-ups claim. Internal profiles *can* legitimately sit in a site's members list — `NetworkMemberGroup` says members "can be either users in your internal org or external users assigned portal profiles", and `Network.allowInternalUserLogin` exists precisely so employees can sign in on the site login page. So the deploy succeeds and the profile really does appear under Members. What breaks is the user record. An internal profile carries an internal user licence, because "every profile belongs to exactly one user license type", so the moment you save that user you have consumed a full Salesforce seat instead of a Community seat. And `User.AccountId` is read-only and null for Salesforce users, so the record is not contact-based: it has no account, it is invisible to the account-driven sharing the portal is built on, and it cannot be reached by the "Enable Partner User" path at all. The org quietly pays internal-licence prices for portal users who then cannot see portal data.

**Correct approach:** Separate the two questions. If the person is a *customer or partner reached through a Contact*, they need an external profile (Customer Community, Customer Community Plus, Partner Community, or External Identity) and a `ContactId` whose Contact has an `AccountId`. If the person is an *employee who should see the site*, leave them on their internal profile, add that profile to `networkMemberGroups` on purpose, and set `allowInternalUserLogin` deliberately. Then check which one you actually built:

```sql
-- Any row here with a null ContactId or a Standard UserType is an internal-licence
-- user wearing a portal costume. UserType is derived from the profile's licence and
-- cannot be set on insert.
SELECT Id, Username, UserType, ContactId, Contact.AccountId,
       Profile.Name, Profile.UserLicense.Name, IsActive, IsPortalEnabled
FROM User
WHERE Profile.Id IN (SELECT ParentId FROM NetworkMemberGroup WHERE NetworkId = '0DBXX0000004CAa')
  AND IsActive = true
ORDER BY Profile.Name
```

Cross-check the licence choice itself against architect/experience-cloud-licensing-model before creating the profile — the licence is fixed at profile creation and cannot be changed afterwards.
