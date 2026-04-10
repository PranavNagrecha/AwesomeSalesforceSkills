# LLM Anti-Patterns — FSL Integration Patterns

Common mistakes AI coding assistants make when generating or advising on FSL Integration Patterns.

## Anti-Pattern 1: Calling schedule() Synchronously Inside IoT Platform Event Handler

**What the LLM generates:**
```apex
trigger IoTWorkOrderTrigger on IoT_Alert__e (after insert) {
    WorkOrder wo = new WorkOrder(Subject = 'IoT Alert');
    insert wo;
    ServiceAppointment sa = new ServiceAppointment(ParentRecordId = wo.Id);
    insert sa;
    FSL.ScheduleService.schedule(sa.Id, POLICY_ID); // throws CalloutException
}
```

**Why it happens:** LLMs sequence operations logically without modeling the Apex callout-DML transaction constraint.

**Correct pattern:** Create WorkOrder and ServiceAppointment in the event handler (DML only). Enqueue scheduling in a separate Queueable that runs in a fresh transaction.

**Detection hint:** Any `FSL.ScheduleService.schedule()` call inside an Apex trigger (including Platform Event triggers) is wrong.

---

## Anti-Pattern 2: Designing Salesforce as the GPS Data Poller

**What the LLM generates:** A Scheduled Apex job that makes outbound REST calls to the fleet GPS API every 1–5 minutes to retrieve vehicle locations.

**Why it happens:** Polling is the intuitive approach when you need data from an external system on a schedule.

**Correct pattern:** Fleet GPS systems push location updates to Salesforce via inbound REST or batch. Salesforce receives; it does not poll. Calculate Daily API limit impact before any outbound polling design.

**Detection hint:** Any integration design where Salesforce makes scheduled outbound calls to GPS/telemetry APIs is likely wrong for high-volume fleets.

---

## Anti-Pattern 3: Inbound-Only ERP Integration (No ProductConsumed Feedback)

**What the LLM generates:** An ERP integration spec that syncs product catalog and stock levels from ERP to Salesforce but has no outbound consumption event from Salesforce back to ERP.

**Why it happens:** LLMs model the most visible integration direction (ERP as source of truth pushing to Salesforce) without modeling the feedback loop.

**Correct pattern:** FSL-ERP inventory integration must be bidirectional: ERP → Salesforce (product catalog, van stock), and Salesforce → ERP (ProductConsumed consumption events). Missing the feedback loop causes phantom stock in ERP.

**Detection hint:** Any FSL-ERP integration design without a ProductConsumed → ERP feedback component is incomplete.

---

## Anti-Pattern 4: Using Direct Apex Callouts Instead of Named Credentials

**What the LLM generates:**
```apex
HttpRequest req = new HttpRequest();
req.setHeader('Authorization', 'Bearer ' + System.Label.ERP_API_Key);
```

**Why it happens:** LLMs generate functional integration code but default to storing credentials in Custom Labels or Custom Settings rather than Named Credentials.

**Correct pattern:** Use Named Credentials for all outbound authenticated callouts. Named Credentials handle certificate management, OAuth token refresh, and prevent credentials from being exposed in Apex code or configuration.

**Detection hint:** Any Apex callout that constructs authorization headers from Custom Labels, Custom Settings, or hard-coded strings instead of Named Credentials is a security anti-pattern.

---

## Anti-Pattern 5: Real-Time Customer Notifications Without Offline Sync Latency Consideration

**What the LLM generates:** A customer notification integration triggered by FSL Mobile "En Route" status that assumes the notification fires in real-time when the technician taps the button.

**Why it happens:** LLMs model the online case without accounting for FSL Mobile offline sync latency.

**Correct pattern:** For technicians in offline areas, the "En Route" status change fires at sync time — potentially 1–4 hours after the technician tapped the button. Customer notifications based on this trigger may arrive after the technician has already arrived. Design notifications with this latency in mind, or implement a scheduled time-based notification independent of status transitions.

**Detection hint:** Any FSL customer notification integration that claims "real-time" notification without discussing FSL Mobile offline sync behavior is incomplete.
