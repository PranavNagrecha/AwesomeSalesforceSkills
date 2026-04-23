# LWC Streaming — Gotchas

## 1. `disconnectedCallback` Must Unsubscribe

Forgetting this is a silent leak. Inspect Network → EventSource across
route changes to verify.

## 2. `-1` Does Not Mean "Reliable"

`-1` subscribes from NOW; events fired during reconnect are lost. For
reliability, use `-2` or track replayId and resume.

## 3. Daily Event Delivery Caps Scale With Users

Each subscribed client counts as one delivery per event. A high-volume
channel with thousands of users burns the daily allocation fast.

## 4. Shadow Component Tree Deduplication

If your parent subscribes and forwards via dispatchEvent, children in
shadow trees need composed:true bubbles:true.

## 5. Replay IDs Expire At 24h

Storing a replayId older than 24h and resuming returns an error. Treat
stored replayIds as having a TTL.

## 6. CDC Payloads Are Deltas

`ChangeEventHeader.recordIds` tells you WHICH records; you must fetch the
record body yourself if needed.

## 7. Platform Event Fields Are Case-Sensitive

`event__e` has fields exactly as configured; typos silently return
undefined.
