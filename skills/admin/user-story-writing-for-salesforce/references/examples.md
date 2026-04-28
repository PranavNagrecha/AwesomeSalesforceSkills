# Examples — User Story Writing For Salesforce

Three worked examples covering: (a) a sales-rep mobile story with declarative implementation, (b) an Apex-required story with multi-system integration, and (c) an XL parent split into three child stories.

---

## Example 1: Mobile Story With Declarative Implementation

**Context:** Field sales reps log meetings on the Salesforce mobile app while on-site. Today they enter notes manually after the meeting; many forget. Marketing needs the contact-touch data for nurture campaigns.

**Problem without this skill:** The BA writes "As a user, I want a button to log a meeting." No persona, no outcome, no AC. The build agent has no idea whether to build a quick action, a flow, or an LWC.

**Solution — story markdown:**

```markdown
## US-FSALES-018 — Log Field Meeting From Mobile

**As a** Field Sales Rep with the Field Sales User profile,
**I want** a one-tap quick action on the Account record page in the Salesforce mobile app to log a meeting with date, attendees, and notes,
**So that** Marketing can launch a follow-up nurture campaign within 24 hours of every field touch.

**Acceptance Criteria:**

- *Given* a Field Sales Rep is viewing an Account on the mobile app,
  *When* they tap the "Log Meeting" quick action,
  *Then* a screen appears with prefilled Account, today's date editable, an attendee multi-select, and a notes textarea.

- *Given* the rep submits with all required fields populated,
  *When* the action saves,
  *Then* a Task is created with Subject "Field Meeting", related to the Account, OwnerId = current user, and ActivityDate = the chosen date.

- *Given* the rep submits with notes empty,
  *When* the action saves,
  *Then* the screen shows the validation error "Meeting notes are required for nurture follow-up" and no Task is created.

**Complexity:** M
```

**Handoff JSON:**

```json
{
  "story_id": "US-FSALES-018",
  "title": "Log Field Meeting From Mobile",
  "as_a": "Field Sales Rep with the Field Sales User profile",
  "i_want": "a one-tap quick action on the Account record page in the Salesforce mobile app to log a meeting with date, attendees, and notes",
  "so_that": "Marketing can launch a follow-up nurture campaign within 24 hours of every field touch",
  "acceptance_criteria": [
    "Given a Field Sales Rep is viewing an Account on the mobile app, When they tap the Log Meeting quick action, Then a screen appears with prefilled Account, today's date editable, an attendee multi-select, and a notes textarea.",
    "Given the rep submits with all required fields populated, When the action saves, Then a Task is created with Subject Field Meeting, related to the Account, OwnerId = current user, and ActivityDate = the chosen date.",
    "Given the rep submits with notes empty, When the action saves, Then the screen shows the validation error Meeting notes are required for nurture follow-up and no Task is created."
  ],
  "complexity": "M",
  "recommended_agents": ["flow-builder", "permission-set-architect"],
  "recommended_skills": ["flow/screen-flows", "admin/quick-actions"],
  "dependencies": [],
  "notes": "Declarative-only. Screen Flow + quick action. No Apex needed at this size."
}
```

**Why it works:** Persona is grounded (Field Sales Rep / Field Sales User profile). The `So That` names a concrete outcome (Marketing nurture within 24h). ACs include happy + sad path. The story does *not* prescribe "use a Screen Flow" in the body — the build agent sees `recommended_skills` and decides.

---

## Example 2: Apex-Required Story With Multi-System Integration

**Context:** Finance needs Salesforce Opportunities to push to NetSuite when Stage = "Closed Won" and amount > $250k for revenue recognition. The integration is bidirectional — NetSuite returns an invoice ID that must be stored on the Opportunity.

**Problem without this skill:** The BA writes "Sync big deals to NetSuite." No persona, no AC, no idea what "sync" means or what the rep sees when it fails.

**Solution — story markdown:**

```markdown
## US-FIN-073 — High-Value Closed-Won Opportunity Syncs To NetSuite

**As a** Revenue Operations Analyst with the RevOps Manager permission set,
**I want** Opportunities that close at $250k or above to push to NetSuite automatically and receive an invoice ID back,
**So that** revenue recognition happens in the same business day instead of the current 3-day manual lag.

**Acceptance Criteria:**

- *Given* an Opportunity with Amount >= 250000,
  *When* StageName is set to "Closed Won" and saved,
  *Then* an outbound message is sent to NetSuite within 5 minutes.

- *Given* NetSuite returns a successful invoice creation,
  *When* the response is received,
  *Then* the Opportunity's NetSuite_Invoice_Id__c field is populated and Sync_Status__c = "Synced".

- *Given* NetSuite returns an error or times out after 30 seconds,
  *When* the failure is logged,
  *Then* Sync_Status__c = "Failed", a Case is created with Origin = "Integration" and Owner = the Integration Failures queue, and the rep sees a banner on the Opportunity record page.

- *Given* an Opportunity with Amount < 250000,
  *When* it is set to Closed Won,
  *Then* no NetSuite call is made and Sync_Status__c remains blank.

**Complexity:** L
```

**Handoff JSON:**

```json
{
  "story_id": "US-FIN-073",
  "title": "High-Value Closed-Won Opportunity Syncs To NetSuite",
  "as_a": "Revenue Operations Analyst with the RevOps Manager permission set",
  "i_want": "Opportunities that close at $250k or above to push to NetSuite automatically and receive an invoice ID back",
  "so_that": "revenue recognition happens in the same business day instead of the current 3-day manual lag",
  "acceptance_criteria": [
    "Given an Opportunity with Amount >= 250000, When StageName is set to Closed Won and saved, Then an outbound message is sent to NetSuite within 5 minutes.",
    "Given NetSuite returns a successful invoice creation, When the response is received, Then the Opportunity's NetSuite_Invoice_Id__c field is populated and Sync_Status__c = Synced.",
    "Given NetSuite returns an error or times out after 30 seconds, When the failure is logged, Then Sync_Status__c = Failed, a Case is created with Origin = Integration and Owner = the Integration Failures queue, and the rep sees a banner on the Opportunity record page.",
    "Given an Opportunity with Amount < 250000, When it is set to Closed Won, Then no NetSuite call is made and Sync_Status__c remains blank."
  ],
  "complexity": "L",
  "recommended_agents": ["object-designer", "flow-builder", "permission-set-architect"],
  "recommended_skills": ["integration/named-credentials", "apex/queueable-callouts", "flow/record-triggered-flows"],
  "dependencies": ["US-FIN-070 (NetSuite Named Credential exists)", "US-FIN-071 (NetSuite_Invoice_Id__c field exists)"],
  "notes": "Apex Queueable + callout required (governor limits on synchronous callouts in record-triggered flow). The story does NOT prescribe Apex — the build agent decides per integration-pattern-selection.md."
}
```

**Why it works:** Persona is grounded. Outcome is dated (same-day vs 3-day lag). Failure path is fully specified (Case + queue + banner). Handoff names the chain (object-designer for the field, flow-builder for the trigger, perm-set-architect for the queue access). Critically, the *story body* doesn't say "use a Queueable" — that's left to the build agent per the integration decision tree.

---

## Example 3: XL Parent Split Into Three Children

**Context:** Parent epic "Quote-to-cash automation for new sales process" came in at XL. We split it.

**Parent (rejected — XL, not committable):**

```markdown
## US-Q2C-PARENT — Quote-to-cash automation

As a Sales Rep, I want quote-to-cash automated, so that we close faster.
```

This fails INVEST on every axis: persona is generic, the I-Want is an epic, no ACs, no sad path, can't be sized.

**Split rationale:** Workflow-step split (per Pattern in SKILL.md). Three discrete workflow stages: quote generation, approval routing, contract handoff. Each ships independently, each demos independently.

### Child 1 — US-Q2C-101: Generate Quote PDF From Opportunity

```markdown
**As a** Inside Sales Rep with the Sales User profile,
**I want** a "Generate Quote" button on the Opportunity that produces a branded PDF using current line items,
**So that** I can send a customer-ready quote in under 60 seconds instead of the current 8-minute Word-template process.

**Acceptance Criteria:**

- *Given* an Opportunity with at least one OpportunityLineItem,
  *When* the rep clicks "Generate Quote",
  *Then* a PDF attaches to the Opportunity with the company logo, line items, total, and a unique quote number.

- *Given* an Opportunity with zero line items,
  *When* the rep clicks "Generate Quote",
  *Then* an inline error appears: "Add at least one product before generating a quote." No PDF is created.

**Complexity:** M
```

```json
{
  "story_id": "US-Q2C-101",
  "complexity": "M",
  "recommended_agents": ["flow-builder", "permission-set-architect"],
  "recommended_skills": ["flow/screen-flows", "admin/quick-actions"],
  "dependencies": []
}
```

### Child 2 — US-Q2C-102: Discount Approval Routing For Quotes Over 15%

```markdown
**As a** Sales Manager with the Sales Manager profile,
**I want** quotes with discount > 15% to enter an approval queue routed to me,
**So that** margin policy is enforced without blocking sub-15% deals.

**Acceptance Criteria:**

- *Given* a Quote with Discount__c > 15,
  *When* the rep submits for approval,
  *Then* the record locks and the manager receives an approval email + bell notification.

- *Given* a Quote with Discount__c <= 15,
  *When* the rep submits,
  *Then* the Quote auto-approves and Status = "Approved" without manager involvement.

- *Given* a manager rejects an approval,
  *When* the rejection is recorded,
  *Then* the Quote returns to the rep with Status = "Rejected" and a comment field populated.

**Complexity:** M
```

```json
{
  "story_id": "US-Q2C-102",
  "complexity": "M",
  "recommended_agents": ["flow-builder", "permission-set-architect"],
  "recommended_skills": ["flow/approval-processes", "admin/approval-routing"],
  "dependencies": ["US-Q2C-101"]
}
```

### Child 3 — US-Q2C-103: Push Approved Quote To Contract Object

```markdown
**As a** Sales Operations Specialist with the Sales Ops permission set,
**I want** an approved Quote to auto-create a Contract record with the customer, value, and effective date populated,
**So that** the legal team starts redlining within 1 hour of approval instead of the current 2-day handoff lag.

**Acceptance Criteria:**

- *Given* a Quote where Status = "Approved",
  *When* the approval finalizes,
  *Then* a Contract is created with AccountId, ContractTerm, StartDate = today, and Status = "Draft - Legal Review".

- *Given* a Quote where Status changes from Approved to Rejected,
  *When* the change is saved,
  *Then* the related Contract is set to Status = "Cancelled" and a Task is created for the Sales Ops queue.

**Complexity:** M
```

```json
{
  "story_id": "US-Q2C-103",
  "complexity": "M",
  "recommended_agents": ["object-designer", "flow-builder"],
  "recommended_skills": ["flow/record-triggered-flows", "admin/object-relationships"],
  "dependencies": ["US-Q2C-102"]
}
```

**Why the split works:** Each child is sized M, fits a sprint, has a real persona, demos on its own, and chains via `dependencies[]`. Shipping order: 101 → 102 → 103. Stakeholder gets value after each ship — they don't have to wait for the whole quote-to-cash to land.

---

## Anti-Pattern: The "As A User" Vacuum Story

**What practitioners do:** Write "As a user, I want X, so that the system works."

**What goes wrong:** No grounded persona means sharing rules can't be reasoned about, FLS is a guess, and the build agent has to call the BA back to ask "which user?" — defeating the purpose of the handoff.

**Correct approach:** Force the persona into Salesforce terms — profile, permission set, or role. If the answer is genuinely "everyone," the story is probably an org-wide setting (OWD, login policy) and not a user story at all.
