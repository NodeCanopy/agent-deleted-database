"""Run every terminal command shown in the video and save its real output.

    python record_terminal.py
"""
import json
import shlex
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

SCENES = {
    "replay": ["python -m keys.replay"],
    "scoped": ["python -m keys.replay --scoped"],
    "gate": ["python -m keys.replay --gate"],
    "delayed": ["python -m keys.replay --delayed"],
}


def run(command):
    argv = shlex.split(command)
    argv[0] = sys.executable
    result = subprocess.run(argv, cwd=HERE, capture_output=True, text=True)
    output = (result.stdout + result.stderr).rstrip("\n")
    return {"cmd": command, "out": output.split("\n") if output else [], "exit": result.returncode}


recorded = {scene: [run(command) for command in commands] for scene, commands in SCENES.items()}
(HERE / "terminal.json").write_text(json.dumps(recorded, indent=2) + "\n")
for scene, runs in recorded.items():
    print(f"== {scene}")
    for entry in runs:
        print(f"$ {entry['cmd']}")
        print("\n".join(entry["out"]))
