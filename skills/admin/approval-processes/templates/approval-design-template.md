# Approval Process Design Template

Use this before building or changing any Approval Process.

---

## Overview

| Property | Value |
|----------|-------|
| Process name | TODO |
| Object | TODO |
| Business purpose | TODO |
| Submitter population | TODO |
| Approver source | TODO |
| Record locks on submit | Yes / No |

## Entry Criteria

| Criterion | Value |
|-----------|-------|
| When can users submit? | TODO |
| Fields required before submit | TODO |
| Who can submit? | TODO |
| How are invalid submissions blocked? | TODO |

## Step Design

| Step | Criteria | Approver | On Approval | On Rejection |
|------|----------|----------|-------------|--------------|
| 1 | TODO | TODO | TODO | TODO |
| 2 | TODO | TODO | TODO | TODO |
| 3 | TODO | TODO | TODO | TODO |

## Submission and Recall

| Event | Actions |
|-------|---------|
| Initial submission | TODO |
| Final approval | TODO |
| Final rejection | TODO |
| Recall | TODO |

## Operational Checks

- [ ] Approver fields are guaranteed populated before submit
- [ ] Locked-record impact tested with real user personas
- [ ] Email templates reviewed
- [ ] Pending approval SLA defined
- [ ] "Wrong tool?" check completed against Flow/custom approval option
