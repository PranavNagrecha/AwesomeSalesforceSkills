# Well-Architected Notes — Custom Notification Type Design

## Relevant Pillars

- **User Experience** — notification fatigue is the dominant failure
  mode.
- **Operational Excellence** — a governance registry stops notification
  sprawl.
- **Security** — deep links must respect user visibility; do not leak
  record summaries the user cannot see.

## Architectural Tradeoffs

- **Broad targeting vs narrow:** broad reaches more eyes but erodes
  signal; narrow keeps signal but risks missing recipients.
- **Bundled digest vs per-event:** digest preserves attention; per-event
  maximizes urgency.
- **Multi-channel vs single-channel:** multi-channel increases reach and
  noise; single-channel is cleaner.

## Official Sources Used

- Custom Notifications — https://help.salesforce.com/s/articleView?id=sf.custom_notifications_overview.htm
- Flow Send Custom Notification — https://help.salesforce.com/s/articleView?id=sf.flow_ref_elements_action_core_custom_notification.htm
- Salesforce Well-Architected User Experience — https://architect.salesforce.com/docs/architect/well-architected/adaptable/adaptable
