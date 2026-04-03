# Examples - List Views And Compact Layouts

## Example 1: Service Queue Triage Without Public List-View Sprawl

**Context:** A support org has dozens of Case list views such as `My Open`, `My Open Today`, `My Open P1`, `Team Open`, `Team Open P1`, and many personal copies that were later shared publicly.

**Problem:** Agents cannot tell which views are authoritative. Queue triage is inconsistent because every team lead creates another near-duplicate working view.

**Solution:**

Create a governed working set:

```text
Case list views
- My Open Cases
  Filters: Owner = Me, Status != Closed
  Columns: Case Number, Priority, Subject, Account, Status, Last Modified

- Team Escalations
  Filters: Queue = Escalations, Status != Closed
  Columns: Case Number, Severity, Account, SLA Breach Risk, Owner, Age

- Unassigned New Cases
  Filters: Queue = Intake, Owner = Queue, Created Date = TODAY
  Columns: Case Number, Channel, Priority, Contact, Created Date
```

**Why it works:** Each view has a single operational purpose. Users browse a smaller, trusted set of working queues instead of navigating public clutter.

---

## Example 2: Compact Layout Optimized For Mobile Field Technicians

**Context:** Field technicians open Work Orders in the Salesforce mobile app. The standard highlights panel surfaces too much administrative data and not enough dispatch context.

**Problem:** Technicians still have to open multiple sections just to confirm the appointment, service address, and job status.

**Solution:**

Use a compact layout that answers recognition and dispatch questions immediately:

```text
Work Order compact layout
- Work Order Number
- Status
- Service Appointment Window
- Contact Phone
- Service Territory
- Priority
```

Move long descriptions, entitlement details, and historical notes out of the compact layout and leave them on the full record page.

**Why it works:** The highlights panel becomes a scan layer that supports mobile decision-making instead of duplicating the entire page layout.

---

## Anti-Pattern: Trying To Fix Search With More List-View Columns

**What practitioners do:** Users complain that search results are unhelpful, so admins keep adding more columns to list views and sharing more views publicly.

**What goes wrong:** Search remains confusing, list views become crowded, and the real problem - search-result presentation and record identification - is never addressed.

**Correct approach:** Treat search-result presentation and browse queues as separate UX problems. Tune each surface for its job.
