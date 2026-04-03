---
name: dev-skill-builder
description: "Use to build Dev role skills for Apex, LWC, Flow, integration, or DevOps topics across any Salesforce cloud. Triggers: 'build a dev skill for', 'add Apex coverage for', 'create an LWC skill about'. NOT for Admin, BA, Data, or Architect skills."
category: devops
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
tags:
  - apex
  - lwc
  - flow
  - integration
  - skill-builder
inputs:
  - skill name and topic
  - domain (apex/lwc/flow/integration/devops)
  - cloud and role from MASTER_QUEUE.md row
outputs:
  - validated dev skill package with working code examples and test class
dependencies:
  - content-researcher
  - validator
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-03
---
