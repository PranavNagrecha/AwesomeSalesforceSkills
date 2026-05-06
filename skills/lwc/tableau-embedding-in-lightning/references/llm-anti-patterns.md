# LLM Anti-Patterns — Tableau Embedding in Lightning

Mistakes AI assistants commonly make when generating Tableau-in-
Lightning embedding code.

---

## Anti-Pattern 1: Hardcoding the Tableau host URL in the LWC

**What the LLM generates.**

```javascript
viz.src = 'https://prod-eu-a.online.tableau.com/views/Sales/Dashboard';
```

**Why it happens.** Examples in docs use specific URLs.

**Correct pattern.** Read the host from a Custom Metadata record.
Tableau Cloud region migrations change host URLs; hardcoded values
break.

**Detection hint.** Any LWC literal Tableau URL outside of a
config-driven pattern.

---

## Anti-Pattern 2: Long-lived JWT for embed token

**What the LLM generates.**

```apex
JWT.setExpiration(System.now().addHours(24));
```

**Why it happens.** Comfortable expiry minimizes regeneration.

**Correct pattern.** 5-minute expiry. The token is generated
per-request from Apex; there is no UX reason for long-lived
tokens, and short expiry mitigates leak / replay.

**Detection hint.** Any JWT generation with expiry over 1 hour.

---

## Anti-Pattern 3: Missing Trusted Sites configuration in setup instructions

**What the LLM generates.**

> Drop the LWC on the Lightning page. The Tableau dashboard will
> appear.

**Why it happens.** The LLM treats embed as drop-in.

**Correct pattern.** Setup -> CSP Trusted Sites must include the
Tableau host URL with `Frame-Source` enabled. Without it, the
iframe is blocked by CSP and the component renders empty.

**Detection hint.** Any embedding instructions that do not mention
Trusted Sites.

---

## Anti-Pattern 4: Storing the Connected App secret in Apex source

**What the LLM generates.**

```apex
private static final String SECRET = 'abc123def...';
```

**Why it happens.** Quick prototype shape.

**Correct pattern.** Store in Named Credential or a protected
Custom Metadata field. Apex reads the secret at request time.

**Detection hint.** Any literal secret string in Apex source.

---

## Anti-Pattern 5: Anonymous embed for "internal" dashboards

**What the LLM generates.**

> Use anonymous embed; no auth needed for internal dashboards.

**Why it happens.** Anonymous embed is the simplest option.

**Correct pattern.** Anonymous embed exposes the dashboard URL to
anyone. "Internal" is not the same as "secure" — the URL leaks via
browser history, screenshots, support cases. Use JWT or SAML SSO.

**Detection hint.** Any "anonymous embed" recommendation for
non-public data.

---

## Anti-Pattern 6: RLS via JavaScript filter (client-side enforcement)

**What the LLM generates.**

```javascript
const filter = document.createElement('viz-filter');
filter.field = 'Owner';
filter.value = currentUserEmail;
viz.appendChild(filter);
```

> Now each user sees only their data.

**Why it happens.** Conflating UI-level filter with security-level
filter.

**Correct pattern.** UI filters can be removed client-side
(browser dev tools, modified URL). Real RLS is enforced on the
Tableau side via a data-source filter that uses
`USERNAME()`. Salesforce passes the user identity via JWT; Tableau
enforces.

**Detection hint.** Any RLS recommendation that puts the security
control in the LWC's filter rather than on the Tableau data
source.

---

## Anti-Pattern 7: Expecting `<tableau-viz>` events to bubble like normal DOM events

**What the LLM generates.**

```javascript
this.template.querySelector('.tableau-container').addEventListener(
    'firstinteractive',
    handler
);
```

**Why it happens.** Generic DOM-listening pattern.

**Correct pattern.** Attach the listener directly to the
`<tableau-viz>` element. LWC Shadow DOM retargets events; listening
on a parent does not always fire.

**Detection hint.** Tableau viz events listened on a parent
container rather than on the viz element directly.
