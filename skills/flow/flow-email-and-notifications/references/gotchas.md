# Gotchas — Flow Email and Notifications

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Send Custom Notification Silently Fails When You Pass Email Addresses as recipientIds

**What happens:** The Send Custom Notification action accepts a Text Collection for `recipientIds`. If the collection contains email address strings instead of 15-char or 18-char Salesforce User IDs, the action either silently delivers nothing or throws a runtime fault, depending on how the platform validates the input. No compile-time warning appears in Flow Builder.

**When it occurs:** Any time a builder queries a Contact or a custom field that holds an email address and assigns that value to the recipient collection. Common when the requirement is worded as "notify the contact" and the builder conflates email notification with in-app notification.

**How to avoid:** Always source the recipient value from a User record's `Id` field. If the requirement is to notify an external contact, switch to the Send Email action — in-app custom notifications are only deliverable to Salesforce Users (internal or Experience Cloud).

---

## Gotcha 2: Exceeding the 10,000 Notification Actions Per Hour Org Limit Drops Notifications Silently — It Does Not Fault

**What happens:** An org can run 10,000 notification actions per hour. This is not a per-flow or per-user limit. The important part is the failure mode, which is the opposite of what practitioners expect: Salesforce documents that once the limit is crossed, "no more notifications are sent in that hour, and all unsent notifications are lost. Notification actions resume in the next hour." The action does **not** throw a fault, so a fault connector never fires and a record-triggered flow is never rolled back. If 10,250 notification actions fire between 4:00 and 4:59, the first 10,000 run and the remaining 250 are silently discarded; processing resumes at 5:00.

**When it occurs:** High-volume record-triggered flows (e.g., triggered on every order or support ticket) can exceed this limit during peak hours or after a bulk data load. Each notification can target up to 10,000 recipients, so the cap is on *actions*, not on delivered notifications — one action fanned out to 5,000 users costs 1, not 5,000.

**How to avoid:** Calculate worst-case notification-action volume before activating a flow against high-volume objects. Do **not** rely on a fault connector to detect exhaustion — there is no exception to catch. If loss is unacceptable, write your own counter (a Custom Metadata threshold plus a custom object tally, or Event Monitoring) or route high-volume scenarios through email or a queued/scheduled flow that spreads the actions across hours. Note separately that an org retains the most recent 1,000,000 custom notifications for the notification tray (trimmed back to 1,000,000 once 1,200,000 accumulate).

---

## Gotcha 3: Flow's Send Email Action Does Not Support Classic Email Templates

**What happens:** A practitioner opens the Send Email action configuration expecting a template picker similar to Email Alerts. There is no such field. The action accepts a body string or a reference to a Flow Text Template resource. Attempts to reference a Classic Email Template ID are not possible through the Send Email action.

**When it occurs:** Any project where the requirement includes "use our existing email templates" and those templates are Classic or Letterhead templates managed in Setup.

**How to avoid:** If the requirement truly requires a Classic Email Template (e.g., for brand consistency via letterhead, or for managed templates edited by non-developers), use an Email Alert (invocable from Flow) instead of the Send Email action. If dynamic content is needed with a managed template, combine an Email Alert with Flow variables passed as merge fields in the template.

---

## Gotcha 4: SMS Action Disappears Without Digital Engagement License

**What happens:** The Send SMS action is absent from the Flow Builder action palette in orgs that do not have the Digital Engagement (Messaging) add-on. There is no placeholder, no disabled button, no error message explaining why. The action simply does not exist.

**When it occurs:** Any org where a builder is trying to implement SMS notifications without checking licensing first. Builders may spend significant time searching the action palette, suspecting a permission or configuration issue, without finding the root cause.

**How to avoid:** Before designing an SMS path in a flow, confirm in Setup > Messaging or with Salesforce licensing that Digital Engagement is provisioned. If it is not, assess whether an outbound Apex HTTP callout to a third-party SMS API is the right alternative — and if so, document that callouts from record-triggered flows require a different execution pattern (such as a Queueable or Platform Event handoff) to avoid callout-from-DML errors.

---

## Gotcha 5: Post Message to Slack Faults If the Workspace Connection Expires or Is Revoked

**What happens:** The Salesforce for Slack integration uses OAuth tokens tied to a connected workspace. If the workspace connection is revoked, the Slack app is uninstalled from the Slack side, or the OAuth token expires and is not refreshed, the Post Message to Slack action faults at runtime with an authentication error. The Flow continues to appear valid in Flow Builder — no design-time error appears.

**When it occurs:** After a Slack workspace admin removes the Salesforce app, after a Salesforce admin disconnects the workspace in Setup, or in sandboxes refreshed from production where the OAuth connection does not carry over.

**How to avoid:** Add a fault connector to every Post Message to Slack action. Monitor the Slack connected app status in Setup > Slack > Connected Slack Apps. For production orgs, set up a scheduled check or admin alert when the connection is disrupted. In sandboxes, verify the Slack connection independently before testing flows that use Slack actions.
