# LWC Streaming — Examples

## Example 1: Record Auto-Refresh On CDC

A case detail page refreshes when any field changes via CDC:

```js
handleSubscribe() {
  subscribe('/data/CaseChangeEvent', -1, (msg) => {
    const changed = msg?.data?.payload?.ChangeEventHeader?.recordIds || [];
    if (changed.includes(this.recordId)) {
      getRecordNotifyChange([{ recordId: this.recordId }]);
    }
  }).then((s) => (this._sub = s));
}
```

**Why:** CDC pushes only the ids; LDS fetches the real record once, keeping
consistency with the rest of the page.

---

## Example 2: Progress Stream For Long-Running Job

Apex publishes `Job_Progress__e` with `jobId` and `percent`. LWC subscribes
with `-1` and updates a progress bar. A Finalizer publishes a final event
with `status=done|failed`.

**Why:** UI never polls; user sees sub-second progress.

---

## Example 3: Leader-Tab De-Duplication

Two tabs of the same user receive the same event. Using
`BroadcastChannel('orders')`:
- Tab A calls `navigator.locks.request('leader', ...)` to claim leadership.
- Leader subscribes; broadcasts events to other tabs.
- Other tabs render without duplicating server-side handlers.

---

## Anti-Pattern: Subscribing Per Row

A list component subscribed per row (100 rows → 100 subscriptions). Daily
event delivery limits were hit within minutes. Fix: one subscription at the
list container; route events to rows by id.
