# LLM Anti-Patterns — LWC Local Development

Common mistakes AI coding assistants make when generating or advising on LWC local development.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Conflating Live Preview with the "unified testing" APIs

**What the LLM generates:** guidance that folds `sf lightning dev component` together with the
Winter '26 "unified testing API," or claims Live Preview runs Apex/Flow tests.

**Why it happens:** both shipped in Winter '26 developer release notes, so the model treats them
as one feature. They are unrelated: Live Preview is an LWC development-workflow tool; Test
Discovery / Test Runner APIs are an **Apex + Flow** testing capability (Application Test
Execution page in Setup, `sf flow run test`).

**Correct pattern:**

```text
LWC local development  -> sf lightning dev component / app / site (rendering, no assertions)
Apex/Flow test running -> Test Discovery / Test Runner APIs (separate; not LWC, not this skill)
```

**Detection hint:** any mention of "Test Discovery", "Test Runner", or "unified testing" inside
LWC local-development guidance.

---

## Anti-Pattern 2: Promising every edit hot-reloads

**What the LLM generates:** "just save and the preview updates automatically" with no caveat.

**Why it happens:** the model generalizes the happy-path live-reload behavior to all edits.

**Correct pattern:**

```text
Hot-reloads: template/HTML attrs, basic CSS, non-API JS methods, new/deleted files
Manual step: new @api props/methods, @wire changes, new @salesforce imports, .js-meta.xml edits
  -> single component: refresh browser   -> app/site: sf project deploy start + restart server
```

**Detection hint:** advice that says changes reload automatically without listing the
`@api`/`@wire`/`@salesforce`/`.js-meta.xml` exceptions.

---

## Anti-Pattern 3: Suggesting Live Preview for Aura components

**What the LLM generates:** "use `sf lightning dev` to preview your Aura component" or a preview
workflow for a `.cmp`/`aura/` bundle.

**Why it happens:** the model treats Aura and LWC as interchangeable client frameworks.

**Correct pattern:**

```text
Live Preview is LWC-only. Aura components can't be previewed — deploy and test them in the org.
```

**Detection hint:** a preview command paired with an `aura/` path, `.cmp`, `.app`, or an Aura
component name.

---

## Anti-Pattern 4: Inventing command names or flags

**What the LLM generates:** made-up commands like `sf lightning preview`, `sfdx force:lightning:preview`,
or flags like `--watch` / `--hot` that don't exist.

**Why it happens:** the model pattern-fills plausible-looking CLI syntax from adjacent tooling.

**Correct pattern:**

```bash
sf lightning dev component -o <org> [-n <component>]
sf lightning dev app       -o <org> [-n <app>] [-t desktop|ios|android] [-i <device-id>]
sf lightning dev site      -o <org> [-n <site>]
# plugin is auto-installed; sf update if the commands are missing
```

**Detection hint:** any `sf lightning dev` invocation whose subcommand isn't `component`, `app`,
or `site`; a `force:lightning:preview`-style legacy command; `sfdx force:lightning:lwc:start`;
`npm run lwc-dev-server`; or `@salesforce/lwc-dev-server` as a required install. Also flag
telling the user to `sf plugins install @salesforce/plugin-lightning-dev` as a prerequisite —
the LWC Developer Guide states the CLI installs the Live Preview plugin automatically.

---

## Anti-Pattern 5: Stating a wrong maturity for single-component preview

**What the LLM generates:** "single-component preview has been GA since Spring '25" or "it's
still Beta" without tying the claim to a release.

**Why it happens:** models pattern-fill maturity labels and default to whatever they saw most.

**Correct pattern:** do not invent a GA/Beta date for single-component preview. The LWC Developer Guide documents `sf lightning dev component` as a Live Preview tool and does not attach a GA/Beta label on that page. Cite the current guide; do not quote a week-of-April-13 GA date that is not on it. The VS Code extension's React preview is a distinct surface from LWC preview.

**Detection hint:** a GA/Beta claim about Live Preview with no citation to the current LWC Developer Guide page.

---

## Anti-Pattern 6: Defaulting to a production org and treating preview as sufficient verification

**What the LLM generates:** a preview command against a production org, and/or a workflow that
ends at "it renders in preview" with no Jest or deploy step.

**Why it happens:** the model optimizes for the shortest path to "see it working" and ignores the
sandbox recommendation and the difference between rendering and testing.

**Correct pattern:**

```text
Target a sandbox/scratch org for preview. Preview = visual inner loop only.
Prove behavior with Jest (lwc/lwc-testing) and deploy through the normal pipeline.
```

**Detection hint:** a `--target-org` pointing at production, or a "done" claim resting on preview
alone with no test/deploy follow-up.
