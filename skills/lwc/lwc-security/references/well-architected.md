# Well-Architected Notes — LWC Security

## Relevant Pillars

### Security

This skill is primarily a Security concern because LWC can expose risk both in the browser and through the Apex controllers it calls.

### Reliability

Security shortcuts in DOM access or Apex exposure often become production incidents, not just code-style issues.

### User Experience

Secure defaults such as LDS and declarative rendering also improve consistency and reduce fragile UI behavior.

## Architectural Tradeoffs

- **LDS simplicity vs custom Apex flexibility:** LDS is usually the safer default, while Apex is justified only when the business logic requires it.
- **Shadow DOM safety vs light DOM flexibility:** Light DOM can enable special cases, but it reduces encapsulation and increases review needs.
- **Template rendering vs manual DOM control:** Manual DOM work offers flexibility at the cost of a larger security surface.

## Anti-Patterns

1. **Using custom Apex for ordinary record access with no security review** — unnecessary server-side exposure.
2. **Casual `innerHTML` or `lwc:dom="manual"` usage** — bypasses safer declarative patterns.
3. **Top-level light DOM without a clear reason** — weakens component isolation for convenience.

## Official Sources Used

- Secure Apex Classes — https://developer.salesforce.com/docs/platform/lwc/guide/apex-security.html
- Light DOM — https://developer.salesforce.com/docs/platform/lwc/guide/create-light-dom.html
- Access Elements the Component Owns — https://developer.salesforce.com/docs/platform/lwc/guide/create-components-dom-work
