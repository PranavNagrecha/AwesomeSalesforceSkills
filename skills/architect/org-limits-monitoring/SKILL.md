---
name: org-limits-monitoring
description: "Use when designing or implementing proactive monitoring of Salesforce org-level limits such as API call consumption, storage usage, custom object counts, or platform event allocations. Trigger phrases: 'how do I monitor org limits programmatically', 'set up alerts before we hit API limits', 'REST Limits resource usage', 'OrgLimits.getAll() in Apex', 'scheduled limit checks', 'proactive limit threshold alerting', 'Company Information limits dashboard', 'we keep getting surprised by limit breaches in production'. NOT for per-transaction governor limit planning (use limits-and-scalability-planning). NOT for Connected App API throttling or rate limiting policies (use api-security-and-rate-limiting). NOT for individual Apex code optimization against transaction limits (use apex-cpu-and-heap-optimization)."
category: architect
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Reliability
  - Security
tags:
  - org-limits
  - api-usage
  - monitoring
  - platform-events
  - storage
  - scheduled-apex
  - alerting
  - limits-api
  - observability
  - proactive-monitoring
triggers:
  - "we need to know when we are approaching org-level limits before they cause failures"
  - "how do I programmatically check API call consumption and remaining daily allowance"
  - "set up automated alerts when storage or API usage crosses a warning threshold"
  - "our integrations failed because we exhausted the daily API limit overnight"
  - "what is the difference between OrgLimits.getAll() and the REST Limits resource"
inputs:
  - "Org edition and license type (determines base limit allocations)"
  - "List of limits to monitor (API calls, storage, custom objects, platform events, etc.)"
  - "Desired alert thresholds (e.g., warn at 70%, critical at 90%)"
  - "Notification channels (email, Platform Event, Slack webhook, custom notification)"
  - "Monitoring frequency (hourly, every 4 hours, daily)"
outputs:
  - "Org limits monitoring architecture recommendation"
  - "Scheduled Apex polling class for limit checks"
  - "Threshold alerting strategy with notification routing"
  - "Dashboard or report-based visibility approach"
  - "Filled org-limits-monitoring-template.md"
dependencies:
  - limits-and-scalability-planning
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-05
---

Use this skill when an org needs proactive, automated visibility into its consumption of Salesforce platform limits. Unlike per-transaction governor limits that are enforced inline during code execution, org-level limits are shared ceilings that accumulate over time -- daily API calls, data storage, file storage, custom object counts, platform event delivery allocations, and more. When these limits are exhausted, the impact is org-wide: all integrations fail, all users are blocked from creating records, or platform events are silently dropped. The correct response is not reactive firefighting but proactive monitoring with automated threshold alerts.

---

## Before Starting

- **Which limits matter most?** Not every org needs to monitor every limit. Identify the limits that are most likely to be exhausted given the org's usage pattern -- integration-heavy orgs should monitor API calls; high-growth orgs should monitor storage; event-driven architectures should monitor platform event delivery allocations.
- **What is the current consumption baseline?** Before setting thresholds, establish what "normal" looks like. A single day's snapshot is not enough -- collect at least two weeks of data to identify peaks and trends.
- **What notification channels are available?** Email is the simplest but most easily ignored. Platform Events can drive real-time LWC dashboards. Custom Notifications appear in-app. Outbound Messages or callouts can reach Slack or PagerDuty.

---

## Core Concepts

### Three Monitoring Surfaces

Salesforce exposes org-level limit data through three distinct surfaces, each with different strengths:

#### Surface 1: Apex OrgLimits Class

The `System.OrgLimits` class (available since API v41.0) provides a `Map<String, System.OrgLimit>` via `OrgLimits.getAll()`. Each `OrgLimit` instance exposes `.getName()`, `.getLimit()`, and `.getValue()` (current consumption). This is the best surface for scheduled Apex-based monitoring because it runs inside the org without consuming an API call.

Key characteristics:
- Returns a curated subset of limits, not every limit the REST resource exposes.
- Does not consume an API call (it is native Apex, not a callout).
- Available in all Apex execution contexts (trigger, batch, queueable, scheduled).
- The map keys are string names like `DailyApiRequests`, `DataStorageMB`, `FileStorageMB`, `DailyAsyncApexExecutions`, `DailyBulkApiRequests`, `DailyStreamingApiEvents`, `HourlyPublishedPlatformEvents`, and others.

#### Surface 2: REST API Limits Resource

`GET /services/data/vXX.0/limits` returns a JSON object with every org limit, including limits not available through the Apex class. Each entry contains `Max` and `Remaining` values.

Key characteristics:
- Most comprehensive surface -- exposes limits that OrgLimits.getAll() does not.
- Consumes one API call per invocation (factor this into API budget calculations).
- Ideal for external monitoring tools, middleware health checks, or CI/CD pre-deployment validation.
- Response payload is a flat JSON object with limit names as keys.

#### Surface 3: Setup -- Company Information

The Setup > Company Information page displays storage usage, API usage (last 24 hours), and feature limits in the UI. This is the only monitoring surface available to administrators without developer tooling.

Key characteristics:
- No programmatic access -- manual inspection only.
- Useful for one-time audits but not for proactive alerting.
- Shows a rolling 24-hour window for API usage.
- Storage breakdown shows data storage, file storage, and big object storage separately.

### Threshold Alerting Architecture

The recommended architecture for proactive limit monitoring follows a simple pattern:

1. **Scheduled Apex** runs on a cron schedule (hourly or every 4 hours).
2. The job calls `OrgLimits.getAll()` and compares each limit's `.getValue()` against `.getLimit()`.
3. When consumption crosses a configured threshold (e.g., 70% warning, 90% critical), the job fires an alert through one or more channels.
4. Alert channels include: `Messaging.SingleEmailMessage` for email, Platform Event publish for real-time dashboard updates, `Messaging.CustomNotification` for in-app bell notifications, or an HTTP callout to an external incident management system.

### Custom Metadata for Threshold Configuration

Store monitoring thresholds in Custom Metadata Type records rather than hard-coding them. This allows administrators to adjust thresholds without code changes and supports per-limit configuration:

- `Limit_Monitor_Config__mdt` with fields: `Limit_Name__c` (text, matches the OrgLimit key), `Warning_Threshold__c` (percent, e.g., 70), `Critical_Threshold__c` (percent, e.g., 90), `Enabled__c` (checkbox), `Notification_Channel__c` (picklist: Email / Platform Event / Custom Notification / External).

### Distinguishing From Related Skills

| Concern | Correct Skill |
|---|---|
| Designing for governor limit headroom in new builds | limits-and-scalability-planning |
| Throttling API consumers via Connected App policies | api-security-and-rate-limiting |
| Optimizing individual Apex transactions for CPU/heap | apex-cpu-and-heap-optimization |
| Monitoring org-wide limit consumption and alerting | **org-limits-monitoring** (this skill) |

---

## Recommended Workflow

1. **Identify critical limits.** Review the org's integration landscape, storage trajectory, and automation density. Select the 5-10 limits most likely to be exhausted. Common high-priority limits: `DailyApiRequests`, `DataStorageMB`, `FileStorageMB`, `DailyBulkApiRequests`, `HourlyPublishedPlatformEvents`, `DailyAsyncApexExecutions`.

2. **Establish baselines.** Run `OrgLimits.getAll()` or `GET /services/data/vXX.0/limits` daily for two weeks. Record peak consumption values. Use these peaks to set meaningful thresholds that avoid false alarms.

3. **Design the monitoring job.** Create a Scheduled Apex class that reads limit values from `OrgLimits.getAll()`, compares them against thresholds stored in Custom Metadata, and dispatches alerts when thresholds are crossed. Schedule the job at an appropriate frequency (hourly for API-heavy orgs, every 4 hours for storage-focused monitoring).

4. **Configure alert routing.** Map each limit to a notification channel. API limit breaches may need to reach the integration team via Slack webhook. Storage warnings may need to reach the data team via email. Critical alerts for any limit should page the platform team.

5. **Build visibility.** Create a Lightning Dashboard or LWC component that displays current limit consumption as gauges or progress bars. If the monitoring job publishes Platform Events, the dashboard can update in near-real-time without polling.

6. **Test with realistic load.** In a full sandbox, simulate high-consumption scenarios (e.g., run a bulk data load that consumes 80% of daily API calls) and verify that alerts fire correctly and reach the intended audience.

7. **Operationalize.** Add the monitoring job to the org's runbook. Document the escalation path for each alert severity. Review thresholds quarterly as org usage patterns evolve.

---

## Modes of Engagement

### Mode 1: Greenfield Monitoring Setup

The org has no limit monitoring in place. Start from Step 1 of the Recommended Workflow. Deliver a complete monitoring solution including Scheduled Apex, Custom Metadata configuration, alert routing, and a visibility dashboard.

### Mode 2: Incident Response -- Limit Exhausted

A limit has already been breached. Start by identifying which limit was exhausted using `GET /services/data/vXX.0/limits` or Setup > Company Information. Determine the root cause (unexpected integration spike, data load, runaway automation). Implement emergency mitigation (disable the offending integration, archive data, increase allocation if contractually possible). Then proceed to Mode 1 to prevent recurrence.

### Mode 3: Existing Monitoring Enhancement

The org has basic monitoring (e.g., a weekly manual check or a simple email alert) but needs more sophistication. Assess the current monitoring coverage, identify blind spots (limits not being tracked, thresholds too high or too low, alert fatigue from false positives), and enhance the solution incrementally.

---

## Key Limit Categories

### API Consumption Limits

| Limit | Scope | How to Check |
|---|---|---|
| DailyApiRequests | Per 24-hour rolling window | OrgLimits / REST /limits |
| DailyBulkApiRequests | Per 24-hour rolling window | OrgLimits / REST /limits |
| DailyBulkV2QueryJobs | Per 24-hour rolling window | REST /limits |
| DailyBulkV2QueryFileStorageMB | Per 24-hour rolling window | REST /limits |

### Storage Limits

| Limit | Scope | How to Check |
|---|---|---|
| DataStorageMB | Org-wide | OrgLimits / REST /limits / Setup |
| FileStorageMB | Org-wide | OrgLimits / REST /limits / Setup |

### Platform Event Limits

| Limit | Scope | How to Check |
|---|---|---|
| HourlyPublishedPlatformEvents | Per clock hour | OrgLimits / REST /limits |
| HourlyPublishedStandardVolumePlatformEvents | Per clock hour | REST /limits |
| DailyStandardVolumePlatformEvents | Per 24-hour rolling window | REST /limits |

### Async Processing Limits

| Limit | Scope | How to Check |
|---|---|---|
| DailyAsyncApexExecutions | Per 24-hour rolling window | OrgLimits / REST /limits |
| ConcurrentAsyncGetReportInstances | Concurrent | REST /limits |

---

## Official Sources Used

- Apex Reference Guide -- OrgLimits class and OrgLimit methods
- REST API Developer Guide -- Limits resource (`/services/data/vXX.0/limits`)
- Salesforce Help -- Monitor API Usage and Limits
- Salesforce Well-Architected Overview -- Operational Excellence pillar
