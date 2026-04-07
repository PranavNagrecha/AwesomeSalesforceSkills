# Examples — Experience Cloud Authentication

## Example 1: OIDC Social Login with Google

**Context:** A customer portal built on Experience Cloud (LWR) needs to let external users sign in with their Google accounts. New users should be auto-provisioned as community members; returning users should be matched by their Google subject ID stored as `FederationIdentifier`.

**Problem:** Without a Registration Handler, Salesforce cannot map the Google identity to a Salesforce user and throws a generic "We can't log you in" error.

**Solution:**

1. In Setup, create an Auth Provider of type "Google". Supply the OAuth client ID and secret from Google Cloud Console. Salesforce generates the Callback URL — register it in Google Cloud under Authorized redirect URIs.

2. Implement the Registration Handler:

```apex
global class GoogleSocialLoginHandler implements Auth.RegistrationHandler {

    global User createUser(Id portalId, Auth.UserData data) {
        // Try to match an existing user by Federation ID (Google subject)
        List<User> existing = [
            SELECT Id FROM User
            WHERE FederationIdentifier = :data.identifier
            AND IsActive = true
            LIMIT 1
        ];
        if (!existing.isEmpty()) {
            return existing[0];
        }

        // Provision a new external community user
        User u = new User();
        u.Username = data.email + '.community@example.com';
        u.Email = data.email;
        u.FirstName = data.firstName;
        u.LastName = (String.isBlank(data.lastName) ? 'User' : data.lastName);
        u.FederationIdentifier = data.identifier;
        u.Alias = data.email.left(8);
        u.TimeZoneSidKey = 'America/Los_Angeles';
        u.LocaleSidKey = 'en_US';
        u.EmailEncodingKey = 'UTF-8';
        u.LanguageLocaleKey = 'en_US';
        u.ProfileId = [SELECT Id FROM Profile WHERE Name = 'Customer Community Login User' LIMIT 1].Id;
        return u;
    }

    global void updateUser(Id userId, Id portalId, Auth.UserData data) {
        User u = new User(Id = userId);
        u.Email = data.email;
        update u;
    }
}
```

3. Assign this class as the Registration Handler on the Auth Provider record.

4. In the LWR site's Administration > Login & Registration, add the Google auth provider to the social login options. For a custom LWC login page, redirect to the Start SSO URL:

```javascript
// In your custom login LWC
handleGoogleLogin() {
    // The community parameter routes the callback back to this site
    const startUrl = '/services/auth/sso/GoogleProvider?community=https%3A%2F%2Fmysite.my.site.com%2Fportal';
    window.location.href = startUrl;
}
```

**Why it works:** `FederationIdentifier` stores the IdP's immutable subject identifier. Matching on it is more reliable than email, which users can change in their Google account. The `community` parameter in the Start SSO URL ensures Salesforce routes the post-authentication redirect back to the Experience Cloud site rather than the internal org.

---

## Example 2: Headless Passwordless OTP Login for Mobile App

**Context:** A branded iOS/Android app uses Experience Cloud as the identity backend. Users register and log in with just their email — no password. The app controls the entire UI; no Salesforce-hosted page is shown.

**Problem:** Standard passwordless login requires a Salesforce-hosted login page. The headless API surface must be used for apps that render their own UI.

**Solution:**

1. Enable Headless Identity in Setup > Digital Experiences > Settings.

2. Implement `HeadlessUserDiscoveryHandler` to resolve the user by email:

```apex
global class MobileUserDiscoveryHandler implements Auth.HeadlessUserDiscoveryHandler {

    global Auth.UserDiscoveryResult discover(
        String identifier,
        Map<String, String> requestAttributes
    ) {
        List<User> users = [
            SELECT Id, Email FROM User
            WHERE Email = :identifier
            AND IsActive = true
            LIMIT 1
        ];

        Auth.UserDiscoveryResult result = new Auth.UserDiscoveryResult();
        if (!users.isEmpty()) {
            result.userId = users[0].Id;
            result.action = Auth.UserDiscoveryAction.CHALLENGE;
        } else {
            result.action = Auth.UserDiscoveryAction.REGISTER;
        }
        return result;
    }
}
```

3. Implement `HeadlessSelfRegistrationHandler` to register new users discovered during the flow:

```apex
global class MobileSelfRegistrationHandler implements Auth.HeadlessSelfRegistrationHandler {

    global User createUser(
        Map<String, String> userAttributes,
        Map<String, String> requestAttributes,
        Id networkId
    ) {
        String email = userAttributes.get('email');
        User u = new User();
        u.Username = email + '.mobile';
        u.Email = email;
        u.LastName = userAttributes.containsKey('lastName') ? userAttributes.get('lastName') : 'Member';
        u.FirstName = userAttributes.containsKey('firstName') ? userAttributes.get('firstName') : '';
        u.Alias = email.left(8);
        u.TimeZoneSidKey = 'America/Los_Angeles';
        u.LocaleSidKey = 'en_US';
        u.EmailEncodingKey = 'UTF-8';
        u.LanguageLocaleKey = 'en_US';
        u.ProfileId = [SELECT Id FROM Profile WHERE Name = 'Customer Community Login User' LIMIT 1].Id;
        return u;
    }

    global Boolean autoConfirm() {
        // Return true to skip email confirmation during headless registration
        return true;
    }
}
```

4. Assign both handlers in the Experience Cloud site's Headless Identity settings.

5. From the mobile app, initiate the passwordless OTP flow:

```
POST https://mysite.my.site.com/services/auth/headless/init/passwordless/login
Content-Type: application/json

{
  "username": "user@example.com",
  "verificationmethod": "email"
}
```

Salesforce sends a one-time code to the user's email. The app collects the code and verifies it:

```
POST https://mysite.my.site.com/services/auth/headless/verify/passwordless/login
Content-Type: application/json

{
  "username": "user@example.com",
  "otp": "847291",
  "identifier": "<identifier_from_init_response>"
}
```

On success, the API returns an access token for the session.

**Why it works:** The `HeadlessUserDiscoveryHandler` routes the flow between challenge (existing user) and registration (new user) without exposing Salesforce UI. The `autoConfirm()` method on the self-registration handler prevents a blocking email confirmation step that would break the seamless mobile UX.

---

## Anti-Pattern: Reusing a Standard Registration Handler for Headless Flows

**What practitioners do:** They already have a working `Auth.RegistrationHandler` for a social login flow and try to assign the same class in the Headless Identity settings for passwordless login.

**What goes wrong:** The Headless Identity settings require a class implementing `Auth.HeadlessSelfRegistrationHandler`. Assigning an `Auth.RegistrationHandler` implementation causes a runtime error when the headless flow attempts to call `createUser()` — the method signatures are different and Salesforce cannot dispatch to the wrong interface type.

**Correct approach:** Implement `Auth.HeadlessSelfRegistrationHandler` as a separate class for headless flows. The two handler types serve distinct flow paths and cannot be mixed.
