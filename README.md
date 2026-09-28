# agent-deleted-database

Lab for "An AI Deleted a Company's Database in 9 Seconds". Replays the
agent's actions from the PocketOS incident (April 2026) against a small
simulated hosting API, then again with three guardrails.

This is a simulation, not Railway's or PocketOS's code. The order of events
follows the founder's own account: a staging task, a token found in an
unrelated file, one `volumeDelete` call, backups stored on the same volume.
File names, the token, row counts and the 48 hour window are ours.

```powershell
python -m pytest -q tests
python -m keys.replay              # what happened
python -m keys.replay --scoped     # the token can only manage domains
python -m keys.replay --gate       # destructive calls wait for a human
python -m keys.replay --delayed    # deletes can be undone for 48h
python record_terminal.py          # rewrites terminal.json for the video
vhs replay.tape                    # optional real-terminal clip, out/replay.mp4
```

| File | What it is |
|---|---|
| `keys/api.py` | the hosting API: volumes, tokens, scopes, delayed delete |
| `keys/gate.py` | a proxy that holds destructive calls for approval |
| `keys/replay.py` | the agent's steps, run against the API |
| `repo/` | the codebase the agent searched; the token is in `scripts/add-domain.sh` |
