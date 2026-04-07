# Gotchas — LWR Site Development

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Aura Components Are Completely Unsupported in LWR Sites

**What happens:** A developer adds an Aura component to a package deployed to an org with an LWR site, expecting it to appear in the Experience Builder Components panel alongside LWC components. The component never appears. If the developer hard-references it from an LWC template, the page fails silently or throws a runtime error with no clear indication that the component type is the problem.

**When it occurs:** Teams migrating from Aura-based communities to LWR templates, or teams with shared component libraries that mix Aura and LWC. The confusion is compounded by the fact that the legacy "Build Your Own" template (without "LWR" in the name) does support Aura components — developers assume the LWR variant behaves the same way.

**How to avoid:** Rewrite every needed Aura component as an LWC component with the appropriate `lightningCommunity__*` targets. Map Aura patterns to LWC equivalents: `{!v.body}` becomes an unnamed default `<slot></slot>`, named facets become named slots, application events become `CustomEvent`, and the Aura navigation service becomes `lightning/navigation` with `NavigationMixin`.

---

## Gotcha 2: Publish-Time Freeze Means the Live Site Does Not See Code Changes Until Republished

**What happens:** A developer fixes a bug in an LWC component, deploys via Salesforce CLI, and confirms the fix works in the Experience Builder preview. The live site continues to show the broken behavior. Users report the bug is still occurring. The developer is confused because the fix is confirmed in the org.

**When it occurs:** Every time a component is changed without republishing — including custom LWC source changes, managed package upgrades, custom label updates, and Apex method signature changes. The Experience Builder preview always fetches current code dynamically, so it diverges from the live site after any deployment without republishing.

**How to avoid:** Republish the site after every code change that should go live. Make site republishing an explicit step in the deployment checklist. Publish during off-peak hours for high-impact changes — CDN HTML cache has a 1-minute TTL after a publish, creating a brief window where some users may still get the previous version. Note that `@salesforce/schema` name references and `@salesforce/customPermission` changes do not require republishing, but `@salesforce/label` and `@salesforce/apex` changes always do.

---

## Gotcha 3: LWS Security Restrictions May Break Existing Component Patterns Without Warning

**What happens:** A component that works correctly in Lightning Experience or an Aura-based community is deployed to an LWR site and fails at runtime. Common failure modes: `window.location.href` assignments do nothing, `document.domain` reads return undefined, `window.top` access is blocked, and third-party libraries that manipulate `document.location` fail silently.

**When it occurs:** When migrating LWC components originally built for Lightning Experience or Aura communities into LWR sites. Also when integrating third-party analytics or charting libraries that assume unrestricted browser global access. The org-level "Use Lightning Web Security" setting has no effect — LWR sites always use LWS at the site level regardless of org settings.

**How to avoid:** Audit all component JavaScript for direct use of restricted DOM APIs (`document.domain`, `document.location`, `window.location`, `window.top`) before migrating to LWR. For navigation, use `lightning/navigation` with `NavigationMixin` instead of manipulating `window.location`. For third-party library integrations, use the `<x-oasis-script>` privileged script tag in Head Markup. Always test LWS compliance on a published LWR site — the Experience Builder preview may not surface LWS enforcement issues that appear on the live site.

---

## Gotcha 4: Dynamic Component Imports Must Use Literal String Paths

**What happens:** A developer uses a variable or template string to construct a dynamic import path (e.g., `` import(`c/${componentName}`) ``). The import silently fails to resolve at runtime or throws an opaque error. The component never loads.

**When it occurs:** When implementing component factories, A/B test pattern selectors, or plugin-style architectures that select components at runtime based on configuration data.

**How to avoid:** LWR sites only support statically analyzable dynamic imports — the import path must be a literal string known at publish time. `import('c/myComponent')` works. `import('c/' + name)` and `` import(`c/${name}`) `` do not work. Use `lwc:if` / `lwc:elseif` conditional rendering in templates for runtime component switching, or use separate `if`/`else` branches each containing a literal import path.

---

## Gotcha 5: camelCase Property Names Are Required in js-meta.xml — PascalCase Breaks Value Binding

**What happens:** A developer names a component property with PascalCase in js-meta.xml (e.g., `HeadingText` or `CTALabel`). The component deploys and appears in Experience Builder, but configured values are never applied to the corresponding `@api` property — it remains `undefined` regardless of what the site admin sets in the property panel.

**When it occurs:** When naming properties in `targetConfig` in js-meta.xml. The failure is invisible at deploy time and only surfaces during site admin configuration testing.

**How to avoid:** Always use camelCase for property names in js-meta.xml (`headingText`, not `HeadingText`; `ctaLabel`, not `CTALabel`). The platform's coercion logic maps property names to JavaScript `@api` variables using camelCase matching — a PascalCase name does not resolve and coercion silently skips the property.
