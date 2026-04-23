# PII Redaction — Examples

## Example 1: Field Classification Register

```text
| Object.Field              | Class        | Strategy   |
|---------------------------|--------------|------------|
| Contact.Email             | Confidential | Mask       |
| Contact.Phone             | Confidential | Mask       |
| Contact.SSN__c            | Regulated    | Drop       |
| Payment.CCLast4           | Regulated    | Mask (last 4) |
| Patient.DOB__c            | Regulated    | Summarise (age band) |
| Account.Name              | Public       | As-is      |
```

## Example 2: Redaction Helper (Apex Sketch)

```java
public class PIIRedactor {
  public static ContactContext redact(Contact c) {
    ContactContext ctx = new ContactContext();
    ctx.name = c.Name;
    ctx.emailMasked = maskEmail(c.Email);
    ctx.phoneMasked = maskPhone(c.Phone);
    // SSN intentionally omitted
    return ctx;
  }

  private static String maskEmail(String e) {
    if (String.isBlank(e)) return null;
    Integer at = e.indexOf('@');
    if (at < 1) return '***';
    return e.substring(0,1) + '***' + e.substring(at);
  }
}
```

Prompts must accept only `ContactContext`, never raw `Contact`.

## Example 3: Input-Side Detection Pattern

```text
Pattern: \b\d{3}-\d{2}-\d{4}\b  → flag as SSN
Pattern: \b(?:\d[ -]*?){13,16}\b → flag as possible card number
```

On match, choose to refuse, redact, or escalate per topic policy.

## Example 4: Summarise Strategy (Age Band)

Instead of `DOB = 1980-03-14`, prompt receives `age_band = "40-49"`.
The model gets enough to reason; the exact DOB never leaves the boundary.

## Example 5: Audit Event Record

```json
{
  "event": "pii_redaction",
  "topic": "BillingInquiry",
  "field": "Contact.Phone",
  "strategy": "mask",
  "at": "2026-04-20T10:15:02Z"
}
```

Note: no value is logged, only the action.
