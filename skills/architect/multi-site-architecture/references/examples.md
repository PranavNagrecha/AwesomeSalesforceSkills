# Examples — Multi-Site Architecture

## Example 1: Customer + Partner + Employee Portal Sharing One Org

**Context:** A manufacturing company runs Salesforce Sales Cloud and Service Cloud in a single Enterprise org. They need to deploy three distinct portals: a customer self-service portal for case creation and order tracking, a partner deal registration and MDF portal, and an employee benefits and HR knowledge base.

**Problem:** Without a deliberate multi-site strategy, teams default to three ad hoc site builds with no shared component library and no plan for the 100-site quota. After one year of iteration, the org has 12 preview sites and 8 inactive prototypes in addition to the 3 live portals — 23 sites consumed with only 3 in active use. Shared LWC components get forked per site and drift out of sync.

**Solution:**

Site topology (three sites, one org):

```
Org: company.my.site.com (My Domain)
│
├── Site: CustomerPortal  → portal.company.com/customers
│     Audience: external customers
│     License: Customer Community Plus
│     Guest access: FAQ articles and case creation (unauthenticated)
│
├── Site: PartnerPortal   → portal.company.com/partners
│     Audience: resellers and distributors
│     License: Partner Community
│     Guest access: none (login required for all pages)
│
└── Site: EmployeePortal  → portal.company.com/employees
      Audience: internal employees
      License: Employee Community or Salesforce license
      Guest access: none
```

Shared LWC component strategy:

```xml
<!-- Component metadata for a shared header component -->
<!-- skills/architect/multi-site-architecture/templates/ for full example -->
<LightningComponentBundle xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>63.0</apiVersion>
    <isExposed>true</isExposed>
    <targets>
        <target>lightningCommunity__Page</target>
        <target>lightningCommunity__Default</target>
    </targets>
    <targetConfigs>
        <targetConfig targets="lightningCommunity__Default">
            <property name="logoUrl" type="String" label="Logo URL"
                description="Site-specific logo URL configured per site in Experience Builder"/>
            <property name="supportEmail" type="String" label="Support Email"
                description="Contact email displayed in the header for this site"/>
        </targetConfig>
    </targetConfigs>
</LightningComponentBundle>
```

`logoUrl` and `supportEmail` are `@api` properties configured separately in each site's Experience Builder. The component code is identical across all three sites; only the configuration differs.

**Why it works:** One component codebase, three independent configurations. When the header design changes, one code update propagates to all three sites on the next deployment. The `isExposed: true` declaration makes the component available in Experience Builder's component palette for all sites in the org.

---

## Example 2: Regional Sub-Portals with Shared Component Library

**Context:** A global B2B software company needs an Experience Cloud self-service portal in three regions: EMEA, APAC, and AMER. Each region requires localized language, regional legal disclaimers, and distinct support contact information. The underlying case management and knowledge data model is the same across regions.

**Problem:** Without architecture guidance, three separate SFDX projects get created — one per region — and LWC components are forked from a master copy. Six months later, a security fix applied in the AMER component is never backported to EMEA or APAC. Translations are embedded in component JavaScript rather than managed through Translation Workbench.

**Solution:**

Regional site topology:

```
Org: globalco.my.site.com
│
├── Site: PortalEMEA  → support.globalco.com/emea
│     Default language: English (United Kingdom)
│     Supported languages: French, German, Spanish
│
├── Site: PortalAPAC  → support.globalco.com/apac
│     Default language: English (Australia)
│     Supported languages: Japanese, Simplified Chinese
│
└── Site: PortalAMER  → support.globalco.com/amer
      Default language: English (United States)
      Supported languages: Spanish (Latin America), Portuguese (Brazil)
```

Externalized content approach in a shared LWC footer component:

```javascript
// footerLinks.js — shared across all three sites
import { LightningElement, api } from 'lwc';

export default class FooterLinks extends LightningElement {
    // Configured per site in Experience Builder — no hard-coded region content
    @api privacyPolicyUrl;
    @api cookiePolicyUrl;
    @api legalEntityName;
    @api supportPhoneNumber;
}
```

Translation Workbench handles all UI string translations via standard Salesforce i18n. Legal disclaimer text differs per region and is stored in a Custom Metadata Type (`Regional_Legal_Text__mdt`) keyed by region code, loaded by the component at runtime.

SFDX project structure:
```
force-app/
  main/
    default/
      lwc/
        footerLinks/          # shared — deployed to all sites
        caseCreationForm/     # shared — deployed to all sites
        regionBanner/         # shared — deployed to all sites
      customMetadata/
        Regional_Legal_Text.EMEA.md-meta.xml
        Regional_Legal_Text.APAC.md-meta.xml
        Regional_Legal_Text.AMER.md-meta.xml
```

**Why it works:** One codebase covers three sites. Security fixes deploy once. Regional content is data-driven (Custom Metadata) rather than code-driven. Translation Workbench handles language without LWC changes. When a fourth region (LATAM) is added, a new Custom Metadata record and a new site are all that is required — no component code changes.

---

## Anti-Pattern: Designing Cross-Site Navigation as a Native Session Hand-Off

**What practitioners do:** After building a customer portal and a partner portal in the same org, the business asks for a "seamless link" between them — a user authenticated in the customer portal should click a link and arrive authenticated in the partner portal without logging in again. Teams design flows or Apex that attempt to pass session tokens or user context between the two sites via URL parameters.

**What goes wrong:** Salesforce Experience Cloud has no native cross-site session sharing. Attempting to pass session context via URL parameters creates a security vulnerability (session token exposure in URLs and server logs). The approach fails when the target site validates the session independently and rejects the passed token. In some configurations it produces authentication errors that are difficult to diagnose.

**Correct approach:** Configure SSO via an external IdP (Okta, Azure AD, Ping Identity) and register both sites as separate Service Providers. The IdP maintains the active user session. When the user navigates from Site A to Site B, the IdP issues a new SAML assertion for Site B transparently — the user is not prompted to log in again because the IdP session is already active. This is the supported, secure pattern for transparent cross-site authentication.
