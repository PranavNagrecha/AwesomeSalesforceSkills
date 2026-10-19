# /add-to-backlog — add one ask to the release plan

```
/add-to-backlog <ask text>
```

Runs the backlog-intake agent ([`agents/backlog-intake/AGENT.md`](../agents/backlog-intake/AGENT.md)). It sizes your ask S, M, or L, adds it to whichever release the slotting rule in `RELEASES.yaml` picks, checks the plan's tests, commits `RELEASES.yaml` alone, and replies with the item id, the release, its ship date, and why that size.

One ask per invocation. It changes no other file, never re-sequences existing items, and never starts the work; `/start-building` does that.

## Example

```
/add-to-backlog make the orchestrator print the next release's freeze date in its final line
```

## Related

- `/start-building` — run the loop that works the plan
- `python3 scripts/release_plan.py status` — see the plan
