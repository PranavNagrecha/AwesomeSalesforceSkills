# LLM Anti-Patterns — LWC Locker → LWS Migration

Common mistakes AI coding assistants make when generating advice or code for the Locker → LWS migration. These help the consuming agent self-check its own output.

---

## Anti-Pattern 1: "LWS allows `eval` now" — re-introducing `eval` / `new Function` as a workaround

**What the LLM generates:** advice like "since LWS no longer wraps `window` in SecureWindow, you can use `eval()` to dynamically evaluate the template" — or a code change that swaps a Locker-era pre-compiled-template approach for `new Function('return ' + expr)()`.

**Why it happens:** the LLM correctly remembers that Locker explicitly blocked `eval`/`new Function`, then incorrectly infers that LWS — being "less restrictive" at the proxy layer — must permit them. It conflates the proxy layer (which LWS removes) with the page CSP (which still disallows `unsafe-eval`).

**Correct pattern:**

```js
// WRONG — uses eval; fails under both Locker and LWS due to page CSP.
const compute = (expr) => eval(expr);

// RIGHT — express the dynamic behaviour without eval.
const COMPUTERS = {
    'sum':   (a, b) => a + b,
    'mul':   (a, b) => a * b,
    'concat': (a, b) => `${a}${b}`,
};
const compute = (op, a, b) => COMPUTERS[op]?.(a, b);
```

**Detection hint:** any post-migration diff that **adds** `eval(`, `new Function(`, `Function('`, or `setTimeout('<string>'`. These are red-flag patterns regardless of sandbox runtime.

---

## Anti-Pattern 2: Removing Locker shims without removing their downstream deep-clones

**What the LLM generates:** when asked to "clean up Locker workarounds," the LLM deletes the explicit `// LOCKER:` comments and the `SecureElement` references, but leaves the supporting `JSON.parse(JSON.stringify(...))` deep-clone in place because it doesn't recognise it as a Locker workaround.

**Why it happens:** the deep-clone shim is rarely commented; it just sits in a line like `const safe = JSON.parse(JSON.stringify(this.config));`. The LLM treats it as defensive copying, not as Locker-era proxy escape.

**Correct pattern:**

```js
// BEFORE — Locker-era shim
const safeData = JSON.parse(JSON.stringify(this.chartData)); // escape proxy
new Chart(canvas, { data: safeData, options: this.opts });

// AFTER — under LWS, pass the reference directly
new Chart(canvas, { data: this.chartData, options: this.opts });
```

**Detection hint:** in any file that previously referenced `SecureElement` / `SecureWindow`, search for `JSON.parse(JSON.stringify(` and `structuredClone(` on the way *into* a third-party library call. If the upstream call shape includes functions, dates, or class instances, those will silently be lost through the clone.

---

## Anti-Pattern 3: Recommending per-component LWS opt-in that does not exist

**What the LLM generates:** advice like "for components that aren't ready, set `disableLws: true` in their `.js-meta.xml`" or "add `<lwsDisabled>true</lwsDisabled>` to the bundle."

**Why it happens:** the LLM pattern-matches the existence of feature-gating syntax in `*.js-meta.xml` (`isExposed`, `apiVersion`, `targets`) and hallucinates a runtime-flag for LWS. It also confuses the legacy `lws.disabled` org setting (which controls Locker for the whole org under some old configurations) with a per-component flag.

**Correct pattern:** there is no per-component LWS opt-out. The setting is org-wide via **Setup → Session Settings → Use Lightning Web Security for Lightning web components**. Plan the migration accordingly: components that aren't ready need to be fixed *before* the org-level flip, not exempted.

**Detection hint:** any advice or generated code that adds a `disableLws`, `lwsDisabled`, `useLocker`, or similar key to an LWC's `js-meta.xml` is wrong. Reject and replace with sandbox-exercise plus fix-forward guidance.

---

## Anti-Pattern 4: Asserting that LWS is "stricter" than Locker — and adding sanitisation that wasn't there before

**What the LLM generates:** a recommendation to wrap every `innerHTML` assignment in DOMPurify "now that LWS enforces stricter sanitisation," or to add `lwc:dom="manual"` precautions that weren't required before.

**Why it happens:** the LLM treats any new security model as "stricter than the old one" by default and adds belt-and-braces safety. In fact, LWS is **less intrusive at runtime** than Locker; it does not introduce new sanitisation rules that Locker enforced. It does enforce realm boundaries differently, but that is not the same as more aggressive HTML sanitisation.

**Correct pattern:** general LWC XSS safety (sanitise untrusted HTML, prefer template binding over `innerHTML`, use `lwc:dom="manual"` deliberately) is **always** required — it is governed by `lwc/lwc-security`, not by the Locker → LWS migration. The migration itself does not change sanitisation rules.

**Detection hint:** if the LLM's "LWS migration" diff adds DOMPurify, escapes user content that was previously trusted, or adds new XSS guards, redirect that work to a separate review under `lwc/lwc-security`. Do not bundle it into the migration PR — it muddies rollback.

---

## Anti-Pattern 5: Recommending Aura wrapper retirement in the same change as the LWS flip

**What the LLM generates:** a single PR that (a) flips LWS in `SecuritySettings.settings-meta.xml`, (b) deletes a `force:hasRecordId` Aura wrapper, and (c) places the inner LWC directly on the record page — all together.

**Why it happens:** the LLM correctly identifies both as "modernization" and bundles them. It misses that the LWS flip is the high-risk change with org-wide blast radius, while the wrapper retirement is a localised follow-up. Bundling them makes rollback ambiguous (if production breaks, was it the flip or the wrapper change?).

**Correct pattern:**

1. **Change 1:** flip LWS in a sandbox, exercise, fix regressions. Ship to production. Stabilise.
2. **Change 2 (separate PR, days/weeks later):** retire the Aura wrapper, place LWC directly on the page.

**Detection hint:** any PR description that contains both "enable LWS" and "delete Aura wrapper" should be split. Each change should be independently revert-able.

---

## Anti-Pattern 6: Treating Jest passes as proof the LWS migration is safe

**What the LLM generates:** a confident "Jest tests pass after enabling LWS in a sandbox — migration verified" when Jest runs in Node + jsdom, not inside Locker or LWS at all.

**Why it happens:** the LLM treats "all tests green" as the universal completion signal. It doesn't distinguish between unit-test runtime (Node + jsdom + `@lwc/jest-preset`) and the actual browser runtime (LWC inside a Lightning page on Locker or LWS).

**Correct pattern:** Jest passes are necessary but not sufficient. The migration sign-off requires:

- Jest suite green (after removing now-unnecessary Locker-only mocks).
- **AND** sandbox manual exercise of every page hosting custom LWCs.
- **AND** sandbox exercise of every third-party-library-driven feature.
- **AND** DevTools console clean (no `SecureElement` / `SecureWindow` reference errors).

**Detection hint:** any agent output that claims migration completion based on Jest alone, with no sandbox manual-test log, should be rejected.

---

## Anti-Pattern 7: Hallucinating an "LWS-compatible" library fork on NPM

**What the LLM generates:** when asked "which Chart.js version works under LWS," the LLM confidently recommends a fork like `chartjs-lws` or `chartjs-salesforce-lws` that doesn't exist on npm.

**Why it happens:** the LLM extrapolates from the known existence of "Locker-compatible" forks (which were a real artefact of the Locker era) and assumes a parallel ecosystem exists for LWS. In reality, LWS is designed to run upstream library builds, so no fork is needed — just upgrade to a current upstream version.

**Correct pattern:** under LWS, use the **upstream** library build. Specify a current major version that the library's release notes indicate runs on standards-compliant modern browsers. Verify in a sandbox.

**Detection hint:** any recommended dependency name with `-lws`, `-salesforce`, or `-locker` in it should be verified against npm before adopting. The vast majority of "Salesforce-flavoured" library forks are LLM hallucinations.

---

## Anti-Pattern 8: Confusing `lws.disabled` (legacy / org-level) with a per-component or per-bundle flag

**What the LLM generates:** instructions like "set `lws.disabled = true` in the bundle's metadata to skip LWS for this component" — invoking the legacy org-level `lws.disabled` configuration as if it were a per-bundle flag.

**Why it happens:** the LLM has seen `lws.disabled` in older docs (it was the org-level toggle name in some early references) and re-applies it at component scope by analogy with other LWC metadata properties.

**Correct pattern:** `lws.disabled` (where it appears in legacy docs) is an **org-level** toggle, not a component-level one. The current canonical control is the **Use Lightning Web Security for Lightning web components** checkbox in **Session Settings**, with metadata at `SecuritySettings.lwsForLwcEnabled`. There is no per-bundle flag.

**Detection hint:** any generated `*-meta.xml` that contains `lws.disabled`, `lwsDisabled`, or similar at component scope is wrong. Reject and replace with the org-level toggle plus a per-component fix plan.
