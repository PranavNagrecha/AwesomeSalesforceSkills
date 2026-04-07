# LLM Anti-Patterns — Experience Cloud Member Management

Common mistakes AI coding assistants make when generating or advising on Experience Cloud Member Management.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Generating Legacy Auth.RegistrationHandler Instead of Auth.ConfigurableSelfRegHandler

**What the LLM generates:** An Apex class that implements `Auth.RegistrationHandler` with `createUser(Id portalId, User newUser, String registrationAttributes, String password)` and `updateUser(Id userId, Id portalId, User newUser, String registrationAttributes, String password, String username)` methods.

**Why it happens:** Salesforce introduced `Auth.RegistrationHandler` years before `Auth.ConfigurableSelfRegHandler`. A large portion of training data — Trailhead modules, blog posts, Stack Exchange answers — references the older interface. LLMs default to the higher-frequency pattern.

**Correct pattern:**

```apex
public class MySelfRegHandler implements Auth.ConfigurableSelfRegHandler {
    public User registerUser(Auth.SelfRegistrationContext context) {
        User u = new User();
        u.Username           = context.email;
        u.Email              = context.email;
        u.FirstName          = context.firstName;
        u.LastName           = context.lastName;
        u.Alias              = context.email.left(8);
        u.CommunityNickname  = u.Alias + String.valueOf(System.currentTimeMillis()).right(5);
        u.TimeZoneSidKey     = 'America/Los_Angeles';
        u.LocaleSidKey       = 'en_US';
        u.EmailEncodingKey   = 'UTF-8';
        u.LanguageLocaleKey  = 'en_US';
        u.ProfileId          = [SELECT Id FROM Profile
                                 WHERE Name = 'Customer Community User' LIMIT 1].Id;
        return u;
    }
}
```

**Detection hint:** Look for method signatures containing `portalId` as the first parameter or a `password` parameter — these are markers of the legacy `Auth.RegistrationHandler` interface, not `Auth.ConfigurableSelfRegHandler`.

---

## Anti-Pattern 2: Recommending Profile License Changes That Violate License Binding

**What the LLM generates:** Advice such as "open the profile, change the User License field from Customer Community to Partner Community, and save." Or instructions to edit the profile XML in a deployment package to swap the `<userLicense>` tag.

**Why it happens:** LLMs generalise from the concept of "profiles are just configuration" without understanding that the user license binding is a permanent platform constraint. The Metadata API technically allows deploying a profile XML with a different license value, but the platform rejects it with a validation error.

**Correct pattern:**

```
When the wrong license type was chosen:
1. Create a NEW profile cloned from the correct external base profile
   (e.g., "Partner Community User" instead of "Customer Community User").
2. Deactivate users on the old profile.
3. Create new user records assigned to the new profile.
4. Re-share records as needed under the new profile/license context.
There is no in-place migration path — a new profile and new user records are required.
```

**Detection hint:** Any instruction that says "edit the license on the existing profile" or "change the User License field" on a profile that already has active users is incorrect. Flag and reject.

---

## Anti-Pattern 3: Omitting the Default New User Account for Self-Registration

**What the LLM generates:** A self-registration setup walkthrough that enables the Self-Registration toggle and sets a Default Profile, but does not mention or configure the Default New User Account. The instructions treat the account field as optional.

**Why it happens:** LLMs trained on incomplete tutorial content often summarise the "enable self-reg" flow at a high level, omitting the account configuration step because it appears lower in the UI and is less frequently discussed as a distinct failure mode.

**Correct pattern:**

```
In Setup > Digital Experiences > [site] > Administration > Registration:
1. Enable Allow customers and partners to self-register.
2. Default New User Account: [set to a dedicated catch-all business Account, NOT a Person Account].
3. Default Profile: [set to the external profile tied to the correct license].
Both fields are required for self-registration to function.
Without the Default New User Account, self-registration silently fails.
```

**Detection hint:** Any self-registration setup guide that does not explicitly name the Default New User Account field as a required step is missing a critical piece. Check for this field's presence before trusting the instructions.

---

## Anti-Pattern 4: Recommending Internal Profiles for Experience Cloud Sites

**What the LLM generates:** Instructions to "add the Standard User profile to the site's Members list" or "use your existing Salesforce profile to grant portal access," treating internal and external profiles as equivalent.

**Why it happens:** LLMs conflate user profiles in general (a concept they have abundant training data on) with the external-user profile concept specific to Experience Cloud. The distinction between internal licenses (Salesforce, Salesforce Platform) and external licenses (Customer Community, Partner Community, etc.) is often blurred in older training material.

**Correct pattern:**

```
External Experience Cloud site membership only accepts profiles tied to
external user licenses:
- Customer Community
- Customer Community Plus
- Partner Community
- External Identity

Internal profiles (tied to the Salesforce or Salesforce Platform license)
cannot be added to the Members list and cannot be used to log in to an
Experience Cloud site. Always create or clone an external profile before
configuring site membership.
```

**Detection hint:** If the profile being recommended has "Standard User," "System Administrator," or any internal role in its description, it is an internal profile and cannot be used for Experience Cloud site membership.

---

## Anti-Pattern 5: Ignoring License Seat Limits When Adding Bulk Users

**What the LLM generates:** A data loader or Apex script that bulk-creates external User records without first checking available license capacity, then recommending to "just run it and see if it errors."

**Why it happens:** LLMs focus on the mechanics of user creation (field mappings, SOQL, DML) and do not model the org-state dependency on available license seats. License exhaustion is a runtime constraint invisible to static code analysis.

**Correct pattern:**

```apex
// Before bulk creating external users, query available license capacity:
List<UserLicense> licenses = [
    SELECT Name, TotalLicenses, UsedLicenses
    FROM UserLicense
    WHERE Name IN ('Customer Community', 'Customer Community Plus', 'Partner Community')
];
for (UserLicense lic : licenses) {
    Integer available = lic.TotalLicenses - lic.UsedLicenses;
    if (available < plannedUserCount) {
        throw new LicenseLimitException(
            'Insufficient ' + lic.Name + ' seats: ' + available + ' available, '
            + plannedUserCount + ' required.'
        );
    }
}
// Proceed with bulk user creation only after confirming capacity.
```

**Detection hint:** Any bulk user creation script that omits a capacity pre-check or does not reference the `UserLicense` sObject is incomplete. Always validate available seats before attempting bulk provisioning.

---

## Anti-Pattern 6: Treating Login Page Changes as Instantly Live

**What the LLM generates:** Instructions to edit the login page in Experience Builder and immediately tell users to test, without mentioning the Publish step.

**Why it happens:** For authenticated community pages, some property changes (like text on a component) can be previewed without publishing. LLMs generalise this to the login page, which has different publish semantics.

**Correct pattern:**

```
After making structural changes to the login or registration page in
Experience Builder (adding/removing components, changing page layout):
1. Click Publish in the top-right of Experience Builder.
2. Wait for the publish to complete.
3. Clear browser cache (or use incognito) before testing.
Changes are NOT live to external users until the site is published.
```

**Detection hint:** Any login-page editing guide that ends without an explicit Publish step is incomplete. Flag and add the publish instruction.
