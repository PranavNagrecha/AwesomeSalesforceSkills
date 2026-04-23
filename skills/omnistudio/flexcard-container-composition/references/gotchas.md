# FlexCard Composition — Gotchas

## 1. Nested FlexCards Each Make Their Own Data Call

Four nested cards mean four datasource calls at load. Flatten when parent
already has the data; use `None` layout for pure containers.

## 2. Event Names Are Global

Event names are strings with no namespace. Two cards emitting
`rowselected` on the same page will interfere. Namespace your event
names: `quoteselected`, `casewidget_rowselected`.

## 3. Input Parameters Vs State

Input parameters are evaluated at render; they do not react to state
changes. If a value should react, bind it to state or fire an event.

## 4. Direct SOQL Datasource Bypasses FLS

The direct SOQL datasource reads regardless of field-level security. If
the card is user-facing, go through an IP with `WITH USER_MODE` or
equivalent enforcement.

## 5. Preview Does Not Fully Match Experience Cloud

Preview runs with the author's permissions. Test in the target context
(Internal, Guest, Experience Cloud user) before declaring success.

## 6. FlexCard Update Action Does Not Fire Triggers Predictably

DR Update through a FlexCard action goes through Salesforce APIs but
lacks the IP's batching and cache invalidation. For anything non-trivial,
use an IP as the action target.

## 7. Navigation From FlexCard Requires Lightning Context

Hardcoded URLs break in Experience Cloud and mobile. Always use the
Navigate action type and let the platform resolve the URL.

## 8. Action Spinner Blocks The Whole Card

Long-running action with default spinner blocks the full card. Surface
progress at a row level or use an IP that returns quickly with a job id.
