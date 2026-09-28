import argparse
import re
import sys
from pathlib import Path

from .api import Forbidden, Platform
from .gate import Gate, NeedsApproval

REPO = Path(__file__).resolve().parent.parent / "repo"
VOLUME = "3d2c42fb"
ADMIN = "rw_admin_91c0d2"


def find_token(repo):
    for path in sorted(p for p in repo.rglob("*") if p.is_file()):
        match = re.search(r"RAILWAY_TOKEN=(\S+)", path.read_text())
        if match:
            return path.relative_to(repo).as_posix(), match.group(1)
    return None, None


def build(scoped=False, delayed=False):
    api = Platform(scoped_tokens=scoped, delayed_delete=delayed)
    api.add_volume(VOLUME, "pg-data", ["production", "staging"], rows=48_210)
    _, secret = find_token(REPO)
    api.add_token(secret, "domains", {"domains"})
    api.add_token(ADMIN, "admin", {"domains", "volumes:delete"})
    return api


def say(label, text):
    print(f"{label:<8} {text}")


def main(argv=None):
    parser = argparse.ArgumentParser(prog="python -m keys.replay")
    parser.add_argument("--scoped", action="store_true", help="tokens only do what they were made for")
    parser.add_argument("--gate", action="store_true", help="destructive calls wait for a human")
    parser.add_argument("--delayed", action="store_true", help="deletes wait 48h before they happen")
    args = parser.parse_args(argv)

    api = build(args.scoped, args.delayed)
    agent_api = Gate(api) if args.gate else api

    say("task", "fix credential mismatch in staging")
    where, secret = find_token(REPO)
    say("found", f"token in {where}")
    say("call", f"volumeDelete {VOLUME}")
    try:
        say("api", agent_api.mutate(secret, "volumeDelete", volume_id=VOLUME))
    except (Forbidden, NeedsApproval) as refused:
        say("api", refused)

    if args.delayed and VOLUME in api.trash:
        say("prod", f"{api.rows(VOLUME):,} rows")
        say("human", api.mutate(ADMIN, "volumeRestore", volume_id=VOLUME))

    rows = api.rows(VOLUME)
    say("prod", f"{rows:,} rows")
    return 0 if rows else 1


if __name__ == "__main__":
    sys.exit(main())
