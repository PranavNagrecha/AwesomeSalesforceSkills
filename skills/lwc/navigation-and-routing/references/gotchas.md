# Gotchas - Navigation And Routing

## Internal URL Strings Feel Stable Until The Component Moves

**What happens:** A path like `/lightning/r/...` or `/s/...` works in one environment and then breaks or behaves oddly in another.

**When it occurs:** Components are copied between Lightning Experience, mobile, and Experience Cloud without revisiting routing assumptions.

**How to avoid:** Use PageReference-based navigation and generated URLs instead of internal route concatenation.

---

## Custom URL State Needs Namespaced Keys

**What happens:** Query parameters appear in the URL, but the component cannot rely on them as a supported custom state contract.

**When it occurs:** State keys are added without a namespace prefix such as `c__`.

**How to avoid:** Namespace every custom state key and keep the state model small and intention-revealing.

---

## `GenerateUrl` And `Navigate` Drift When Built Separately

**What happens:** The link a user copies does not match the page the button actually opens.

**When it occurs:** The component constructs `href` strings manually while using NavigationMixin elsewhere.

**How to avoid:** Derive both behaviors from the same PageReference object.

---

## Experience Cloud Support Must Be Verified Explicitly

**What happens:** A pattern that works in internal Lightning pages fails in a site because the destination type or assumptions are different.

**When it occurs:** Components are built against internal-app navigation only and later reused in Experience Cloud.

**How to avoid:** Check supported page-reference types for the actual site container before finalizing the contract.
