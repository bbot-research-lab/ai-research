"""Bounded synthetic continuation batches; never dispatches live trading.

Each invocation is finite, and remote persistence is provided by the caller.
"""
from __future__ import annotations
import argparse
import subprocess
import sys

from .structure_proposals import FRAMES

def run_iterations(frame, root, *, batches, runner=None):
    if frame not in FRAMES or not 1 <= batches <= 24:
        raise ValueError("invalid bounded continuation")
    runner = runner or subprocess.run
    completed = 0
    for n in range(batches):
        result = runner([sys.executable, "-m", "research_addon.training_orchestrator",
                         "--frame", frame, "--root", str(root), "--dry-synthetic"],
                        check=False)
        if result.returncode:
            raise RuntimeError("synthetic batch failed; refuse continuation")
        completed += 1
    return completed

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--frame", required=True, choices=FRAMES)
    p.add_argument("--root", required=True)
    p.add_argument("--batches", type=int, default=2)
    a = p.parse_args()
    print("BATCHES_COMPLETED=" + str(run_iterations(a.frame, a.root, batches=a.batches)))

if __name__ == "__main__":
    main()
