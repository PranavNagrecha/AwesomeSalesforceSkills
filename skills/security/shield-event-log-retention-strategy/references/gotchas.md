# Shield Event Log Retention — Gotchas

## 1. Default Retention Is Short

Do not assume Event Monitoring keeps logs for audit retention. Design the archive pipeline explicitly.

## 2. Hourly Gaps

The Event Log File API emits hourly; occasional gaps happen. Monitor for missing intervals.

## 3. "Shield Enabled" ≠ "Every Event On"

Some event types require explicit enablement. Audit the active-events list.

## 4. Big Object Auditor UX

Big Objects have no out-of-the-box reporting UI. Plan for a custom auditor app or CLI.

## 5. Real-Time Events Are Separate

The real-time event bus has its own retention — much shorter than ELF. Use for detection, not audit.
