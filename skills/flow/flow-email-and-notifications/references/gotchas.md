# Gotchas — Flow Email and Notifications

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Send Custom Notification Silently Fails When You Pass Email Addresses as recipientIds

**What happens:** The Send Custom Notification action accepts a Text Collection for `recipientIds`. If the collection contains email address strings instead of 15-char or 18-char Salesforce User IDs, the action either silently delivers nothing or throws a runtime fault, depending on how the platform validates the input. No compile-time warning appears in Flow Builder.

**When it occurs:** Any time a builder queries a Contact or a custom field that holds an email address and assigns that value to the recipient collection. Common when the requirement is worded as "notify the contact" and the builder conflates email notification with in-app notification.

**How to avoid:** Always source the recipient value from a User record's `Id` field. If the requirement is to notify an external contact, switch to the Send Email action — in-app custom notifications are only deliverable to Salesforce Users (internal or Experience Cloud).

---

## Gotcha 2: The 1,000 Custom Notifications Per Hour Org Limit Applies Across All Flows

**What happens:** Salesforce enforces a limit of 1,000 custom notifications per hour at the org level. This is not a per-flow or per-user limit. When the limit is crossed, the Send Custom Notification action faults for every subsequent invocation in that hour, regardless of which flow triggered it.

**When it occurs:** High-volume record-triggered flows (e.g., triggered on every order or support ticket) can exceed this limit quickly during peak hours or after a bulk data load. The failure shows up as a fault on the action element.

**How to avoid:** Calculate worst-case notification volume before activating a flow against high-volume objects. Add a fault connector to every Send Custom Notification action. Consider batching notifications through a scheduled flow or using email for high-volume scenarios where the hourly cap cannot be avoided.

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
