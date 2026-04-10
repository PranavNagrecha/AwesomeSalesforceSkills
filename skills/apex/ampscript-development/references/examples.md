# Examples — AMPscript Development

## Example 1: Subscriber-Specific Product Recommendations Using LookupOrderedRows

**Context:** A retailer stores product recommendation scores in a DE called `ProductRecs_DE` with fields `SubscriberKey`, `ProductName`, `Score`, and `ImageURL`. Each subscriber has 1–20 rows. The email must render the top 3 recommendations for each subscriber as a visual product grid.

**Problem:** Without AMPscript, every subscriber receives the same static product grid. Using a single `Lookup()` call only retrieves one product. Practitioners unfamiliar with FOR loops try to hardcode three separate `Lookup()` calls with different index filters, which is fragile and fails when a subscriber has fewer than three records.

**Solution:**

```
%%[
SET @subKey = _subscriberkey
SET @recs = LookupOrderedRows("ProductRecs_DE", 3, "Score", "DESC", "SubscriberKey", @subKey)
SET @recCount = RowCount(@recs)
]%%

%%[ IF @recCount > 0 THEN ]%%
<table>
  <tr>
  %%[ FOR @i = 1 TO @recCount DO ]%%
    %%[ SET @rec = Row(@recs, @i) ]%%
    <td>
      <img src="%%=Field(@rec, "ImageURL")=%%" alt="%%=Field(@rec, "ProductName")=%%">
      <p>%%=Field(@rec, "ProductName")=%%</p>
    </td>
  %%[ NEXT @i ]%%
  </tr>
</table>
%%[ ELSE ]%%
<p>Check out our latest products at example.com/shop</p>
%%[ ENDIF ]%%
```

**Why it works:** `LookupOrderedRows()` with count=3 retrieves only the top 3 rows by Score descending, capping the result intentionally rather than relying on `LookupRows()` returning an arbitrary 2,000-row set. The `RowCount > 0` guard ensures the table markup is not emitted when the subscriber has no recommendation records. `Row(@recs, @i)` with `Field()` is the correct pattern for accessing rowset data inside a FOR loop.

---

## Example 2: Multi-Tier Conditional Discount Block in Email Subject and Body

**Context:** A loyalty program sends a monthly email. The subject line must include the subscriber's tier name, and the body must display a tier-specific discount code. Tier data lives in the sendable DE with a field called `LoyaltyTier`. The discount codes are static per tier.

**Problem:** The team initially places a `%%[ SET @tier = ... ]%%` block in the subject line field. This renders the literal block syntax to subscribers rather than the tier value. Additionally, they use a generic preview to test, which shows the subject correctly because personalization is not evaluated — so the bug reaches production.

**Solution:**

Subject line field (inline only):
```
Your %%=AttributeValue("LoyaltyTier")=%% Member Rewards — This Month's Offer Inside
```

Email body AMPscript block:
```
%%[
SET @tier = AttributeValue("LoyaltyTier")
SET @code = ""

IF @tier == "Platinum" THEN
  SET @code = "PLAT30"
ELSEIF @tier == "Gold" THEN
  SET @code = "GOLD20"
ELSEIF @tier == "Silver" THEN
  SET @code = "SILVER10"
ELSE
  SET @code = "WELCOME5"
ENDIF
]%%

<p>Your exclusive discount code: <strong>%%=v(@code)=%%</strong></p>
```

**Why it works:** The subject line uses only `%%= AttributeValue() =%%` inline syntax — Marketing Cloud evaluates inline expressions in subject and preheader fields but ignores block syntax. The body uses a full `%%[ ... ]%%` block to set the discount code variable before rendering it inline with `%%=v(@code)=%%`. The ELSE branch ensures every subscriber receives a fallback code even if `LoyaltyTier` is null or unexpected.

---

## Example 3: Safe Single-Value Lookup With Null Fallback

**Context:** A transactional email needs to display the subscriber's assigned Account Manager name from a `AccountManager_DE` (keyed on `SubscriberKey`). Some subscribers have no assigned manager.

**Problem:** `Lookup()` returns an empty string when no match is found. Without a null/empty check, the email renders "Your account manager is " with no name, which looks broken.

**Solution:**

```
%%[
SET @subKey = _subscriberkey
SET @managerName = Lookup("AccountManager_DE", "ManagerName", "SubscriberKey", @subKey)

IF EMPTY(@managerName) THEN
  SET @managerName = "our support team"
ENDIF
]%%

<p>For questions, contact %%=v(@managerName)=%%.</p>
```

**Why it works:** `EMPTY()` returns true for both null and empty-string returns from `Lookup()`. Guarding with `IF EMPTY() THEN` and providing a fallback string ensures the sentence always reads naturally regardless of data completeness.

---

## Anti-Pattern: Using SSJS for Per-Subscriber Field Personalization

**What practitioners do:** A developer, more comfortable with JavaScript, writes SSJS using `Platform.Load("Core", "1")` and `DataExtension.Init("MyDE").Rows.Lookup([{Name:"SubscriberKey", Value:subKey}])` to retrieve a single field value for personalization in an email body.

**What goes wrong:** SSJS has higher initialization overhead than AMPscript for simple lookups. It requires a `<script runat="server">` block, which is valid in Cloud Pages but adds unnecessary complexity in email content. More critically, SSJS error handling in email content is harder to debug because runtime errors in SSJS blocks can suppress content without a visible subscriber-facing error, while AMPscript errors more often surface in test sends. SSJS is also not available in SMS or push notification content.

**Correct approach:** Use `AttributeValue("FieldName")` for fields in the sendable DE, or `Lookup("DE_Name", "ReturnField", "MatchField", _subscriberkey)` for fields in a related DE. Reserve SSJS for use cases that genuinely require it: REST/SOAP API calls, complex string manipulation unavailable in AMPscript functions, or Cloud Page server-side logic.
