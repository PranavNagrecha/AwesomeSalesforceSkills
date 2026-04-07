# Well-Architected Notes — Experience Cloud Guest Access

## Relevant Pillars

- **Security** — Guest user configuration is a security-critical operation. Every decision about page access, profile permissions, OWD, and sharing rules has a direct security consequence. Least-privilege is the governing principle: expose only the objects, fields, and records that public pages genuinely need. Unnecessary permissions cannot be "cleaned up later" — they represent live exposure the moment the site goes public.
- **Operational Excellence** — The one-guest-profile-per-site model means that the guest profile is a shared configuration artifact with site-wide scope. Operational clarity requires treating profile changes as site-wide changes, not page-level changes. A documented change process and a pre-publish checklist (see templates/) reduce operational errors.
- **Reliability** — A public page that fails for unauthenticated visitors due to missing profile permissions or misconfigured OWD is a reliability failure. The three-gate model (page access + profile permissions + sharing/OWD) must all be validated before a public page launch. Testing in an incognito browser is a required reliability check, not optional.

## Architectural Tradeoffs

**Public Read Only OWD vs. Private OWD + Sharing Rules**

Setting external OWD to Public Read Only is simpler to configure and eliminates the need for Guest User Sharing Rules. However, it exposes all records of that object to all guest users across all public pages. This tradeoff is acceptable for objects like Product2 where records are inherently meant for public consumption. It is unacceptable for custom objects that may contain customer data, financial data, or internal metadata, even if the current records are benign — a future record insert could inadvertently become public.

The recommended default is Private OWD plus criteria-based Guest User Sharing Rules that selectively expose only intended records. This requires more configuration but is reversible and auditable.

**One Flexible Public Site vs. Separate Sites per Audience**

A single site can serve both public and authenticated pages by mixing page access settings. This reduces infrastructure overhead. However, it means the guest profile and authenticated member profiles coexist in the same site, and changes to one can affect the other. When the public and authenticated use cases diverge significantly (different branding, different objects, different compliance requirements), separate sites with independent guest profiles are architecturally cleaner.

## Anti-Patterns

1. **Setting External OWD to Public Read Only "to fix" an empty public page** — this is the most common shortcut in guest access configuration. It exposes every record of the object to every unauthenticated visitor on every site, far beyond the scope of the page being fixed. The correct fix is to create a Guest User Sharing Rule with the criteria that match the intended public records.

2. **Granting View All or Modify All on the guest user profile** — View All bypasses all record-level security including OWD and sharing rules, making every record of the object visible to any unauthenticated user globally. This is never appropriate for a public site. Modify All on a guest profile allows anonymous write operations across all records, which is a critical security risk.

3. **Not testing as a guest user before publishing** — configuration errors in guest access are invisible until the page is loaded in an unauthenticated context. Testing in an authenticated session (even as an admin) will show data that the guest profile cannot access. Incognito browser testing is the only reliable pre-publish validation method.

## Official Sources Used

- Securely Share Experience Cloud Sites with Guest Users — https://help.salesforce.com/s/articleView?id=sf.networks_guest_user_sharing.htm
- Secure Guest Users Sharing Settings — https://help.salesforce.com/s/articleView?id=sf.networks_secure_guest_users.htm
- Give Secure Access to Unauthenticated Users — https://help.salesforce.com/s/articleView?id=sf.networks_unauthenticated_access.htm
- Experience Cloud Developer Guide (Guest User Context) — https://developer.salesforce.com/docs/atlas.en-us.communities_dev.meta/communities_dev/communities_dev_guest_user.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
