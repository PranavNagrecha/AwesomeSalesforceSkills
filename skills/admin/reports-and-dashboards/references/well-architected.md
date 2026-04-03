# Well-Architected Mapping: Reports and Dashboards

---

## Pillars Addressed

### Security

**Principle: Data Visibility Matches Access Rights**
Reports and dashboards are a data access vector. A dashboard "running as specified user" effectively grants viewers the data access level of that specified user — not their own access. This is a security concern that must be designed deliberately, not accidentally.

- WAF check: Does the dashboard running user expose more data than the viewer should see?
- WAF check: Are report subscriptions sending data to recipients who shouldn't have access to all rows?
- WAF check: Are reports in shared folders appropriate for the users who can access those folders?

**How this skill addresses it:**
- Running user options are explained with security implications
- Subscription risk is documented explicitly
- Mode 2 (Audit) flags dashboards running as high-access users

**Risk of not following this:** Data leakage through dashboards and subscriptions. Users seeing pipeline data, compensation data, or customer data beyond their job function. Compliance issues in regulated industries.

### Operational Excellence

**Principle: Reports Are Maintained and Owned**
A Salesforce org accumulates reports over time. Reports in private folders, reports no one has run in a year, dashboards with broken underlying reports — these are signs of poor reporting governance. Reports should have owners, be in appropriate folders, and be reviewed periodically.

- WAF check: Are reports in organised, shared folders (not private folders)?
- WAF check: Are there owners responsible for maintaining key reports and dashboards?
- WAF check: Are stale and unused reports cleaned up regularly?

**How this skill addresses it:**
- Mode 2 (Audit) identifies private folders, stale reports, and broken dashboards
- Dashboard design template captures owner and review cadence
- Proactive trigger fires for reports in private folders

**Risk of not following this:** Report sprawl — orgs routinely accumulate thousands of reports, most unused. Storage impact is minimal but administrative burden is high. When a key stakeholder leaves, their reports become inaccessible (private folder).

---

## Pillars Not Addressed

- **Performance** — Report performance is affected by filtering, grouping, and data volume. Very large reports (millions of records) benefit from async processing. This skill doesn't cover report query optimisation — that's in data/soql-optimisation.
- **Scalability** — Report performance degrades with data volume. Beyond 2,000 records in Joined reports, or 50,000+ rows in standard reports, consider CRM Analytics. Not in scope here.
- **Reliability** — Reports are generally reliable once built. The "0 results" cases are sharing/filter issues, documented in gotchas.
- **User Experience** — Dashboard design (chart types, layout, color) is touched but not deeply covered. Dashboard UX design is a broader topic.

---

## Reporting as a Data Quality Signal

Reports have a secondary value: they surface data quality issues.

A report showing 30% of Accounts with no owner is a data quality alert. A pipeline report where 40% of Opportunities have no Close Date is a validation rule gap. Use reports proactively to monitor org data health, not just to answer business questions.

**Recommended monitoring reports to build:**
- Accounts with no Activity in 90 days (relationship health)
- Opportunities with missing Close Date or Amount (data completeness)
- Cases open > 30 days (SLA monitoring)
- Contacts with no Email (integration readiness)

These reports are operational health signals — schedule them as subscriptions to relevant team leads.

## Official Sources Used

- Salesforce Well-Architected Overview — operational reporting quality framing
- Metadata API Developer Guide — report and dashboard metadata deployment behavior
- Object Reference — object semantics that affect report design and completeness
