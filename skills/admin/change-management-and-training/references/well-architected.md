# Well-Architected Notes — Change Management and Training

## Relevant Pillars

- **Operational Excellence** — The primary pillar. Change management and training directly determine whether a Salesforce implementation delivers operational value or sits unused. The Well-Architected Framework's Operational Excellence pillar covers adoption, sustainable operations, and continuous improvement — all of which require structured human change processes alongside technical delivery.

- **User Experience** — Training and in-app guidance directly shape the end-user experience of the platform. Poorly communicated changes degrade UX even when the technical implementation is sound. Role-specific training and Path coaching text are UX decisions, not just operational tasks.

- **Reliability** — Untrained users entering low-quality data, bypassing validation rules, or creating duplicate records degrades org reliability. Change management reduces reliability failures caused by human behavior, not platform faults.

## Architectural Tradeoffs

**In-App Guidance vs. External Training Material**
In-app guidance (walkthroughs, prompts) is delivered at the moment of need inside Salesforce. It scales without scheduling and degrades gracefully when users ignore it. External training (documents, videos, live sessions) is richer and allows practice in a safe environment but requires user initiative to consume. For simple behavioral changes (new required field, new stage), in-app guidance is sufficient. For complex workflow changes affecting multiple objects and steps, both are required — external training first, in-app guidance as reinforcement.

**Centralized Training Org vs. Sandbox for Practice**
A dedicated training org allows persistent, realistic data for exercises without risking sandbox refresh cycles. However, it requires ongoing maintenance to keep configuration in sync with production. Sandboxes are easier to maintain but get refreshed, wiping training scenarios. Choose a dedicated training org when training is repeated (e.g., onboarding new hires), use a full sandbox for one-time project rollouts.

## Anti-Patterns

1. **Big-Bang Training on Go-Live Day** — Delivering all training on the morning of go-live combines the highest cognitive load (new system) with the highest stress (live work). Users retain almost nothing. The correct approach is training 1–2 weeks before go-live in a sandbox with realistic scenarios, followed by a brief reminder communication on launch day.

2. **One-Size-Fits-All Training** — Presenting a tour of all Salesforce features to a mixed audience of Sales Reps, Service Agents, and Managers simultaneously. Each role gets confused by features they will never use and misses depth on what they will. Training must be segmented by role and anchored to the specific tasks that role performs, not to the platform's feature inventory.

3. **No Adoption Baseline Before Go-Live** — Measuring adoption improvement requires a baseline. If no data is captured before go-live on current login patterns or task completion rates, there is nothing to compare against. Define and start capturing the baseline metric at least 2 weeks before go-live even if the system being replaced is not Salesforce.

## Official Sources Used

- Salesforce Well-Architected Overview — Operational Excellence and Engaging pillar framing
  URL: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html

- Salesforce Well-Architected — Engaging sub-pillar (Easy pillar) — user adoption as an architecture quality dimension
  URL: https://architect.salesforce.com/well-architected/easy/engaging

- Trailhead: User Training and Motivation — four-step training plan workflow, super user program, training library structure
  URL: https://trailhead.salesforce.com/content/learn/modules/user-training-and-motivation

- Trailhead: Training Strategy and Communication Plan — role-specific communications, "What's in it for me?" framing
  URL: https://trailhead.salesforce.com/content/learn/modules/user-training-and-motivation/create-your-training-strategy-and-communication-plan

- Trailhead: Leveraging Change — Six Levers of Change model (Leadership, Ecosystem, Values, Enablement, Rewards, Structure)
  URL: https://trailhead.salesforce.com/content/learn/modules/levers-of-change-model/learn-the-levers-of-change

- Trailhead: Salesforce Adoption Strategies — adoption planning, go-live readiness, internal communication
  URL: https://trailhead.salesforce.com/content/learn/modules/salesforce-adoption-strategies

- Trailhead: Release Readiness Strategies — pre-release sandbox preview workflow, Release Notes triage, user communication timing
  URL: https://trailhead.salesforce.com/content/learn/modules/sf_releases/sf_releases_strategy

- Trailhead: Improve User Engagement with In-App Guidance — prompt types, targeting, walkthrough configuration
  URL: https://trailhead.salesforce.com/content/learn/modules/user-engagement

- Salesforce In-App Guidance Help — configuring walkthroughs and prompts in Lightning Experience
  URL: https://help.salesforce.com/s/articleView?id=sales.customhelp_lexguid.htm&type=5

- Salesforce Path documentation — Stage coaching text, record type scoping, Path setup
  URL: https://help.salesforce.com/s/articleView?id=sf.sales_path_overview.htm

- Trailhead: Enhance User Adoption Metrics — LoginHistory-based adoption measurement
  URL: https://trailhead.salesforce.com/content/learn/modules/user-adoption-metrics
