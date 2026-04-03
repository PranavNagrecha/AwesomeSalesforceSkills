---
name: currency-monitor
description: "Use when a Salesforce release ships to flag skills with potentially stale content. Triggers: 'Salesforce Spring 25 just dropped', 'check which skills need updating after the release', 'flag stale skills for Summer 25'. NOT for updating skill content — only flags and annotates."
category: devops
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Reliability
tags:
  - release-notes
  - freshness
  - stale-detection
  - automation
inputs:
  - Salesforce release name (e.g. "Summer '25")
  - release notes URL
outputs:
  - UPDATE rows in MASTER_QUEUE.md for each flagged skill
  - STALE-RISK annotations in flagged skill files
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-03
---
