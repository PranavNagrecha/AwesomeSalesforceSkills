# LLM Anti-Patterns — Data Cloud Consent and Privacy

## Anti-Pattern 1: Assuming Opt-Out Records Block Segment Membership

**What the LLM generates:** "Once a customer has an Opt-Out record in ssot__ContactPointConsent__dlm, they will automatically be excluded from all Data Cloud segments."

**Why it happens:** LLMs infer that consent records work like blocklists. They model the platform as automatically enforcing consent state, as some marketing platforms do.

**Correct pattern:** Data Cloud consent is NOT auto-enforced. Opted-out individuals appear in segments unless the segment definition includes an explicit filter joining to `ssot__ContactPointConsent__dlm` with `Status = 'OptIn'` for the applicable Data Use Purpose.

**Detection hint:** Any statement that consent records "automatically" exclude individuals from segments is incorrect.

---

## Anti-Pattern 2: Treating Privacy Center Deletion as Complete GDPR Compliance

**What the LLM generates:** "Submit a deletion request via Privacy Center to satisfy the GDPR Right to Be Forgotten obligation — this will delete all data about the individual."

**Why it happens:** LLMs understand Privacy Center as the designated GDPR tool and describe it as comprehensive. They do not model the downstream activation systems that have already received the data.

**Correct pattern:** Privacy Center deletion propagates across the Data Cloud unified profile only. It does NOT reach Marketing Cloud contacts, ad platform custom audiences, SFTP exports, or other downstream systems. A complete GDPR erasure workflow must include cascade deletion from all downstream systems that were seeded by Data Cloud activations.

**Detection hint:** Any GDPR deletion workflow that ends at "submit Privacy Center request" without mentioning downstream cascade deletion is incomplete.

---

## Anti-Pattern 3: Hardcoding "Marketing" as a Universal Data Use Purpose

**What the LLM generates:** "Create one Data Use Purpose called 'Marketing' and use it for all email, SMS, and push notification consent."

**Why it happens:** LLMs default to simple, broad categorizations. A single "Marketing" purpose seems clean and reduces complexity.

**Correct pattern:** GDPR and CCPA require purpose-specific consent. If a customer consents to email but not SMS, a single "Marketing" purpose cannot model this distinction. Create separate Data Use Purposes for each channel (e.g., "Marketing Email", "Marketing SMS", "Marketing Push Notification") and link consent records to the specific applicable purpose.

**Detection hint:** A single broad "Marketing" Data Use Purpose that covers multiple channels is likely inadequate for GDPR compliance.

---

## Anti-Pattern 4: Assuming Retroactive Retention Policy Application

**What the LLM generates:** "Set the DLO retention policy to 365 days to purge all data older than 1 year retroactively."

**Why it happens:** LLMs model retention policies as applying to all existing data immediately upon configuration, similar to database TTL settings in some systems.

**Correct pattern:** Data Cloud DLO retention policies apply to data written after the policy is configured. They do not retroactively purge existing records that predate the policy. To purge existing data beyond the retention window, use the Data Deletion API to submit explicit deletion requests.

**Detection hint:** Any claim that setting a retention policy will "immediately" or "retroactively" purge existing data is incorrect.

---

## Anti-Pattern 5: Conflating CRM ContactPointTypeConsent with Data Cloud ContactPointConsent DMO

**What the LLM generates:** "Update the ContactPointTypeConsent object in Salesforce CRM to manage Data Cloud consent."

**Why it happens:** Both objects contain "Consent" and relate to contact points. LLMs conflate them because they serve similar conceptual purposes in different product layers.

**Correct pattern:** `ContactPointTypeConsent` (standard CRM object) manages consent in the Salesforce CRM layer for standard contact channels. `ssot__ContactPointConsent__dlm` (Data Cloud DMO) manages consent in Data Cloud for unified profile-level consent enforcement. They are in different product layers, with different object names, different APIs, and different enforcement mechanisms. Changes to one do not automatically propagate to the other.

**Detection hint:** Instructions to use `ContactPointTypeConsent` for Data Cloud consent management are targeting the wrong layer.
