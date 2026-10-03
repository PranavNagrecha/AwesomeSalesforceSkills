# Prompt Builder Templates — Work Template

Use this template when building, reviewing, or troubleshooting a Salesforce Prompt Builder template.

---

## Scope

**Skill:** `prompt-builder-templates`

**Request summary:** (fill in what was asked — e.g., "Create a Field Generation template to populate Case Resolution Summary", "Audit all Flex templates for inactive versions", "Diagnose why agent action returns blank output")

**Mode (circle one):** Create / Review-Audit / Troubleshoot

---

## Context Gathered

Answer these before taking action:

| Question | Answer |
|---|---|
| Einstein generative AI enabled in this org? | Yes / No / Unknown |
| Author has Prompt Template Manager; end users have Prompt Template User? | Yes / No / Unknown |
| Template type needed or in scope | Field Generation / Record Summary / Sales Email / Flex |
| Target object (for Field Generation) | |
| Target field (for Field Generation) | |
| Deployment surface | Record page / Agent action / Quick action / Screen flow / Email composer |
| Data to ground (sources) | Record fields / Related objects / Flow / Apex / External API / Data Cloud |
| Active version exists already? | Yes / No |
| Grounding resources (Flows, Apex classes) | List names here |
| Trust Layer masking rules active in target environment? | Yes / No / Unknown |

---

## Template Design

*(Complete this section for Mode 1 — Create)*

**Template name:** (API-friendly, no spaces, reflects object + purpose — e.g., `Case_Resolution_Summary`)

**Template type:** Field Generation / Record Summary / Sales Email / Flex

**Anchor object:** (e.g., `Case`, `Opportunity`, `Contact`)

**Target field (Field Generation only):** (e.g., `Resolution_Summary__c`)

**Grounding strategy decision:**

| Data needed | Where it lives | Grounding method chosen | Rationale |
|---|---|---|---|
| | | Record merge field / Flow / Apex / Related list / Einstein Search | |
| | | Record merge field / Flow / Apex / Related list / Einstein Search | |

**Prompt body draft:**

```
[Role / persona assignment]
[Task instruction with format constraints — specify length, tone, structure]
[Merge field placeholders — use Insert Resource panel, not hand-typed tokens]
[Output constraints — e.g., "Write 3–5 sentences. Do not include a greeting."]
```

**Flow or Apex grounding resource names:**

- Flow name: `_________________________` (must be Template-Triggered Prompt Flow type)
- Apex class: `_________________________` (one `@InvocableMethod`; `List<Request>` in, `List<Response>` with String `Prompt` out)
- CapabilityType (optional; omit for Flex and for einstein_gpt__caseEmailDraft): `PromptTemplateType://einstein_gpt______________`

---

## Review Findings

*(Complete this section for Mode 2 — Review/Audit)*

| Template name | Type | Active version? | Grounding resources active? | Permission gap? | Notes |
|---|---|---|---|---|---|
| | | Yes / No | Yes / No / N/A | Yes / No | |
| | | Yes / No | Yes / No / N/A | Yes / No | |
| | | Yes / No | Yes / No / N/A | Yes / No | |

**Summary of findings:**

- Templates with no active version: (list)
- Templates with inactive grounding Flows: (list)
- Templates whose Flow or Apex inputs changed since the template was built: (list)
- Permission gaps (Prompt Template Manager for authors, Prompt Template User for users): (describe)

---

## Troubleshooting Log

*(Complete this section for Mode 3 — Troubleshoot)*

**Symptom:** Blank output / Hallucinated output / Wrong data / Template not visible / Other

**Steps taken:**

1. Opened template in Prompt Builder — active version: Yes / No
2. Save & Preview with record ID: `_________________`
3. Resolved Prompt result: All tokens resolved / Unresolved tokens found (list below)
4. Unresolved tokens: `{! _________________________ }` — reason: field renamed / relationship null / Flow failed / Apex mismatch
5. Flow tested independently in Flow Builder: Pass / Fail / Not applicable
6. Apex contract checked by `scripts/check_prompt_builder_templates.py`: Pass / Fail / Not applicable
7. Trust Layer masking checked: Masking active / Masking not active / Unknown

**Root cause:** (one sentence)

**Remediation:** (steps to fix)

---

## Checklist

- [ ] Template type matches deployment surface
- [ ] At least one version is active
- [ ] Save & Preview run against a real record with populated data
- [ ] Resolved Prompt panel shows all merge fields resolved to actual values
- [ ] Grounding Flows tested independently in Flow Builder
- [ ] Apex Request and Response contract verified; no `FlexTemplate://` CapabilityType
- [ ] Running user object/field permissions confirmed for all fields used in merge fields
- [ ] Prompt Template User assigned to everyone who runs the template
- [ ] Trust Layer masking validated in the target environment
- [ ] If packaged: subscriber permission requirement documented in release notes

---

## Notes and Deviations

(Record any decisions that deviate from the standard patterns described in SKILL.md and why.)
