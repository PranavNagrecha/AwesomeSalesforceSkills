# Well-Architected Notes — Persona And Journey Mapping (Salesforce-Anchored)

## Relevant Pillars

- **User Experience** — primary pillar. Persona + journey artifacts are the
  input that make UX decisions (Dynamic Forms, Quick Actions, page redesign,
  Path, list view tuning) auditable and persona-specific rather than generic.
- **Operational Excellence** — anchoring personas to PSGs, record types, and
  measured posture means the artifacts stay maintainable across releases
  rather than turning into shelfware.
- **Performance** — by tagging `cognitive_load` and `click_count` friction,
  the persona work directly drives Lightning page performance interventions
  (component count reduction, lazy-loaded related lists, conditional visibility).

## Architectural Tradeoffs

- **Persona granularity vs. maintainability.** More personas (per role) →
  sharper UX targeting, but more artifacts to keep current. Fewer personas
  (per PSG) → easier maintenance, but risk of one persona masking two distinct
  user populations. Cap at ≤7 per phase; merge personas that share a PSG and
  primary-task profile.
- **Mobile/desktop precision vs. measurement cost.** Lightning Usage app +
  EventLogFile gives a real split, but requires Event Monitoring license and
  effort to enable. Surveys give a cheap split but a noisy one. Prefer
  measured data; if surveys are the only option, mark `mobile_pct` as a soft
  estimate so downstream UX decisions are weighted accordingly.
- **Friction enum vs. open tagging.** A fixed five-value enum sacrifices
  expressiveness for routing reliability. The bet is that downstream agents
  benefit more from a consistent vocabulary than from custom tags. If a
  friction genuinely doesn't fit, log it in `notes` rather than invent a tag.

## Anti-Patterns

1. **Title-based persona ("Sales Rep").** Anchors to nothing in the org;
   cannot be audited; collides with adjacent personas. Replace with PSG-anchored,
   record-type-anchored, list-view-anchored personas.
2. **Journey ends at save.** Misses `mode_switch` friction which is often the
   highest-frequency complaint. Always model the next task and the surface
   transition.
3. **Persona designed without org artifacts.** A persona that doesn't name a
   real PSG, dashboard, or list view is a UX exercise, not a Salesforce
   persona — it cannot drive the configuration decisions this skill exists to
   inform.

## Official Sources Used

- Salesforce Help — Lightning Usage App: https://help.salesforce.com/s/articleView?id=sf.lightning_usage_app.htm
- Salesforce Help — Event Monitoring & EventLogFile: https://help.salesforce.com/s/articleView?id=sf.event_monitoring_setup.htm
- Salesforce Help — Salesforce Mobile App Overview: https://help.salesforce.com/s/articleView?id=sf.salesforce_app_intro.htm
- Salesforce Help — Permission Set Groups: https://help.salesforce.com/s/articleView?id=sf.perm_set_groups.htm
- Salesforce Lightning Design System (SLDS): https://www.lightningdesignsystem.com/
- Salesforce Architects — Well-Architected User Experience: https://architect.salesforce.com/well-architected/adaptable/personalized
- Salesforce Architects — Well-Architected Overview: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_concepts.htm
- Metadata API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm
