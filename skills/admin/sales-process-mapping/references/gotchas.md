# Gotchas — Sales Process Mapping

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: The Five ForecastCategoryName Values Are Platform-Fixed and Cannot Be Renamed

**What happens:** During the mapping exercise, a sales leader assigns stages to forecast categories using business-specific labels such as "Called", "Upside", "Strong Upside", and "Won". When the admin attempts to implement these, there is no way to set a ForecastCategoryName to anything other than Pipeline, Best Case, Commit, Closed, or Omitted. The custom labels do not exist at the platform level.

**When it occurs:** Any time a mapping exercise documents forecast category names that differ from the documented platform values. This is common when the business has a legacy forecasting language that predates Salesforce adoption, or when a Salesforce partner produces a mapping document without checking the platform constraint first.

**How to avoid:** During the mapping session, present the documented values by name and explain they cannot be changed. `OpportunityStage.ForecastCategoryName` has exactly these members: `Best Case`, `Closed`, `Commit`, `Most Likely`, `Omitted`, `Pipeline` (object_reference.txt:195492–195504) — six, not the five that most mapping decks show, because `Most Likely` is routinely left out of the slide. Ask the sales leader to assign each stage to one of these values, not to invent new ones. If the business uses different internal labels for their forecast tiers, document a translation table in the mapping artefact showing the internal label alongside the corresponding platform value. This translation is communicated through field help text and training, not by modifying the platform picklist.

---

## Gotcha 2: Generic Stage Names Create Cross-Business-Unit Collisions in Shared Orgs

**What happens:** Stage names defined during a mapping exercise for one business unit (e.g., "Evaluation", "Proposal") are entered as global picklist values. A second business unit onboarded later wants to use different definitions for stages with the same names, or wants stages with the same labels but different ForecastCategoryName or probability defaults. Because stage picklist values are global, both business units share the same values — the second BU's settings are applied globally.

**When it occurs:** Multi-BU or multi-product orgs where stage mapping is done BU-by-BU over time without a global naming convention. The collision is discovered when the second BU's admin tries to set a different forecast category or probability on a stage that already has settings set by the first BU.

**How to avoid:** During the mapping exercise, ask whether other business units currently use Salesforce or are planned to. If yes, prefix stage names with the BU or motion identifier (e.g., "ENT — Evaluation", "SMB — Proposal"). Alternatively, establish a global naming convention during the first mapping exercise that other BUs will follow. Document the convention in the mapping artefact and flag it explicitly in the handoff brief.

---

## Gotcha 3: Win/Loss Capture Enforced Only on the Page Layout Is Bypassed by Bulk Updates and Mass-Close Operations

**What happens:** The mapping exercise specifies that win/loss reasons are required on close and the admin implements a validation rule that blocks save when StageName = 'Closed Won' or 'Closed Lost' and the reason field is blank. In testing, the rule works. In production, managers use the list view "Change Owner" or "Mass Update" actions, or the Data Loader, to close multiple opportunities at once. These operations bypass the validation rule if the API call does not include the required field, and records close with blank win/loss data.

**When it occurs:** Anytime bulk-close operations are used — end-of-quarter mass closes, CSM-driven renewal batch closes, admin-initiated data corrections.

> **Grounded (2026-09-05):** validation rules are NOT bypassed by bulk or API saves. The Apex Developer Guide's order of execution, step 5, runs "any custom validation rules" for every save request type — standard UI, Apex, SOAP/REST/Bulk API alike (apexdev.txt L15442–15444, `Triggers and Order of Execution`). What bulk operations bypass is the *layout*: page-layout required fields and layout-specific rules apply only to standard UI edit pages (L15419–15423), so a rule that lives on the layout instead of in a validation rule is the real gap.
Be precise about the mechanism when you write this into a mapping document, because the sloppy version ("bulk edit bypasses validation rules") gets repeated and then designed around wrongly. The exposure that matters for a mapping exercise is narrower: a rule that only fires on the *save that sets* the closed stage misses records closed by a path the rule does not cover, and a rule written against a field the bulk operation never touches has nothing to evaluate. Establish which close paths exist before choosing the enforcement point.

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

The platform reason: `DefaultProbability` is a field of the `OpportunityStage` picklist *value*, one row per stage name (object_reference.txt:195451–195457) — not a property of a Sales Process. Two processes that share a stage name share that one row.

**How to avoid:** During the mapping exercise, if distinct probability norms are needed per motion, give stages distinct names per process (e.g., "ENT Proposal" vs "SMB Proposal") so each can have its own global default. Alternatively, note in the mapping document that probability overrides will be managed at the record level via a Flow that sets a custom field, not via the global stage default. Either approach must be flagged in the handoff brief; a probability mismatch discovered after go-live requires a data fix and a change to the configuration.

---

## Gotcha 6: The Vocabulary the Mapping Document Uses Is Not the Vocabulary the Deploy File Accepts

**What happens:** The mapping document records each stage's forecast category as the sales leader said it — `Commit`, `Best Case` — because that is what the UI and a SOQL export show. The configuration team pastes those strings straight into the stage value set XML, and the deploy fails on an invalid enumeration value. The Metadata API element `forecastCategory` is typed as the `ForecastCategories` enumeration whose members are `Omitted`, `Pipeline`, `BestCase`, `Forecast`, `Closed` (api_meta.txt:47578–47585). `Commit` is `Forecast` there, `Best Case` loses its space, and `Most Likely` — a legal `ForecastCategoryName` (object_reference.txt:195492–195504) — has no metadata token at all.

**When it occurs:** Every time the ladder is round-tripped through a spreadsheet, a slide or an LLM. Nothing in either artefact signals that the same concept has two spellings, so the substitution looks like a typo fix rather than a vocabulary error.

**How to avoid:** Fix one vocabulary per artefact and say so in the artefact. The design map speaks `ForecastCategoryName` (labels, with spaces); the deployed XML speaks the enumeration tokens. `scripts/check_sales_process_mapping.py --map` errors when a metadata token appears in a design map and names the label to use instead; the same script's `--manifest-dir` metadata check validates deployed XML against the enumeration, which is why it will not accept `Commit` in a file. `admin/opportunity-management` `references/gotchas.md` Gotcha 13 carries the full three-way mapping table including `Opportunity.ForecastCategory` — cite it in the handoff brief rather than restating it.

---

## Gotcha 7: Stage Values Deployed Through the Metadata API Are Invisible to Users Until Each Record Type Is Edited

**What happens:** The mapping document is signed off, the stage value set deploys green, and the admin confirms in Setup that every new stage exists. Reps then report that the new stages are missing from the picklist on their opportunities. The stages exist globally but were never added to the record type. The guide is explicit:

> "When setting `standardValue` on Record Types, including person account record types, new picklist values loaded into your organization through the Metadata API don't display in the picklist UI by default. For users to see the new values, go to the Record Types list for the object containing the picklist field, click Edit, and add the new value to the Selected Fields list." (api_meta.txt:130774–130779)

**When it occurs:** On every org that uses record types on Opportunity — which is every org where the mapping exercise produced more than one selling motion, because a sales process is only reachable through a record type. It is the standard outcome of a metadata-only deploy, not an edge case.

**How to avoid:** The handoff brief must carry a **per-record-type stage availability matrix**, not a flat stage list: for each record type, which stages are selected and which is the default. Treat the record-type edit as a required manual post-deploy step in the runbook, with a named owner, and verify it by opening a record of each type rather than by reading the deploy log. A related trap sits one step earlier: a stage must exist globally before a Sales Process can reference it, so the value set deploys first — see `admin/opportunity-management` `references/gotchas.md` Gotcha 6.

---

## Gotcha 8: `OpportunityStage` Is Read-Only Through the API — the Ladder Cannot Be Loaded From the Spreadsheet It Was Designed In

**What happens:** The stage map is built in a spreadsheet with a column per attribute, and the plan is to load it — the object exists, it has exactly the right fields, and Data Loader is right there. It cannot be done. `OpportunityStage` supports only `describeSObjects()`, `query()` and `retrieve()` (object_reference.txt:195438–195439), and the guide states plainly: "This object is read-only via the API" (object_reference.txt:195577). The same restriction covers the whole family of picklist-value objects: "These objects are read-only via the API. To modify items in picklists, you must use the Salesforce user interface." (object_reference.txt:2384–2389)

**When it occurs:** At the point the mapping document is handed to whoever is doing the build, usually with a load-ready CSV attached. The plan collapses and the ladder gets typed into Setup by hand instead, which is where transcription errors in probabilities and forecast categories enter.

**How to avoid:** Design the map to be *deployed*, not loaded: the `StandardValueSet` file is the machine-readable delivery mechanism (see `references/worked-examples.md` §5), and the CSV is only the workshop's working format. Two knock-on constraints belong in the mapping document because they bound what the artefact can carry: `Description` and `MasterLabel` on a stage value are each limited to 255 characters (object_reference.txt:195459–195464, 195548–195552), so a paragraph-long stage definition cannot live on the stage itself and needs a home in the design document. And because the object is read-only, the post-deploy verification is a `query()` against `OpportunityStage`, not a Data Loader export-and-diff.

---

## Gotcha 9: Separating Motions Buys Different Stages, Not Different Visibility

**What happens:** The mapping session produces two clean motions and, alongside them, a requirement recorded in the same table: "the renewal team must not see new-logo pipeline." Everyone reads the record-type split as satisfying it. It does not. Both `BusinessProcess` and `RecordType` carry the same warning:

> "Don't use business processes as an access control mechanism. Profile assignment governs create and edit access for business process but doesn't govern read access. For example, a user assigned to a profile that isn't enabled for a particular business process can't create or edit it, but they can read the business process record." (api_meta.txt:42960–42966)

and, on `RecordType`: "a user assigned to a profile that isn't enabled for a particular record type can't create records with that record type, but can access records associated with that record type." (api_meta.txt:44974–44980)

**When it occurs:** Whenever a visibility requirement is voiced during a *stage* workshop — which is most of the time, because the same person owns both concerns and the two requirements sound adjacent. The gap is discovered in UAT, after record types, layouts and paths have been built on the assumption.

**How to avoid:** Split the requirement the moment it is spoken. The stage sequence goes in the stage map; the visibility requirement goes in the open-questions log, routed to `standards/decision-trees/sharing-selection.md` and resolved before configuration starts. Two further costs belong in the same handoff so the record-type decision is priced honestly: `businessProcess` is *required* on lead, opportunity, solution and case record types and not allowed elsewhere (api_meta.txt:45007–45014), and "only one path can be created per record type for each object, including `__Master__` record type" (api_meta.txt:94494–94496) — so a second motion means a second Path as well.

---

## Gotcha 10: A `--manifest-dir` Scan Pointed at the Build Root Can Pass Without Checking Anything

**What happens:** A milestone that spans several steps deploys its OpportunityStage value set inside one step's own folder (for example `M1-S01/standardValueSets/OpportunityStage.standardValueSet-meta.xml`), because that is where the Metadata API retrieved it and where the build tooling naturally puts a step's artefacts. Someone runs `scripts/check_sales_process_mapping.py --manifest-dir` against the build's top-level artefacts directory expecting one pass to cover every step. Before this was fixed, the metadata check only ever looked at `<manifest-dir>/standardValueSets/...` and `<manifest-dir>/globalValueSets/...` — one fixed hop below whatever directory was named on the command line. Point it at the build root instead of the step folder and it finds nothing, checks nothing, and still prints "No issues found." with exit 0. A stage carrying an invalid `<forecastCategory>` token ships clean because the directory that was actually inspected was empty, not because the value set was valid.

**When it occurs:** Any time `--manifest-dir` is pointed at a directory that is a parent of the one actually holding the value set — which is the normal case for a multi-step milestone, since each step gets its own subfolder and the build-level directory is one or more levels above all of them. It is easy to miss because the failure mode is silent: no error, no warning, a clean exit code, and a message that reads exactly like a real pass.

**How to avoid:** The checker now walks the whole tree under `--manifest-dir` at any depth for both the sales-process map files and the OpportunityStage value-set metadata, so pointing it at a build root or a single step folder finds the same files either way. It also refuses to let an empty scan read as a clean one: if nothing matched anywhere under the given directory, it prints `Scanned 0 file(s) — nothing asserted; check --manifest-dir` instead of "No issues found." — treat that line as a prompt to re-check the path, not as a pass. A run against a directory that genuinely contains no OpportunityStage metadata or stage map (a milestone that never touches sales stages) will print that same line and is not itself a bug; the point is only that "No issues found." must never be the message for a scan that inspected nothing.
