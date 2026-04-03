# Examples — Global Actions and Quick Actions

## Example 1: Create-Child Object-Specific Quick Action with Pre-filled Lookup

**Context:** A sales team's Account managers frequently need to create new Contacts directly from Account records. The manual flow (New → Contact → type Account Name) is error-prone and slow. The Account Name lookup is often left blank.

**Problem:** Without a quick action, users navigate away from the Account, create a Contact from the Contacts object or list view, and must manually fill in the Account Name lookup. Contacts get created without an Account association roughly 20% of the time.

**Solution:**

1. In Setup → Object Manager → Account → Buttons, Links, and Actions → New Action.
2. Action Type: **Create**. Target Object: **Contact**. Label: `New Contact`. Name: `New_Contact`.
3. Click **Save**, then click **Edit Layout** on the action detail page.
4. In the action layout editor, add: **First Name**, **Last Name**, **Title**, **Phone**, **Email**. Remove all other default fields to keep the form compact.
5. Click **Save** on the action layout.
6. Return to the action detail page. Click **New** under **Predefined Field Values**.
   - Field: `Account Name`
   - Type: Field Reference
   - Value: `{!Account.Name}`
   - Save.
7. Open Object Manager → Account → Page Layouts → [Your Layout]. Drag **New Contact** from the Actions palette into the **Salesforce Mobile and Lightning Experience Actions** section. Save.
8. Test: Open any Account record. Click **New Contact** in the highlights panel action bar. Confirm Account Name is pre-filled and read-only in the dialog.

**Why it works:** The object-specific action runs in the context of the Account record. The predefined value formula `{!Account.Name}` resolves to the current Account's name at runtime, linking the new Contact automatically. Because the field is set via predefined value but removed from the action layout, users cannot accidentally clear it.

---

## Example 2: Update Quick Action for Case Status Change

**Context:** A support team has agents who close cases from a queue list view. The current process requires opening each case, scrolling to the Status field, editing, and saving — approximately 8 clicks. With 50+ cases per day per agent, the friction is significant.

**Problem:** The full record edit page is slow and provides too many editable fields. Inline edit on list views is enabled but agents keep accidentally editing the wrong field.

**Solution:**

1. Setup → Object Manager → Case → Buttons, Links, and Actions → New Action.
2. Action Type: **Update**. Label: `Close Case`. Name: `Close_Case`.
3. Edit the action layout: add only **Status** and **Internal Comments**. Remove everything else.
4. Add a predefined value: Field = `Status`, Value = `Closed` (literal value). This pre-selects Closed but lets agents override if needed.
5. Add to Case page layout in the Salesforce Mobile and Lightning Experience Actions section. Place it as one of the first 3 actions.
6. Test from a Case record — the action opens a small dialog with Status pre-set to Closed and a Comments field. Two clicks to close.

**Why it works:** Update actions modify the current record without navigation. Pre-filling Status to "Closed" reduces the action to a confirm + optional comment. The compact action layout keeps the experience fast.

---

## Example 3: Global Quick Action for Logging Calls from Any Page

**Context:** Sales reps frequently leave Salesforce to make calls, then return and need to log the call. They may return to a dashboard, Chatter feed, or Home — not necessarily to the account they called.

**Problem:** Object-specific Log a Call actions require the rep to first navigate to the Account or Contact record. Reps often log calls to the wrong record or skip logging entirely because the navigation is disruptive.

**Solution:**

1. Setup → Global Actions → New Action.
2. Action Type: **Log a Call**. Label: `Log a Call`. Name: `Log_a_Call`.
3. Edit the action layout: add **Subject**, **Description**, **Date**, **Name** (Who lookup), **Related To** (What lookup). Keep it to 5 fields.
4. Open Setup → Global Publisher Layouts → Global Layout. Drag **Log a Call** into the Global Actions section. Save.
5. Test: From the Salesforce Home page, click the "+" / quick actions button in the global header. Log a Call is available immediately. The rep fills in Subject, Description, and then uses the "Name" and "Related To" lookups to associate the log with the correct Contact and Account.

**Why it works:** Global actions appear in the global header on every Salesforce page. No navigation required. The Who/What lookups let the rep link the activity to the correct record after the fact. This is the standard Salesforce pattern for logging activities outside of a record's detail page.

---

## Anti-Pattern: Adding Fields to Page Layout Expecting Them to Appear in the Action

**What practitioners do:** An admin needs the "Priority" field to appear when users click a "New Case" quick action. The admin opens the Case page layout, adds the Priority field to the layout, and saves. Users still don't see Priority in the quick action form.

**What goes wrong:** The page layout controls the record detail view. The quick action form is governed by the **action layout**, which is an entirely separate configuration on the action itself. Adding a field to the page layout has no effect on what appears inside the quick action dialog.

**Correct approach:** Navigate to Setup → Object Manager → Case → Buttons, Links, and Actions → [Action Name] → Edit Layout. Add the Priority field to the **action layout**. Save there. The field will then appear in the quick action dialog.
