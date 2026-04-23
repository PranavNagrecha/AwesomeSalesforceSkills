# Gotchas — Apex Custom Notifications From Apex

Non-obvious Salesforce platform behaviors that cause real production problems.

## Gotcha 1: Notification Type Id Is Org-Specific

**What happens:** Code hardcoded with a production Id fails with `INVALID_NOTIFICATION_TYPE_ID` after sandbox refresh.

**When it occurs:** Any deploy from one org to another where the developer hardcoded the Id instead of querying by DeveloperName.

**How to avoid:** Always resolve via `SELECT Id FROM CustomNotificationType WHERE DeveloperName = '...'`. Cache at class scope after the first resolution.

---

## Gotcha 2: Deactivated Users Silently Swallow Notifications

**What happens:** `send()` succeeds without exception, but the user never receives the notification because they are deactivated.

**When it occurs:** Any dynamic recipient resolution that doesn't filter `User.IsActive = true`.

**How to avoid:** Pre-filter `User.IsActive = true` when resolving recipients from SOQL. There is no post-send delivery receipt.

---

## Gotcha 3: Mobile Push Truncates The Body

**What happens:** A developer writes a 500-character body and verifies it in the web bell icon. Mobile users see only the first ~200 characters.

**When it occurs:** Sends to users with Salesforce Mobile app enabled.

**How to avoid:** Keep the body under 190 characters with an ellipsis. Put detail on the target record so the user can drill in.

---

## Gotcha 4: 500-Recipient Cap Per `send()` Call

**What happens:** A `send(Set<String>)` with 800 user Ids throws `LimitException: CustomNotification: Recipient count exceeds limit`.

**When it occurs:** Any broadcast use case larger than 500.

**How to avoid:** Split the audience into batches of 500 and call `send()` per batch. Or use a Queue/Group Id that expands server-side (no explicit limit).

---

## Gotcha 5: Custom Notifications Have No Apex-Accessible History

**What happens:** A QA team wants to verify "did the notification go out?" — there is no `CustomNotificationLog` object. The platform does not persist sent notifications.

**When it occurs:** Audit, compliance, or debugging investigations.

**How to avoid:** If you need proof, write your own log row at send time: `insert new Notification_Log__c(...)`.

---

## Gotcha 6: `setTargetId` Is Required For A Clickable Notification

**What happens:** A notification arrives but clicking it does nothing or opens the home page.

**When it occurs:** Developers omit `setTargetId` thinking it's optional.

**How to avoid:** Always set `setTargetId` to the record the user should land on.

---

## Gotcha 7: Test Context Does Not Deliver Notifications

**What happens:** A test that asserts a notification was received to a mocked email inbox always fails.

**When it occurs:** Trying to assert delivery in `@IsTest` context.

**How to avoid:** Assert only that `send()` did not throw. Wrap the send in a method and verify it was called; use dependency injection to swap a mock sender.

---

## Gotcha 8: Queue Ids Look Like Group Ids

**What happens:** Developers validate recipients with `id.getSobjectType() == User.SObjectType` and reject Queue Ids thinking they are invalid.

**When it occurs:** Id-type gating code.

**How to avoid:** Queues are `Group` records with `Type = 'Queue'`. Allow `Group.SObjectType` alongside `User.SObjectType` in recipient validation.
