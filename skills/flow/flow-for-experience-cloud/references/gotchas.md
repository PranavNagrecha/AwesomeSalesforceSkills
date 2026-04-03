# Gotchas — Flow For Experience Cloud

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Guest Access Multiplies Risk Faster Than Complexity Suggests

**What happens:** A simple public flow becomes a data-exposure risk because it reads too much data or invokes privileged Apex.

**When it occurs:** Teams treat guest users like lightweight authenticated users instead of a public attack surface.

**How to avoid:** Narrow the flow to the minimum required data operations and review every server-side dependency.

---

## Site Runtime Differences Show Up Late If Nobody Tests In-Site

**What happens:** The flow works in builder previews but fails or renders differently once placed in the actual Experience Cloud page.

**When it occurs:** Teams validate only in Flow Builder or internal Lightning pages and skip site-runtime testing.

**How to avoid:** Test the full site page, finish behavior, and permissions in the target Experience Cloud runtime.

---

## LWR Limitations Matter For Screen Component Choice

**What happens:** A flow using custom screen components is embedded on an LWR site and then cannot be used the way the team expected.

**When it occurs:** Teams choose `lightning-flow` on an LWR site before checking whether the flow includes custom Aura or custom LWC screen components.

**How to avoid:** Confirm site runtime and screen-component compatibility early in the architecture decision.
