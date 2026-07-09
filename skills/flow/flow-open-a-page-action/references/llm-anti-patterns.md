# LLM Anti-Patterns — Flow Open A Page Action

Common mistakes AI coding assistants make when generating or advising on the Flow Open a Page
action. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Reaching for a custom LWC when the native action exists

**What the LLM generates:** a full `NavigationMixin` / `lightning/navigation` Lightning web
component ("here's a screen component to redirect the user") for a plain "open the new record"
requirement.

**Why it happens:** the model has seen the `NavigationMixin` redirect pattern thousands of
times in training data; the Summer '26 native action is new and rare, so it defaults to code.

**Correct pattern:**

```text
Screen Flow → Create Records → Action: Open a Page (target = {!newRecord.Id})
```

Recommend the declarative action first; reserve a custom component for navigation the action
can't express (see `flow/flow-screen-lwc-components`).

**Detection hint:** a `NavigationMixin`/`import { NavigationMixin } from 'lightning/navigation'`
component proposed for a generic "navigate to record after flow" ask.

---

## Anti-Pattern 2: Recommending the retURL / finish-URL hack as the answer

**What the LLM generates:** guidance to customize the flow's finish URL (`retURL`) or build a
`force:navigateToURL` local action as *the* way to redirect after a Screen Flow.

**Why it happens:** those were the established pre-Summer-'26 workarounds and dominate older
docs and community posts in training data.

**Correct pattern:** lead with the native **Open a Page** action; mention the retURL/local-action
approaches only as legacy alternatives being migrated away from.

**Detection hint:** advice centered on `retURL`, finish-URL customization, or `force:navigateToURL`
without mentioning the native action.

---

## Anti-Pattern 3: Putting the action in a background flow

**What the LLM generates:** an Open a Page action inside a record-triggered or autolaunched flow
"so the user is taken to the record after the trigger runs."

**Why it happens:** the model treats "navigate after save" as trigger logic and doesn't surface
the constraint that navigation needs an interactive Screen Flow.

**Correct pattern:** state that Open a Page is a **Screen Flow** action; if a background flow does
the work, own the navigation in the Screen Flow the user runs.

**Detection hint:** an Open a Page action described alongside `<recordTriggerType>` /
`AutoLaunchedFlow` / "before-save" / "after-save" with no Screen Flow in the design.

---

## Anti-Pattern 4: Inventing input names and open-location options

**What the LLM generates:** a confident, specific parameter list — e.g. "set `Page Type` to
`Record`, `Page Reference` to the Id, and `Open In` to `New Console Tab`" — as if quoting the
docs.

**Why it happens:** the model pattern-fills a plausible input schema (often borrowed from
`PageReference` / `NavigationMixin`) rather than admitting the labels aren't confirmed.

**Correct pattern:** reference only what's confirmed — the action opens a **record or external
URL**, configured via a **Where to Open Page** input — and tell the user to read the exact input
labels and options in Flow Builder. Do not fabricate a field list.

**Detection hint:** specific input/option labels (`Page Type`, `Page Reference`, `Open In`,
`New Console Tab`) stated as fact without a source, beyond "Where to Open Page."

---

## Anti-Pattern 5: Asserting a GA/Beta status the release notes don't state

**What the LLM generates:** "the Open a Page action is Generally Available in Summer '26" (or
"Beta"), stated as fact.

**Why it happens:** models pattern-fill maturity labels for any newly shipped feature and default
to "GA."

**Correct pattern:** say the action shipped in Summer '26 and that the retrievable official pages
don't stamp a GA/Beta/Pilot maturity — confirm it in-org. Never invent a maturity level.

**Detection hint:** the strings "Generally Available", "GA", "Beta", or "Pilot" attached to this
action without a release-notes citation.

---

## Anti-Pattern 6: Promising a related-tab or current-page behavior

**What the LLM generates:** "configure it to open the Contacts related tab" or "set it to refresh
the current page," presented as supported configuration.

**Why it happens:** those are natural user asks, and the model assumes the action is as flexible
as `NavigationMixin`.

**Correct pattern:** state the documented limits — the action opens the record's **default view**
(no related-tab targeting) and has **no "Current Page" option** — both are open IdeaExchange
requests, not shipped behavior.

**Detection hint:** guidance to target a specific related tab, or to reuse/refresh the current
page, via the action's inputs.
