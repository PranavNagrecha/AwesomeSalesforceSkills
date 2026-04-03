# Gotchas - LWC Data Table

## `key-field` Problems Masquerade As Rendering Bugs

**What happens:** Selected rows, inline edits, or rerendered cells appear to attach to the wrong record.

**When it occurs:** The table uses an unstable or non-unique value for `key-field`.

**How to avoid:** Treat row identity as part of the data model. Use a stable key such as `Id` and carry it through every load and refresh.

---

## Draft State Stays Until You Reset It

**What happens:** The table keeps showing pending edits after save, or later saves include stale changes.

**When it occurs:** The component never clears `draftValues` after a successful save or refresh.

**How to avoid:** Clear `draftValues` only after persistence succeeds and the latest data has been reconciled.

---

## Infinite Loading Without A Stop Rule Becomes A Memory Problem

**What happens:** The table keeps requesting and holding more rows until the page becomes sluggish.

**When it occurs:** The component enables infinite loading but never disables it or pages aggressively enough on the server.

**How to avoid:** Use bounded server pages and turn off loading when the dataset is exhausted or a practical browse limit is reached.

---

## Type Attributes Fail Quietly When Misnamed

**What happens:** Formatting or custom behavior seems ignored for a column even though the code looks plausible.

**When it occurs:** `typeAttributes` use HTML-style names instead of the camelCase names expected by the datatable configuration object.

**How to avoid:** Shape column configuration exactly the way the component reference expects and test each non-default type explicitly.
