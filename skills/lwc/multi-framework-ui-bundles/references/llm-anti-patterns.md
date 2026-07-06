# LLM Anti-Patterns — Multi-Framework UI Bundles

Common mistakes AI coding assistants make when generating or advising on Salesforce
Multi-Framework UI bundles. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Wrapping React in Visualforce or Lightning Out 1.0

**What the LLM generates:** a Visualforce page with a `<script>` tag loading a React build
from a static resource, or `$Lightning.use()` (Lightning Out 1.0) glue code, presented as
"how to run React on Salesforce."

**Why it happens:** for years those were the only documented paths, so training data
overwhelmingly shows them; the UIBundle runtime is new (API 66.0+).

**Correct pattern:**

```bash
sf template generate ui-bundle   # starter React app in force-app/main/default/uiBundles
```

Package as a `UIBundle` (`.uibundle-meta.xml`) — the app runs natively with platform
authentication, security, and governance built in.

**Detection hint:** `apex:page`, `$Lightning.use`, or "upload the React build as a static
resource" in an answer about React on Salesforce.

---

## Anti-Pattern 2: Hand-rolling OAuth / token management in the app

**What the LLM generates:** jsforce clients, connected-app OAuth flows, refresh-token storage,
or `Authorization: Bearer` headers inside the React code.

**Why it happens:** most "React + Salesforce" training examples are *external* SPAs calling
the REST API, where manual auth is genuinely required.

**Correct pattern:**

```javascript
import { createDataSDK } from '@salesforce/sdk-data';
const sdk = createDataSDK(); // authentication handled automatically — no token code
```

**Detection hint:** `client_id`, `refresh_token`, `jsforce`, or Bearer-header construction in
a UI-bundle codebase.

---

## Anti-Pattern 3: Claiming GA / production availability

**What the LLM generates:** "Multi-Framework is generally available — deploy your React app
to production," or omitting the org restrictions entirely.

**Why it happens:** models pattern-fill maturity labels and default to the happy path;
"introducing X" blog language reads like a GA launch.

**Correct pattern:** state explicitly that Multi-Framework is in **open beta** for **scratch
orgs and sandboxes with English as the org default language**, that **beta apps cannot be
deployed to production orgs**, and that the ACC Web SDK carries its own **Beta** label while
Lightning-page micro-frontend embedding is only a **closed pilot** (Spring 2026).

**Detection hint:** any answer recommending a production deploy, or missing the words
"beta" / "scratch org" / "sandbox" when scoping this capability.

---

## Anti-Pattern 4: Wrong metadata type or API floor

**What the LLM generates:** a manifest listing `LightningComponentBundle`,
`AuraDefinitionBundle`, or an invented `ReactBundle` type for the React app, and/or
`<version>58.0</version>`.

**Why it happens:** `LightningComponentBundle` is the dominant "UI bundle" string in training
data, and old API versions are the statistical default.

**Correct pattern:**

```xml
<types><members>*</members><name>UIBundle</name></types>
<version>67.0</version>  <!-- UIBundle: 66.0+; CustomApplication target: 67.0+ -->
```

**Detection hint:** a React-on-Salesforce manifest without `UIBundle`, or a `<version>` below
`66.0`.

---

## Anti-Pattern 5: Recommending a wholesale LWC → React rewrite

**What the LLM generates:** "now that Salesforce supports React, migrate your Lightning Web
Components to React for consistency."

**Why it happens:** the model generalizes "new framework support" into "framework
replacement," a common web-dev narrative.

**Correct pattern:** Salesforce Multi-Framework **doesn't replace LWC; it runs alongside
it** — existing Lightning Web Components continue to work. Use React where a standalone
app benefits from that ecosystem; keep LWC for Lightning-page work (drag-and-drop placement
of React components in App Builder is unsupported in beta).

**Detection hint:** any "migrate from LWC to React" recommendation, or a plan that removes
working LWC in favor of beta React components on Lightning pages.

---

## Anti-Pattern 6: Rebuilding agent chat instead of embedding ACC

**What the LLM generates:** a bespoke React chat component wired to raw REST endpoints to
"talk to Agentforce," with hand-built streaming and message rendering.

**Why it happens:** "add a chatbot to my React app" pattern-matches to generic
chat-completion integrations the model has seen thousands of times.

**Correct pattern:** embed the **Agentforce Conversation Client (ACC)** — a Lightning Web
Component Interface built on **Lightning Out 2.0** — as a prebuilt conversational UI
container. Interactive outputs render dynamically from **Lightning Types**; customize them
via `agentforce/agentforce-custom-lightning-types`, not by hardcoding components.

**Detection hint:** custom message-bubble components plus direct REST calls where an
Agentforce Employee Agent conversation was requested, with no mention of ACC.
