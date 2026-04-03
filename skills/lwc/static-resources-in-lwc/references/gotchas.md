# Gotchas - Static Resources In LWC

## `renderedCallback()` Replays Unless You Guard It

**What happens:** The same library loads and initializes multiple times.

**When it occurs:** `loadScript()` or `loadStyle()` is called from `renderedCallback()` without a one-time flag.

**How to avoid:** Use a clear initialization guard and reset it only if the load fails and needs a retry.

---

## Zip Internal Paths Become Part Of The Contract

**What happens:** A library or asset suddenly fails to load after a resource refresh even though the resource name stayed the same.

**When it occurs:** The internal zip structure changed, but consumer code still appends the old file path.

**How to avoid:** Treat the internal archive layout as part of the versioned interface and document it for consumers.

---

## CDN Instructions Usually Mislead Salesforce Teams

**What happens:** A third-party library guide says to paste a script tag from a CDN, but the approach does not map well to Salesforce UI constraints.

**When it occurs:** Teams follow generic web instructions instead of Salesforce-specific asset loading guidance.

**How to avoid:** Repackage the library into a static resource and load it through `platformResourceLoader`.

---

## Trust Escalation Is A Review Trigger

**What happens:** A library only works after extra trust or global access allowances are added.

**When it occurs:** The dependency expects direct control over browser globals or DOM behavior that conflicts with platform boundaries.

**How to avoid:** Document the trust requirement explicitly and challenge whether the library is a good Salesforce UI fit before normalizing the exception.
