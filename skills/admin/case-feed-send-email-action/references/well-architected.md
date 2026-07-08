# Well-Architected Notes — Case Feed Send Email Action

## Relevant Pillars

- **Security** — the composer is an outbound egress point for customer data, and the fields that
  govern it are configuration, not code. A BCC defaulted by Apex sends every case reply to a
  third mailbox; a `RelatedToId` default silently associates the message with an account. Treat
  the action layout as an access-control surface: any field an agent can edit is a field an agent
  can send data through. A `QuickActionDefaultsHandler` runs in the agent's context and can query
  the case — enforce CRUD/FLS on anything it reads beyond the draft (see
  `templates/apex/SecurityUtils.cls`), and never hard-code an internal mailbox that leaks
  routing structure to an external recipient via a visible CC.
- **Operational Excellence** — the Default Email Template lives on the Setup surface and is not
  documented as a Metadata API field on `QuickAction`, so it does not reliably travel with a
  change set. Verify it after every deployment and org refresh. Likewise, the action must be on
  each Case page layout a support persona uses; a layout swap driven by a record type or profile
  change can remove the composer from a whole team with no error anywhere.
- **Reliability** — a `QuickActionDefaultsHandler` sits in the synchronous path of every case-feed
  Email action init, org-wide. An unhandled exception or an unbounded query there degrades the
  composer for every agent at once. Keep it to one bounded SOQL per init, fail soft when a
  template can't be resolved, and log through `templates/apex/ApplicationLogger.cls` rather than
  swallowing the error.
- **Performance** — the documented attachment limits are the real constraints agents hit, and they
  are scoped to the UI: Lightning Experience allows up to 10 files with a 25 MB total file size;
  Salesforce Classic allows more than 10 files with an 18 MB total. Design templates with linked,
  not inlined, imagery, and size the guidance to the UI the support team actually uses.

## Architectural Tradeoffs

- **Declarative defaults vs. an Apex handler.** Predefined field values and the Default Email
  Template cost nothing to operate and cannot break the composer. A `QuickActionDefaultsHandler`
  buys case-awareness (`getContextId()`, `getInReplyToId()`) at the price of org-wide blast radius,
  a test class, and a deployment for every rule change. Exhaust the declarative path first; adopt
  Apex only when the default genuinely varies by case.
- **Composer-with-review vs. one-click send.** A quick action always presents a draft the agent
  can edit before sending. Bypassing it with `Messaging.sendEmail` is faster for the agent and
  removes the last human check on outbound customer communication. The review step is the feature,
  not the friction.
- **Correcting misfiled email vs. fixing the routing.** The move-email capability repairs one
  record. Rising move volume is telemetry about Email-to-Case matching, and treating the symptom
  indefinitely is cheaper each time and more expensive in aggregate.
- **Template subject discipline.** Applying the template subject names the conversation on a first
  touch; applying it on a reply breaks the customer's thread. One checkbox
  (**Don't Apply Template Subject**) or one boolean (`setIgnoreTemplateSubject`) separates the two,
  which argues for separate actions per intent rather than one action doing both jobs.

## Anti-Patterns

1. **Treating the outbound composer as an Email-to-Case detail** — the two are separate surfaces
   with separate configuration, even though the outbound one depends on the inbound one being
   enabled. Answering an outbound question with routing-address setup wastes the whole engagement.
2. **A `QuickActionDefaultsHandler` as the first resort** — org-wide synchronous Apex to achieve
   what a Default Email Template and two predefined field values already do. Reserve it for
   context-dependent defaults.
3. **Bypassing the composer with programmatic sends** — an Apex `Messaging.sendEmail` button
   discards the draft, the template configuration, the attachment UI, quick text, and the agent's
   review, and it produces no `EmailMessage` the composer's configuration governs.
4. **Prepopulating a read-only field** — the value is dropped silently. Configuration that fails
   with no signal is worse than configuration that fails loudly.

## Official Sources Used

- Email Customers in Lightning Experience — https://help.salesforce.com/s/articleView?id=service.cases_email_lex.htm&language=en_US&type=5
- Create a Send Email Quick Action for Cases — https://help.salesforce.com/s/articleView?id=service.case_interaction_send_email_quick_action_create.htm&language=en_US&type=5
- Send Email Action Considerations for Cases — https://help.salesforce.com/s/articleView?id=service.case_interaction_send_email_quick_action_considerations.htm&language=en_US&type=5
- Send Email Fields — https://help.salesforce.com/s/articleView?id=service.case_interaction_send_email_quick_action_fields.htm&language=en_US&type=5
- Apply a Default Email Template Using the Send Email Quick Action — https://help.salesforce.com/s/articleView?id=service.case_interaction_send_email_quick_action_default_email_template_lex.htm&language=en_US&type=5
- Create Predefined Field Values for Email Recipients in the Send Email Action — https://help.salesforce.com/s/articleView?id=sales.send_email_action_predefined_fields.htm&language=en_US&type=5
- Set Predefined Field Values for Quick Action Fields — https://help.salesforce.com/s/articleView?id=sf.predefined_field_values.htm&language=en_US&type=5
- Notes on Predefined Field Values for Quick Actions — https://help.salesforce.com/s/articleView?id=sf.predefined_field_values_notes.htm&language=en_US&type=5
- Add Quick Actions to the Case Page Layout for Lightning Experience — https://help.salesforce.com/s/articleView?id=service.case_interaction_add_actions_to_page_layout_lex.htm&language=en_US&type=5
- Move Emails to a Different Case (agents) — https://help.salesforce.com/s/articleView?id=service.move_email_agents.htm&language=en_US&type=5
- Let Agents Move Emails to a Different Case (admins) — https://help.salesforce.com/s/articleView?id=service.move_email_admin.htm&language=en_US&type=5
- Release Notes: Move Emails Easily to the Relevant Case (Winter '25) — https://help.salesforce.com/s/articleView?id=release-notes.rn_move_email.htm&language=en_US&release=252&type=5
- Knowledge: Outbound Email Attachment Limits in Lightning Experience and Salesforce Classic — https://help.salesforce.com/s/articleView?id=000381295&language=en_US&type=1
- Knowledge: Email Quick Action Not Available on Case Feed — https://help.salesforce.com/s/articleView?id=000382424&language=en_US&type=1
- Customizing the Email Action (`apex:emailPublisher`) — https://developer.salesforce.com/docs/atlas.en-us.case_feed_dev.meta/case_feed_dev/case_feed_dev_guide_email_publisher.htm
- Visualforce Component Reference: `apex:emailPublisher` — https://developer.salesforce.com/docs/atlas.en-us.pages.meta/pages/pages_compref_emailPublisher.htm
- Apex Reference: `QuickAction.QuickActionDefaultsHandler` — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_interface_QuickAction_QuickActionDefaultsHandler.htm
- Apex Reference: `QuickAction.QuickActionDefaults` — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_class_QuickAction_QuickActionDefaults.htm
- Apex Reference: `QuickAction.SendEmailQuickActionDefaults` — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_class_QuickAction_SendEmailQuickActionDefaults.htm
- Metadata API Developer Guide — QuickAction — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_quickaction.htm
- Object Reference — EmailMessage — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_emailmessage.htm
- LWC Developer Guide — Create an Email as a Quick Action — https://developer.salesforce.com/docs/platform/lwc/guide/use-quick-actions-email.html
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
