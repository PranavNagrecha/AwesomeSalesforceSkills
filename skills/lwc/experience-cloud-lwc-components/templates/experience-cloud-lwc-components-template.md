# Experience Cloud LWC Component — Work Template

Use this template when building or reviewing a custom LWC component for an Experience Cloud site.

## Scope

**Skill:** `experience-cloud-lwc-components`

**Request summary:** (fill in what the user asked for — e.g., "Build a guest-accessible product search component for an LWR portal" or "Review an existing component for guest security issues")

---

## Context Gathered

Answer each question before writing any code.

- **Site runtime:** [ ] LWR  [ ] Aura-based community
- **User access model:** [ ] Guest (unauthenticated) only  [ ] Authenticated portal users only  [ ] Both
- **Portal user license (if applicable):** [ ] Customer Community  [ ] Customer Community Plus  [ ] Partner Community  [ ] Other: ___
- **Apex required:** [ ] Yes — class name(s): ___  [ ] No, wire adapter only  [ ] No Apex
- **Navigation required:** [ ] Yes — target pages: ___  [ ] No
- **Admin-configurable properties needed:** [ ] Yes — properties: ___  [ ] No

---

## Component Development Checklist

### JS-meta.xml Configuration

- [ ] `<isExposed>true</isExposed>` is set
- [ ] `<target>lightningCommunity__Default</target>` declared (for Experience Builder palette)
- [ ] `<target>lightningCommunity__Page</target>` declared if component is a full-page component
- [ ] No internal Lightning targets (`lightning__AppPage`, `lightning__RecordPage`) if community context modules are imported
- [ ] `<targetConfig>` entries created for each admin-configurable `@api` property
- [ ] Design attribute labels are human-readable (for Experience Builder admin use)

### Community Context Imports

- [ ] `@salesforce/community/Id` imported only if community scoping is required in Apex calls
- [ ] `@salesforce/community/basePath` imported; used for all site-internal URL construction
- [ ] `@salesforce/user/isGuest` imported if guest vs. authenticated UI branching is needed
- [ ] No community context imports in components that also target internal Lightning pages

### Guest User Security

Only complete this section if the component is accessible to unauthenticated (guest) users.

- [ ] All called Apex classes use `with sharing`
- [ ] SOQL/SOSL queries include `WITH USER_MODE` where CRUD/FLS enforcement is required
- [ ] After deployment: Guest User Profile > Apex Class Access > all called classes are added
- [ ] Component tested in Experience Builder preview as guest user (not logged in)
- [ ] No sensitive fields or records returned to guest context

### Authenticated Portal User Security

- [ ] All called Apex classes use `with sharing`
- [ ] After deployment: Portal User Profile (or Permission Set) > Apex Class Access > all called classes are added
- [ ] Component tested as an authenticated portal user with the correct profile/license

### Navigation

- [ ] `NavigationMixin` imported from `lightning/navigation` (not Aura event channels)
- [ ] Page reference types verified against site runtime (LWR vs Aura)
- [ ] No hard-coded site path prefixes in URL construction — `basePath` used instead
- [ ] Navigation tested end-to-end in the target runtime

### Code Quality

- [ ] `@AuraEnabled(cacheable=true)` used on read-only Apex methods
- [ ] No `@AuraEnabled` methods without explicit sharing keyword on the containing class
- [ ] `@api` properties are used for all admin-configurable component values
- [ ] Component does not hard-code org-specific IDs, usernames, or paths

---

## Approach

Which pattern from SKILL.md applies?

- [ ] Guest-Accessible Component (product catalog, knowledge base, public form)
- [ ] Authenticated Portal User Component (dashboard, profile, case management)
- [ ] Mixed Guest + Authenticated Component (uses `isGuest` branching)

Why this pattern: (fill in reasoning)

---

## Deployment Steps

1. Deploy component bundle (JS, HTML, CSS, JS-meta.xml) and Apex class(es).
2. For guest access: Setup > Experience Cloud Sites > [Site] > Workspaces > Administration > Guest User Profile > Apex Class Access — add all called Apex classes.
3. For portal user access: Setup > Profiles > [Portal Profile] > Apex Class Access — add all called Apex classes (or grant via Permission Set and assign to portal users).
4. In Experience Builder, verify the component appears in the component palette.
5. Add component to a test page. Confirm configuration properties appear in the property panel.
6. Preview as guest user. Confirm data loads, no 403 errors.
7. Preview as authenticated portal user. Confirm data loads, navigation works.
8. Publish the site page.

---

## Notes

Record any deviations from the standard pattern and why.

- Deviation 1:
- Deviation 2:
