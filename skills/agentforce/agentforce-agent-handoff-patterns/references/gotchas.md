# Agentforce Agent Handoff — Gotchas

## 1. Omni-Channel Presence Gates

If no agent is available, Omni-Channel can park the conversation without telling the user. Always design a presence-aware fallback.

## 2. Case Owner vs Queue

Routing via owner assignment bypasses queue capacity rules; routing via queue honors Omni-Channel logic. Pick deliberately.

## 3. Raw Transcript Dumps Are Useless

Human agents skim; they do not read 30-turn transcripts. Send a link + structured summary.

## 4. Agent-To-Agent Resets Topic Context

The receiving agent starts with its own topic set; previous topic instructions do not carry over.

## 5. Hand-Back Needs Explicit Resumption

Salesforce does not resume agent sessions automatically after a human takes over. If you need hand-back, design the resume protocol.
