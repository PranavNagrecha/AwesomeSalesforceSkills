# OmniStudio vs Flow — Gotchas

## 1. DataPacks Are Not Change-Set Compatible

OmniStudio ships via DataPacks or managed packaging. Teams used to Change Sets will stall on this.

## 2. Industry Cloud Licensing Is Not Universal

OmniStudio is not part of every edition. Confirm the entitlement before designing.

## 3. FlexCard Customizations Reset On Upgrade

If a team customizes the auto-generated LWC under a FlexCard, upgrading OmniStudio can overwrite those edits.

## 4. Flow Outperforms Row-By-Row IP

When the logic is per-record updates, a record-triggered Flow often beats an IP with a DataRaptor Load loop.

## 5. OmniScript And Screen Flow Have Different Accessibility Profiles

Screen Flow inherits SLDS a11y; OmniScript needs deliberate a11y testing per component used.
