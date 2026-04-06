# Examples — IP Range and Login Flow Strategy

## Example 1: Apex Invocable for IP Detection in a Login Flow

**Context:** A Login Flow needs to branch based on whether the user is logging in from a corporate IP range. The flow requires the user's source IP address, which is not directly available as a flow system variable.

**Problem:** Without a reliable IP detection method, the flow cannot make IP-based decisions. Formula-only approaches are unreliable in the login context.

**Solution:**

```apex
public class LoginFlowIpDetector {

    @InvocableMethod(
        label='Get Login Source IP'
        description='Returns the source IP of the current login session for use in Login Flows'
    )
    public static List<String> getSourceIp(List<String> unused) {
        // Auth.SessionManagement provides login-context session attributes
        Map<String, String> session = Auth.SessionManagement.getCurrentSession();
        String sourceIp = session.get('SourceIp');

        // Fallback: check request headers (works in Visualforce login contexts)
        if (String.isBlank(sourceIp)) {
            sourceIp = ApexPages.currentPage()?.getHeaders()?.get('True-Client-IP');
        }
        if (String.isBlank(sourceIp)) {
            sourceIp = ApexPages.currentPage()?.getHeaders()?.get('X-Forwarded-For');
        }

        return new List<String>{ sourceIp != null ? sourceIp : 'UNKNOWN' };
    }
}
```

**Why it works:** `Auth.SessionManagement.getCurrentSession()` is available in the login context and returns the authenticated session's source IP. The fallback headers handle edge cases where the session map does not contain the IP (e.g., certain Visualforce login page contexts). Returning `'UNKNOWN'` instead of null prevents downstream null-pointer faults in the flow's Decision element.

---

## Example 2: Custom Metadata for Corporate IP Range Lookup

**Context:** The Login Flow needs to compare the user's IP against a list of corporate IP ranges. Hardcoding ranges in flow formulas is brittle and requires a flow version change for every IP update.

**Problem:** IP ranges change when offices move, VPN providers change exit nodes, or new locations are added. Hardcoded ranges create maintenance debt and deployment risk.

**Solution:**

Custom Metadata Type: `Corporate_IP_Range__mdt`

| Field | Type | Purpose |
|---|---|---|
| `Label` | Text | Human-readable name (e.g., "NYC Office") |
| `Start_IP__c` | Text(45) | Start of the IP range (e.g., "203.0.113.10") |
| `End_IP__c` | Text(45) | End of the IP range (e.g., "203.0.113.254") |
| `Is_Active__c` | Checkbox | Toggle ranges on/off without deleting |
| `Location__c` | Text | Description of the location for audit purposes |

```apex
public class CorporateIpRangeChecker {

    @InvocableMethod(
        label='Check If IP Is Corporate'
        description='Returns true if the given IP falls within any active Corporate_IP_Range__mdt record'
    )
    public static List<Boolean> isCorporateIp(List<String> ipAddresses) {
        String ip = ipAddresses[0];
        Long ipLong = ipToLong(ip);

        if (ipLong == null) {
            return new List<Boolean>{ false };
        }

        List<Corporate_IP_Range__mdt> ranges = [
            SELECT Start_IP__c, End_IP__c
            FROM Corporate_IP_Range__mdt
            WHERE Is_Active__c = true
        ];

        for (Corporate_IP_Range__mdt range : ranges) {
            Long startLong = ipToLong(range.Start_IP__c);
            Long endLong = ipToLong(range.End_IP__c);
            if (startLong != null && endLong != null
                && ipLong >= startLong && ipLong <= endLong) {
                return new List<Boolean>{ true };
            }
        }

        return new List<Boolean>{ false };
    }

    private static Long ipToLong(String ip) {
        if (String.isBlank(ip)) return null;
        List<String> octets = ip.split('\\.');
        if (octets.size() != 4) return null;
        try {
            return (Long.valueOf(octets[0]) * 16777216)
                 + (Long.valueOf(octets[1]) * 65536)
                 + (Long.valueOf(octets[2]) * 256)
                 + Long.valueOf(octets[3]);
        } catch (Exception e) {
            return null;
        }
    }
}
```

**Why it works:** Custom Metadata records are deployable, versionable, and queryable in Apex without counting against SOQL limits in the same way as Custom Settings. The `Is_Active__c` flag allows toggling ranges during maintenance windows without deleting records. The `ipToLong` conversion enables numeric range comparison instead of string matching.

---

## Example 3: Login Flow with Terms-of-Service Gate for Experience Cloud

**Context:** An Experience Cloud site must require community users to accept updated terms of service. Users who have already accepted the current version should pass through without interruption.

**Problem:** Without a Login Flow, there is no declarative way to force terms acceptance during login. Building a custom Visualforce login page is expensive and hard to maintain.

**Solution:**

Flow design (Screen Flow):

1. **Get Records:** Query the current user's `Terms_Accepted_Version__c` (custom field on User).
2. **Decision:** Compare against the current terms version (stored in a Custom Metadata record `Terms_Config__mdt.Current_Version__c`).
   - If versions match: proceed to End (user enters org).
   - If versions differ or field is null: proceed to Terms Screen.
3. **Screen: Terms Acceptance** -- Display the terms text (from a Custom Metadata long text field or a static resource URL). Include a checkbox: "I accept these terms."
4. **Decision:** If checkbox is checked, proceed to Update. If unchecked, display a rejection screen and end the flow (user cannot enter org).
5. **Apex Action:** Update the user's `Terms_Accepted_Version__c` and `Terms_Accepted_Date__c` fields.
6. **End:** User proceeds to org.

```apex
public class UpdateTermsAcceptance {

    @InvocableMethod(label='Update Terms Acceptance' description='Sets terms version and date on User record')
    public static void updateTerms(List<TermsInput> inputs) {
        TermsInput input = inputs[0];
        User u = new User(
            Id = input.userId,
            Terms_Accepted_Version__c = input.termsVersion,
            Terms_Accepted_Date__c = Date.today()
        );
        // Must run without sharing — Login Flow User lacks standard update permission
        update u;
    }

    public class TermsInput {
        @InvocableVariable(required=true)
        public Id userId;

        @InvocableVariable(required=true)
        public String termsVersion;
    }
}
```

**Why it works:** The flow checks the user's acceptance status before displaying any screen, so returning users experience zero additional login latency. The Apex action runs in system context to bypass the Login Flow User's limited permissions. Storing the terms version in Custom Metadata makes version bumps deployable without a flow change.

---

## Anti-Pattern: Hardcoding IP Ranges in Flow Formulas

**What practitioners do:** Embed IP range logic directly in a flow formula resource, such as `IF(CONTAINS({!sourceIp}, "203.0.113"), true, false)`.

**What goes wrong:** String-based IP matching is unreliable (e.g., `203.0.113` also matches `203.0.1130` if no delimiter check exists). When IP ranges change, the flow must be versioned and redeployed. In orgs with multiple environments, formula-hardcoded IPs drift between sandboxes and production.

**Correct approach:** Store IP ranges in Custom Metadata (`Corporate_IP_Range__mdt`), perform numeric range comparison in an Apex Invocable, and let the flow consume a boolean result. This separates configuration from logic and makes IP changes deployable without touching the flow.
