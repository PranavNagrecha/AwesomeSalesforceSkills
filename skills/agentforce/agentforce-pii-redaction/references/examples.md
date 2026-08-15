# Examples — Agentforce PII Redaction

Five worked examples. Every one of them exists because of a single documented
platform fact that most teams get wrong:

> **Pattern-based and field-based data masking for LLMs is disabled for
> agents.** It remains available for embedded generative AI features such as
> Einstein Service Replies and Einstein Work Summaries, where you configure it
> in Einstein Trust Layer setup.
> — [Data Masking Limitations in Agentforce](https://help.salesforce.com/s/articleView?id=ai.agent_trust_data_masking.htm&type=5)

So if you are building an **agent**, the Trust Layer does not scrub your prompt
for you. Zero-retention agreements with the model providers still apply, and
data is still protected in transit — but the *content* of the prompt reaches the
model unmasked. Redaction is your application's job, in your own Apex, before
the context is assembled.

---

## Example 1 — Field classification register, and the two columns most teams omit

### Context

A financial-services org is grounding a service agent on `Contact`, `Case`, and
a custom `Financial_Account__c`. The team produced a two-column register
(field → "sensitive yes/no") and stopped there.

### Problem

"Sensitive yes/no" does not tell an implementer what to *do*. Two fields that
are both "sensitive" need opposite handling: an email address is usually needed
for the agent to confirm identity (mask, keep the domain), while a full account
number is never needed for reasoning (drop it, keep only a last-4 display
token).

### Solution — the four-column register

| Object.Field | Class | Strategy | Why the agent still works without the raw value |
|---|---|---|---|
| `Account.Name` | Public | As-is | Needed for every response; already visible to the user. |
| `Contact.Title` | Internal | As-is | Used for tone; no re-identification risk on its own. |
| `Contact.Email` | Confidential | Mask local part (`j***@acme.com`) | Agent only needs to say "I'll email the address ending in @acme.com". |
| `Contact.Phone` | Confidential | Mask to last 4 (`***-***-1234`) | Agent confirms the number, never reads it out. |
| `Contact.MailingStreet` | Confidential | Drop; substitute `city_state` | Address line is never needed for routing decisions. |
| `Financial_Account__c.Account_Number__c` | Regulated | Drop; emit `account_ref` surrogate | Actions resolve the surrogate to the real Id server-side. |
| `Contact.SSN__c` | Regulated | Drop, unconditionally | No agent task requires it. |
| `Contact.Birthdate` | Regulated | Summarise to `age_band` (`40-49`) | Eligibility rules need the band, not the date. |
| `Case.Description` | Confidential (free text) | Detector pass, then truncate | Free text is the highest-risk field on the object. |

The two columns teams omit are **Strategy** and **why the agent still works**.
The second one is the review gate: if nobody can write that sentence, the field
is being sent for no reason and should be dropped.

Keep the register in source control next to the redaction class. The template
in `templates/redaction-register.md` (skill-local) is the starting shape.

---

## Example 2 — WRONG vs RIGHT: assembling agent context

### WRONG — raw SObject reaches the prompt

```apex
public with sharing class CustomerContextProvider {

    @InvocableMethod(label='Get Customer Context')
    public static List<Response> run(List<Request> requests) {
        List<Response> out = new List<Response>();
        for (Request req : requests) {
            Contact c = [
                SELECT Id, Name, Email, Phone, Birthdate, SSN__c, MailingStreet
                FROM Contact
                WHERE Id = :req.contactId
                WITH USER_MODE
            ];
            Response r = new Response();
            // WRONG: JSON.serialize on the SObject ships every queried field,
            // including SSN__c and MailingStreet, straight into the prompt.
            r.contextJson = JSON.serialize(c);
            out.add(r);
        }
        return out;
    }
    // ...
}
```

Two independent failures here. First, `JSON.serialize(sObject)` emits every
field the SOQL selected — adding a field to the query silently adds it to the
prompt, with no code review signal. Second, there is no Trust Layer masking
behind this for an agent, so `SSN__c` reaches the model verbatim.

### RIGHT — a redacted DTO is the only thing that can be serialised

```apex
/**
 * CustomerContextProvider
 *
 * The ONLY path from Contact data into agent prompt context.
 * Rule: this class returns CustomerContext, never Contact. There is no
 * overload that returns the SObject.
 */
public with sharing class CustomerContextProvider {

    /** Redacted transfer object. Every field here is safe to send to an LLM. */
    public class CustomerContext {
        public String displayName;      // "Jordan P."
        public String emailDomain;      // "acme.com"
        public String phoneLast4;       // "1234"
        public String ageBand;          // "40-49"
        public String cityState;        // "Austin, TX"
        public String accountRef;       // surrogate, resolved server-side
        // Deliberately absent: SSN, full email, full phone, street, birthdate.
    }

    public class Request {
        @InvocableVariable(required=true label='Contact Id')
        public Id contactId;
    }

    public class Response {
        @InvocableVariable(label='Redacted customer context as JSON')
        public String contextJson;
        @InvocableVariable(label='Status' description='OK or NOT_FOUND')
        public String status;
    }

    @InvocableMethod(
        label='Get Customer Context'
        description='Returns a redacted customer profile. Never returns raw PII.'
    )
    public static List<Response> run(List<Request> requests) {
        Set<Id> ids = new Set<Id>();
        for (Request req : requests) {
            ids.add(req.contactId);
        }

        // USER_MODE enforces the running user's FLS and sharing. It does NOT
        // redact — a user who can see SSN__c will still get it back. FLS and
        // redaction are orthogonal controls; you need both.
        Map<Id, Contact> byId = new Map<Id, Contact>([
            SELECT Id, FirstName, LastName, Email, Phone, Birthdate,
                   MailingCity, MailingState, Financial_Account__c
            FROM Contact
            WHERE Id IN :ids
            WITH USER_MODE
        ]);

        // One Response per Request, same order — required by @InvocableMethod.
        List<Response> out = new List<Response>();
        for (Request req : requests) {
            Response r = new Response();
            Contact c = byId.get(req.contactId);
            if (c == null) {
                r.status = 'NOT_FOUND';
                r.contextJson = '{}';
            } else {
                r.status = 'OK';
                r.contextJson = JSON.serialize(PIIRedactor.toContext(c));
            }
            out.add(r);
        }
        return out;
    }
}
```

```apex
/**
 * PIIRedactor — the single redaction boundary.
 *
 * Every transformation is pure and unit-testable. Nothing in this class
 * reads from the database, so the tests need no DML.
 */
public with sharing class PIIRedactor {

    public static CustomerContextProvider.CustomerContext toContext(Contact c) {
        CustomerContextProvider.CustomerContext ctx =
            new CustomerContextProvider.CustomerContext();
        ctx.displayName = abbreviateName(c.FirstName, c.LastName);
        ctx.emailDomain = domainOnly(c.Email);
        ctx.phoneLast4  = last4(c.Phone);
        ctx.ageBand     = ageBand(c.Birthdate);
        ctx.cityState   = joinNonBlank(c.MailingCity, c.MailingState);
        ctx.accountRef  = surrogate(c.Financial_Account__c);
        return ctx;
    }

    /** "Jordan" + "Priestley" -> "Jordan P." */
    private static String abbreviateName(String first, String last) {
        if (String.isBlank(first) && String.isBlank(last)) return 'Customer';
        String initial = String.isBlank(last) ? '' : ' ' + last.substring(0, 1) + '.';
        return (String.isBlank(first) ? '' : first) + initial;
    }

    /** "jordan@acme.com" -> "acme.com". Local part never leaves the boundary. */
    private static String domainOnly(String email) {
        if (String.isBlank(email)) return null;
        Integer at = email.indexOf('@');
        return at < 0 ? null : email.substring(at + 1);
    }

    private static String last4(String phone) {
        if (String.isBlank(phone)) return null;
        String digits = phone.replaceAll('[^0-9]', '');
        return digits.length() < 4 ? null : digits.right(4);
    }

    /**
     * Date of birth -> decade band. Bands, not ages: an exact age plus a
     * city is often enough to re-identify someone in a small population.
     */
    private static String ageBand(Date dob) {
        if (dob == null) return null;
        Integer years = dob.daysBetween(Date.today()) / 365;
        Integer decade = (years / 10) * 10;
        return decade + '-' + (decade + 9);
    }

    /**
     * Surrogate reference. The agent passes `account_ref` back into actions;
     * the action resolves it to the real Id. The model never sees an account
     * number and cannot fabricate a valid one.
     */
    private static String surrogate(Id recordId) {
        return recordId == null
            ? null
            : 'ACCT_' + EncodingUtil.convertToHex(
                  Crypto.generateDigest('SHA-256', Blob.valueOf(String.valueOf(recordId)))
              ).substring(0, 12).toUpperCase();
    }

    private static String joinNonBlank(String a, String b) {
        List<String> parts = new List<String>();
        if (String.isNotBlank(a)) parts.add(a);
        if (String.isNotBlank(b)) parts.add(b);
        return parts.isEmpty() ? null : String.join(parts, ', ');
    }
}
```

### Why the DTO shape is load-bearing

The rule "prompts receive `CustomerContext`, never `Contact`" is enforceable in
code review with a grep: any `JSON.serialize` of an SObject inside a prompt
assembly path is a finding. "Remember to redact" is not enforceable. The
skill-local checker in `scripts/check_agentforce_pii_redaction.py` looks for
exactly this shape.

---

## Example 3 — Input-side detection, and why the agent must not be the detector

### Context

A retail agent handles order enquiries. Customers routinely volunteer card
numbers in the chat: *"my card 4111 1111 1111 1111 was charged twice."*

### Problem

The obvious fix — a subagent instruction (subagents were called topics before
April 2026) saying *"If the user provides a card number, do not repeat it"* —
is a request to the model, not a control. It fails open: the number is already
in the conversation transcript that gets sent to the model, and instruction
adherence is probabilistic.

### Solution — detect and neutralise before the turn reaches the planner

Run detection in the channel/pre-processing layer you control (an Apex service
in front of the Agent API, or a Flow on the inbound message), not inside the
agent's own reasoning.

```apex
/**
 * SensitiveInputDetector — pattern pass over an inbound user turn.
 *
 * Deliberately conservative: over-matching is a UX cost, under-matching is a
 * compliance incident. Patterns live here, in one class, with tests.
 */
public with sharing class SensitiveInputDetector {

    public enum Category { CARD, SSN, IBAN, NONE }

    // 13-19 digits, optionally separated by spaces or hyphens.
    private static final Pattern CARD = Pattern.compile(
        '\\b(?:\\d[ -]*?){13,19}\\b');
    // US SSN, tolerant of space and dot separators as well as hyphen.
    private static final Pattern SSN = Pattern.compile(
        '\\b\\d{3}[-. ]\\d{2}[-. ]\\d{4}\\b');
    private static final Pattern IBAN = Pattern.compile(
        '\\b[A-Z]{2}\\d{2}[A-Z0-9]{11,30}\\b');

    public class Finding {
        public Category category;
        public String scrubbedText;
    }

    public static Finding scan(String userTurn) {
        Finding f = new Finding();
        f.category = Category.NONE;
        f.scrubbedText = userTurn;
        if (String.isBlank(userTurn)) return f;

        String cardScrubbed = redactValidCards(userTurn);

        if (SSN.matcher(userTurn).find()) {
            f.category = Category.SSN;
            f.scrubbedText = SSN.matcher(userTurn).replaceAll('[REDACTED_SSN]');
        } else if (cardScrubbed != userTurn) {
            f.category = Category.CARD;
            f.scrubbedText = cardScrubbed;
        } else if (IBAN.matcher(userTurn).find()) {
            f.category = Category.IBAN;
            f.scrubbedText = IBAN.matcher(userTurn).replaceAll('[REDACTED_IBAN]');
        }
        return f;
    }

    /**
     * Luhn-check every CARD match INDIVIDUALLY and redact only the ones that
     * pass. Returns the input unchanged when nothing valid was found.
     *
     * Luhn must be applied per match, never to the whole turn: "card
     * 4111 1111 1111 1111, order 8842" has 20 digits in total, so a
     * whole-string check fails the length guard and the detector silently
     * fails open on a real card number.
     */
    private static String redactValidCards(String userTurn) {
        Matcher m = CARD.matcher(userTurn);
        String out = userTurn;
        while (m.find()) {
            String candidate = m.group();
            if (passesLuhn(candidate)) {
                out = out.replace(candidate, '[REDACTED_CARD]');
            }
        }
        return out;
    }

    /**
     * Luhn check on a single candidate. Without it, order numbers and
     * tracking numbers match the CARD pattern and get scrubbed, which breaks
     * the very lookups the agent needs to perform.
     */
    private static Boolean passesLuhn(String text) {
        String digits = text.replaceAll('[^0-9]', '');
        if (digits.length() < 13 || digits.length() > 19) return false;
        Integer sum = 0;
        Boolean alternate = false;
        for (Integer i = digits.length() - 1; i >= 0; i--) {
            Integer n = Integer.valueOf(digits.substring(i, i + 1));
            if (alternate) {
                n *= 2;
                if (n > 9) n -= 9;
            }
            sum += n;
            alternate = !alternate;
        }
        return Math.mod(sum, 10) == 0;
    }
}
```

Three dispositions, chosen per subagent sensitivity:

| Disposition | When | What the user sees |
|---|---|---|
| **Refuse** | Regulated categories in a low-assurance channel | "For your security, please don't share full card or ID numbers here." Turn is dropped. |
| **Redact and continue** | Confidential categories, conversation should not stall | Scrubbed text goes to the planner; agent proceeds. |
| **Route to human** | Category implies a fraud/compliance path | Escalation subagent fires; the raw turn is stored in the case, not the prompt. |

**Why the Luhn check matters:** `4111111111111111` and an order number
`10004561234567` both match a naive 13–19 digit pattern. Without Luhn, the
detector scrubs the order number, the agent can't look up the order, and the
team disables the detector within a week. Precision is what keeps a control
switched on.

---

## Example 4 — The grounding corpus is prompt context too

### Context

A support agent grounds on a Knowledge base. A Knowledge article titled
"Escalation contacts for Tier 3 outages" lists five engineers by name, mobile
number, and personal email.

### Problem

Field-level classification covered `Contact` and `Case`. Nobody classified
Knowledge. The retrieved article chunk goes into the prompt intact, and the
agent will happily read a mobile number out to an external customer who asks
"who can I escalate to?"

### Solution — treat every retrievable corpus as an input requiring the same pass

1. **Inventory the retrievable set.** Knowledge articles, ChatterFeed items,
   files indexed for search, any Data Cloud object exposed as a retriever.
2. **Sample and scan.** Run `SensitiveInputDetector.scan()` over article bodies
   in a batch job. Report, do not auto-edit — publishing decisions belong to the
   Knowledge owner.
3. **Gate at publish time.** Add a validation rule or a
   before-save record-triggered Flow on the Knowledge article that blocks
   publishing when the body matches a regulated pattern.
4. **Scope the retriever.** Prefer a retriever restricted to an article *type*
   or data category that only contains customer-safe content, over one pointed
   at the whole base with a prompt-level instruction to "avoid internal
   articles."

The general rule: anything that can end up inside the prompt window is prompt
context, regardless of which platform feature put it there.

---

## Example 5 — Audit event that records the action without recording the value

### Context

Compliance asks: "prove that SSN never reached the model in Q3."

### Problem

The obvious implementation logs the field and its value so you can show what was
scrubbed. That turns the audit log itself into the largest PII store in the org,
usually with weaker access controls than the source object.

### Solution — log the decision, never the datum

```apex
/**
 * Emitted from PIIRedactor at each redaction decision. Platform Event, so it
 * survives a rollback of the transaction that triggered it.
 */
PII_Redaction__e evt = new PII_Redaction__e(
    Topic__c            = 'BillingInquiry',
    Field_Api_Name__c   = 'Contact.SSN__c',
    Strategy__c         = 'DROP',
    Value_Hash__c       = hashForCorrelation(rawValue),  // salted SHA-256
    Session_Id__c       = sessionId,
    Occurred_At__c      = System.now()
);
EventBus.publish(evt);
```

```json
{
  "event": "pii_redaction",
  "topic": "BillingInquiry",
  "field": "Contact.SSN__c",
  "strategy": "DROP",
  "value_hash": "9f2c...e41a",
  "session_id": "0Mv...",
  "at": "2026-08-14T10:15:02Z"
}
```

Notes on the shape:

- **No `value`.** The field name plus strategy is what an auditor needs.
- **`value_hash` is salted and org-scoped.** It lets you answer "was this the
  same value across two sessions?" without storing the value. An unsalted hash
  of an SSN is reversible by brute force in seconds — the keyspace is under a
  billion. Salt it, or omit the column.
- **Platform Event, not a `Log__c` insert.** If the transaction rolls back, a
  DML-inserted log row disappears; the redaction still happened and you still
  want the record. Confirm the event's publish behaviour in Setup before relying
  on this — the "publish immediately" behaviour is what decouples the audit
  record from the transaction's outcome, and it is a per-event configuration.

### The report compliance actually wanted

A Data Cloud / CRM Analytics lens over the event stream, grouped by
`Field_Api_Name__c` × `Strategy__c` × week. Two things make it a control rather
than a log:

- A **zero row is a finding.** If `Contact.SSN__c` shows zero `DROP` events in a
  week when the agent handled 4,000 sessions, either nobody asked about
  accounts, or the redaction boundary was bypassed. Alert on the absence.
- A **new field appearing** in the stream means someone added a field to a
  context query. That is the change-detection signal for the register in
  Example 1.

---

## Anti-Pattern — "we enabled the Trust Layer, so PII is handled"

**What practitioners do:** open Einstein Trust Layer setup, tick the masking
entities, and close the compliance ticket.

**What goes wrong:** for **agents**, pattern-based and field-based LLM data
masking is disabled — Salesforce turns it off to improve agent performance and
accuracy ([Data Masking Limitations in
Agentforce](https://help.salesforce.com/s/articleView?id=ai.agent_trust_data_masking.htm&type=5)).
The setup screen still shows your configuration, because the same screen governs
embedded features like Einstein Service Replies and Work Summaries, where
masking *does* apply. Nothing in the UI tells you the agent path skips it. The
team believes it has a control it does not have.

**Correct approach:** for agent workloads, treat Trust Layer masking as absent
and redact in your own code (Examples 2 and 3). What the Trust Layer *does*
still give agents is the part that matters most legally: zero-retention
agreements with the model providers, protection in transit, and the audit trail.
That is a data-handling guarantee about the provider, not a content filter about
your prompt. Write both facts into the design doc so the next reviewer does not
re-derive them.
