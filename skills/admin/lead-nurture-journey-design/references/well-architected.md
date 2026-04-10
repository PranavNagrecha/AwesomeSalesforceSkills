# Well-Architected Notes — Lead Nurture Journey Design

## Relevant Pillars

### Operational Excellence

Operational Excellence is the primary pillar for lead nurture journey design. A well-designed nurture program is inherently operational: it must be observable (which stage is each prospect in?), maintainable (can steps be edited without breaking active cohorts?), and recoverable (what happens when a prospect exits unexpectedly?).

Key operational excellence requirements for nurture programs:
- Every program path must terminate with a status-setting step ("Change Prospect Field" or "Add Tag") so that any prospect's stage is visible in CRM without querying Engagement Studio.
- Program design decisions (entry criteria, suppression list, branching trigger logic, wait periods, MQL threshold) must be documented in a decision record before the program launches — not reconstructed from the canvas after the fact.
- Change control applies to active programs. Structural edits to running programs must be preceded by a program pause, and changes must be reviewed against the active prospect cohort.

### Reliability

Reliability governs whether the nurture program consistently delivers the intended content to the intended prospects and triggers the intended handoffs without silent failures.

Key reliability requirements:
- The MQL handoff must be backed by a standalone Automation Rule in addition to any program-internal rule step. Program-internal steps fire on the weekly run; prospects who cross the MQL threshold through channels outside the program are missed without the Automation Rule.
- Suppression lists must be explicitly configured and reviewed at launch. Silent over-inclusion (existing customers receiving nurture emails) is a reliability failure with reputational consequences.
- Test prospects must verify both the "Yes" and "No" branch paths before the program goes live, not just the happy path.

### Scalability

Scalability concerns in nurture journey design arise at the program and database levels:
- Engagement Studio programs with very large entry lists (tens of thousands of prospects) may experience longer weekly evaluation windows. Design entry lists with appropriate dynamic list criteria rather than adding the entire prospect database.
- Programs with many steps and deep branching trees are harder to maintain as the content library grows. Use a modular design: one program per funnel stage or per product line rather than a single monolithic program covering all segments and all stages.
- Content library scalability: the content inventory must be maintained as a living document. As new assets are created, the program design should be reviewed to incorporate them rather than letting the program become stale.

## Architectural Tradeoffs

**Branching depth vs. maintenance complexity:** Deeply branched programs (10+ rule steps with 4–5 levels of Yes/No paths) create highly personalized journeys but become difficult to audit and modify. Programs with 5+ levels of branching are typically best split into separate programs per segment or stage, with list membership as the handoff mechanism between programs. The tradeoff is slightly less granular in-program personalization versus significantly easier maintenance and troubleshooting.

**Engagement Studio programs vs. Automation Rules for nurture logic:** Automation Rules are always-on, evaluate continuously, and are not constrained to the weekly schedule. For simple single-threshold logic ("When score >= 100, assign to Sales"), Automation Rules are more reliable than a program step. Use Engagement Studio programs where the value is in the sequenced content delivery and branching — not as a substitute for Automation Rules for threshold-based routing.

**Real-time vs. batch execution:** The weekly execution schedule is a fundamental platform constraint, not a configuration choice. Orgs that need near-real-time nurture responses (e.g., a follow-up email within one hour of a webinar registration) must use Completion Actions or Automation Rules for the time-sensitive step and reserve Engagement Studio for the multi-week behavioral journey that follows. Do not attempt to engineer real-time behavior out of Engagement Studio by setting 1-day Wait periods — the platform will not honor them at that frequency.

## Anti-Patterns

1. **Building the program before the content inventory exists** — Designing the Engagement Studio canvas before knowing what content exists for each funnel stage forces either placeholder "Send Email" steps (which launch a broken program) or post-design content mapping (which usually reveals stage gaps that require structural program changes). Always complete the content inventory audit first. A program skeleton with no content is not progress — it is technical debt that blocks launch.

2. **Relying solely on program-internal steps for MQL handoff** — If the only Sales notification is a "Notify User" step inside the Engagement Studio program, then: (a) it only fires during the weekly run, not when the threshold is crossed; (b) it only covers prospects who are in that specific program. Prospects who reach MQL through direct form fills, event registrations, or other programs are silently missed. A standalone Automation Rule that independently monitors score+grade and triggers Sales assignment is a mandatory architectural complement to any program-internal handoff step.

3. **Using one undifferentiated program for all prospect segments** — A single Engagement Studio program that sends the same content sequence to Enterprise IT decision-makers and SMB operations managers produces irrelevant content for both segments. Either create separate programs per segment or implement early-program grade-based branching that routes prospects to segment-appropriate content paths before the first email is sent. Sending irrelevant content increases unsubscribe rates, reduces score accumulation (prospects don't click), and delays MQL conversion.

## Official Sources Used

- Engagement Studio (MCAE Help) — https://help.salesforce.com/s/articleView?id=sf.pardot_engagement_studio.htm
- Scoring and Grading (MCAE Help) — https://help.salesforce.com/s/articleView?id=sf.pardot_scoring_and_grading_about.htm
- Lead Nurturing with MCAE (Trailhead) — https://trailhead.salesforce.com/content/learn/modules/pardot-lead-nurturing
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
