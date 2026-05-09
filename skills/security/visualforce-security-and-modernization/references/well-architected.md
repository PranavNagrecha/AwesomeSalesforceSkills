# Well-Architected Notes — Visualforce Security And Modernization

## Relevant Pillars

- **Security** — Visualforce hardening is fundamentally a Security pillar exercise. The CSRF model, FLS enforcement on getters and bindings, and the controller sharing keyword are all Security concerns. The largest real-world failure mode is treating `with sharing` as a complete security posture and missing the FLS gap on custom getters; the second largest is reflexively turning off the platform CSRF token to "fix" a third-party integration that should have been fixed at the integration boundary instead. Ongoing audits should re-examine FLS posture every time the underlying object schema changes (a new field added later may be FLS-permissive by default and inherit the page's gap).
- **Operational Excellence** — Modernization triage is an Op-Ex exercise. Treating "rewrite all VF to LWC" as a goal in itself is a misallocation of engineering time; treating "every VF page is fine forever" misses the finding-on-the-old-page that becomes a breach. The discipline is per-page disposition (rewrite / harden / leave) re-evaluated quarterly as the audience and findings change. The bundled checker script and the inventory output are the operational-cadence artifacts.

## Architectural Tradeoffs

| Tradeoff | Why it matters |
|---|---|
| Rewrite to LWC vs harden in place vs leave alone | Rewriting is high-cost and high-risk. Hardening is low-cost but does not fix structural issues like LEX iframe behavior. Leaving alone is correct for stable internal pages. The default disposition for a working page is *leave alone* — modernization is justified by a real signal, not a default policy. |
| `csrfProtection="false"` vs fixing the integration | Disabling CSRF protection is almost always the wrong response to "an external system can't submit." The right response is to fix the external system to use OAuth + REST, or to make it acquire the form token first. CSRF disablement should require a written security-review justification. |
| `with sharing` alone vs `with sharing` + `WITH USER_MODE` | `with sharing` covers records only. Field-level enforcement requires either `WITH USER_MODE` on SOQL (Summer '23+) or `Schema.sObjectType.X.fields.Y.isAccessible()` checks. The latter is verbose and fragile; prefer `WITH USER_MODE` everywhere. |
| Lightning Out interop vs full LWC rewrite | Hosting an LWC inside a VF shell is a gradual migration path — useful when a page is too large to rewrite in one quarter. The cost is operational complexity (two security models, two session contexts). For pages under ~500 lines, full rewrite is usually faster than incremental migration. |
| `<apex:dynamicComponent>` vs static components with `rendered=` | Dynamic components are harder to security-review and harder to test. Static components with `rendered="{!boolean}"` are equivalent for almost every real use case and trivial to reason about. The presence of `<apex:dynamicComponent>` is a reliable indicator that the page is a rewrite candidate. |
| View state vs JS Remoting for read-heavy pages | View state has a 170 KB ceiling and round-trips on every postback. JS Remoting bypasses view state entirely. For read-heavy pages, remoting is structurally better; the cost is loss of `<apex:form>` postback semantics, which sometimes matter. The tradeoff is between platform-managed state and explicit state. |

## Anti-Patterns

1. **Disabling CSRF protection to make a third-party integration work.** The integration belongs on a REST endpoint with proper authentication, not on a VF page with the platform's CSRF defense turned off. Once `csrfProtection="false"` ships, every page request becomes a CSRF vector, including the next 17 unrelated forms a developer adds to the same page assuming the platform default applies.
2. **Assuming `with sharing` covers FLS.** It does not. The keyword governs record sharing only. FLS and CRUD enforcement is a separate layer requiring `WITH USER_MODE` (or equivalent). Code reviews that pass solely on the presence of the sharing keyword have a structural gap.
3. **Mass-rewriting all Visualforce pages to LWC.** Stable, internal-only, working pages are not a security or maintenance liability. Modernization budget should be allocated to pages with real signals (security findings, LEX-broken UX, controller maintenance burden), not by a calendar. Several Salesforce orgs have wasted engineer-quarters rewriting pages that nobody complained about.
4. **Migrating `renderAs="pdf"` pages to LWC.** LWC has no PDF rendering equivalent. Either keep the VF page as a thin PDF wrapper, or introduce an external PDF service (Conga, DocGen, custom Lambda). The "rewrite to LWC" decision tree should explicitly carve out PDF generators.
5. **Using `<apex:outputText>` for sObject field values.** `<apex:outputText>` does not enforce FLS. `<apex:outputField>` does (when bound to a standard-controller record or to a USER_MODE-queried sObject). The convention should be: `outputField` for sObject fields, `outputText` for controller-computed display strings only.

## Official Sources Used

- Visualforce Developer's Guide — https://developer.salesforce.com/docs/atlas.en-us.pages.meta/pages/
- Visualforce Developer's Guide — Cross Site Request Forgery (CSRF) — https://developer.salesforce.com/docs/atlas.en-us.pages.meta/pages/pages_security_csrf.htm
- Apex Developer Guide — Enforcing Object and Field Permissions (`WITH USER_MODE` / `WITH SECURITY_ENFORCED`) — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_classes_perms_enforcing.htm
- Salesforce Secure Coding Guidelines — https://developer.salesforce.com/docs/atlas.en-us.secure_coding_guide.meta/secure_coding_guide/
- Salesforce Help — View State on Visualforce Pages — https://help.salesforce.com/s/articleView?id=sf.pages_view_state.htm
- Salesforce Well-Architected — Trusted (Security pillar) — https://architect.salesforce.com/well-architected/trusted/
- Salesforce Well-Architected — Adaptable (Operational Excellence framing for legacy modernization) — https://architect.salesforce.com/well-architected/adaptable/
- Lightning Components Developer Guide — Add Lightning Web Components in Visualforce Pages — https://developer.salesforce.com/docs/component-library/documentation/en/lwc/lwc.use_outside_lwc_in_visualforce
