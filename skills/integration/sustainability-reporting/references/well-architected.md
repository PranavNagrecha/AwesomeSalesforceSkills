# Well-Architected Notes — Sustainability Reporting

## Relevant Pillars

- **Reliability** — Disclosure outputs go to regulators and
  auditors. The data, emission factors, and assessment provenance
  must be reproducible. Treat each report run as a versioned
  artifact with the inputs frozen.
- **Operational Excellence** — Sustainability reporting is a
  recurring annual cycle. Each cycle compounds: emission-factor
  refreshes, framework updates (ESRS amendments, SASB sector
  refreshes), and supplier-data freshness. Build the cadence in.
- **Security / Governance** — Disclosed numbers are externally
  audited. Internal controls on who can run / approve / publish
  reports are governance-critical.

## Architectural Tradeoffs

- **CSRD vs SASB vs GRI vs CDP.** Different audiences, different
  data prerequisites. Most companies file against more than one;
  the underlying emissions data is shared but each framework's
  output is distinct.
- **Net Zero Cloud native vs third-party tools.** Net Zero Cloud is
  the native option with native integration to other Salesforce
  data (procurement, asset, supplier records). Third-party
  sustainability platforms (Watershed, Persefoni, Sphera, etc.)
  compete on coverage of niche frameworks and supplier-engagement
  workflows. Pick by the framework + supplier-engagement
  requirements.
- **Sustainability Scorecard vs framework reports.** Scorecard for
  internal monitoring (high-frequency, simplified). Reports for
  external disclosure (annual, framework-specific).
- **Custom Data Mapper extensions vs standard outputs.** Standard
  outputs cover the framework requirements; deeper customization
  buys narrative differentiation at the cost of OmniStudio
  expertise.

## Anti-Patterns

1. **Skipping double-materiality for CSRD.** Non-compliant.
2. **Generic "SASB" without sector.** SASB is sector-specific.
3. **Reading low Scope 3 totals as good news.** Often missing data.
4. **Confusing Net Zero Cloud reporting with CRM Analytics
   dashboards.** Different surfaces.
5. **Treating Net Zero Cloud as part of Enterprise licensing.**
   Separately licensed.

## Official Sources Used

- Net Zero Cloud ESRS Report — https://help.salesforce.com/s/articleView?id=ind.netzero_manager_generate_esrs_report.htm&type=5
- Net Zero Cloud Developer Guide — https://developer.salesforce.com/docs/industries/netzero-cloud/guide/netzero_cloud_dev_overview.html
- Sustainability Scorecard Developer Guide — https://developer.salesforce.com/docs/industries/netzero-cloud/guide/netzero_calc_sustainability_scorecard.html
- Track Emissions with Net Zero Cloud — Trailhead — https://trailhead.salesforce.com/content/learn/modules/net-zero-cloud-basics/track-emissions-with-net-zero-cloud
- CSRD Guide for Companies — https://www.salesforce.com/net-zero/csrd-reporting/
- Salesforce Well-Architected Resilient — https://architect.salesforce.com/well-architected/trusted/resilient
