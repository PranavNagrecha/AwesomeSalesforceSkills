# Gotchas — Guest User Security Audit

Real-world surprises in Experience Cloud guest-user security.

---

## Gotcha 1: Each Experience Cloud site has its own Guest User

**What happens.** Auditor reviews "the Guest User" profile and
declares the org safe. Other sites have their own Guest Users with
different permissions.

**When it occurs.** Multi-site orgs.

**How to avoid.** Enumerate all sites first (Setup -> All Sites)
and audit each Guest User profile separately. They are clones, not
shared.

---

## Gotcha 2: Spring '21 secure-by-default does not retroactively migrate orgs

**What happens.** Org existed pre-Spring '21. Admin assumes "secure
by default" applies. In reality, grandfathered permissions are
still active until explicitly removed.

**When it occurs.** Older orgs that never executed a guest-user
hardening project.

**How to avoid.** Treat the audit as if the secure-by-default
release never happened. Verify each setting explicitly.

---

## Gotcha 3: `without sharing` is not the default sharing mode

**What happens.** Apex class with `@AuraEnabled` methods has no
sharing declaration. Default is `inherited sharing`, which inherits
the calling context's sharing — for an Aura / LWC call from the
guest user, that becomes a complex chain. Many devs assume
`with sharing` is the default. It is not.

**When it occurs.** Quick prototypes that never had a sharing
declaration added.

**How to avoid.** Make sharing declarations explicit and required
in code review. Default to `with sharing` for any guest-reachable
class.

---

## Gotcha 4: `WITH SECURITY_ENFORCED` does not protect against sharing bypass

**What happens.** Apex uses `WITH SECURITY_ENFORCED`; the dev
believes this addresses guest exposure. It does not — that clause
enforces field-level security and CRUD, but a `without sharing`
class still bypasses record-level sharing.

**When it occurs.** Misunderstanding of what `WITH SECURITY_ENFORCED`
covers.

**How to avoid.** Combine `with sharing` for record-level + `WITH
SECURITY_ENFORCED` (or `Security.stripInaccessible`) for FLS / CRUD.

---

## Gotcha 5: Sharing rules with `Type = 'Guest user'` are limited but not blocked entirely

**What happens.** Modern orgs restrict the kinds of sharing rules
you can create for guest. Some grants are blocked outright; others
produce a warning but save anyway.

**When it occurs.** Admins clicking past warnings.

**How to avoid.** Audit existing rules in addition to enforcing
review on new rules. The platform's warnings are not a substitute
for a security review.

---

## Gotcha 6: Public sites can call standard Salesforce APIs by default

**What happens.** A guest user can hit `/services/data/...` REST
endpoints to query objects the guest profile has Read on. This is
distinct from the site's custom Apex REST endpoints.

**When it occurs.** Sites where the "Restrict guest user from
accessing standard Salesforce APIs" toggle has not been enabled.

**How to avoid.** Set the restriction on every site (Setup ->
Sites -> Public Access Settings) unless a documented use case
needs it.

---

## Gotcha 7: Guest user record ownership produces unexpected access

**What happens.** Records owned by the guest user inherit some
implicit access patterns (the guest can see records they own).
Sometimes legacy code created records owned by guest as a
convenience.

**When it occurs.** Custom Apex that creates records and assigns
`OwnerId = guestUserId`.

**How to avoid.** Audit `OwnerId` distribution; flag any custom
object with rows owned by the guest. Reassign to a service user.

---

## Gotcha 8: LWC `cacheable=true` does not bypass sharing

**What happens.** `@AuraEnabled(cacheable=true)` declarations are
sometimes assumed to be safer because they are read-only. They are
not — sharing semantics still apply via the class declaration.

**When it occurs.** Code review confusion between "cacheable" and
"safe".

**How to avoid.** Treat `cacheable` as a performance hint, not a
security control. The `with sharing` declaration is the security
control.

---

## Gotcha 9: Site activation toggles reset some defaults

**What happens.** Site goes from inactive -> active -> inactive ->
active. Some configuration resets; admins assume their settings
persist.

**When it occurs.** Sites that bounce through deployment cycles.

**How to avoid.** Re-audit guest-user configuration after any
significant site change (activation, member profile changes,
template change).
