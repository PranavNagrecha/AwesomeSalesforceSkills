# Examples — Flow Open A Page Action

The Flow snippets below are illustrative configuration sketches (Flow is clicks-not-code, so
these describe the elements you build in Flow Builder, not literal file contents). The action
is a Summer '26 Screen Flow capability; confirm the exact input labels and open-location
options in your org's Flow Builder before promoting.

## Example 1: Redirect the user to the record their flow just created

**Context:** a "Log a Case" Screen Flow creates a Case and the agent should land on that new
Case immediately, without an extra click.

**Problem:** without the action you either bolt on a custom `NavigationMixin` LWC (code you now
own) or customize the finish URL with a retURL hack (fragile, fires only at completion).

**Solution:**

Screen Flow element outline:

```text
Screen: "Case details"           (collect Subject, Description)
Create Records: newCase          (stores Id in {!newCase.Id})
Action: Open a Page              (core action)
    - Target:            Salesforce record → {!newCase.Id}
    - Where to Open Page: <choose the open location; read the labels in Flow Builder>
```

Corresponding metadata shape (heuristic — the exact `actionName` is set by the platform; do
not hand-invent it):

```xml
<actionCalls>
    <name>Open_the_new_Case</name>
    <actionType>...</actionType>       <!-- native Open a Page action type -->
    <label>Open a Page</label>
    <!-- inputParameters carry the target record and the Where to Open Page value -->
</actionCalls>
<screens>...</screens>                 <!-- presence of screens = this is a Screen Flow -->
```

**Why it works:** the Id exists once Create Records runs, so the action has a concrete record
to open; the whole navigation is declarative metadata that survives platform upgrades.

---

## Example 2: Open an external URL built earlier in the flow

**Context:** after collecting payment details, the flow must send the user to an external
payment page whose URL includes a token the flow computed.

**Problem:** the `force:navigateToURL` local action still works but is undocumented-feeling
glue, and putting the URL logic in a component hides it from the flow.

**Solution:**

```text
Assignment / Formula: paymentUrl = "https://pay.example.com/checkout?token=" & {!token}
Action: Open a Page
    - Target:            External web page → {!paymentUrl}
    - Where to Open Page: <new tab / new window — confirm option label in Flow Builder>
```

**Why it works:** the URL lives in a named resource you can debug and reuse; the action is the
supported path for opening it, replacing the local-action / retURL workarounds.

---

## Example 3: Migrate a legacy redirect onto the native action

**Context:** an existing Screen Flow ends with a custom `c:navigateToUrl` local action that
redirects to the edit page of the record it updated.

**Problem:** the custom action is extra metadata to maintain and a common source of "why did
the redirect break after the release?" tickets.

**Solution:**

1. Confirm the flow has `<screens>` (it's a Screen Flow — the action requires one).
2. Add an **Open a Page** action targeting the same record, matching the old open location in
   **Where to Open Page**.
3. Delete the `navigateToUrl` local action and any URL-string variables it needed.
4. Re-test the destination and open location on every surface the flow runs.

Run the skill checker to find these candidates automatically:

```bash
python3 scripts/check_flow_open_a_page_action.py --manifest-dir force-app/main/default
```

**Why it works:** one supported action replaces the homegrown redirect and its dead variables,
so there's a single navigation mechanism instead of two competing ones.

---

## Anti-Pattern: putting the action in a background flow

**What practitioners do:** add an Open a Page action to a record-triggered or autolaunched flow
expecting it to "send the user to the record after save."

**What goes wrong:** background flows run with no interactive UI — there is no user session
screen for the action to redirect, so nothing happens where they expect it.

**Correct approach:** own the navigation in the **Screen Flow** the user actually runs. If a
record-triggered flow does the work, hand off to (or launch from) a Screen Flow, and place the
Open a Page action there.

---

## Anti-Pattern: treating navigation as an access grant

**What practitioners do:** navigate a user to a record and assume "opening it" means they'll see
it, then are surprised by an insufficient-access page.

**What goes wrong:** the action only routes the browser; the destination record page still
enforces sharing and FLS for the running user, so a user without access lands on an error page.

**Correct approach:** confirm the running user can see the target record (sharing, role, FLS)
before relying on the redirect — see `flow/flow-runtime-context-and-sharing`. Navigation is not
a data-exposure mechanism.
