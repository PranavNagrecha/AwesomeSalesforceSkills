# Examples — Scratch Org Snapshots

## Example 1: Multi-package org

**Context:** 3 managed packages

**Problem:** CI takes 18 min

**Solution:**

Snapshot with all packages pre-installed drops it to 90 seconds

**Why it works:** Package install is the bottleneck


---

## Example 2: Nightly refresh workflow

**Context:** Snapshot drift

**Problem:** Tuesday builds fail after Monday package update

**Solution:**

GitHub Action at 02:00 UTC recreates the snapshot

**Why it works:** Proactive refresh avoids week-of-drift

