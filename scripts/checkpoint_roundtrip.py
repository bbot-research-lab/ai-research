"""Test-only checkpoint roundtrip. NOT financial research or production deployment."""
import argparse
from pathlib import Path
from research_addon.checkpoint_store import load, record_trial, save

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", type=Path, required=True)
    args = parser.parse_args()
    state = load(args.checkpoint)
    next_id = state["completed_trials"]
    # Fixed input fingerprint includes monotonically increasing test counter.
    ok = record_trial(state, {"diagnostic_cycle": next_id}, "CANDIDATE")
    if not ok:
        raise SystemExit("Unexpected duplicate diagnostic trial")
    save(args.checkpoint, state)
    again = load(args.checkpoint)
    if again["completed_trials"] != next_id + 1:
        raise SystemExit("Checkpoint verification failed")
    print("CHECKPOINT_DIAGNOSTIC_PASS", again["completed_trials"])

if __name__ == "__main__":
    main()
