# Well-Architected Notes — Salesforce Shield Deployment

## Relevant Pillars

- **Security** — Primary pillar, and the one most easily faked. Shield's three
  capabilities give an org a data-at-rest control, a forensic history, and a
  detection surface. Each can be enabled and produce a green tick while delivering
  nothing: encryption without re-encryption leaves historical data in plaintext;
  Field Audit Trail on the wrong fields records nothing an auditor asked for; Event
  Monitoring with no consumer is a log nobody reads. The real security outcome is a
  function of the gates between phases, not of the enablement.

- **Operational Excellence** — Shield converts three purchases into three permanent
  operational commitments: a re-encryption job that must run and complete on every
  policy change, a retention policy that deletes nothing on your behalf, and an
  analyst persona with three distinct permissions who has to actually answer
  questions. None of these are visible from the Setup screens, and all three are
  where Shield programmes quietly fail.

- **Reliability** — Platform Encryption is the only one of the three that changes
  application behaviour, and it does so silently: filters return fewer rows, reports
  come back empty, automations stop firing, and nothing throws. One object per change,
  with a before-and-after query snapshot, is the only way to keep cause and effect
  attributable.

- **Performance** — The Field Audit Trail first copy is the schedule risk: "The first
  copy writes the field history that's defined by your policy to archive storage and
  sometimes takes a long time. Subsequent copies transfer only the changes since the
  last copy and are faster." Re-encryption is similarly proportional to data volume
  and belongs in the window estimate rather than after it.

## Architectural Trade-offs

**Phase order.** Field Audit Trail first, Event Monitoring second, Platform
Encryption last. FAT first because its value is time-dependent — history not
collected today cannot be bought later. Event Monitoring second because it is the
instrument that shows you what phase three changed. Encryption last because it is the
only capability that alters query semantics, and it should be the only variable in
flight when it is.

The cost of that order is the one interaction worth stating out loud: history archived
between phases one and three is stored unencrypted, and "If you turn on Platform
Encryption, the previously archived data remains unencrypted." That is defensible —
the archive is a separate store with its own controls — but it must be a written
position rather than a discovered gap.

**Retention as a mechanism, not a number.** With Field Audit Trail, "Salesforce
retains archived field history data until you delete it," and `archiveRetentionYears`
is explicitly "a reminder for manually deleting data." A *minimum* retention
obligation is therefore satisfied by doing nothing. A *maximum* obligation ("must not
retain beyond N years") is satisfied by a deletion process you build, schedule, and
own. Most compliance programmes specify the first and are audited on the second.

**Which monitoring surface.** Event Log Files suit bulk analysis and SIEM ingestion;
Event Log Objects suit ad-hoc SOQL; Real-Time Event Monitoring suits detection within
seconds; Enhanced Transaction Security suits blocking in flight. They carry different
permissions and different retention. Picking one and calling it "monitoring" leaves
questions unanswerable — the analyst persona needs all the permissions the
investigations will require, and the compliance retention requirement usually forces
an off-platform destination regardless of which surface you prefer.

**Blocking versus observing.** Enhanced Transaction Security can act, not just
record, which is genuinely valuable and genuinely risky: the MFA action "isn't
available in the Salesforce mobile app, Lightning Experience, or via API for any
events. Instead, the block action is used." A policy authored as a challenge is, for
every integration, a block. Choose deliberately and test on every surface the covered
event can occur on.

**Encryption scope.** Every encrypted field is a query capability given up and a
regression surface acquired. The trade is per field, not per object, and it is decided
by whether that specific field appears in a filter, a matching key, or an automation
criterion — which is why the inventory step precedes the enablement step and cannot be
skipped. See `security/platform-encryption`.

## Anti-Patterns

1. **Planning "enable Shield" as one step.** Three capabilities, three enablement
   paths, three failure modes — and Field Audit Trail is not even self-service.

2. **Quoting a fixed FAT retention figure.** The mechanism is "until you delete it,"
   with `archiveAfterMonths` capped at 18 and `archiveRetentionYears` deleting
   nothing.

3. **Auditing retention by metadata retrieve.** "Salesforce doesn't include the
   default retention policy when you retrieve the object's definition through Metadata
   API." An empty retrieve means the *default* is in effect — 18 months in production,
   one month in sandboxes — not that no policy exists.

4. **Batching encryption across objects.** Silent semantic changes plus N objects
   equals N candidate causes for every regression.

5. **Declaring encryption complete without re-encryption.** Enabling a policy
   encrypts subsequent writes; historical records wait for an explicit job. Verify per
   object on Encryption Statistics.

6. **Counting Event Monitoring as done when enabled.** Detection needs a person, a
   permission, an alert path, and retention. Close the phase with a scripted incident
   rehearsal whose deliverable is the list of what was missing.

7. **Accepting a compliance field scope without validating trackability.** Formula,
   roll-up, auto-number, long text, and multi-select fields cannot be tracked;
   >255-character fields are tracked without old and new values; and changes made in
   system context by automation are not tracked at all.

8. **Omitting `FieldHistoryArchive` from deletion workflows.** The record delete
   cascades to history but not to the archive, which is precisely the copy a regulator
   asks about.

9. **Buying Shield and never onboarding the logs.** The org pays for a detection
   capability it does not have, and discovers this when the relevant period has already
   aged out.

## Official Sources Used

- Salesforce Security Guide — Salesforce Shield ("a trio of security tools ... Shield Platform Encryption, Event Monitoring, and Field Audit Trail") — https://help.salesforce.com/s/articleView?id=platform.security_overview.htm&type=5
- Salesforce Security Guide — Field Audit Trail (200 vs 20 tracked fields per object, "retains archived field history data until you delete it", the `FieldHistoryArchive` big object, the default 18-month/one-month policy and its invisibility to Metadata retrieve, the supported-object list, the untrackable field list, storage exemption, first-copy duration, the delete-cascade exclusion, and the Platform Encryption interaction) — https://help.salesforce.com/s/articleView?id=platform.field_audit_trail.htm&type=5
- Salesforce Security Guide — Field History Tracking (18-month / 24-month API retention without FAT; >255-character fields tracked without values; system-context automation changes not tracked) — https://help.salesforce.com/s/articleView?id=platform.tracking_field_history.htm&type=5
- Metadata API Developer Guide — HistoryRetentionPolicy (`archiveAfterMonths` min 1 / max 18 / default 18, `archiveRetentionYears` as a manual-deletion reminder, `gracePeriodDays` first-archive-only, `RetainFieldHistory` permission) — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_historyretentionpolicy.htm
- Salesforce Security Guide — Real-Time Event Monitoring, and the LoginEvent / EventLogFile / LoginHistory comparison with its three distinct permissions — https://help.salesforce.com/s/articleView?id=platform.real_time_event_monitoring_overview.htm&type=5
- Salesforce Security Guide — Event Log File Browser and Store and Query Log Data with Event Log Objects — https://help.salesforce.com/s/articleView?id=platform.event_monitoring_elf_browser.htm&type=5
- Salesforce Security Guide — Enhanced Transaction Security (the MFA action degrading to block on mobile, Lightning Experience, and API) — https://help.salesforce.com/s/articleView?id=platform.enhanced_transaction_security_intro.htm&type=5
- Salesforce Security Guide — Monitor Login History (20,000 records / 6 months; Source IP vs Forwarded for IP) — https://help.salesforce.com/s/articleView?id=platform.security_login_history.htm&type=5
- Salesforce Help — Strengthen Your Data's Security with Shield Platform Encryption — https://help.salesforce.com/s/articleView?id=platform.security_pe_overview.htm&type=5
- Salesforce Well-Architected — Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html

<!-- UNVERIFIED: the Setup navigation paths "Platform Encryption Analyzer" and
     "Encryption Statistics" are referenced from the in-repo
     security/platform-encryption package rather than re-verified here. Both
     surfaces exist; confirm the current menu labels before writing them into a
     runbook. -->
<!-- UNVERIFIED: the three-phase ordering (Field Audit Trail, then Event
     Monitoring, then Platform Encryption) is this package's recommendation
     based on the documented properties of each capability. Salesforce does not
     publish a prescribed Shield rollout sequence. The individual facts each
     phase gate rests on are cited; the ordering itself is judgement. -->
<!-- UNVERIFIED: Event Log File generation latency and per-event-type retention
     were NOT established in this pass. Widely-repeated figures (hourly vs
     24-hour log generation, 30-day retention) were not confirmed against
     Salesforce documentation, so this package deliberately makes no latency or
     retention claim for Event Log Files beyond the Login History cap, which IS
     quoted. Verify against the Event Monitoring documentation before promising
     a latency or retention window to a compliance programme. -->
