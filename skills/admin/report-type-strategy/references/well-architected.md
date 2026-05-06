# Well-Architected Notes — Report Type Strategy

## Relevant Pillars

- **Operational Excellence** — Custom Report Types are the
  foundation users build reports on. A well-curated CRT (3-5
  field sections, ~30-50 fields, an explanatory description)
  results in fewer wrong-report bugs, fewer fields used by
  mistake, and faster build times. A neglected CRT (all fields,
  no grouping, no description) produces a report-builder
  experience users describe as "I just gave up and built it
  myself in Excel". The investment is up-front and pays back over
  every report built on it.
- **Performance** — CRT join shape and field count both affect
  report execution speed. Heavy CRTs with all-1,000 fields slow
  the builder; deep joins (3 levels) hit query limits faster.
  Curating both keeps reports fast at scale. For very wide
  data, a flattened reporting object populated by Flow or
  Reporting Snapshots beats live joins.

## Architectural Tradeoffs

The main tradeoff is **standard vs custom**. Standard report
types update automatically as the schema evolves; CRTs do not.
Standard report types expose every field; CRTs let you curate.
Standard report types support the join shapes Salesforce thought
of; CRTs support more.

Specifically:

- **One-off ad-hoc analysis**: standard report type if it fits.
- **Repeated curated reporting (renewals, support SLAs)**: CRT
  with curated fields.
- **A-without-B / negation**: Cross Filter on a CRT, or joined
  report.
- **Wide aggregate reporting**: Reporting Snapshot to a flattened
  object.

## Anti-Patterns

1. **CRT for what a standard already covers.** Adds maintenance
   for no benefit.
2. **Wrong join shape (inner vs outer).** Silently filters rows
   the user expected. CRT recreation is the only fix.
3. **All-fields layout.** Past 60 fields the picker gates them
   behind search; users miss them.

## Official Sources Used

- Create a Custom Report Type — https://help.salesforce.com/s/articleView?id=sf.reports_defining_report_types.htm
- Cross Filters in Reports — https://help.salesforce.com/s/articleView?id=sf.reports_cross_filters.htm
- Joined Reports Overview — https://help.salesforce.com/s/articleView?id=sf.reports_joined_about.htm
- Considerations for Custom Report Types — https://help.salesforce.com/s/articleView?id=sf.reports_define_report_types_limits.htm
- Salesforce Reports & Dashboards Limits — https://help.salesforce.com/s/articleView?id=sf.limits_reports.htm
- Salesforce Well-Architected: Adaptable — https://architect.salesforce.com/well-architected/adaptable/composable
