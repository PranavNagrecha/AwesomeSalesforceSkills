# Well-Architected Notes — Guest User Security Audit

## Relevant Pillars

- **Security** — The dominant concern. Guest user mis-grants are
  textbook OWASP A01 Broken Access Control. The audit's purpose
  is to make A01 / A03 / A05 risks explicit and prioritized.
- **Reliability** — Public-site exposure is also reliability:
  incidents shut down the site or trigger emergency lockdown. A
  hardened guest config is part of reliability.
- **Operational Excellence** — The audit is recurring. Each new
  Experience Cloud site, each Apex deploy that touches `with
  sharing` declarations, each sharing rule change, can introduce
  new exposure. Build a periodic re-audit cadence.

## Architectural Tradeoffs

- **Guest profile permissions vs sharing rules.** Modern best
  practice: profile grants minimal CRUD on objects needed by public
  components; sharing rules grant access to specific records. Avoid
  blanket profile grants.
- **`with sharing` vs `without sharing` Apex.** Default to `with
  sharing` everywhere; reach for `without sharing` only when there
  is a documented system-context reason and the class is unreachable
  from guest.
- **Public site standard-API access on vs off.** Off is the safer
  default. Turn on only when a documented use case requires it.
- **JIT-style ad-hoc grants vs documented sharing baseline.** Each
  ad-hoc "let's just give the guest profile Read on this object for
  the demo" decision needs to be reverted post-demo or documented.

## Anti-Patterns

1. **`without sharing` on guest-reachable Apex.**
2. **Sharing rule granting "All" records to Type = Guest.**
3. **`@RestResource` exposed publicly without `with sharing`.**
4. **`WITH SECURITY_ENFORCED` used as the sole control.**
5. **Auditing only "the" Guest User instead of per-site Guest
   Users.**

## Official Sources Used

- Secure Your Experience Cloud Site (Spring '21 Secure-by-Default) — https://help.salesforce.com/s/articleView?id=sf.networks_security_overview.htm&type=5
- Best Practices and Considerations When Configuring the Guest User Profile — https://help.salesforce.com/s/articleView?id=sf.guest_users_best_practice.htm&type=5
- Apex Sharing Modes — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_classes_keywords_sharing.htm
- Field-Level Security via WITH SECURITY_ENFORCED — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_classes_with_security_enforced.htm
- OWASP Top 10 — https://owasp.org/www-project-top-ten/
- Salesforce Well-Architected Trustworthy — https://architect.salesforce.com/well-architected/trusted/secure
