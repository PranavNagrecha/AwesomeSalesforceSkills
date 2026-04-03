---
name: content-researcher
description: "Use before writing any skill to research the topic across all 4 source tiers. Triggers: 'research this topic before building', 'what do the official docs say about X', 'ground this skill in sources'. NOT for building skill content — produces a research brief consumed by skill builder agents."
category: devops
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Reliability
tags:
  - research
  - source-grounding
  - skill-framework
  - automation
inputs:
  - skill topic or name
  - domain and cloud context
  - role audience
  - specific questions to answer
outputs:
  - structured research brief with tier-tagged findings
  - contradiction analysis
  - stale-risk flags
  - recommended official sources list
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-03
---
