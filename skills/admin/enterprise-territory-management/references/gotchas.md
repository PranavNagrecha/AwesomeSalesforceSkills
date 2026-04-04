# Gotchas — Enterprise Territory Management

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Activating a Territory Model Triggers Immediate Full Assignment Recalculation

**What happens:** The moment a territory model is transitioned from Planning to Active, Salesforce queues a background job to run all account assignment rules across the entire model. This is not deferred until business hours — it starts immediately. For orgs with tens of thousands of accounts, this job can run for several hours, during which assignment data is transitional and reports may show incomplete territory coverage.

**When it occurs:** Every time a model is activated (Planning → Active). There is no way to defer or batch this recalculation.

**How to avoid:** Schedule activation during off-peak hours (nights or weekends). Before activation, validate rule coverage in preview mode. Monitor the `Territory2AlignmentLog` object to track job completion. Do not treat territory reports or forecasts as reliable until the log shows all rules have finished running.

---

## Gotcha 2: Assignment Rules Are Not Retroactive — New Rules Don't Apply to Existing Accounts

**What happens:** When you create a new account assignment rule or modify an existing one, the rule is not automatically applied to accounts that already exist. Only accounts created or updated after the rule is saved (with IsActive = true) will be evaluated automatically. Existing accounts remain in their current territory assignments unchanged.

**When it occurs:** Any time a new rule is added or a rule's criteria are changed in an active model. This catches practitioners off guard when they add a new territory mid-year and expect all qualifying accounts to immediately appear in it.

**How to avoid:** After creating or modifying an assignment rule, manually run assignment rules at the territory level (for targeted updates) or the model level (for comprehensive recalculation). Do this during off-peak hours for large account volumes. Build this step into your territory change runbook.

---

## Gotcha 3: Archived Territory Models Cannot Be Reactivated

**What happens:** When a territory model is moved to Archived state, it becomes permanently read-only. The model cannot be promoted back to Active or Planning. If you accidentally archive your active model or archive a model you intended to reuse, you must recreate the entire structure from scratch — hierarchy, territory types, assignment rules, and user memberships.

**When it occurs:** Any time an admin clicks "Archive" on a territory model, including accidentally archiving the wrong model or archiving a Planning model that was being iterated.

**How to avoid:** Treat the Archive action as permanent and irreversible — build a confirmation step into your change process. Keep alternative territory designs in Planning state, not Archived. Before archiving, export the territory hierarchy structure and rule configurations for reference. Consider deploying a backup of the model configuration via Metadata API before archiving.

---

## Gotcha 4: Territory Forecast Sharing Is Not Supported

**What happens:** Territory-based forecast types do not support the forecast sharing feature that role-based forecast types offer. If a user tries to share their territory forecast with a colleague, the action has no effect. This is by design — Salesforce explicitly documents this limitation — but it frequently surprises teams migrating from role-based to territory-based forecasting.

**When it occurs:** When an organization enables territory-based forecasting and sales managers expect the same forecast sharing behavior they had with role-based forecasts.

**How to avoid:** Document this limitation during the territory design phase. If forecast sharing is a hard requirement, consider whether the organization can remain on role-based forecasting for forecast purposes while using territory-based assignment for account access and coverage. There is no workaround within ETM.

---

## Gotcha 5: Territory Membership Grants Access Regardless of Account Owner — OWD Still Sets the Floor

**What happens:** Territory membership adds access to accounts assigned to a territory, regardless of account ownership. This is intentional and useful, but it means that users gain visibility to accounts they do not own — sometimes surprising account owners or managers who expect OWD Private to fully restrict access.

Conversely, if OWD for Account is already set to "Public Read/Write," territory membership adds no additional access — the OWD floor already grants everyone access. Territory access is purely additive and cannot be used to restrict access below the OWD setting.

**When it occurs:** When admins configure territory membership assuming it can restrict access (it cannot), or when account owners are surprised that reps in their territory can see "their" accounts.

**How to avoid:** Treat territory membership as an access-expansion tool, not an access-restriction tool. If fine-grained restriction is needed, design OWD and sharing rules first (see the sharing-and-visibility skill), then layer ETM access on top. Communicate to account owners that territory membership is intentional and by design.
