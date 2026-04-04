# Gotchas — OmniScript Versioning

## 1. Activating One Version Immediately Deactivates the Previous One

**What happens:** A team activates version 4 of a production OmniScript. The OmniScript has 50 users actively mid-session. Version 3 deactivates the moment version 4 activates. Mid-session users may encounter errors or get redirected depending on how the OmniScript runtime handles in-flight sessions.

**Why:** The platform enforces a single active version per Type+Subtype+Language triplet. There is no "canary" mode, no staged rollout, and no graceful drain period for in-flight sessions.

**How to avoid:** Schedule activations during low-traffic windows. Alert active users before activation if the site has long session flows. Consider showing a maintenance message during the activation window.

---

## 2. There Is No "Draft" State — Only Active and Inactive

**What happens:** A developer assumes they can work on version 5 "in draft" in production while version 4 remains active for users. They save changes incrementally, expecting users to keep seeing version 4. When they check, users see the partially completed version 5 because the developer accidentally clicked Activate.

**Why:** OmniScripts have only two states: Active and Inactive. There is no draft, in-progress, or staging state. The moment you activate a version, it is live.

**How to avoid:** Always do development in a sandbox. Only deploy (via DataPack import or Metadata API) to production when the version is fully tested and approved. Never edit OmniScripts directly in production.

---

## 3. Deleted Versions Cannot Be Recovered from the UI

**What happens:** An admin performs a cleanup of old inactive OmniScript versions and deletes versions 1 through 3. Version 4 becomes defective and must be rolled back to version 3. Version 3 is gone — the only recovery path is a DataPack import from a backup.

**Why:** Deleting an inactive version removes it permanently from the org. The Recycle Bin does not contain deleted OmniScript versions (they are metadata, not data records).

**How to avoid:** Export a DataPack of the currently active version before any version change or cleanup operation. Store DataPack backups with timestamps in your version control system.

---

## 4. Version Numbers Are Per-Triplet, Not Global

**What happens:** A team has `CreateCase / Default / English` at version 8 and `CreateCase / Default / French` at version 3. They refer to "activating version 3" in a release note without specifying the triplet. The wrong language version is activated.

**Why:** Version numbers are scoped to the Type+Subtype+Language triplet. Version 3 of the English OmniScript and version 3 of the French OmniScript are completely different objects.

**How to avoid:** Always specify the full triplet (Type/Subtype/Language/VersionNumber) in release notes, rollback procedures, and activation checklists. Never refer to a version number without the triplet context.
