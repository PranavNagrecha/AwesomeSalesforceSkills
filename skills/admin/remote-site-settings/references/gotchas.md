# Gotchas — Remote Site Settings and CSP Trusted Sites

## Gotcha 1: CSP Trusted Sites Have No Effect on Apex Http.send() Callouts

**What happens:** An admin adds an external endpoint to CSP Trusted Sites to fix a failing Apex callout. The callout continues to fail with `CalloutException: Unauthorized endpoint`. The admin tries multiple CSP directive types (connect-src, all-sources) with no change in behavior.

**When it occurs:** Any time an Apex class calls an external URL via Http.send() without the URL registered in Remote Site Settings. Extremely common because "CSP Trusted Sites" sounds like the relevant control for any kind of "trust this site" configuration, and the Setup navigation places them close together.

**How to avoid:** For Apex callout failures, always check Remote Site Settings first (Setup > Security > Remote Site Settings). The `CalloutException: Unauthorized endpoint` error message even specifies the correct location: "check Setup > Security > Remote Site Settings." CSP Trusted Sites are for browser-side Lightning component resource loading — not server-side Apex code.

---

## Gotcha 2: Remote Site Settings Not Included in Change Sets by Default

**What happens:** An Apex class is deployed to production via Change Set. The class makes external callouts. After deployment, every callout fails with `CalloutException: Unauthorized endpoint`. The sandbox version works because the Remote Site Setting was added manually there. The Change Set included the Apex class but not the Remote Site Setting.

**When it occurs:** Every Change Set deployment of Apex code that calls external URLs when the Remote Site Setting is not explicitly added to the Change Set. Change Set's "dependency detection" does not include Remote Site Settings as automatic dependencies of Apex callout code.

**How to avoid:** Before uploading a Change Set that contains Apex callout code, explicitly add the dependent Remote Site Settings as "Remote Site Setting" component type entries. Develop a pre-deployment checklist item: "If this Change Set contains Apex callout code, verify the Remote Site Settings are included." Document the Remote Site Setting names in code comments near the callout so future developers know to include them.

---

## Gotcha 3: Protocol Mismatch Between Remote Site Setting and Apex Callout URL

**What happens:** A Remote Site Setting is added for `http://api.example.com`. The Apex code calls `https://api.example.com`. The callout fails with `CalloutException: Unauthorized endpoint` even though the Remote Site Setting exists and the domain matches.

**When it occurs:** When the URL protocol in the Remote Site Setting (http:// vs. https://) does not exactly match the protocol used in the Apex callout. This occurs when an admin adds the Remote Site Setting from memory with the wrong protocol, or when an external service migrates from HTTP to HTTPS and the Remote Site Setting is not updated.

**How to avoid:** Always copy the exact URL (including protocol) from the Apex callout code into the Remote Site Setting URL field. Do not type the URL from memory. After adding the setting, test the callout in anonymous Apex to confirm the exact URL in use is covered. If the external service changes protocols, update the Remote Site Setting immediately and include the update in the deployment package.
