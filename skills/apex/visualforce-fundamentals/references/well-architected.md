# Well-Architected Notes — Visualforce Fundamentals

## Relevant Pillars

### Security

Visualforce custom controllers are a historically common source of security vulnerabilities because the standard controller's FLS enforcement does not extend to custom Apex methods. Security risks include:

- **SOQL injection:** Dynamic queries built with string concatenation of user-supplied URL parameters or form values allow attackers to extract arbitrary data.
- **FLS/CRUD bypass:** Custom controller methods that query or DML without `WITH USER_MODE` expose or modify data regardless of the running user's permissions.
- **CSRF on GET:** Page `action` attributes that trigger DML on every GET request can be exploited by crafting a URL that causes the action to fire in the context of an authenticated user.

Mitigation: Use `WITH USER_MODE` on all SOQL in custom controllers, enforce POST-only for state-changing actions via `<apex:form>` and `<apex:commandButton>`, and test with low-privilege users before deployment.

### Performance Efficiency

The 170 KB view state limit is a hard platform constraint that directly impacts user experience. Pages that exceed this limit fail at runtime with no graceful degradation. Performance anti-patterns include:

- Non-transient collections serialized into view state unnecessarily.
- SOQL queries fetching all fields when only a subset are rendered.
- SOQL inside loops triggered by page rendering (one query per row in a `<apex:repeat>`).

Mitigation: Mark display-only collections `transient`, restrict SOQL field lists, pre-load related data into maps in the constructor, and use `<apex:remoteAction>` for heavy read operations to bypass view state entirely.

## Architectural Tradeoffs

**Standard Controller vs. Custom Controller:**
The standard controller provides FLS enforcement and standard actions for free, but limits customization. A custom controller gives full control at the cost of manual FLS/CRUD enforcement. Extensions are the preferred middle ground — they let you add custom logic while keeping the standard controller's automatic field-level enforcement for bound fields.

**View State vs. No-View-State Patterns:**
Pages with `<apex:form>` carry view state overhead on every postback. For display-heavy pages with frequent updates, JavaScript Remoting (`<apex:remoteAction>`) or `<apex:actionFunction>` calling lightweight methods can reduce postback cost significantly, but requires more JavaScript and moves data-binding responsibility to the client.

**Visualforce vs. LWC:**
For new development, Lightning Web Components are the recommended approach for custom UI on the Salesforce platform. Visualforce remains appropriate for PDF generation (`renderAs="pdf"`), email templates, and maintenance of existing Classic pages. New interactive UI should use LWC unless VF-specific platform features are required.

## Anti-Patterns

1. **Full-Custom Controller Without FLS Enforcement** — Building a custom controller and omitting `WITH USER_MODE` or explicit Schema checks exposes the page to security-review failure and real data leakage. Every custom or extension controller method that queries data must apply user-mode enforcement.

2. **Non-Transient Display Collections** — Declaring `List<SObject>` properties as non-transient when they are only used for display bloats view state on every postback, moves toward the 170 KB limit silently, and increases page load time without providing any correctness benefit.

3. **DML Triggered on Page Load via `action` Attribute** — Using the `<apex:page action="{!doSomething}">` attribute to perform DML or side-effecting callouts fires those operations on every page load, including refreshes and bookmarked URLs. This pattern causes duplicate records, unexpected audit entries, and is exploitable via CSRF.

## Official Sources Used

- Visualforce Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.pages.meta/pages/pages_intro.htm
- Visualforce Limits Quick Reference — https://help.salesforce.com/s/articleView?id=000385650&type=1
- Apex Developer Guide (WITH USER_MODE) — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_classes_enforce_usermode.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Optimize View State Best Practices — https://developer.salesforce.com/docs/atlas.en-us.pages.meta/pages/pages_best_practices_optimizing_viewstate.htm
