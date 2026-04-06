# Agentforce Persona Design — Work Template

Use this template when working on tasks in this area.

## Scope

**Skill:** `agentforce-persona-design`

**Request summary:** (fill in what the user asked for)

## Context Gathered

- **Target audience:** (enterprise customers, consumer end-users, internal employees, etc.)
- **Target channel:** [ ] Web chat  [ ] Slack  [ ] API  [ ] Mobile  [ ] Embedded Service
- **Brand voice adjectives:** (e.g., empathetic, professional, concise, trustworthy)
- **Prohibited phrases or topics:** (from brand guidelines)

## Persona Instruction Draft

```
You are [Agent Name], [role description] for [Company Name]. You communicate with
[voice adjective 1] and [voice adjective 2]. [One sentence describing communication style].

When [edge case scenario], [behavioral description]. If [scope boundary],
[fallback behavior without modal verb chains].
```

## Conversation Preview Test Plan

| Utterance | Expected Tone | Pass/Fail |
|---|---|---|
| Routine query | warm, concise | |
| Frustrated user | empathetic, acknowledges concern first | |
| Off-topic query | polite redirect | |
| Complex question | professional, offers to escalate | |
| Scope boundary | clear boundary statement + next step | |

## Checklist

- [ ] Persona is in agent-level instructions only (not topic instructions)
- [ ] Opening instruction has role declaration and voice adjectives
- [ ] No contradictory directives (checked with AI Assist)
- [ ] No long must/never/always chains
- [ ] AI Assist run — all issues resolved
- [ ] Conversation preview completed with 5+ scripted utterances
- [ ] Multi-persona strategy: separate agents per audience if needed

## Notes

(Record any deviations from the standard pattern and why.)
