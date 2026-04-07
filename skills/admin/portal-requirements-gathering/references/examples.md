# Examples — Portal Requirements Gathering

## Example 1: Requirements Workshop for a B2C Support Portal

**Context:** A B2C software company receives approximately 4,000 inbound support contacts per month across phone, email, and chat. The support director wants to build a customer self-service portal on Experience Cloud to reduce volume. No contact reason data has been collected, and stakeholders are already discussing adding a community forum, idea board, and live chat widget to the portal.

**Problem:** Without contact reason analysis, the team is designing features based on stakeholder preference rather than customer need. The forum and idea board add development scope without contributing to deflection. The team has not decided whether the portal will be public, authenticated, or hybrid, and has not confirmed which license the org currently owns.

**Solution:**

```text
Requirements Workshop Agenda — B2C Support Portal

1. Data Pull (before workshop)
   - Extract 90 days of case records, closed activities, and web form submissions
   - Tag each record with the primary contact reason (use top-level categories, not sub-categories)
   - Categorize each contact reason as Answers, Status, or Action

2. Contact Reason Review (workshop session 1)
   - Present top 10 contact reasons by volume
   - Confirm categorization with support team lead
   - Identify which reasons are already partially deflectable via existing content

3. Access Architecture Decision (workshop session 2)
   - Decide: authenticated-only (customers log in) vs. hybrid (some public pages)
   - If hybrid: list every public page; confirm guest user profile lockdown requirements
   - Record decision; get technical sign-off

4. License Confirmation (workshop session 2)
   - Confirm org has Customer Community or Customer Community Plus licenses
   - If custom objects need selective sharing: Customer Community Plus required
   - Record decision with rationale

5. Top-3 Jobs Definition (workshop session 3)
   - Translate top contact reasons into customer job statements
   - Write success criteria per job
   - Set deflection baseline (current self-service containment rate) and 6-month target

6. Scope Lock (workshop session 4)
   - In-scope: knowledge base, case submission, case status tracking
   - Deferred: community forum, idea exchange, gamification (phase 2 after deflection validated)
   - Out-of-scope: internal agent console, live chat (separate project)
```

**Why it works:** Anchoring the feature list to contact reason data forces the conversation from "what would be nice" to "what will reduce the 4,000 monthly contacts." Explicitly deferring forum and gamification removes scope creep without killing the ideas — they are recorded as deferred, not rejected.

---

## Example 2: PRM Requirements Gathering for a Partner Community

**Context:** A manufacturing company sells through 200+ regional distributors. The sales ops team wants to build a partner portal to enable deal registration, pipeline visibility, and co-marketing asset downloads. The IT team has suggested using Customer Community Plus because the org already has those licenses provisioned.

**Problem:** Customer Community Plus does not provide access to the Lead and Opportunity objects that deal registration and pipeline visibility require. Building PRM on the wrong license will require a full license migration mid-project when the object access gap is discovered during build.

**Solution:**

```text
PRM Requirements Workshop — License and Access Decisions

1. Partner Tier Definition
   - Define partner tiers (e.g., Silver, Gold, Platinum)
   - List what each tier needs to see and do:
     Silver: view product catalog, submit leads
     Gold: Silver + register deals, view pipeline, download co-marketing assets
     Platinum: Gold + view MDF balance, submit MDF requests

2. License Review
   - Required objects: Lead, Opportunity, custom MDF object
   - Customer Community Plus: does NOT include Lead/Opportunity
   - Partner Community: includes Lead and Opportunity — required for this use case
   - Confirm org has Partner Community licenses; if not, submit license procurement request
     before any build work begins

3. Access Architecture
   - All pages authenticated (partners must log in)
   - Partner account hierarchy: Yes — child partner account users should see their
     account's deals but NOT other partners' deals
   - Confirm role hierarchy design: one role per partner tier, scoped to account

4. Content Taxonomy
   - Product enablement: owned by Product Marketing; reviewed quarterly
   - Partner agreements: owned by Legal; reviewed annually
   - Co-marketing assets: owned by Channel Marketing; reviewed per campaign
   - Deal registration form: owned by Sales Ops; reviewed semi-annually

5. Jobs and Success Criteria
   - Job 1: Register a new deal — success: partner can submit registration in < 5 minutes
     without emailing channel manager
   - Job 2: Check pipeline status — success: partner can view open deal statuses
     without calling their channel manager
   - Job 3: Download co-marketing assets — success: partner finds and downloads
     relevant asset in < 2 minutes

6. Deferred Features
   - MDF request workflow (phase 2 — requires custom object build and approval process)
   - Partner leaderboards (phase 2 — after core jobs validated)
```

**Why it works:** Identifying the Lead and Opportunity object requirement in session 1 prevents the license mistake. Catching the wrong license during requirements costs zero effort to fix; catching it during build requires reprovisioning hundreds of partner user records.

---

## Anti-Pattern: Jumping to Template and Theme Selection Before Requirements Are Locked

**What practitioners do:** Stakeholders get excited about the portal and immediately start reviewing Experience Cloud templates (Customer Service template, Partner Central template, Build Your Own) and branding options before access architecture, license type, or top-3 jobs are defined.

**What goes wrong:** Template selection influences what features are available out of the box. Choosing a template that does not match the access model (e.g., selecting Build Your Own for a simple B2C support case without needing full customization) leads to over-engineering. More importantly, stakeholder energy is consumed on visual decisions while critical architectural decisions remain unmade.

**Correct approach:** Template selection is a build-phase decision. During requirements, record only the access model, license type, and feature scope. The template is chosen during design, after the requirements doc is signed off.
