# Gotchas — Patient Engagement Requirements

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Experience Cloud for Health Cloud Is Not Included in Base Health Cloud

**What happens:** An implementation proceeds to the portal configuration phase and discovers that Experience Cloud for Health Cloud requires a separately purchased add-on SKU, including per-user licenses for all patient portal users.

**When it occurs:** When the project scope assumes patient-facing portal capability is included in Health Cloud, based on product documentation that describes Health Cloud portal features without prominently disclosing the separate licensing requirement.

**How to avoid:** At project inception, explicitly confirm that Experience Cloud for Health Cloud is included in the contract. Request the full license breakdown from the Salesforce account team. Identify the per-user license cost and user count estimate before project budgeting.

---

## Gotcha 2: CRM Analytics Is Required for IAM No-Show Prediction

**What happens:** The implementation delivers Intelligent Appointment Management for patient self-scheduling, but no-show risk prediction — prominently featured in IAM marketing — is unavailable because CRM Analytics is not licensed.

**When it occurs:** When no-show prediction is included in requirements based on IAM marketing materials but CRM Analytics is not included in the license scope. The IAM core scheduling functionality works without CRM Analytics; only the predictive analytics layer requires it.

**How to avoid:** When scoping IAM, explicitly separate core scheduling requirements from predictive analytics requirements. If no-show prediction is in scope, add CRM Analytics as a separate license line item. Confirm with stakeholders whether the predictive features are must-have vs. nice-to-have before finalizing the license scope.

---

## Gotcha 3: OmniStudio and Discovery Framework Must Be Explicitly Installed

**What happens:** Health assessments using OmniScript forms fail to work or cannot be configured because OmniStudio was never installed in the org, even though the license is included in the Health Cloud contract.

**When it occurs:** When admins assume that licensing OmniStudio (included in Health Cloud) automatically installs and activates it. OmniStudio is a managed package that must be explicitly installed via the Salesforce AppExchange or managed package installer. Discovery Framework is a separate managed package that must also be installed.

**How to avoid:** During implementation kickoff, verify OmniStudio installation status: Setup > Installed Packages > search for OmniStudio. If not installed, follow the Health Cloud Administration Guide's OmniStudio installation steps. Install Discovery Framework after OmniStudio. Document both as go-live prerequisites.

---

## Gotcha 4: Secure Patient Messaging Must Use HIPAA-Covered Channels

**What happens:** Clinical communications (appointment reminders containing PHI, care plan instructions, assessment results) are routed through standard Salesforce email (Email-to-Case) or standard Chatter, both of which may not be covered under the standard Salesforce BAA for PHI.

**When it occurs:** When the messaging channel is designed for convenience rather than HIPAA compliance, or when the team assumes all Salesforce features are BAA-covered.

**How to avoid:** For any patient communication channel that may carry PHI (appointment details, care instructions, assessment results), explicitly verify BAA coverage for that channel. Use Salesforce's Messaging for In-App and Web with the Messaging User permission set for secure HIPAA-compliant patient-clinician messaging. Do not use standard Chatter or Email-to-Case for PHI-containing clinical communications without explicit BAA coverage confirmation.
