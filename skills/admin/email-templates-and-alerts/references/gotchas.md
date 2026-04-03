# Gotchas: Email Templates and Alerts

---

## Duplicate Automation Causes Duplicate Email

**What happens:** A flow updates a record twice in one transaction, or two different automations react to the same business event. Users receive two or three emails and stop trusting the system.

**When it bites you:** Status changes, approval notifications, and escalation logic.

**How to avoid it:** Design send criteria around the exact transition, not the final field value alone.

**Example:**
```text
Bad trigger: Status = Closed
Better trigger: Status changed from Open to Closed
```

---

## Merge Fields Depend on Correct Record Context

**What happens:** The template references related-object fields that are not available in the email's actual context. The email arrives with blanks or broken copy.

**When it bites you:** Approval emails, custom-object notifications, and heavily related templates.

**How to avoid it:** Test templates with real records and verify every merge field from the actual sending automation.

**Example:**
```text
Template expects {!Opportunity.Account.Name}
Automation sends from a context that does not supply Opportunity
Result: blank merge value
```

---

## Sender Identity Is Operational, Not Cosmetic

**What happens:** Emails come from whichever default sender setup happened to exist. Replies go to the wrong mailbox or fail audit expectations.

**When it bites you:** Customer-facing support mail, legal/compliance notices, and branded operations emails.

**How to avoid it:** Decide the sender explicitly, configure Org-Wide Email Addresses, and test reply handling.

**Example:**
```text
Customer notification should come from support@example.org, not from an individual admin mailbox
```

---

## Transactional Email Tools Get Misused for Marketing

**What happens:** Teams try to use admin-managed templates and alerts for broad recurring outreach. Limits, unsubscribes, and content governance quickly become problems.

**When it bites you:** Newsletters, nurture campaigns, and recurring mass updates.

**How to avoid it:** Keep admin email for transactional or operational communication. Move campaign-style communication to the right platform.

**Example:**
```text
Monthly customer newsletter -> not an Email Alert use case
```
