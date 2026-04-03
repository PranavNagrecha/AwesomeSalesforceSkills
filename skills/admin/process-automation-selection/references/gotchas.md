# Process Automation Selection — Gotchas

## 1. A Working Legacy Automation Is Still Architecture Debt

Teams often keep Workflow Rule or Process Builder logic because it has not failed loudly yet.

Avoid it:
- Inventory the legacy behavior explicitly.
- Rebuild it on a current automation boundary instead of planning around it.

## 2. Before-Save Flow Is Underused

The team may jump straight to Apex or after-save Flow for the simple reason that those surfaces feel more flexible.

Avoid it:
- Ask whether the requirement only updates the triggering record.
- Choose before-save Flow when that answer is yes.

## 3. Mixed Automation Layers Hide Ownership Problems

One business rule split across Flow, trigger logic, and validation often becomes hard to support.

Avoid it:
- Keep one clear owner for each automation concern.
- Document the exceptions when both Flow and Apex are deliberately involved.

## 4. Tool Choice Changes At Scale

A prototype-friendly Flow may not remain the right answer when imports, integrations, or heavy reuse arrive.

Avoid it:
- Evaluate real transaction volume early.
- Revisit the boundary when performance or operability changes.
