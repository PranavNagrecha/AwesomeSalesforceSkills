# LLM Anti-Patterns — Agentforce Custom Lightning Types

Common mistakes AI coding assistants make when generating or advising on Agentforce Custom
Lightning Types. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Treating it like a Flow custom property editor

**What the LLM generates:** a Flow-style `configurationEditor` reference in a `js-meta.xml`,
or a `c-myEditor` wired through Flow's screen/action config — and calls it a custom Lightning
type.

**Why it happens:** "custom editor for an input UI" pattern-matches to the more common Flow
custom property editor, which the model has seen far more often in training data.

**Correct pattern:**

```json
// editor.json inside lightningTypes/<type>/<channel>/
{ "editor": { "componentOverrides": { "$": { "definition": "c/flightFilter" } } } }
```

**Detection hint:** look for `configurationEditor` or `lightning__FlowScreen` where a
`LightningTypeBundle` / `lightning__AgentforceInput` was expected.

---

## Anti-Pattern 2: Inventing the schema field list instead of binding to Apex

**What the LLM generates:** a verbose `schema.json` with a full `properties` object listing
every field and type, and no `lightning:type` binding.

**Why it happens:** JSON Schema training data overwhelmingly shows explicit `properties`, so
the model reproduces that shape rather than the Salesforce projection mechanism.

**Correct pattern:**

```json
{ "title": "Flight", "lightning:type": "@apexClassType/c__Flight" }
```

**Detection hint:** a `schema.json` with a large `properties` block and no `@apexClassType`
reference is almost always wrong.

---

## Anti-Pattern 3: Wrong or missing LWC target

**What the LLM generates:** a renderer/editor LWC whose `js-meta.xml` declares
`lightning__RecordPage`, `lightning__AppPage`, or no target at all.

**Why it happens:** those are the most common LWC targets in training data; the
`lightning__Agentforce*` targets are new and rare.

**Correct pattern:**

```xml
<targets><target>lightning__AgentforceOutput</target></targets>  <!-- renderer -->
<targets><target>lightning__AgentforceInput</target></targets>   <!-- editor   -->
```

**Detection hint:** an editor/renderer LWC without `lightning__AgentforceInput` /
`lightning__AgentforceOutput` will not be selectable as an override.

---

## Anti-Pattern 4: Claiming it works for any agent action

**What the LLM generates:** guidance that a custom Lightning type can re-skin any action,
including ones with `String`/primitive input or output.

**Why it happens:** the model generalizes "custom UI override" without surfacing the
documented constraint.

**Correct pattern:** state explicitly that only actions whose input or output is an **Apex
class** can be overridden, and recommend refactoring the invocable signature when it isn't.

**Detection hint:** any advice that omits the Apex-class constraint, or proposes overriding
an action returning a primitive.

---

## Anti-Pattern 5: Asserting a GA/Beta status or a wrong API floor

**What the LLM generates:** "this GA feature, available since Spring '25..." or a sample
`package.xml` at `version 58.0`.

**Why it happens:** models pattern-fill maturity labels and default to older API versions seen
frequently in training data.

**Correct pattern:** target API `64.0`+ in `package.xml` and `js-meta.xml`, and do not state a
GA/Beta status the release notes don't explicitly give.

**Detection hint:** a `<version>` below `64.0`, or any "Generally Available"/"Beta" claim that
isn't backed by a release-notes citation.

---

## Anti-Pattern 6: Putting renderer.json under experienceBuilder

**What the LLM generates:** a `renderer.json` inside an `experienceBuilder/` channel folder to
customize output in an Experience site.

**Why it happens:** the model assumes channel folders are symmetric for editor and renderer.

**Correct pattern:** use editor overrides for `experienceBuilder`; `renderer.json` is not
supported there. Place renderer overrides under `lightningDesktopGenAi` / `lightningMobileGenAi`
/ `enhancedWebChat`.

**Detection hint:** a `renderer.json` path containing `experienceBuilder/`.
