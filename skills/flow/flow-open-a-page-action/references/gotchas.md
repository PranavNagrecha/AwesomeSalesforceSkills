# Gotchas — Flow Open A Page Action

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Only Screen Flows can navigate

**What happens:** you add an Open a Page action to a record-triggered or autolaunched flow and
the user is never redirected — with no error to explain it.

**When it occurs:** the flow has no screens / no interactive UI. The action is introduced as a
Screen Flow capability ("Screen Flows now support the new Open a Page action"); a background
flow has no user session view to send anywhere.

**How to avoid:** put the navigation in the Screen Flow the user actually runs. If a
background flow does the processing, hand off to (or launch from) a Screen Flow and place the
action there.

---

## Gotcha 2: It opens the record's default view, not a related tab

**What happens:** you want the user to land on a specific related list / related tab of the
record, but they always land on the record's default view.

**When it occurs:** any time you target a Salesforce record — the action opens that record's
default page, and there's no input to select a related tab. A live IdeaExchange request
("Provision to navigate to a related tab from Open a Page action in Flow") exists because of
this exact limitation.

**How to avoid:** if the related tab is mandatory, use a targeted URL to that tab or a custom
`NavigationMixin` component; otherwise accept the default view and set expectations.

---

## Gotcha 3: No "Current Page" open option

**What happens:** you want the action to reuse or refresh the exact page the user is already
on, and there's no option for it.

**When it occurs:** configuring **Where to Open Page** — the shipped option set does not include
a "Current Page" choice. A live IdeaExchange request ("Open a Page Flow Action - Add 'Current
Page' as Where to Open Page Option") asks Salesforce to add one.

**How to avoid:** design around the available open locations, and verify the actual option
labels in Flow Builder for your org rather than assuming a same-tab/current-page behavior.

---

## Gotcha 4: Navigation doesn't override record access

**What happens:** the user is redirected to a record and gets an "insufficient access"
page instead of the data.

**When it occurs:** the running user can't see the target record (OWD/sharing/role) or field
(FLS). The action only changes what the browser opens; the destination record page still
enforces access.

**How to avoid:** confirm the running user can see the record before relying on the redirect —
see `flow/flow-runtime-context-and-sharing`. Never treat the action as a way to surface data a
user otherwise can't reach.

---

## Gotcha 5: Open location behaves differently per surface

**What happens:** the redirect works as expected on desktop Lightning Experience but behaves
differently (or not at all) in an Experience Cloud site, on mobile, or in a console app.

**When it occurs:** the "where to open" semantics (new tab / new window / console tab) depend
on the runtime surface, and Screen Flows run in several. A value that opens a clean new tab on
desktop may not be what an external community user experiences.

**How to avoid:** test the chosen Where to Open Page value on **every** surface the flow runs,
and review `flow/flow-for-experience-cloud` for guest/external-user differences.

---

## Gotcha 6: Assuming a maturity or edition it doesn't state

**What happens:** you build and promote on the assumption the action is GA and available in
your edition, then hit a surprise in a lower environment.

**When it occurs:** the retrievable Summer '26 official pages do not stamp this action with a
GA/Beta/Pilot label, and the full Help reference renders only as an app shell to automated
fetchers — so the maturity and edition/license availability were not pinned by a citable quote.

**How to avoid:** open the action in a Summer '26 Flow Builder and read its in-product help to
confirm maturity, exact inputs, and edition availability before committing a design.
