# Gotchas — Tableau Embedding in Lightning

Real-world surprises in embedding Tableau dashboards in Lightning.

---

## Gotcha 1: CSP / Trusted Sites must allow `frame-src` and `connect-src`

**What happens.** LWC renders empty; browser console shows CSP
violations like "Refused to frame ... because it violates CSP".

**When it occurs.** First-time embed without Trusted Sites
configuration. Or after a Tableau Cloud region migration that
changes the host URL.

**How to avoid.** Setup -> CSP Trusted Sites -> add the Tableau
host URL with `Frame-Source` checked. If Apex fetches Tableau APIs,
also add `Connect-Source`.

---

## Gotcha 2: JWT subject claim must match Tableau-provisioned identity

**What happens.** Embed loads, but RLS filter shows empty data.
Browser network tab shows the viz authenticated successfully.

**When it occurs.** JWT `sub` claim is set to the Salesforce user's
email, but the Tableau user is provisioned with a different email
(e.g. due to SCIM / case-sensitivity / domain alias mismatch).

**How to avoid.** Audit Salesforce user emails vs Tableau user
emails. Standardize provisioning. Test with a known-good user
identity end-to-end.

---

## Gotcha 3: JWT expiry must be short

**What happens.** Long-lived JWT (e.g. 24h) leaks via browser dev
tools or proxy logs and is replayed by an attacker.

**When it occurs.** Engineers generating JWTs with comfortable
expiry windows.

**How to avoid.** Keep expiry to 5 minutes. The JWT is generated
per-request from Apex; there is no UX reason to make it long-lived.

---

## Gotcha 4: Tableau Cloud region URL changes break embeds

**What happens.** Tableau Cloud site migrates from one cluster to
another (e.g. `prod-eu-a` to `prod-eu-b`). All embedded URLs break
because the host changed.

**When it occurs.** Tableau region migrations or site moves.

**How to avoid.** Source the host URL from a Custom Metadata
record, not hardcoded in LWC / Apex. Migration becomes a one-row
update.

---

## Gotcha 5: Connected App secret rotation invalidates outstanding JWTs

**What happens.** Tableau-side Connected App secret rotates. Apex-
generated JWTs from before the rotation are rejected. Users see
"unauthorized" until Apex picks up the new secret.

**When it occurs.** Scheduled secret rotation or compromise
remediation.

**How to avoid.** Store the secret in Named Credentials or a Custom
Metadata Type that Apex re-reads per request. Rotate Salesforce-side
in coordination with Tableau-side.

---

## Gotcha 6: `<tableau-viz>` events do not bubble naturally in LWC shadow DOM

**What happens.** Engineer adds an event listener for a Tableau
viz event (e.g. mark-selected). The listener doesn't fire because
of LWC's Shadow DOM event-retargeting.

**When it occurs.** Custom interactivity beyond simple display.

**How to avoid.** Attach the event listener directly to the
`<tableau-viz>` element after creation, not to a parent container.
Use the `lwc:dom="manual"` template directive on the container.

---

## Gotcha 7: Tableau Embedding API loads its own scripts that may need CSP

**What happens.** The Embedding API SDK transitively loads
Tableau-side scripts (telemetry, analytics, viz rendering). These
need `script-src` in CSP, which Lightning's CSP may block.

**When it occurs.** Strict CSP environments.

**How to avoid.** Read the Embedding API CSP requirements
documentation; configure Trusted Sites / CSP appropriately. In
some scenarios, using the Tableau Viz LWC (rather than custom
embed) is simpler because Salesforce has pre-cleared its CSP needs.

---

## Gotcha 8: Tableau Pulse is not a drop-in replacement for dashboards

**What happens.** Stakeholder asks for "Pulse instead of the
dashboard"; team swaps the embed and discovers Pulse is metric-
focused, not free-form-dashboard.

**When it occurs.** Confusion about what Pulse is for.

**How to avoid.** Pulse = AI-summarized metrics; suitable for
"what's the trend on KPI X?". Dashboards = free-form analytical
canvas. They complement; one is not a substitute for the other.

---

## Gotcha 9: Filter parameters require exact field-name match

**What happens.** Embed passes `viz-filter field="AccountId"` but
the Tableau data source uses `Account ID` (with a space). Filter
silently does not apply.

**When it occurs.** Tableau data source field names that do not
match Salesforce field API names.

**How to avoid.** Use the exact Tableau field name (case and
whitespace). Audit by opening the Tableau view in author mode and
copying the field name verbatim.
