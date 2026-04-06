# Gotchas — Sales Process Mapping

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: The Five ForecastCategoryName Values Are Platform-Fixed and Cannot Be Renamed

**What happens:** During the mapping exercise, a sales leader assigns stages to forecast categories using business-specific labels such as "Called", "Upside", "Strong Upside", and "Won". When the admin attempts to implement these, there is no way to set a ForecastCategoryName to anything other than Pipeline, Best Case, Commit, Closed, or Omitted. The custom labels do not exist at the platform level.

**When it occurs:** Any time a mapping exercise documents forecast category names that differ from the five hardcoded platform values. This is common when the business has a legacy forecasting language that predates Salesforce adoption, or when a Salesforce partner produces a mapping document without checking the platform constraint first.

**How to avoid:** During the mapping session, present the five platform values by name and explain they cannot be changed. Ask the sales leader to assign each stage to one of these five values, not to invent new ones. If the business uses different internal labels for their forecast tiers, document a translation table in the mapping artefact showing the internal label alongside the corresponding platform value. This translation is communicated through field help text and training, not by modifying the platform picklist.

---

## Gotcha 2: Generic Stage Names Create Cross-Business-Unit Collisions in Shared Orgs

**What happens:** Stage names defined during a mapping exercise for one business unit (e.g., "Evaluation", "Proposal") are entered as global picklist values. A second business unit onboarded later wants to use different definitions for stages with the same names, or wants stages with the same labels but different ForecastCategoryName or probability defaults. Because stage picklist values are global, both business units share the same values — the second BU's settings are applied globally.

**When it occurs:** Multi-BU or multi-product orgs where stage mapping is done BU-by-BU over time without a global naming convention. The collision is discovered when the second BU's admin tries to set a different forecast category or probability on a stage that already has settings set by the first BU.

**How to avoid:** During the mapping exercise, ask whether other business units currently use Salesforce or are planned to. If yes, prefix stage names with the BU or motion identifier (e.g., "ENT — Evaluation", "SMB — Proposal"). Alternatively, establish a global naming convention during the first mapping exercise that other BUs will follow. Document the convention in the mapping artefact and flag it explicitly in the handoff brief.

---

## Gotcha 3: Win/Loss Capture Enforcement Is Bypassed by Bulk Updates and Mass-Close Operations

**What happens:** The mapping exercise specifies that win/loss reasons are required on close and the admin implements a validation rule that blocks save when StageName = 'Closed Won' or 'Closed Lost' and the reason field is blank. In testing, the rule works. In production, managers use the list view "Change Owner" or "Mass Update" actions, or the Data Loader, to close multiple opportunities at once. These operations bypass the validation rule if the API call does not include the required field, and records close with blank win/loss data.

**When it occurs:** Anytime bulk-close operations are used — end-of-quarter mass closes, CSM-driven renewal batch closes, admin-initiated data corrections. Validation rules run on individual record saves through the UI, but their enforcement via API or bulk DML depends on how the operation is constructed.

**How to avoid:** During the mapping exercise, document who will close deals and how (rep via UI, manager via bulk edit, CSM via a portal). If bulk close is a real workflow, note in the mapping document that win/loss enforcement will require a Flow on record update or a trigger-based check — not only a validation rule — or that a Process Automation restriction on bulk API edit must be considered. Flag this as a configuration requirement in the handoff brief rather than assuming the validation rule alone is sufficient.

---

## Gotcha 4: Backward Stage Movement Is Silently Allowed Without a Validation Rule

**What happens:** The mapping document specifies "no backward stage movement without manager approval past the Proposal stage." The configuration team adds Path guidance but does not write a validation rule. Reps move opportunities backward through stages freely, corrupting stage velocity data and allowing forecast sandbagging.

**When it occurs:** Whenever a mapping exercise documents transition restrictions but the handoff brief does not explicitly list each restriction as a validation rule requirement. Configuration teams that receive only a stage list and a written policy statement, rather than an explicit list of validation rules to implement, often rely on Path (which enforces nothing).

**How to avoid:** For every transition rule documented in the mapping artefact, the mapping practitioner must write an explicit implementation note: "This transition restriction requires a validation rule with the following logic: [condition]." Do not leave it implied. The handoff brief should include a dedicated "Validation Rules Required" section listing each rule, its condition, and the error message to display.

---

## Gotcha 5: Stage Probability Defaults Are Set Globally, Not Per Sales Process

**What happens:** The mapping exercise assigns a probability to each stage (e.g., Discovery = 20%, Proposal = 60%). The admin enters these as defaults on the global picklist values. A second sales process for a different motion (e.g., partner/channel deals) uses the same stage names but has different win probability norms for those stages. The probability defaults from the first mapping apply to the second process because defaults are set globally on the stage value, not per Sales Process.

**When it occurs:** Multi-process orgs where the same stage names are shared across Sales Processes but have different probability expectations per motion. Very common in organisations that have both a direct enterprise process and a transactional SMB process.

**How to avoid:** During the mapping exercise, if distinct probability norms are needed per motion, give stages distinct names per process (e.g., "ENT Proposal" vs "SMB Proposal") so each can have its own global default. Alternatively, note in the mapping document that probability overrides will be managed at the record level via a Flow that sets a custom field, not via the global stage default. Either approach must be flagged in the handoff brief; a probability mismatch discovered after go-live requires a data fix and a change to the configuration.
