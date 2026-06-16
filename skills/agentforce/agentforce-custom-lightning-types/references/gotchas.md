# Gotchas — Agentforce Custom Lightning Types

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Override silently no-ops on non-Apex actions

**What happens:** you deploy a clean `LightningTypeBundle`, but the agent still shows the
default UI and there's no deployment error.

**When it occurs:** the agent action's input or output is a primitive or a standard type
rather than an Apex class. Only Apex-class input/output can be overridden.

**How to avoid:** before building the bundle, confirm the `@InvocableMethod` takes/returns an
Apex wrapper class. If it returns a `String` or `List<Id>`, refactor the invocable signature
first — the bundle cannot fix it.

---

## Gotcha 2: Channel-scoped fallback is invisible

**What happens:** the custom UI appears on desktop but the same agent on mobile (or in a
Service chat) shows the default UI.

**When it occurs:** the bundle ships a folder for one channel (e.g. `lightningDesktopGenAi`)
but not the others. There is no warning — the override just doesn't apply where no folder
exists.

**How to avoid:** enumerate every surface the agent runs on and add the matching channel
folder (`lightningMobileGenAi`, `enhancedWebChat`, `experienceBuilder`) for each. Remember
`renderer.json` is not supported under `experienceBuilder`.

---

## Gotcha 3: schema.json drifts from the Apex class

**What happens:** the renderer receives fields that are `undefined`, or validation rejects
data the action accepts.

**When it occurs:** the field list is hand-authored in `schema.json` instead of being
projected from the Apex class, and the two fall out of sync when the class changes.

**How to avoid:** rely on the `@apexClassType/` binding and keep the Apex class as the single
source of truth; annotate exposed fields with `@AuraEnabled` so the projection stays accurate.

---

## Gotcha 4: Apex visibility breaks projection in namespaced orgs

**What happens:** the type projects no fields, or deployment behaves differently in a managed
package than it did in a scratch org.

**When it occurs:** the input/output class is nested, `public`, or `private`, or its fields
lack `@AuraEnabled` / the class lacks `@JsonAccess`. Non-`global` top-level classes can fail
to serialize correctly across namespaces.

**How to avoid:** make the class top-level and `global`, annotate it with
`@JsonAccess(serializable='always' deserializable='always')`, and put `@AuraEnabled` on every
field you expect the UI to receive.

---

## Gotcha 5: Wrong component prefix for the packaging context

**What happens:** the override resolves in your dev org but fails when installed from a
managed package (or vice versa).

**When it occurs:** `componentOverrides` uses `c/<lwc>` (org metadata) when the component is
delivered in a managed package, which expects the `isv/<lwc>` prefix.

**How to avoid:** use `c/` for unmanaged/org components and `isv/` for components shipped in a
managed package; verify the prefix matches the deployment context.
