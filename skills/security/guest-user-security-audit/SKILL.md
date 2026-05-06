---
name: guest-user-security-audit
description: "Auditing the security posture of an Experience Cloud (Community) site's Guest User. Covers the post-Spring '21 secure-by-default lockdown (object permissions removed, sharing rule grants required for any access), the Guest User profile permissions to remove (View All Data, Modify All Data, Manage Users, etc.), guest sharing rules, the Run-As-Guest test, OWASP A01 (Broken Access Control) mapping, and the standard set of leakage vectors (Apex with `without sharing`, Aura / LWC `@AuraEnabled` methods, public-site Visualforce, REST endpoints under `/services/apexrest`). NOT for Experience Cloud authenticated user setup (see experience/experience-cloud-user-management), NOT for general Salesforce profile design (see admin/profile-permset-design)."
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
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-05-05
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

This skill is the audit playbook. It walks the standard surfaces
where guest data leakage happens and the OWASP Top 10 mapping for
each.

## What changed in Spring '21

| Before Spring '21 | After Spring '21 (secure by default) |
|---|---|
| Guest profile could grant View All Data | Removed; cannot be granted |
| Guest profile could grant Modify All Data | Removed |
| Guest profile could grant Manage Users | Removed |
| Object permissions on by default | Off by default |
| Implicit access via OWD | Sharing rule required |
| Guest could update other users' records | Blocked unless explicit sharing rule + record ownership rules |

Orgs that existed before Spring '21 do not auto-migrate. They
inherit grandfathered permissions until an admin removes them. The
audit's first job is identifying grandfathered permissions still
active.

## The leakage surfaces

Even with secure-by-default, leakage can still happen through:

1. **Guest profile permissions still granted** by an admin since
   Spring '21 (the platform allows some grants, just with warnings).
2. **Apex with `without sharing`** runs as the guest user but
   bypasses sharing — guest can read records they shouldn't.
3. **`@AuraEnabled` Apex methods exposed to LWC / Aura** — the
   guest user's session can call them; they execute with the
   sharing mode of the class (`with sharing` / `without sharing` /
   default `inherited sharing`).
4. **REST endpoints under `/services/apexrest`** — Apex REST
   classes exposed publicly inherit the same sharing rules; default
   `without sharing` is dangerous.
5. **Public Visualforce / Sites pages** — older feature; still in
   use; same sharing concerns as Apex.
6. **Sharing rules granting access to records owned by guest** —
   the platform restricts these in modern orgs but legacy
   configurations may still exist.

## Standard audit surfaces

| Surface | Question to ask | Tool |
|---|---|---|
| Guest profile permissions | What object / system permissions are still granted? | Setup -> Profiles -> Guest User -> Object / System Permissions |
| Sharing rules granting to guest | Which records are shared to the guest user? | Setup -> Sharing Settings; Object's Sharing Rules; filter Type = 'Guest user' |
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
2. **Audit each Guest profile's permissions.** Object permissions, system permissions, FLS. Modern target: zero object permissions unless explicit need; zero `View All` / `Modify All` (these should already be blocked by secure-by-default but legacy grants need removal).
3. **Audit sharing rules with Type = 'Guest user'.** Each rule should map to a documented business justification. Anything granting "all records" of a sensitive object is a finding.
4. **Static-analyze Apex.** Find classes with `without sharing`. Cross-check whether they are reachable by guest (called from `@AuraEnabled` method or `@RestResource` exposed to public site).
5. **Run-As-Guest the site.** Setup -> Users -> Guest User -> Login. Walk every component on every page; capture network requests. Anything returning data that shouldn't be public is a finding.
6. **Validate REST and Aura/LWC endpoints separately.** Use a tool / manual probe to call `@AuraEnabled` and Apex REST endpoints with no auth and see what returns.
7. **Prioritize remediation.** Findings that expose PII or regulated data go first. Findings that expose internal configuration go second. Map each to OWASP A01 / A03 / A05 in the report.

## What This Skill Does Not Cover

| Topic | See instead |
|---|---|
| Authenticated Experience Cloud user mgmt | `experience/experience-cloud-user-management` |
| General profile / permset design | `admin/profile-permset-design` |
| Apex security at large (CRUD / FLS) | `apex/apex-with-sharing-patterns` |
| Encrypted fields and Shield Platform Encryption | `security/shield-platform-encryption` |
