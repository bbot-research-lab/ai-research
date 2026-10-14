"""Bounded research subprocess supervisor with periodic local snapshots.

A job must be supplied explicitly. Never runs original V3 work by default.
Snapshots alone are NOT remotely durable; the CI caller must upload/verify them.
"""
from __future__ import annotations
import argparse
import os
from pathlib import Path
import subprocess
import sys
import time

from .frame_snapshot import snapshot
from .structure_proposals import FRAMES

def supervise(command, *, frame, root, snapshots, max_seconds=19800,
              checkpoint_seconds=600, grace_seconds=1200, poll_seconds=1,
              checkpoint_callback=None):
    if frame not in FRAMES or not command:
        raise ValueError("invalid job")
    if max_seconds <= grace_seconds or checkpoint_seconds <= 0 or poll_seconds <= 0:
        raise ValueError("invalid timing configuration")
    work = Path(root) / frame
    work.mkdir(parents=True, exist_ok=True)
    store = Path(snapshots) / frame
    process = subprocess.Popen(command, cwd=os.getcwd())
    started = time.monotonic()
    next_save = started + checkpoint_seconds
    deadline = started + max_seconds - grace_seconds
    timed_out = False
    def save_checkpoint():
        if (work / 'training_ledger.sqlite3').exists():
            snapshot(work, store)
            if checkpoint_callback is not None:
                checkpoint_callback(frame, store)
    try:
        while process.poll() is None:
            now = time.monotonic()
            if now >= next_save:
                save_checkpoint()
                next_save = now + checkpoint_seconds
            if now >= deadline:
                timed_out = True
                process.terminate()
                try:
                    process.wait(timeout=min(grace_seconds, 60))
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
                break
            time.sleep(poll_seconds)
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
        save_checkpoint()
    if timed_out:
        # Safe bounded end: caller may request next iteration after remote upload.
        return 0
    return process.returncode


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--frame", required=True, choices=FRAMES)
    parser.add_argument("--root", required=True)
    parser.add_argument("--snapshots", required=True)
    parser.add_argument("--max-seconds", type=int, default=19800)
    parser.add_argument("--checkpoint-seconds", type=int, default=600)
    parser.add_argument("--grace-seconds", type=int, default=1200)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    sys.exit(supervise(command, frame=args.frame, root=args.root,
                       snapshots=args.snapshots, max_seconds=args.max_seconds,
                       checkpoint_seconds=args.checkpoint_seconds,
                       grace_seconds=args.grace_seconds))

if __name__ == "__main__":
    main()
