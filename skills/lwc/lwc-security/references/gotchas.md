# Gotchas — LWC Security

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Browser Isolation Does Not Replace Apex Security

**What happens:** Teams trust LWS or Locker to protect sensitive data even though the Apex controller returns fields the user should not see.

**When it occurs:** Components depend on custom Apex and nobody reviews sharing, CRUD, or FLS enforcement.

**How to avoid:** Treat the server boundary as part of the component security model and prefer LDS when it fits.

---

## Light DOM Is Easier To Reach Across Boundaries

**What happens:** A component becomes easier for surrounding code to inspect or influence than the team expected.

**When it occurs:** Light DOM is used casually or at the top level of the hierarchy.

**How to avoid:** Default to shadow DOM and use light DOM only with a reviewed reason and safe nesting.

---

## Manual DOM Work Expands The Review Surface

**What happens:** A small UI need turns into broad DOM manipulation that is harder to reason about and harder to secure.

**When it occurs:** Teams use `innerHTML`, `lwc:dom="manual"`, or global DOM queries instead of declarative markup.

**How to avoid:** Keep the DOM ownership boundary narrow and prefer template-driven rendering.
