# Experience Cloud Member Management — Work Template

Use this template when working on member management tasks for an Experience Cloud site.

## Scope

**Skill:** `experience-cloud-member-management`

**Request summary:** (fill in what the user asked for)

## Context Gathered

Answer the Before Starting questions from SKILL.md before proceeding:

- **Site name / Network ID:**
- **Required external license type** (Customer Community / CC Plus / Partner Community / External Identity):
- **Membership method** (self-registration / manual / profile-based):
- **Default New User Account** (required for self-reg; must be a business Account, not a Person Account):
- **Default Profile** (must be tied to the external license above):
- **Custom handler needed?** (yes/no — if yes, implement `Auth.ConfigurableSelfRegHandler`):
- **Login page branding requirements:**
- **Current license seat availability** (check Setup > Company Information):

## Approach

Which pattern from SKILL.md applies?

- [ ] Customer Portal Self-Registration (declarative or custom Apex handler)
- [ ] Partner User Onboarding via Manual Addition
- [ ] Profile-based membership (bulk / existing external profile)
- [ ] Login page branding only

Explain why this pattern was chosen:

## Checklist

Work through these items in order:

- [ ] External profile identified and confirmed tied to the correct license type
- [ ] License seat count confirmed — sufficient available seats
- [ ] Site membership method configured (Members list updated if profile-based)
- [ ] Self-registration: Default New User Account set (business Account, not Person Account)
- [ ] Self-registration: Default Profile set
- [ ] Self-registration: Handler class confirmed (declarative OR `Auth.ConfigurableSelfRegHandler` Apex — not legacy `Auth.RegistrationHandler`)
- [ ] Login/registration page branding applied in Experience Builder
- [ ] Site published after any structural change to the login page
- [ ] End-to-end test completed in a guest/incognito browser session
- [ ] No internal profiles used in place of external profiles

## Custom Handler Details (if applicable)

**Class name:**

**Interface implemented:** `Auth.ConfigurableSelfRegHandler` (confirm — not `Auth.RegistrationHandler`)

**Custom logic summary** (e.g., domain allow-list, dynamic account assignment):

**Test class name:**

**Coverage %:**

## Notes

Record any deviations from the standard pattern and why:
