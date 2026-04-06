# Session Management And Timeout — Work Template

Use this template when working on tasks in this area.

## Scope

**Skill:** `session-management-and-timeout`

**Request summary:** (fill in what the user asked for)

## Context Gathered

Record the answers to the Before Starting questions from SKILL.md here.

- Current org-wide timeout value:
- Profile-level overrides in place (list profiles and values):
- Connected Apps with session timeout policies (list apps and values):
- Concurrent session limit (current value or "unlimited"):
- Session IP locking enabled (yes/no):
- Compliance mandate driving the change (PCI-DSS, HIPAA, SOC 2, etc.):

## Effective Timeout Analysis

Calculate the effective timeout per user persona using the minimum-wins rule.

| User Persona / Profile | Org-Wide Timeout | Profile Override | Connected App Timeout | Effective Timeout |
|---|---|---|---|---|
| (profile name) | (value) | (value or N/A) | (value or N/A) | MIN(all applicable) |
| (profile name) | (value) | (value or N/A) | (value or N/A) | MIN(all applicable) |

## Concurrent Session Assessment

| User Population | Typical Session Types | Recommended Limit | Rationale |
|---|---|---|---|
| Interactive users | Browser + Mobile | (value) | (reason) |
| Developers | Browser + CLI + Mobile | (value) | (reason) |
| Integration users | API only | (value or unlimited) | (reason) |

## SecuritySettings Metadata Snippet

```xml
<SecuritySettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <sessionSettings>
        <sessionTimeout><!-- TwoHours | FourHours | etc. --></sessionTimeout>
        <lockSessionsToIp><!-- true | false --></lockSessionsToIp>
        <forceLogoutOnSessionTimeout><!-- true | false --></forceLogoutOnSessionTimeout>
    </sessionSettings>
</SecuritySettings>
```

## Approach

Which pattern from SKILL.md applies and why:

- [ ] Tiered Timeout by User Role — (explain if applicable)
- [ ] Connected App Session Isolation — (explain if applicable)
- [ ] Other — (describe)

## Review Checklist

Copy from SKILL.md and tick items as you complete them.

- [ ] Org-wide timeout value is set and documented
- [ ] Profile-level overrides are applied only where necessary, with effective timeout calculated per profile
- [ ] Connected App session policies are configured and documented for OAuth integrations
- [ ] Concurrent session limit is set to an appropriate value (or intentionally left unlimited with justification)
- [ ] Session IP locking decision is documented with rationale
- [ ] Metadata API SecuritySettings snippet is committed to version control for repeatable deployment
- [ ] Affected users are notified of timeout changes

## Notes

Record any deviations from the standard pattern and why.
