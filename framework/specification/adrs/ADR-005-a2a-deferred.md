# ADR-005-a2a-deferred: Defer A2A to independent service interoperability

**Status:** Accepted  
**Date:** 2026-08-19

## Context

SfSkills is evolving from a skill library into a Salesforce AI engineering framework and must make an explicit decision on this architectural boundary.

## Decision

Use host-native subagents internally and MCP for tools. Add A2A only when an external agent service and identity/authorization model exist.

## Consequences

Prevents protocol-driven architecture without a product need.

## Revisit when

Two or more shipped products produce evidence that the decision creates measurable quality, safety, usability, or maintenance problems.
