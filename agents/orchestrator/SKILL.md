---
name: orchestrator
description: "Use to autonomously advance the MASTER_QUEUE.md skill build queue. Routes each task to the correct specialized agent. Triggers: '/run-queue', 'advance the queue', 'build the next skill', 'run one queue cycle'. NOT for building skills directly — delegates all building to role-specific agents."
category: devops
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
tags:
  - orchestration
  - queue-management
  - automation
  - routing
inputs:
  - MASTER_QUEUE.md (read automatically)
outputs:
  - one completed, blocked, or duplicated task per invocation
  - updated MASTER_QUEUE.md with current status
dependencies:
  - task-mapper
  - admin-skill-builder
  - dev-skill-builder
  - data-skill-builder
  - architect-skill-builder
  - content-researcher
  - validator
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-03
---
