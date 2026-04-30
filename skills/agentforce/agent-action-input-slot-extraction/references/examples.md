# Examples — Agent Action Input Slot Extraction

## Example 1: Schedule appointment — date + severity slots

**Context:** Service agent action `ScheduleAppointment` takes `Date appointmentDate`, `String customerAccountName`, and a Severity enum.

**Problem:** Agent fills `appointmentDate` with today when the user said "next Tuesday afternoon" because the LLM picks the parseable noun nearest the action keyword.

**Solution:**

```apex
public class ScheduleAppointment {

    public class Request {
        @InvocableVariable(
            label='Appointment Date'
            description='The customer\'s requested appointment date in ISO 8601 (YYYY-MM-DD), in the running user\'s timezone. Example: "2026-05-12". Reject relative phrases like "next week" — re-prompt the user for an explicit date.'
            required=true)
        public Date appointmentDate;

        @InvocableVariable(
            label='Customer Account Name'
            description='The customer\'s account name as the user said it (e.g., "Acme Corp", "ACME"). Do NOT emit a Salesforce ID. The action resolves the name to an account internally.'
            required=true)
        public String customerAccountName;

        @InvocableVariable(
            label='Severity'
            description='Issue severity, one of: LOW (cosmetic, no impact), MEDIUM (workaround exists), HIGH (production blocked). Synonyms: "critical"/"urgent" = HIGH; "minor"/"trivial" = LOW. Emit the uppercase value only.'
            required=true)
        public String severity;
    }

    @InvocableMethod(label='Schedule Appointment')
    public static List<Response> run(List<Request> reqs) {
        // resolve customerAccountName → Account.Id with ambiguity handling
        // normalize severity to uppercase
        // ...
    }
}
```

**Test utterances:**

```yaml
- utterance: "schedule for Acme on next Tuesday afternoon, it's urgent"
  expected:
    appointmentDate: <re-prompt; "next Tuesday" rejected>
    customerAccountName: "Acme"
    severity: "HIGH"

- utterance: "Book Acme Corp for 2026-05-12, it's blocking production"
  expected:
    appointmentDate: "2026-05-12"
    customerAccountName: "Acme Corp"
    severity: "HIGH"
```

**Why it works:** The description teaches the LLM exactly what to extract and what to reject. Severity synonyms are enumerated. Account is taken as a string and resolved server-side, eliminating ID hallucination.

---

## Example 2: Per-slot re-prompt configuration

**Context:** Required slot `appointmentDate` gets rejected (relative phrasing). Generic agent re-prompt: "Please provide more information."

**Problem:** Generic re-prompt confuses the user; they don't know which slot is missing.

**Solution:** Configure per-slot re-prompt in the agent topic configuration:

```yaml
topic: schedule_appointment
required_slot_re_prompts:
  appointmentDate:
    text: "What date should I book the appointment for? Please give an explicit date like 'May 12' or 'next Tuesday May 19'."
  customerAccountName:
    text: "Which account is this for?"
  severity:
    text: "How severe is the issue — low, medium, or high?"
```

**Why it works:** The user gets a precise question identifying the missing slot with an example.

---

## Anti-Pattern: taking a record Id directly

**What practitioners do:**

```apex
@InvocableVariable(description='Account ID')
public Id accountId;
```

**What goes wrong:** LLM hallucinates `001000000000XYZAA` from "Acme Corp". The ID is well-shaped but doesn't exist. The action fails with a generic SOQL error the agent can't recover from.

**Correct approach:** Take a `String accountName` and resolve inside Apex:

```apex
List<Account> matches = [
    SELECT Id FROM Account WHERE Name = :req.customerAccountName LIMIT 5
];
if (matches.isEmpty()) throw new ActionError('No account named ' + req.customerAccountName);
if (matches.size() > 1) throw new AmbiguousAccount(matches);
Id accountId = matches[0].Id;
```

`AmbiguousAccount` is a custom exception type the agent topic handles by asking the user to clarify.
