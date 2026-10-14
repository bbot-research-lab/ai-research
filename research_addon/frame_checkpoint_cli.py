"""CLI bridge used by opt-in synthetic GitHub frame persistence workflow."""
import argparse
import os
from pathlib import Path

from .frame_snapshot import snapshot
from .git_frame_checkpoint import restore_frame, stage_frame


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("restore", "stage"))
    parser.add_argument("--frame", required=True)
    parser.add_argument("--root", required=True)
    parser.add_argument("--worktree", required=True)
    args = parser.parse_args()
    key = os.environ["BBOT_RESEARCH_STATE_KEY"]
    root = Path(args.root) / args.frame
    if args.action == "restore":
        print("RESTORED" if restore_frame(args.frame, key, args.worktree, root) else "FIRST_RUN")
    else:
        snapshots = Path(args.root) / "_snapshot" / args.frame
        snapshot(root, snapshots)
        result = stage_frame(args.frame, snapshots, key, args.worktree)
        print("STAGED_FRAME=" + result["frame"])


if __name__ == "__main__":
    main()
