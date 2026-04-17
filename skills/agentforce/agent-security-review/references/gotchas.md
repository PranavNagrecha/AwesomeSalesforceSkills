# Gotchas — Agent Security Review

## Gotcha 1: Agent run-as has View All

**What happens:** Agent sees cross-owner records even when user shouldn't.

**When it occurs:** Integration user cloned as run-as.

**How to avoid:** Create dedicated `agentforce_service_agent` user with minimum permset; review quarterly.


---

## Gotcha 2: Conversation retention unset

**What happens:** GDPR subject request cannot locate conversation logs.

**When it occurs:** Default retention, no archive job.

**How to avoid:** Configure retention per data class; document in the privacy register.


---

## Gotcha 3: Shield Event Monitoring not streamed

**What happens:** Agent anomaly is invisible to SOC.

**When it occurs:** Event Monitoring add-on not licensed or not streamed.

**How to avoid:** License + stream to SIEM; add agent events to standing alert rules.

