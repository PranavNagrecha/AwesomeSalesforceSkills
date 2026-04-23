# Custom Notification Type — Gotchas

## 1. User Preferences Can Silence A CNT Per Channel

Each user toggles channels independently. If mobile push is OFF
globally, your CNT's mobile channel does nothing.

## 2. CNT Send Is Not Free

Daily send limits apply; sending per record update in a bulk load can
blow past them.

## 3. Bulk Send From Flow Is Per User

`Send Custom Notification` action in Flow fires one per recipient. A list
of 500 recipients = 500 sends in the transaction.

## 4. No Native Retry

If the CNT send fails (throttle or service error), there is no retry.
Capture errors in a log object and replay if needed.

## 5. Deep Links Must Use Lightning Paths

Classic URLs will land users in a broken page in Lightning. Always use
`/lightning/r/<ObjectName>/<Id>/view` or app-aware paths.

## 6. Slack Channel Needs App Setup

Slack-targeted CNTs require Slack integration + the user's Salesforce
account to be linked to Slack.

## 7. Mobile Push Needs The Mobile App

Desktop browser push is different from mobile app push; users need the
app + push permissions on device.
