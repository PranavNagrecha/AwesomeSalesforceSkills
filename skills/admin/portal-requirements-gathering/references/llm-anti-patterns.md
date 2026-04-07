# LLM Anti-Patterns — Portal Requirements Gathering

Common mistakes AI coding assistants make when generating or advising on portal requirements gathering for Experience Cloud. These patterns help the consuming agent self-check its own output.

---

## Anti-Pattern 1: Jumping to Template Selection Before Requirements Are Locked

**What the LLM generates:** The AI immediately recommends an Experience Cloud template (Customer Service, Help Center, Partner Central) and begins describing component layout, branding options, and theme settings when asked to help with portal requirements.

**Why it happens:** LLMs associate "portal" with visible UI elements and Experience Cloud template names appear frequently in training data alongside portal planning questions. Template selection is concrete and easy to describe, so the model defaults to it.

**Correct pattern:**
```
Requirements must lock in the following before template selection:
1. Access architecture (public / authenticated / hybrid)
2. License type per audience segment
3. Top-3 high-volume customer jobs
4. Content taxonomy and ownership

Template selection is a build-phase decision made after requirements sign-off.
```

**Detection hint:** Any response that mentions template names (Customer Service, Help Center, Partner Central, Build Your Own) before documenting the access model and license decision is exhibiting this anti-pattern.

---

## Anti-Pattern 2: Recommending the Highest-Tier License by Default

**What the LLM generates:** The AI recommends External Apps or Customer Community Plus as the "safest" or "most flexible" choice without considering the actual object access and sharing requirements of the use case, and without confirming whether the org owns the license.

**Why it happens:** LLMs learn that more flexible licenses avoid future limitations, so they apply a "recommend the most capable option" heuristic. This conflates license flexibility with license fit.

**Correct pattern:**
```
License selection process:
1. List the objects the portal must access (Cases, Knowledge, Opportunities, custom objects)
2. List the sharing requirements (selective sharing on custom objects? partner account hierarchy?)
3. Map requirements to license tier:
   - Customer Community: standard objects, no manual sharing on custom objects
   - Customer Community Plus: adds manual sharing and role hierarchy on custom objects
   - Partner Community: adds Lead and Opportunity; required for PRM
   - External Apps: broadest object access; use only when community licenses are insufficient
4. Confirm the org owns the required license before recommending it
```

**Detection hint:** Any recommendation of External Apps or Customer Community Plus without first listing the specific sharing and object requirements that justify it is exhibiting this anti-pattern.

---

## Anti-Pattern 3: Missing the Contact Reason Analysis Step

**What the LLM generates:** The AI produces a requirements framework that goes directly from "define your audience" to "select features" without including a step to analyze existing support contact volume and categorize contact reasons.

**Why it happens:** Feature lists are easier to generate than data analysis prescriptions. LLMs pattern-match on portal planning templates from practitioner blogs, which often skip the data pull step because it is assumed as prior knowledge.

**Correct pattern:**
```
Step 1 (non-negotiable): Pull 60–90 days of support contact data.
Categorize by contact reason into:
- Answers: customer needed information
- Status: customer needed to check on something
- Actions: customer needed to do something

The Answers/Status/Actions ratio determines the feature priority stack.
Do not define a feature list without this data.
```

**Detection hint:** Any portal requirements framework that starts with audience definition or feature brainstorming without a named data pull step is missing this analysis.

---

## Anti-Pattern 4: Not Differentiating Audience Segments and Applying One License to All

**What the LLM generates:** The AI applies a single license recommendation (e.g., Customer Community) to all portal users — customers, partners, and potentially anonymous visitors — without acknowledging that different audiences require different license types, access models, and data visibility rules.

**Why it happens:** The prompt often says "users" as a single group and LLMs process that as a homogeneous population. Multi-segment license design requires the model to hold multiple license types and access rules simultaneously, which it shortcuts by applying one recommendation.

**Correct pattern:**
```
Audience Segment | Access Model     | License Type
--------------------------------------------------
B2C Customers    | Authenticated    | Customer Community or Customer Community Plus
B2B Account Users| Authenticated    | Customer Community Plus (if sharing needed)
Partners         | Authenticated    | Partner Community
Anonymous Visitors| Public (if any) | Guest User (no license cost; profile lockdown required)

Each segment has its own profile, sharing rules, and data visibility design.
```

**Detection hint:** Any requirements output that assigns a single license type to all portal visitors without listing the distinct audience segments is collapsing this distinction.

---

## Anti-Pattern 5: Including Social and Gamification Features in Phase 1 Scope

**What the LLM generates:** The AI includes idea exchange, chatter, leaderboards, badges, and community forums in the initial portal feature list, treating them as standard portal components rather than phase 2 additions.

**Why it happens:** Salesforce Experience Cloud marketing materials and community showcase content prominently feature social and gamification capabilities. LLMs associate "portal" and "community" with these features and include them as defaults.

**Correct pattern:**
```
Phase 1 scope (core deflection loop only):
- Knowledge base and search (Answers)
- Case status visibility (Status)
- Case submission or transactional self-service (Actions)
- Deflection baseline measurement and reporting

Phase 2 scope (deferred — gate: deflection target met):
- Idea exchange
- Community chatter / discussion boards
- Gamification (badges, leaderboards, reputation scoring)
- Partner forums

Rationale: Social features add scope without contributing to measurable deflection.
Phase 2 is unlocked when Phase 1 deflection target is validated.
```

**Detection hint:** Any phase 1 scope that includes "idea exchange," "gamification," "badges," "leaderboard," or "community forums" before the core deflection loop is defined is exhibiting this anti-pattern.

---

## Anti-Pattern 6: Omitting Content Taxonomy and Ownership

**What the LLM generates:** The AI produces a portal requirements document that defines features (knowledge base, FAQ section, co-marketing assets) without identifying who will own each content type, how content will be reviewed, or how the taxonomy will be structured.

**Why it happens:** Content governance is operational rather than technical, so LLMs focus on platform features and omit the process layer. Content taxonomy questions require understanding of the client's organizational structure, which the model does not have.

**Correct pattern:**
```
For each content type in scope, document:
- Content type name (e.g., Knowledge Articles, Partner Enablement Documents)
- Content owner (the team or role responsible for keeping it current)
- Review cadence (quarterly, annually, per product release)
- Taxonomy: top-level categories and subcategories the portal will use
- Publication workflow: who drafts, who approves, how it gets into the portal

A portal with great features but stale or disorganized content will not achieve deflection goals.
```

**Detection hint:** Any portal requirements document that lists a knowledge base or document library as an in-scope feature without naming a content owner and review cadence is missing this step.
