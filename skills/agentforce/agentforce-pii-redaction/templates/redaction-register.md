# PII Redaction Register

## Classification

| Object.Field | Class (Public/Internal/Confidential/Regulated) | Strategy (asis/mask/tokenize/drop/summarise) | Owner |
|---|---|---|---|

## Input-Side Detection

- [ ] SSN pattern
- [ ] Credit card pattern
- [ ] Email pattern
- [ ] Phone pattern

## Output-Side Pass

- [ ] Second-pass redaction on agent response before send.

## Audit

- [ ] Redaction events logged (without values).
- [ ] Weekly review.
- [ ] PII adversarial cases included in eval suite.

## Sign-Off

- [ ] No raw sensitive fields referenced in prompt templates.
- [ ] Central redaction module is the only path to prompt context.
- [ ] KB corpus sanitised.
- [ ] Debug logging of PII forbidden.
