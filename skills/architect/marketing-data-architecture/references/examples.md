# Examples — Marketing Data Architecture

## Example 1: Normalized Relational DE Model for a Retail B2C Program

**Context:** A retail brand sends post-purchase email sequences. They have three data entities: Contacts (sourced from Salesforce CRM via MC Connect), Orders (sourced from an ERP via SFTP), and Products (sourced from the same ERP). Each send must personalize on the contact's most recent order and the products in that order.

**Problem:** The initial implementation used a single wide DE with one row per contact per order line, containing 180 columns of flattened contact + order + product data. With 8 million rows, Automation Studio Query Activities to build segments exceeded the 30-minute timeout. Updating a product name required re-importing millions of rows.

**Solution:**

Three normalized DEs:

```
Contacts_DE (sendable)
  ContactKey     TEXT(18)   PK
  EmailAddress   EMAIL(254)
  FirstName      TEXT(50)
  LastName       TEXT(50)
  Send Relationship: ContactKey → All Subscribers.Subscriber Key

Orders_DE (non-sendable)
  OrderID        TEXT(20)   PK
  ContactKey     TEXT(18)
  OrderDate      DATE
  TotalAmount    DECIMAL(10,2)
  Status         TEXT(20)

Products_DE (non-sendable)
  LineItemID     TEXT(30)   PK
  OrderID        TEXT(20)
  ProductName    TEXT(100)
  SKU            TEXT(50)
  Quantity       NUMBER
```

Contact Builder Data Relationships defined:
- Contacts_DE.ContactKey → Orders_DE.ContactKey (one-to-many)
- Orders_DE.OrderID → Products_DE.OrderID (one-to-many)

Automation Studio Query Activity to build post-purchase segment (runs after each SFTP import):

```sql
SELECT DISTINCT c.ContactKey, c.EmailAddress, c.FirstName, o.OrderID, o.TotalAmount
INTO PostPurchase_Segment_DE
FROM Contacts_DE c
INNER JOIN Orders_DE o ON c.ContactKey = o.ContactKey
WHERE o.Status = 'Shipped'
  AND o.OrderDate >= DATEADD(day, -1, GETDATE())
```

AMPscript at send time to pull order line items:

```ampscript
SET @rows = LookupRows("Products_DE", "OrderID", @orderID)
SET @count = RowCount(@rows)
FOR @i = 1 TO @count DO
  SET @row = Row(@rows, @i)
  OUTPUT(CONCAT(Field(@row, "ProductName"), " x", Field(@row, "Quantity"), "<br>"))
NEXT @i
```

**Why it works:** Each DE scans only its own rows. The segment query joins two DEs of manageable size instead of scanning one massive wide table. Product name updates require only updating a few rows in Products_DE, not millions of rows in a flat table.

---

## Example 2: MC Connect SDE to Sendable DE Pipeline for a B2B Sales Motion

**Context:** A B2B software company uses Salesforce CRM as the system of record for Contacts and Accounts. Marketing Cloud sends onboarding and renewal emails. The marketing team needs near-real-time sync of CRM contact opt-out status and account tier into Marketing Cloud for audience segmentation.

**Problem:** An earlier implementation exported a CSV from CRM nightly and imported it into Marketing Cloud via SFTP. Contacts who opted out in CRM during the day continued to receive Marketing Cloud sends until the next day's import, creating compliance risk.

**Solution:**

1. MC Connect configured with Contact and Account objects synced in Automatic (triggered) mode.
2. Contact SDE (read-only, synced from CRM): Contact_Salesforce with Id, Email, FirstName, LastName, HasOptedOutOfEmail, AccountId fields selected.
3. Account SDE (read-only): Account_Salesforce with Id, Name, TierSegment__c fields selected.
4. Sendable Contacts DE created (writable):

```
Contacts_Marketing_DE (sendable)
  ContactKey     TEXT(18)   PK
  EmailAddress   EMAIL(254)
  FirstName      TEXT(50)
  LastName        TEXT(50)
  AccountTier    TEXT(20)
  Send Relationship: ContactKey → All Subscribers.Subscriber Key
```

5. Automation Studio Query Activity runs every 15 minutes to refresh the sendable DE from SDEs:

```sql
SELECT
  c.Id          AS ContactKey,
  c.Email       AS EmailAddress,
  c.FirstName,
  c.LastName,
  a.TierSegment__c AS AccountTier
INTO Contacts_Marketing_DE
FROM Contact_Salesforce c
LEFT JOIN Account_Salesforce a ON c.AccountId = a.Id
WHERE c.HasOptedOutOfEmail = 'false'
  AND c.Email IS NOT NULL
```

6. Journey Builder references Contacts_Marketing_DE as the entry source. Because opt-outs in CRM propagate to the SDE within minutes, the 15-minute query refresh reduces compliance exposure to under 15 minutes instead of up to 24 hours.

**Why it works:** MC Connect's near-real-time sync eliminates the daily batch gap. The intermediate Query Activity transforms the read-only SDE into a writable sendable DE that Journey Builder can use as an entry source. The LEFT JOIN to Account_SDE enriches each contact row with account tier at query time rather than requiring a wide flat contact record.

---

## Anti-Pattern: Using Email Address as the Cross-DE Join Key

**What practitioners do:** Build a data model where `EmailAddress` (TEXT 254) is the primary key on the Contacts DE and the foreign key on all attribute DEs (Orders_DE.EmailAddress, Preferences_DE.EmailAddress). The Send Relationship on the sendable DE maps EmailAddress to All Subscribers Email Address field.

**What goes wrong:**
- All Subscribers does not enforce unique email addresses. The same email address can appear on multiple subscriber records with different SubscriberKeys. When this happens, AMPscript LookupRows on EmailAddress returns multiple rows, causing personalization to select data for the wrong subscriber.
- When a contact changes their email address in CRM, the Contact Key in All Subscribers remains the same, but the EmailAddress value changes. All DEs using email as the join key now have orphaned rows with the old address and no connection to the new record.
- Unsubscribe processing uses SubscriberKey as the matching key. If the sendable DE maps to Email Address instead of SubscriberKey, unsubscribe tracking can fail to match the correct subscriber record.

**Correct approach:** Use Contact Key (Salesforce CRM Contact ID, or a stable org-wide unique identifier) as the SubscriberKey value and as the foreign key on all attribute DEs. Define the Send Relationship to map ContactKey → All Subscribers Subscriber Key. Use EmailAddress only as a display or deliverability field, not as a join key.
