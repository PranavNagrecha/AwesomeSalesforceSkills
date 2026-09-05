# Custom Notification Types — Work Template

Fill this in before writing the `.notiftype` file. Each section maps to a
question in `SKILL.md` → `## Questions to Ask Before Configuring`; an
unanswered row is a design decision you are about to make by accident.

## Scope

**Skill:** `custom-notification-types`

**Request summary:** _(what the user asked for, in their words)_

**Business event that fires it:** _(the state change, precisely — "Case
Priority changes to High", not "cases get escalated")_

---

## 1. The type

| Field | Value | Constraint |
|---|---|---|
| `customNotifTypeName` (API name) | | required, max 80, unique org-wide, not namespaced |
| `masterLabel` | | required — customer-visible copy, not the API name |
| `description` | | max 255, shown to admins beside the type name |
| `desktop` | `true` / `false` | required boolean; defaults to `false` |
| `mobile` | `true` / `false` | required boolean; defaults to `false` |
| `actionGroups` needed? | no / yes (Beta) | Beta — needs a fallback if yes |

**Existing type that already means this?** _(run
`SELECT DeveloperName, MasterLabel, Desktop, Mobile FROM CustomNotificationType`
first — record the answer, including "none")_

**If `mobile` is true — is a real-device test in scope?** _(a bell test does
not prove push)_

---

## 2. The audience

**Expressed as:** ☐ User Ids ☐ Group Id ☐ Queue Id ☐ Account Id (Account Team)
☐ Opportunity Id (Opportunity Team)

**Count of Ids per send:** _(not count of people — the 500 cap counts Ids)_

**If a hand-built user set: why can this not be a group or queue Id?**

**What happens when a recipient is deactivated?** _(inactive users are dropped
silently, not reported)_

---

## 3. The target

☐ Real record Id — which object: ______
☐ `targetPageRef` — pageReference JSON: ______
☐ Documented dummy Id `000000000000000AAA` — because this notification opens
nothing

**Can every recipient read the target record?** _(if no, they land on
Insufficient Privileges — notifications ignore sharing, the click does not)_

---

## 4. The send path

☐ Flow (`customNotificationAction`) — flow name: ______
☐ Apex (`Messaging.CustomNotification`) — class: ______

**How is the type Id resolved at run time?** _(query by `DeveloperName`, or
Custom Metadata — a `0ML…` literal is not an answer)_

**Running user / context:** _(system context, or a named end user? if an end
user, which permission set grants **Send Custom Notifications**?)_

---

## 5. Volume

| | Value |
|---|---|
| Typical sends per hour | |
| Worst-hour burst (data load, batch, mass reassignment) | |
| Send `()` calls per transaction at worst | |
| Suppression switch for bulk/system writes | |

**If the worst case needs more than a handful of send calls:** which async
container splits it across transactions, and where is the resume marker?

---

## 6. Deploy

- [ ] `notificationtypes/<DevName>.notiftype-meta.xml` written
- [ ] `NotificationTypeConfig` entry needed? ☐ no ☐ yes — retrieved real
      connected-app API names from the target org
- [ ] `package.xml` names each type explicitly (no wildcard support)
- [ ] Type deploys before the Flow / class that references it
- [ ] `python3 scripts/check_custom_notification_types.py --manifest-dir <dx-root>` clean

---

## 7. Verification (fill in after deploy, with results)

| Check | Expected | Actual |
|---|---|---|
| `SELECT DeveloperName, Desktop, Mobile FROM CustomNotificationType WHERE DeveloperName = '…'` | one row, ≥1 channel `true` | |
| Bell entry appears for the recipient | yes | |
| Tap lands on the intended target, as the recipient | yes | |
| Mobile push arrives on a real device (if `mobile` is true) | yes | |

---

## 8. Notes

_(Deviations from the patterns in `SKILL.md` and why. Anything the checker
flagged that was accepted deliberately — record the reason here so the next
reviewer does not re-litigate it.)_
