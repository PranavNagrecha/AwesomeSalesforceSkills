# Gotchas — FSL Scheduling Optimization Design

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Null DueDate Means the Appointment May Never Be Scheduled

**What happens:** Service appointments with a null `DueDate` field receive the lowest possible optimizer priority score. In any optimization run where the schedule cannot accommodate all appointments — which is normal in fully-loaded territories — null-DueDate appointments are consistently left unscheduled. The optimizer does not log a per-appointment warning; the appointment simply remains in the unscheduled list with no explanation.

**When it occurs:** Whenever Global or In-Day optimization runs against a territory that has service appointments with null `DueDate`. This is most common in orgs that create service appointments automatically via Flow without populating `DueDate`, or where the source work order does not set a due date.

**How to avoid:** Treat `DueDate` as an operationally required field even though the platform does not enforce it. Add a validation rule or Flow to block a service appointment from being activated without a `DueDate`. Periodically run a report filtering for `ServiceAppointment.DueDate = null` and remediate records before optimization runs.

---

## Gotcha 2: Work Rules (Pass/Fail) and Priority Score (Points) Are Separate Mechanisms — Conflating Them Causes Wrong Tuning

**What happens:** Practitioners troubleshoot optimizer output by adjusting service objective weights in the scheduling policy when the real problem is appointment Priority or DueDate data quality — or vice versa. Work rules are hard pass/fail gates (a slot passes or is eliminated). Service objectives are weighted grades applied to slots that survive work rules. The optimizer's priority score (derived from the Priority field and DueDate) is a third mechanism that determines which appointments are scheduled first when the run is constrained. These three layers are independent.

**When it occurs:** When unscheduled appointments are blamed on "the optimizer ignoring priority," practitioners increase ASAP objective weight expecting this to fix the problem. But ASAP affects slot ranking within a candidate set, not which appointments get into the candidate set first. If priority 1 appointments are not being scheduled, the issue is almost always null DueDate or a too-restrictive work rule filtering out all candidates — not objective weights.

**How to avoid:** Diagnose optimizer issues by layer: (1) check data quality (Priority and DueDate), (2) check work rules (are candidates being eliminated?), (3) check service objectives (are remaining candidates being ranked correctly?). Do not start with objective weight adjustments — they are the last layer to tune.

---

## Gotcha 3: Priority Score Is Not Linear — Priority 1 Generates Approximately 25,500 Points

**What happens:** Practitioners assume the optimizer's priority scoring is a linear 1–10 scale where priority 1 is 10x more important than priority 10. It is not. Priority 1 generates approximately 25,500 optimizer points, and the gap between priority 1 and priority 2 is disproportionately large compared to lower-priority intervals. Organizations that assign priority 1 to all "important" work eliminate meaningful differentiation: if all high-value appointments are priority 1, the optimizer cannot distinguish between them and falls back to DueDate proximity for ordering.

**When it occurs:** Any time priority 1 is used as a general "important" label rather than a reserve for the most time-critical appointments in the org. Common in orgs that set priority via a simple checkbox rule ("if customer-facing, set priority = 1").

**How to avoid:** Design a tiered priority model where priority 1 is reserved for genuine emergencies — appointments with SLA breach windows under 4 hours. Map routine and planned work to priority 4–7. Document the tier definitions and enforce them via Flow-based automation on appointment creation.

---

## Gotcha 4: Street-Level Routing Is a Paid Add-On and Is Not Enabled by Default

**What happens:** The FSL Optimizer defaults to Aerial (straight-line) travel mode for all installations. Aerial is free and computationally fast but inaccurate for dense urban areas. Practitioners sometimes assume road-network routing is included in the Field Service license because the product is inherently about driving to appointments. Enabling Street-Level Routing requires a separate add-on license that must be purchased and activated independently.

**When it occurs:** When an org goes live with FSL in an urban territory and observes that technician routes look geographically reasonable on a map but real-world drive times consistently exceed optimizer estimates — a symptom that Aerial mode is underestimating road distances and traffic.

**How to avoid:** Evaluate geography early in implementation. For rural or low-density territories, Aerial is acceptable. For urban territories with highway avoidance, one-way streets, or significant traffic variation, budget for the Street-Level Routing add-on. Confirm the add-on license is active in Setup > Field Service Settings > Routing before go-live. Switching travel modes after go-live changes optimizer output and requires re-baselining dispatcher and customer expectations.

---

## Gotcha 5: Global Optimization Can Reschedule Already-Confirmed Appointments

**What happens:** A Global optimization run with a multi-day horizon does not protect appointments that are already scheduled. If rescheduling a confirmed appointment improves the overall territory score, the optimizer will move it — including appointments that dispatchers manually arranged or that customers have confirmed. Dispatchers who expect Global optimization to fill empty slots only are surprised when confirmed appointments appear at different times or on different days after a run.

**When it occurs:** Any time Global optimization is run with a horizon that includes days with existing confirmed appointments and no explicit "lock" or exclusion configuration is applied to those appointments.

**How to avoid:** Use the service appointment's scheduling status or a custom field to pin appointments that must not be moved. Configure the optimizer to respect a "Pinned" or "In Jeopardy" flag, or use the "Exclude from Optimization" capability available in some FSL managed package versions. Educate dispatchers that Global optimization is a full-reschedule operation, not an append operation, and that its output should always be reviewed before schedule delivery.
