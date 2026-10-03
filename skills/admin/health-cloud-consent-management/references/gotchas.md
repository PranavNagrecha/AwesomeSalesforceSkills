# Gotchas: Health Cloud Consent Management

Non-obvious consent behaviors that cause real production problems. Sources are listed in `well-architected.md`. Line references cite the `pdftotext -layout` extraction of the Summer '26 Object Reference (`object_reference`), Metadata API Developer Guide (`api_meta`), and Security Guide (`salesforce_security_impl_guide`). A claim that could not be re-read in an official source carries an inline `UNVERIFIED (2026-10-03):` marker.

## Gotcha 1: Turning consent management off purges stored consent forms

**What happens:** Every object in the consent hierarchy carries the rule "This object is available if Data Protection and Privacy is enabled" (`object_reference L45957`, `L46093`, `L46304`, `L46420`, `L95167`). In metadata, `PartyDataModelSettings.enableConsentManagement` "indicates whether data protection details are available in records", defaults to true, and carries the note: "Setting this field to false purges all data protection details, such as privacy preferences and stored consent forms" (`api_meta L123969-123974`).

**When it occurs:** A settings file retrieved from an org with the feature off is deployed to production, or an admin toggles the setting while troubleshooting.

**How to avoid:** Keep `PartyDataModel.settings` in source control with `enableConsentManagement` set to true, review every diff to it, and restrict who can change Data Protection and Privacy in Setup. UNVERIFIED (2026-10-03): the guide's own sample uses the element name `enableConsentManagementEnabled` (`L123985`) while the field table names `enableConsentManagement`; retrieve the file from a real org before deploying it, and deploy the name the org returns.

---

## Gotcha 2: The default text is a lookup on the form, not a flag on the text

**What happens:** `AuthorizationForm.DefaultAuthFormTextId` is described as "Required. The ID of the default authorization form text to use if text isn't available for a specific language" (`object_reference L45962-45972`). `AuthorizationFormText` has `Locale` and `LocaleSelection` ("Locale and LocaleSelection have the same function"), but no `IsDefault` field (`L46505-46530`). Earlier versions of this skill described an `IsDefault` flag on the text; it does not exist.

**When it occurs:** A form has texts in English and Spanish, no default is set on the form, and a patient whose language matches neither sees no text. Scripts that set `IsDefault` fail.

**How to avoid:** Create the form, create its texts, then set `DefaultAuthFormTextId` on the form to the fallback text. Check with `SELECT Id, Name, DefaultAuthFormTextId FROM AuthorizationForm WHERE DefaultAuthFormTextId = null`. UNVERIFIED (2026-10-03): the field shows the Nillable property despite the "Required" description, so whether the platform blocks a form without a default is not stated; treat it as required in your process.

---

## Gotcha 3: `Status` has no `Withdrawn` value

**What happens:** `AuthorizationFormConsent.Status` is a restricted picklist whose documented values are `Rejected`, `Seen`, and `Signed` (`object_reference L46253-46262`). Earlier versions of this skill told teams to set `Status = Withdrawn`.

**When it occurs:** A withdrawal flow writes `Withdrawn` and fails, or an admin "fixes" it by overwriting the `Signed` record with `Rejected` and losing the evidence of the original signature.

**How to avoid:** Record withdrawal as `Rejected`, and keep the signed evidence: either insert a new consent record for the withdrawal event, or update the existing record with field history tracking on (`AuthorizationFormConsentHistory` exists, `L46279`) and, where Field Audit Trail is licensed, a retention policy; Authorization Form Consent is on the list of objects that support Field Audit Trail policies (`salesforce_security_impl_guide L4842`). UNVERIFIED (2026-10-03): whether an admin can add a custom value to this restricted standard picklist is not stated.

---

## Gotcha 4: Capture source type is a restricted picklist, and the source text is required

**What happens:** `ConsentCapturedSourceType` is required and restricted to `Email`, `InPerson`, `MailingAddress`, `Phone`, `Social`, `Video`, and `Web`. `ConsentCapturedSource` is a required string, "for example, user@example.com, www.example.com". `ConsentCapturedDateTime` and `ConsentGiverId` are also required (`object_reference L46112-46160`). Earlier versions of this skill used `ConsentCapturedSource = Verbal` or `Written`, which mixes up the two fields and uses values that do not exist.

**When it occurs:** A data load or flow sets "Verbal" as the source type, or leaves the source text blank, and inserts fail.

**How to avoid:** Map each capture channel to a source type (a phone call is `Phone`, a clinic signature is `InPerson`) and decide what goes in the free-text source (staff user, portal URL, email address).

---

## Gotcha 5: `ConsentGiverId` is polymorphic, and `DataUsePurpose` has no `PurposeId`

**What happens:** `ConsentGiverId` refers to Account, Contact, Individual, Lead, or User (`object_reference L46153-46165`), not only Individual. `DataUsePurpose` fields are `Name`, `Description`, `CanDataSubjectOptOut` (required), and `LegalBasisId` (a lookup to `DataUseLegalBasis`); there is no `PurposeId` field (`L95156-95230`). An earlier example in this skill set `PurposeId = treatment`.

**When it occurs:** Reports filter consent by Individual only and miss consents given against the Person Account; setup scripts copied from the old example fail on `PurposeId`.

**How to avoid:** Decide which record type gives consent (Person Account, Contact, or Individual) and use it consistently. Build purposes with `Name`, `Description`, `CanDataSubjectOptOut`, and a legal basis where the program needs one.

---

## Gotcha 6: Evidence capture for e-signatures is a settings decision

**What happens:** `PrivacySettings` has `authorizationCaptureIp`, `authorizationCaptureEmail`, `authorizationCaptureBrowser`, and `authorizationCaptureLocation`, each indicating whether that detail "is captured during authorization consent capture", all defaulting to false (API 59.0). `authorizationLockingAndVersioning` enables locking and versioning for authorization consent records (API 59.0) (`api_meta L124620-124655`).

**When it occurs:** Compliance asks, after go-live, for the IP address and browser of each electronic signature, and nothing was recorded.

**How to avoid:** Decide the evidence requirements with compliance before launch, and deploy the matching `Privacy.settings` (see `metadata-examples.md`). UNVERIFIED (2026-10-03): where the captured values are stored is not described in the settings entry.

---

## Gotcha 7: Portal sharing of consent forms is opt-in

**What happens:** Health Cloud's `IndustriesSettings.enableAuthorizationCustomSharingPCU` enables custom sharing "to give your users access to view and manage electronic consent forms. Users with a Customer Community Plus license can share Authorization Form Texts and Data Use Purpose records with Accounts, Contracts, and Users specified in the Information Authorization Request record" (`api_meta L119541-119546`). `PrivacySettings.authorizationCustomSharing` (API 59.0) and `authorizationCustomSharingPCU` (API 62.0) control custom sharing for authorization consent records (`L124641-124648`).

**When it occurs:** A patient or caregiver portal is expected to show forms for signature, and portal users see nothing.

**How to avoid:** Name the external audiences in the requirements and enable the matching settings deliberately, then design sharing for exactly the forms each audience must see.

---

## Gotcha 8: Consent records do not enforce access to PHI

**What happens:** `AuthorizationFormConsent` "represents the date and way in which a user consented to an authorization form" (`object_reference L46076-46077`). Nothing in the object reference ties it to record access. A patient without a signed authorization can still have records read by any user whose sharing allows it.

**When it occurs:** Teams assume that creating the consent hierarchy restricts who can see PHI.

**How to avoid:** Implement access with org-wide defaults, sharing, and permission sets. Make the enrollment flow check consent status before it activates enrollment or grants care team access.
