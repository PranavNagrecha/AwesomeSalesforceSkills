# LLM Anti-Patterns — Experience Cloud Integration Patterns

Common mistakes AI coding assistants make when generating or advising on Experience Cloud external integration configurations. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Using the Org-Level Entity ID for Experience Cloud SAML Configuration

**What the LLM generates:** Instructions to copy the Salesforce org entity ID from Setup > Company Information (e.g., `https://saml.salesforce.com`) and provide it to the external IdP as the Service Provider entity ID for an Experience Cloud site SSO configuration.

**Why it happens:** LLMs trained on general Salesforce SSO documentation frequently conflate org-level SAML configuration with Experience Cloud site-level SAML. The org-level entity ID is mentioned prominently in older Salesforce SSO guides and is the correct value for main org login SSO. LLMs over-apply this to Experience Cloud sites.

**Correct pattern:**

```
1. Create the SAML SSO configuration record in Setup > Identity > SAML Single Sign-On Settings.
2. After saving, click "Download Metadata" on the configuration record.
3. Provide the downloaded metadata XML to the external IdP administrator.
The entity ID in the XML is the site-scoped value (e.g., https://partnerportal.example.com/saml/metadata),
not the org entity ID.
```

**Detection hint:** Look for `saml.salesforce.com` or `https://<MyDomain>.my.salesforce.com` in the entity ID field of generated SSO instructions for an Experience Cloud site. If the entity ID does not contain the Experience Cloud site domain, it is likely wrong.

---

## Anti-Pattern 2: Recommending `<script>` Tags Inside LWC Component Templates for Script Injection

**What the LLM generates:** A custom LWC component with `<script src="https://vendor.example.com/widget.js"></script>` inside the component's HTML template, intended to load a third-party widget on every Experience Cloud page.

**Why it happens:** LLMs draw on web development patterns where placing `<script>` in HTML is the standard injection mechanism. LWR's compile-time stripping of `<script>` elements from LWC templates is an unusual constraint not found in other frameworks, and LLMs underfit to it.

**Correct pattern:**

```
Use Privileged Script Tag in Experience Builder:
Settings > Security > Privileged Script Tags > Add

Enter the vendor script URL:
https://vendor.example.com/widget.js

This is the only CSP-compliant injection mechanism for third-party
scripts in LWR Experience Cloud sites.
Do NOT place <script> tags in LWC component templates.
```

**Detection hint:** Presence of `<script src=` in an LWC HTML template file (`.html` extension) for an Experience Cloud integration. Any generated code suggesting `document.createElement('script')` or `appendChild` for third-party script loading in LWR context should also be flagged.

---

## Anti-Pattern 3: Assuming Privileged Script Tag Is an Org-Wide Setting

**What the LLM generates:** Instructions stating "add the script to Privileged Script Tags in Setup" or "configure the Privileged Script Tag at the org level so it applies to all sites." The instructions do not specify navigating into Experience Builder for each individual site.

**Why it happens:** LLMs associate Salesforce settings with the Setup menu, which is org-level. The Experience Builder site-specific settings area is a distinct UI that LLMs underrepresent in training data relative to the Setup wizard.

**Correct pattern:**

```
Privileged Script Tag is configured per-site in Experience Builder:
1. Open Experience Builder for the target site.
2. Navigate to Settings (gear icon) > Security.
3. Find the Privileged Script Tags section.
4. Add the script source URL here.

Repeat this step for EACH site that needs the script.
There is no org-level Privileged Script Tag configuration.
```

**Detection hint:** Generated instructions that reference "Setup" rather than "Experience Builder" for Privileged Script Tag configuration, or instructions that do not mention per-site repetition when multiple sites are in scope.

---

## Anti-Pattern 4: Treating Salesforce SP and IdP Roles as Mutually Exclusive

**What the LLM generates:** Advice stating that enabling Salesforce as an Identity Provider (to issue assertions to a downstream system) will conflict with or disable the inbound SAML SSO configuration that allows Experience Cloud users to authenticate via an external IdP. The LLM recommends using a separate org or a workaround to avoid the "conflict."

**Why it happens:** The two configuration areas — inbound SAML SSO (SP role) and outbound SAML assertions (IdP role) — appear in different Setup locations and are conceptually distinct. LLMs may conflate them because both involve SAML and are described in the same documentation section, leading to an incorrect inference that they interfere.

**Correct pattern:**

```
SP role (inbound SAML from external IdP):
  Setup > Identity > SAML Single Sign-On Settings

IdP role (outbound SAML assertions to downstream app):
  Setup > Identity > Identity Provider
  + Connected App for the downstream system

These are independent. Both can be active simultaneously.
Enabling the IdP role does not affect inbound SSO configuration.
```

**Detection hint:** Generated content that recommends a separate Salesforce org, a proxy service, or any workaround specifically to avoid "conflicts" between inbound SSO and outbound IdP assertions on the same org. Also flag advice that says "you can only use Salesforce as SP or IdP, not both."

---

## Anti-Pattern 5: Recommending iFrame Embedding Without Flagging the X-Frame-Options Constraint

**What the LLM generates:** Architecture diagrams or implementation instructions that embed an Experience Cloud site in an iFrame on an external web application, without mentioning the `X-Frame-Options: SAMEORIGIN` header that blocks this by default. The instructions proceed directly to HTML `<iframe src="...">` markup as the implementation.

**Why it happens:** iFrame embedding is a common, simple web pattern. LLMs default to it when asked about "embedding" or "displaying one site inside another." The Salesforce-specific `X-Frame-Options` constraint is platform-specific and not universally applied in other web frameworks, so LLMs underweight it.

**Correct pattern:**

```
Before recommending iFrame embedding for an Experience Cloud site:

1. Flag the constraint: Salesforce sets X-Frame-Options: SAMEORIGIN
   by default. Cross-origin iFrame embedding will be blocked.

2. Explore alternatives:
   - Redirect flow: navigate users to the Experience Cloud site directly
   - Widget API: if the vendor provides a JavaScript embed API
   - Salesforce Support case: can enable trusted-origin exception
     for specific domains at the infrastructure level (not self-serve)

3. If iFrame embedding must proceed, document the Support case
   requirement in the design before implementation begins.
```

**Detection hint:** Generated output that includes `<iframe src="https://...my.site.com/..." />` or equivalent markup for embedding an Experience Cloud site in an external application, without any mention of `X-Frame-Options`, SAMEORIGIN, or the need to contact Salesforce Support for cross-origin framing enablement.
