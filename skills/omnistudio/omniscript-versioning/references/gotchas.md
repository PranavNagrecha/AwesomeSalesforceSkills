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

---

## 5. FlexCards Embedded in an OmniScript Have Their Own Version Rules

**What happens:** A release plan promotes an OmniScript and the FlexCards embedded in it under one procedure. The team plans a label fix on the live FlexCard, the designer refuses the edit, and they deactivate the card to make it editable — taking it off the page for the duration of the change.

**Why:** FlexCards share the single-active-version rule — "When you activate a version, Omnistudio deactivates all other versions of the Flexcard" — and add an explicit edit restriction: "You can't edit or delete an active Flexcard. To make changes, deactivate it first." Activation is also a compile step: "When you activate a Flexcard, Omnistudio generates a custom Lightning web component." Adding that LWC to a Lightning page or Experience Builder page is a separate step — activation alone does not place it.

**How to avoid:** For a FlexCard change, use **New Version** — the name and author stay the same, only one version can be active at a time, and the previously active version stays active until you activate the replacement, so you never have to take the live card down to edit it. Use **Clone** only when you want a genuinely separate FlexCard: a clone needs the same setup information as a new FlexCard and carries its own version history.

---

## 6. Inactive Versions Remain Callable; Name-Based FlexCard Share Ignores `IsActive`

**What happens:** A family keeps 13–17 IP versions in source; one is active. Inactive OmniProcess versions stay invocable by uniqueName/version. Guest FlexCard sharing is often **by Name**, so inactive versions of that Name remain readable. DataPack/source deploy of an older version can deactivate the live one.

**When it occurs:** "We keep versions as history." Guest portals.

**How to avoid:** Delete superseded versions in guest-reachable orgs. Smoke the **active** version Id after deploy. Share FlexCards by the active uniqueName, not Name. One Named Credential path only — old versions with hardcoded URLs must not exist.
