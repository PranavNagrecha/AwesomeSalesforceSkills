---
name: validator
description: "Use when a skill package needs structural and quality validation before shipping. Triggers: 'validate this skill', 'run quality gates', 'check if skill is ready', 'skill failing validation'. NOT for building skill content — use role-specific skill builder agents for that."
category: devops
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
tags:
  - validation
  - quality-gates
  - skill-framework
  - automation
inputs:
  - path to skill package (skills/<domain>/<skill-name>)
outputs:
  - structured validation report (SHIPPABLE / BLOCKED / NEEDS REVIEW)
  - committed skill package if SHIPPABLE
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-03
---
