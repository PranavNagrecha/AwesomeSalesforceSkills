---
name: guest-user-security-audit
description: "Audit Experience Cloud guest user access — object/field CRUD, sharing, login, and hardening. Triggers: guest user audit, Experience Cloud guest security, site guest profile. NOT for member/community user provisioning — use admin/experience-cloud-member-management. NOT for profile/permset architecture — use admin/permission-sets-vs-profiles."
category: security
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
triggers:
  - "guest user experience cloud security audit"
  - "spring 21 secure guest user release"
  - "guest user object permissions view all data"
  - "guest user sharing rules without sharing apex"
  - "auraenabled apex guest exposure leakage"
  - "owasp top 10 broken access control salesforce"
  - "run as guest test public site"
tags:
  - guest-user
  - experience-cloud
  - secure-by-default
  - owasp-a01
  - access-control
inputs:
  - "Experience Cloud site (or all sites) in scope"
  - "Whether the org has Apex / LWC custom code or REST endpoints exposed to guest"
  - "Risk tolerance (regulated data demands stricter posture)"
outputs:
  - "Guest User profile audit (which permissions are still on)"
  - "Apex / LWC / REST endpoint leakage audit"
  - "Sharing-rule audit for guest grants"
  - "Prioritized remediation list mapped to OWASP A01"
dependencies: []
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-10-20
---

# Guest User Security Audit

Experience Cloud sites can serve unauthenticated visitors via the
**Guest User**. Historically the Guest User was provisioned with
broad permissions on by default, leading to a class of public-data-
exposure incidents that hit the press through the late 2010s. The
**Spring '21 secure-by-default release** locked this down: object-
level permissions are off by default, Modify All / View All are
removed, sharing rules are required to grant any record access, and
the platform actively warns when a configuration would expose data.
Grounded: guest org-wide defaults are Private for all objects and "can't
be changed" (secguide 262 L2868-2869), and a guest user sharing rule is
"the only way to grant record access" and can "only grant Read Only
access" (secguide 262 L2986-2987). The `enableSecureGuestAccess` setting
is "always true" as of API version 50.0 (api_meta 264 L130643-130645).
UNVERIFIED (2026-10-20): the Spring '21 release name, object permissions
off by default, the View All / Modify All removal, and the warnings.

This skill is the audit playbook. It walks the standard surfaces
where guest data leakage happens and the OWASP Top 10 mapping for
each.

## Questions to Ask Before Configuring

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| How many Experience Cloud sites are active, and which guest profile backs each? | Gotcha 1: each site has its own guest user | A complete per-site audit list |
| Was any site created before secure guest access was enforced? | Gotcha 2: profile grants from that era may still be on | A legacy-grant sweep target |
| What `apiVersion` does each guest-reachable class pin, and does it declare sharing? | Gotcha 3: an omitted declaration is `without sharing` at ≤ 66.0 for a standalone class (apexdev 264 L4994-5000) | The P0 list of bare `@RestResource` classes |
| Which classes still use `WITH SECURITY_ENFORCED`? | Gotcha 4: it can't be used at API 67.0+ (apexdev 264 L11926) and never covered sharing | A migration list to `WITH USER_MODE` |
| Which guest user sharing rules exist, and what criteria do they use? | Gotcha 5: each rule opens every matching record to anyone (secguide 262 L3068-3069) | A justification per rule |
| Does the guest profile have API Enabled? | Gotcha 6: the guidance is to leave it unchecked (secguide 262 L9629) | The standard-API exposure decision |
| Which objects hold records owned by a guest user? | Gotcha 7: guest-created records should move to an internal owner (secguide 262 L9630-9631) | A reassignment plan |

A proper configuration makes every guest grant traceable to a site, a rule and a business reason; "just doing it" leaves legacy grants and bare classes nobody re-reads.

## What changed in Spring '21

| Before Spring '21 | After Spring '21 (secure by default) |
|---|---|
| Guest profile could grant View All Data | Removed; cannot be granted |
| Guest profile could grant Modify All Data | Removed |
| Guest profile could grant Manage Users | Removed |
| Object permissions on by default | Off by default |
| Implicit access via OWD | Sharing rule required (secguide 262 L2868-2869, L2986) |
| Guest could update other users' records | Blocked: guest user sharing rules "can only grant Read Only access" (secguide 262 L2987; `SharingGuestRule` accessLevel "can be set only to Read", api_meta 264 L132881) |

UNVERIFIED (2026-10-20): the Spring '21 release name in this heading and
the first four rows (View All Data, Modify All Data, Manage Users,
object-permission defaults) — not in the corpus.

Orgs that existed before Spring '21 keep any profile permissions an
admin granted until an admin removes them (UNVERIFIED (2026-10-20)).
Record access is not grandfathered: `enableSecureGuestAccess` "is always
true, even if it reads false", applied "retroactively back to API version
47.0" (api_meta 264 L130645-130652). The audit's first job is identifying
profile grants still active.

## The leakage surfaces

Even with secure-by-default, leakage can still happen through:

1. **Guest profile permissions still granted** by an admin since
   Spring '21 (the platform allows some grants, just with warnings —
   UNVERIFIED (2026-10-20): not in the corpus).
2. **Apex with `without sharing`** runs as the guest user but
   bypasses sharing — guest can read records they shouldn't.
3. **`@AuraEnabled` Apex methods exposed to LWC / Aura** — the
   guest user's session can call them; they execute with the
   sharing mode of the class. With no declaration, an Aura controller
   or an `@AuraEnabled` method called from an LWC runs `with sharing`
   at every API version (apexdev 264 L4994, L4998-4999) — never
   `inherited sharing`, which is a keyword you write.
4. **REST endpoints under `/services/apexrest`** — with no
   declaration, an Apex REST class runs `with sharing` at API 67.0+
   and `without sharing` at 66.0 and earlier (apexdev 264
   L18941-18942); `without sharing` written explicitly bypasses
   sharing at every version (L18932-18934).
5. **Public Visualforce / Sites pages** — older feature; still in
   use; same sharing concerns as Apex.
6. **Sharing rules granting access to records owned by guest** —
   these are not blocked: by default sharing rules include "records
   owned by authenticated users, guest users, and queues" (secguide 262
   L3247-3248; api_meta 264 L132901-132903). The guide's advice is to
   transfer guest-created records to an internal user (secguide 262
   L9630-9632).

## Standard audit surfaces

| Surface | Question to ask | Tool |
|---|---|---|
| Guest profile permissions | What object / system permissions are still granted? | Setup -> Profiles -> Guest User -> Object / System Permissions |
| Sharing rules granting to guest | Which records are shared to the guest user? | Setup -> Sharing Settings; Object's Sharing Rules; rule type "Guest user, based on criteria" (secguide 262 L3239) |
| Apex sharing mode | Which Apex classes are `without sharing`? | Static analysis / `ApexClass.Body` SOQL |
| @AuraEnabled methods | Which Apex methods are callable from LWC / Aura? | ApexClass with `@AuraEnabled` annotations |
| Apex REST endpoints | Which classes expose REST? | Apex with `@RestResource(urlMapping=...)` |
| Public site visibility | What pages / endpoints are reachable without login? | Setup -> Sites; Run-As-Guest test |

## OWASP Top 10 mapping

The dominant risk class is **A01: Broken Access Control**. Guest
user mis-grants are textbook A01. Secondary: A03 Injection (if
guest-callable Apex constructs SOQL/SOSL from input), A05 Security
Misconfiguration (default permissions left on), A07
Identification and Authentication Failures (insufficient guest
session controls).

## Recommended Workflow

1. **Enumerate Guest Users.** Each Experience Cloud site has its own Guest User. List them via Setup -> All Sites -> per-site -> Public Access Settings (which is the per-site Guest profile clone).
2. **Audit each Guest profile's permissions.** Object permissions, system permissions, FLS. Modern target: zero object permissions unless explicit need; zero `View All` / `Modify All` (these should already be blocked by secure-by-default but legacy grants need removal — UNVERIFIED (2026-10-20)); API Enabled unchecked (secguide 262 L9629).
3. **Audit guest user sharing rules ("Guest user, based on criteria").** Each rule should map to a documented business justification. Anything granting "all records" of a sensitive object is a finding.
4. **Static-analyze Apex.** Find classes with `without sharing`. Cross-check whether they are reachable by guest (called from `@AuraEnabled` method or `@RestResource` exposed to public site).
5. **Run-As-Guest the site.** Browse the site logged out (a guest user can't be logged in as from Setup — UNVERIFIED (2026-10-20): the Setup login path is not in the corpus). Walk every component on every page; capture network requests. Anything returning data that shouldn't be public is a finding.
6. **Validate REST and Aura/LWC endpoints separately.** Use a tool / manual probe to call `@AuraEnabled` and Apex REST endpoints with no auth and see what returns.
7. **Prioritize remediation.** Findings that expose PII or regulated data go first. Findings that expose internal configuration go second. Map each to OWASP A01 / A03 / A05 in the report.

## What This Skill Does Not Cover

| Topic | See instead |
|---|---|
| Authenticated Experience Cloud user mgmt | `admin/experience-cloud-member-management` |
| General profile / permset design | `admin/permission-sets-vs-profiles` |
| Apex security at large (CRUD / FLS) | `apex/apex-with-without-sharing-decision` |
| Encrypted fields and Shield Platform Encryption | `security/platform-encryption` |
