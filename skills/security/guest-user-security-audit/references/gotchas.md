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
shared. Guest users reach a site "via the Guest User license associated
with each site" (obj 264 L299563-299564), and each retrieved `CustomSite`
names its own profile in the read-only `guestProfile` field (api_meta 264
L49340-49341).

---

## Gotcha 2: Secure guest record access is retroactive; old profile grants are not

**What happens.** Org existed pre-Spring '21. Admin assumes "secure
by default" applies. Record access does: `enableSecureGuestAccess` is
always true as of API 50.0 and the change "applies retroactively back to
API version 47.0" (api_meta 264 L130645-130648), so guest org-wide
defaults are Private everywhere. Profile permissions an admin granted
earlier stay until removed (UNVERIFIED (2026-10-20): not in the corpus).

**When it occurs.** Older orgs that never executed a guest-user
hardening project.

**How to avoid.** Treat the audit as if the secure-by-default
release never happened. Verify each setting explicitly.

---

## Gotcha 3: An omitted sharing declaration is not `inherited sharing` — and what it means flipped at API 67.0

**What happens.** A guest-reachable class carries no sharing
keyword and the reviewer scores it as `inherited sharing`. It is
not — that is a keyword you write, and an omitted declaration is a
separate rule that Summer '26 changed. The Apex Developer Guide
states "Apex without an explicit sharing declaration runs as with
sharing by default" (apexdev 264 L4894) and gates it: "In API version
67.0 and later" (L4994). At API 66.0 and earlier the mode is
resolved from the class instead, by these factors (L4995-5001): `with sharing` if
any class in its inheritance chain is saved at 67.0 or later, or if
it is an Aura controller or an `@AuraEnabled` method called from a
Lightning web component; the calling class's mode if it isn't an
Apex entry point; "Otherwise, the class runs in `without sharing`
mode."

**When it occurs.** Legacy guest-reachable classes that never had a
declaration added. The gate is the `apiVersion` in the class's
`.cls-meta.xml`, not the org's release — a Summer '26 org still runs
a class pinned to 58.0 under the old rules.

**How to avoid.** Read the `.cls-meta.xml` before scoring. The P0 is
a standalone bare `@RestResource` class pinned to ≤ 66.0: no Aura or
LWC entry point and no 67.0+ ancestor, so it lands on the
"otherwise" branch and runs `without sharing` — a full sharing
bypass on a public endpoint. Bare `@AuraEnabled`-from-LWC classes
are the mild case (`with sharing` at every version). Either way,
declare it: Salesforce's guidance is to "always include an explicit
sharing declaration" (apexdev 264 L4897).

**One caveat no version changes.** "Apex triggers can't have an
explicit sharing declaration" and they always run in a
`without sharing` context (apexdev 264 L4905). Database operations inside a trigger body
default to user mode — which reapplies the running user's sharing
and so overrides that context (L4907-4909) — only at `apiVersion` 67.0+; at
≤ 66.0 they default to system mode and the bypass stands (apexdev 264 L45133-45135; L11928-11929). That
adjacent flip is tabled in
[`AGENT_CONTRACT.md`](../../../../agents/_shared/AGENT_CONTRACT.md#apex-security-idiom-by-api-version)
§ *Apex security idiom by API version*, which covers access mode,
not the class declaration rule above.

---

## Gotcha 4: `WITH SECURITY_ENFORCED` does not protect against sharing bypass

**What happens.** Legacy Apex uses `WITH SECURITY_ENFORCED`; the dev
believes this addresses guest exposure. It does not — that clause
enforces field-level security and CRUD, but a `without sharing`
class still bypasses record-level sharing.

**When it occurs.** Misunderstanding of what `WITH SECURITY_ENFORCED`
covers. Expect to find it in older guest-reachable classes: the gate
is the `apiVersion` in the class's `.cls-meta.xml`, not the org's
release, so a Summer '26 org runs a class pinned to 58.0 with the
clause intact.

**How to avoid.** Declare the class `with sharing` — it is what
covers the queries and DML in it that carry no clause — and write
`WITH USER_MODE` (GA at API 57.0 — UNVERIFIED (2026-10-20): the GA
version is release-notes only), which enforces FLS, object
permissions, and the running user's sharing rules on the query it
sits on (user mode applies "the sharing rules, field-level security
(FLS), and object permissions of the running user", apexdev 264
L12116-12117), or
`Security.stripInaccessible(AccessType.READABLE, records)` — operate
on the returned `SObjectAccessDecision`'s `.getRecords()` — where a
result must be trimmed rather than throw. The audit **flags** every
`WITH SECURITY_ENFORCED` it finds rather than scoring the query
clean: on a class at `apiVersion` 67.0+ it is a P0 — "In API version
67.0 and later, you can't use the WITH SECURITY_ENFORCED clause"
(apexdev 264 L11926; the exact compiler message is UNVERIFIED
(2026-10-20)); at 57.0–66.0 it is P2 tech debt with a named migration to
`WITH USER_MODE`; at ≤ 56.0 it is the idiom available, and the fix is
to raise the class's `apiVersion`.

---

## Gotcha 5: Guest user sharing rules are Read Only but open every matching record to anyone

**What happens.** A guest user sharing rule is the "only way to grant
record access" to guests and "can only grant Read Only access"
(secguide 262 L2986-2987). Saving one is allowed; the guide's warning
is that it gives "immediate and unlimited access to all records
matching the sharing rule's criteria to anyone" (L3068-3069).

**When it occurs.** Admins clicking past warnings.

**How to avoid.** Audit existing rules in addition to enforcing
review on new rules. The platform's warnings are not a substitute
for a security review.

---

## Gotcha 6: Public sites can call standard Salesforce APIs when the guest profile allows it

**What happens.** A guest user can hit `/services/data/...` REST
endpoints to query objects the guest profile has Read on. This is
distinct from the site's custom Apex REST endpoints. UNVERIFIED
(2026-10-20): the behaviour is not described in the corpus.

**When it occurs.** Guest profiles with API Enabled checked.

**How to avoid.** Uncheck API Enabled on every guest profile — the
guide's checklist: "Confirm that Object access, and the API Enabled
and Access Activities checkboxes are unchecked" (secguide 262 L9629)
— unless a documented use case needs it. A per-site "Restrict guest
user from accessing standard Salesforce APIs" toggle is UNVERIFIED
(2026-10-20): no such setting is named in the corpus.

---

## Gotcha 7: Guest user record ownership produces unexpected access

**What happens.** Records owned by the guest user inherit some
implicit access patterns (the guest can see records they own).
Sometimes legacy code created records owned by guest as a
convenience.

**When it occurs.** Custom Apex that creates records and assigns
`OwnerId = guestUserId`.

**How to avoid.** Audit `OwnerId` distribution; flag any custom
object with rows owned by the guest. Reassign to an internal user —
the guide: "Ensure that ownership of all existing records is
transferred to an internal user" (secguide 262 L9632). New guest
records go to the user named in `CustomSite.siteGuestRecordDefaultOwner`
(api_meta 264 L49432-49433). UNVERIFIED (2026-10-20): the "implicit
access to own records" pattern in What happens.

---

## Gotcha 8: LWC `cacheable=true` does not bypass sharing

**What happens.** `@AuraEnabled(cacheable=true)` declarations are
sometimes assumed to be safer because they are read-only. They are
not — sharing semantics still apply via the class declaration;
`cacheable=true` only caches results of methods that "retrieve data
but don't modify it" (apexdev 264 L5096).

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
template change). UNVERIFIED (2026-10-20): which settings reset on
activation is not in the corpus.
