# Deploy order — M1-S01

One component, one deploy step:

1. `Flow: Case_Escalation_Notify_Account_Owner` — no dependencies on any other artefact in this
   build. Deploys standalone against the standard `Case`, `Account`, `User`, and (assumed
   pre-existing in the target org) `Application_Log__c` objects.

## Pre-deploy checklist (human, before running the validate-only command below)

- [ ] Confirm `Application_Log__c` (with `Severity__c`, `Source__c`, `Message__c`,
      `Request_Id__c` fields) already exists in the target org. This build does not create it —
      it is the same object the repo's Apex `ApplicationLogger` template and
      `templates/flow/FaultPath_Template.md` both write to. If it does not exist yet in this org,
      deploy it first (see `templates/apex/ApplicationLogger.cls` and its companion custom object
      metadata) or the two `recordCreates` elements in this Flow will fail every time and fall
      through to the fault chain's own log-write, which will fail identically.
- [ ] Replace the two placeholder addresses before activating in production:
      `support-manager@example.com` (Send_Email_To_Support_Manager_Fallback) and
      `sfadmin@example.com` (Notify_Admin_On_Fault) — both are literal stand-ins per Q3/Q4's
      answers, not real distribution-list addresses.
- [ ] Confirm an Organization-Wide Email Address exists if the org wants the notification to send
      from something other than the default no-reply sender (Q2 answer: no OWEA is required, but
      confirm once against the actual org).

## Validate-only command (human decision; nothing in this build runs it)

```bash
sf project deploy validate --source-dir .sfskills/builds/case-escalation-email-alert/artefacts/M1-S01 --target-org <alias> --test-level RunLocalTests
```

Or, non-destructively:

```bash
python3 scripts/mock_deploy.py .sfskills/builds/case-escalation-email-alert/plan.json --org-alias <alias> --milestone M1 --dry-run
```
