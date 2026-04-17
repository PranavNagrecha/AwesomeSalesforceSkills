# Gotchas — LWC Error Boundaries

## Gotcha 1: Async errors uncaught

**What happens:** Promise rejection doesn't hit errorCallback.

**When it occurs:** Fetch inside connectedCallback.

**How to avoid:** Try/catch + set hasError manually.


---

## Gotcha 2: Deep wrapping

**What happens:** App-level boundary blanks everything.

**When it occurs:** Wrapping root.

**How to avoid:** Wrap at widget granularity.


---

## Gotcha 3: Fallback with deps

**What happens:** Fallback also fails.

**When it occurs:** Fallback renders complex LWC.

**How to avoid:** Minimal inline fallback.

