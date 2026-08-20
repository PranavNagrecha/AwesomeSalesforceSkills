# ADR-004-native-subagents-curated: Expose a small host-native subagent set

**Status:** Accepted  
**Date:** 2026-08-19

## Context

SfSkills is evolving from a skill library into a Salesforce AI engineering framework and must make an explicit decision on this architectural boundary.

## Decision

Only roles with an isolated-context or independent-review benefit become native subagents. Existing agents remain catalog specialists by default.

## Consequences

Avoids discovery overload and context/tool ambiguity.

## Revisit when

Two or more shipped products produce evidence that the decision creates measurable quality, safety, usability, or maintenance problems.
