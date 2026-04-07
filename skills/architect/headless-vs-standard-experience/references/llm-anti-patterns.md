# LLM Anti-Patterns — Headless vs Standard Experience

Common mistakes AI coding assistants make when advising on Experience Cloud architecture decisions.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending LWR Without Flagging the Republish Requirement

**What the LLM generates:** A recommendation to migrate from Aura to LWR focused entirely on performance gains (50% faster, CDN caching, etc.) without mentioning that every component change requires an explicit Publish action before users see it.

**Why it happens:** LLMs are trained on articles that emphasize the performance story. The publish model is an operational detail that appears in LWR limitation docs, not benchmark posts. It gets omitted because it does not sound like a "feature."

**Correct pattern:**

```
Recommendation: Migrate to LWR for the performance and roadmap benefits.

Operational requirement: LWR uses a publish-gated change model. Every deployment of
component code or content changes must be followed by a Publish action (via Experience
Builder UI or the publish REST endpoint) before changes are visible to end users.
This must be added to your CI/CD pipeline and release runbooks.
```

**Detection hint:** Any LWR recommendation that does not include the word "publish" or "Publish" is incomplete.

---

## Anti-Pattern 2: Claiming Aura Components Can Be Wrapped to Work on LWR

**What the LLM generates:** Advice suggesting that existing Aura components can be wrapped in an LWC adapter, compatibility shim, or `lightning:container` to work on an LWR site without a full rewrite.

**Why it happens:** LLMs generalize from web framework compatibility patterns (React wrappers for Angular components, etc.) and from Salesforce's own guidance that LWC can call Apex in both engines. The specific incompatibility of Aura components on LWR is a hard platform constraint, not an adapter problem.

**Correct pattern:**

```
Aura components are not supported on LWR sites. There is no compatibility layer,
wrapper, or shim. Each Aura component used on the current site must be rewritten
as a Lightning Web Component (LWC) before the LWR site can be launched.

Audit required: Count all custom Aura components and AppExchange Aura components.
Each requires a full rewrite. This is the primary migration cost driver.
```

**Detection hint:** Any response containing phrases like "wrap your Aura component," "use it as-is," or "Aura compatibility" in the context of LWR migration is incorrect.

---

## Anti-Pattern 3: Treating LWS and Locker Service as Equivalent

**What the LLM generates:** Advice that existing LWC components and third-party libraries tested under Aura/Locker Service will work unchanged on LWR under Lightning Web Security (LWS).

**Why it happens:** Both Locker Service and LWS provide JavaScript isolation. LLMs conflate them as "the Salesforce security sandbox" and assume forward compatibility. The mechanisms are different: Locker wraps runtime APIs; LWS enforces at module import time.

**Correct pattern:**

```
LWR uses Lightning Web Security (LWS), not Locker Service. These are different
isolation mechanisms. Third-party libraries that worked under Locker may fail
under LWS, particularly those using:
- eval() or new Function(string)
- Direct prototype chain manipulation
- window.__proto__ access

Test all third-party dependencies in an LWR sandbox before committing to the migration.
```

**Detection hint:** Any response that says "your existing LWC components will work on LWR without changes" without qualifying third-party library compatibility is potentially incomplete.

---

## Anti-Pattern 4: Recommending Headless for Performance Without Justifying UX Constraints

**What the LLM generates:** A recommendation to go headless (React/Vue custom frontend) primarily because "headless is faster" or "gives better performance" compared to LWR, without identifying a specific UX constraint that LWR cannot satisfy.

**Why it happens:** "Headless = modern = fast" is a common web development narrative. LLMs trained on frontend engineering content overweight this framing. In reality, LWR's CDN-cached static layer closes most of the performance gap. Headless for performance alone is an expensive overengineering decision.

**Correct pattern:**

```
Headless is the right choice when:
- The required UX cannot be delivered within Experience Builder's layout and component model
- The client is a native mobile app that cannot render WebView-based pages
- The team is a full-stack web team with no Salesforce skills and the business justifies the cost

LWR closes ~50% of the Aura performance gap via CDN caching. For standard portal
use cases, LWR performance is sufficient without the full custom frontend overhead.
Recommend headless only when there is a specific, documented UX or client constraint
that LWR cannot satisfy.
```

**Detection hint:** Any headless recommendation where the justification is purely "better performance" or "more flexibility" without naming a specific constraint should be challenged.

---

## Anti-Pattern 5: Assuming Headless Inherits Experience Cloud Security Controls

**What the LLM generates:** Guidance that a headless frontend "backed by an Experience Cloud site" automatically enforces Experience Cloud sharing rules, guest user profiles, or audience-based visibility configured in Experience Builder.

**Why it happens:** "Headless Experience Cloud" sounds like a variant of Experience Cloud. LLMs associate Experience Cloud with its security model and transfer that association incorrectly to headless frontends that merely connect to Salesforce APIs.

**Correct pattern:**

```
A headless frontend using Connected App + Salesforce APIs does NOT inherit
Experience Builder security controls (sharing rules, guest profiles, audience
targeting). Security must be enforced explicitly at the API layer:

- Connected App scopes control what APIs are accessible
- Apex REST methods must use `with sharing` to enforce record-level security
- Object and field permissions are governed by the running user's profile/permission sets

There is no Experience Cloud security configuration to fall back on.
Design the access control model explicitly for every endpoint.
```

**Detection hint:** Any headless architecture guidance that mentions "Experience Cloud sharing rules will apply" or omits explicit API-level access control design is incorrect.

---

## Anti-Pattern 6: Giving an Architecture Recommendation Without Asking About Existing Aura Component Count

**What the LLM generates:** A direct LWR migration recommendation without first asking how many custom Aura components exist on the current site — the single most important input to migration effort estimation.

**Why it happens:** LLMs default to answering the question asked ("should we migrate to LWR?") rather than gathering the context needed to answer it accurately. The instinct is to be helpful by giving a direct answer.

**Correct pattern:**

```
Before recommending an Aura-to-LWR migration timeline or effort level:

1. Ask: How many custom Aura components are used on the current site?
2. Ask: Are any AppExchange components Aura-only?
3. Ask: Which third-party JavaScript libraries are used?

Each Aura component requires a full LWC rewrite. A site with 3 components is a
very different migration than a site with 30. No timeline estimate is credible
without this count.
```

**Detection hint:** Any LWR migration recommendation that includes effort estimates without referencing Aura component count is speculative and should not be trusted.
