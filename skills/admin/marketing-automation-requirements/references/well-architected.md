# Well-Architected Notes — Marketing Automation Requirements

## Relevant Pillars

- **Operational Excellence** — The primary pillar for this skill. A marketing automation requirements document is the single source of truth for the entire automation program: scoring model, MQL threshold, lifecycle stages, handoff mechanism, and sales SLA. Without it, implementation decisions are made ad hoc, rework is common, and post-launch troubleshooting is slow because there is no baseline to compare against. Operational excellence requires that all threshold agreements be documented with approver names and dates so they survive personnel turnover and can be revisited during calibration reviews.

- **Reliability** — Score decay rules and the recycle automation are reliability mechanisms: they ensure that stale MQL flags are cleared and that the Sales queue does not accumulate invalid entries that degrade rep trust in the system. Requirements that omit decay or the de-MQL recycle process produce a system that degrades over time — MQL quality drops, reps stop accepting leads, and the automation program is abandoned even though the implementation was technically correct. Specifying decay and recycle in requirements is a reliability investment.

- **Security** — Field-level security for MCAE-synced fields (`Score`, `Grade`) must be addressed in requirements. If CRM-side automation or users can overwrite these fields, MCAE sync silently discards the changes, producing divergent data. Requirements should flag these fields as protected and specify that write access is restricted to the MCAE integration user. This is a data integrity security requirement, not just a configuration nicety.

- **Performance** — For high-volume orgs (>200 leads/day), the choice between record-triggered Flow score updates and scheduled batch recalculation has performance implications. Requirements must document the expected lead volume so the implementation team can choose the correct automation mechanism. Record-triggered Flow on every Lead edit causes governor limit risk at high volume; this decision must be made at requirements time, not discovered during load testing.

- **Scalability** — Requirements should address how the scoring model scales as new products, segments, or geographies are added. A single global scoring model may not scale to multiple ICP segments — multiple Profiles or scoring tiers may be needed. Documenting the expected growth trajectory at requirements time prevents the need for a full scoring model redesign six months post-launch.

## Architectural Tradeoffs

**Score alone vs. score + grade:**
Using score alone is simpler to configure and requires no ICP field data quality investment. However, it admits high-engagement, low-fit contacts (competitors, researchers, students) into the MQL queue, degrading Sales trust over time. The score + grade model is more accurate but requires reliable field data for `Title`, `Industry`, and `NumberOfEmployees` on Lead records. If field data quality is poor at requirements time, score-only is the pragmatic starting point — but requirements should include a planned upgrade to score + grade once data quality is addressed.

**MCAE Automation Rule threshold vs. Engagement Studio step:**
An Automation Rule fires continuously across the entire prospect database whenever criteria are met. An Engagement Studio program step fires only for prospects enrolled in that program. For MQL routing, Automation Rules are the correct mechanism — they catch prospects that cross the threshold via any activity, regardless of campaign enrollment. Requirements that use Engagement Studio steps for MQL routing will miss prospects who engage outside the enrolled program.

**Requirements document scope vs. implementation scope:**
The requirements skill is deliberately upstream of implementation. The outputs of this skill (threshold definition, scoring spec, SLA) are inputs to `mcae-lead-scoring-and-grading`. Requirements practitioners should not specify MCAE configuration paths or UI steps — that is implementation scope. Mixing implementation detail into requirements documents creates confusion about what is decided vs. what is being built.

## Anti-Patterns

1. **Specifying MQL threshold without sales sign-off** — This is the single most damaging anti-pattern in marketing automation requirements. If marketing sets the threshold unilaterally, sales will dispute MQL quality immediately after launch. The platform gets blamed, the automation program is sidelined, and re-alignment requires a full requirements re-do under worse conditions (live system, existing data, frustrated stakeholders). The requirement is not complete without documented joint sign-off from both marketing and sales leadership.

2. **Conflating MCE Automation Studio with MCAE Engagement Studio in requirements** — These are different engines with different data models, trigger mechanisms, and integration points. Writing requirements that describe MCE Automation Studio SQL activities as the mechanism for real-time MQL routing will produce an implementation that does not work — Automation Studio cannot evaluate individual prospect scores in real time. Requirements that mix platform terminology force the implementation team to re-interpret the document, introducing scope risk and rework.

3. **Omitting score decay and recycle automation from requirements** — Decay rules and the de-MQL recycle process are not bonus features; they are required for the system to remain accurate over time. A scoring model without decay accumulates stale MQLs. A handoff process without a recycle mechanism leaves unaccepted MQLs in the Sales queue indefinitely, degrading data quality and rep trust. Requirements that omit these components are incomplete.

## Official Sources Used

- MCAE Scoring and Grading Overview — https://help.salesforce.com/s/articleView?id=sf.pardot_scoring_and_grading_about.htm
- MCAE Lifecycle Report Metrics — https://help.salesforce.com/s/articleView?id=sf.pardot_lifecycle_report.htm
- Automation Studio Overview (Marketing Cloud Engagement) — https://developer.salesforce.com/docs/marketing/marketing-cloud/guide/automation-studio-overview.html
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
