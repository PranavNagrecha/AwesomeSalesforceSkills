# Examples — FlexCard Design Patterns

## Example 1: Account 360 Summary Card

**Context:** A financial services org needs a FlexCard on the Account record page that shows the account tier, assigned CSM, open opportunity count, and a list of the three most recent cases. The card must allow the CSM to launch a "Schedule Follow-Up" OmniScript from the card without navigating away.

**Problem:** The initial design used three separate SOQL data sources — one for Account fields, one for Opportunity count, and one for recent Cases. On busy records, the card rendered noticeably slowly and occasionally timed out under load.

**Solution:**

Consolidate into a single Integration Procedure data source:

```yaml
# Integration Procedure: AccountSummaryCard_IP
# Steps:
#   1. DataRaptor Extract — pull Account fields (Tier, CSM lookup)
#   2. SOQL Action — COUNT open Opportunities WHERE AccountId = {input:recordId}
#   3. SOQL Action — SELECT Id, CaseNumber, Status, Subject FROM Case
#                    WHERE AccountId = {input:recordId}
#                    ORDER BY CreatedDate DESC LIMIT 3
#   Output map:
#     accountTier   -> Step1.Account.Tier__c
#     csmName       -> Step1.Account.CSM__r.Name
#     openOppCount  -> Step2.count
#     recentCases   -> Step3.records
```

FlexCard configuration:
- One data source: Integration Procedure `AccountSummaryCard_IP`, passing `{Record.Id}` as input.
- Default state template: display `{IntegrationProcedure.accountTier}`, `{IntegrationProcedure.csmName}`, `{IntegrationProcedure.openOppCount}`.
- Child FlexCard: iterate over `{IntegrationProcedure.recentCases}`, render `CaseSummaryCard` per row.
- Action button "Schedule Follow-Up": OmniScript Launch, passes `{Record.Id}` and `{IntegrationProcedure.csmName}` as input variables.
- Error state: bind to `{IntegrationProcedure.errorMessage}`, display "Unable to load account summary. Refresh the page or contact support."

**Why it works:** Single IP call eliminates three parallel network round-trips. The IP is independently testable. Child card iteration keeps per-case actions (view, escalate) encapsulated in `CaseSummaryCard`. The OmniScript launch passes full context so the script does not need to re-query the record.

---

## Example 2: Case Management Card with Status-Driven Actions

**Context:** A service cloud team needs a FlexCard on Case record pages that shows current status, priority, and assigned agent. The available actions must change based on status: open cases show "Escalate" and "Reassign"; resolved cases show only "Reopen".

**Problem:** The initial build put all three action buttons in the template and relied on separate card states for Open and Resolved. This required duplicating the entire template into two states, making maintenance difficult when the layout changed.

**Solution:**

Use a single Default state with conditional visibility on individual action elements:

```yaml
# FlexCard: CaseManagementCard
# Data source: SOQL
#   SELECT Id, Status, Priority, Owner.Name FROM Case WHERE Id = :recordId
#
# Template elements:
#   - Field: Case Status    -> {Record.Status}
#   - Field: Priority       -> {Record.Priority}
#   - Field: Assigned To    -> {Record.Owner.Name}
#   - Button "Escalate"
#       Visibility condition: {Record.Status} != 'Closed' AND {Record.Status} != 'Resolved'
#       Action: OmniScript Launch -> EscalateCaseOS
#   - Button "Reassign"
#       Visibility condition: {Record.Status} != 'Closed' AND {Record.Status} != 'Resolved'
#       Action: OmniScript Launch -> ReassignCaseOS
#   - Button "Reopen"
#       Visibility condition: {Record.Status} == 'Resolved' OR {Record.Status} == 'Closed'
#       Action: DataRaptor Turbo Action -> ReopenCaseDR
#
# Saved state: "Case updated successfully."
# Error state: {DataSource.errorMessage} display block
```

**Why it works:** One template covers all status combinations. Conditional visibility is evaluated at render time against live data — no manual state switching required. Adding a new action for a new status value is a one-step change (add button, set condition) rather than editing multiple state templates.

---

## Example 3: Flyout for Related Contact Detail

**Context:** An Account FlexCard lists related Contacts. The team wants users to click a contact name and see a detail panel (phone, email, last activity date) without navigating to the Contact record page.

**Solution:**

Configure a flyout action on the child contact card:

```yaml
# Parent: AccountContactsCard
#   Data source: IP returning { contacts: [{Id, Name, ...}, ...] }
#   Child card: ContactRowCard, iterates over {IntegrationProcedure.contacts}

# Child card: ContactRowCard
#   Template:
#     - Text: {Record.Name}
#     - Action on name click: Flyout
#         Flyout card: ContactDetailFlyoutCard
#         Pass: {Record.Id} as flyoutContactId

# Flyout card: ContactDetailFlyoutCard
#   Data source: SOQL
#     SELECT Name, Phone, Email, LastActivityDate FROM Contact WHERE Id = :flyoutContactId
#   Template: display all four fields
```

**Why it works:** The flyout keeps the user on the Account page, avoids a full navigation event, and loads the detail card data only when the user explicitly clicks — not on initial page load. This deferred loading pattern prevents the parent card from being slowed down by data the user may never request.

---

## Anti-Pattern: Multiple SOQL Data Sources on a Single Card

**What practitioners do:** Add two or three SOQL data sources to a FlexCard because each query is simple and "it's just a SELECT."

**What goes wrong:** Each data source fires an independent network call when the card renders. On a Lightning App Page with multiple FlexCards (e.g., an Account 360 page with four cards), this creates a burst of parallel queries at page load. Under load, cards race, some time out, and the Error state (if not configured) renders blank — appearing to the user as a broken page.

**Correct approach:** When a card needs data from more than one query, build an Integration Procedure that returns a single shaped response. Use one IP data source on the card. The IP is also easier to debug (it has a built-in debugger), cache (IP-level caching), and test in isolation.
