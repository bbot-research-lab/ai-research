"""Atomic distributed synthetic handoff claim using create-only Git refs.

The Git server accepts at most one initial creation of a given claim ref.
Claims remain for audit. If a caller crashes after claiming, operators must
reconcile the outcome; never auto-retry a possibly dispatched handoff.
"""
from __future__ import annotations
import subprocess
import secrets
from pathlib import Path
from .structure_proposals import FRAMES

PREFIX="refs/heads/synthetic-handoff-claim-"

def claim_ref(frame,run_id,hop):
    if frame not in FRAMES or type(run_id) is not int or run_id<=0 or type(hop) is not int or not 0<=hop<48:
        raise ValueError("invalid synthetic handoff")
    return f"{PREFIX}{run_id}-{frame}-{hop}"

def claim_remote(remote,frame,run_id,hop,*,runner=subprocess.run):
    ref=claim_ref(frame,run_id,hop)
    # Create-only push rejects any existing remote ref. The immutable claim
    # object itself is the observed base commit; no mutable shared index.
    with __import__("tempfile").TemporaryDirectory() as temp:
        path=Path(temp)
        def git(*args):
            r=runner(["git",*map(str,args)],cwd=path,capture_output=True,text=True)
            if r.returncode:
                raise RuntimeError("Git claim command failed")
            return r.stdout.strip()
        git("init","-q")
        git("config","user.name","github-actions[bot]")
        git("config","user.email","41898282+github-actions[bot]@users.noreply.github.com")
        (path/"claim.txt").write_text(ref+"\\n"+secrets.token_hex(16)+"\\n")
        git("add","claim.txt")
        git("commit","-qm","Synthetic immutable handoff claim")
        git("remote","add","origin",remote)
        # A second runner must not overwrite the first claim. Git push
        # without force refuses non-fast-forward, but an identical commit
        # may be accepted. Randomness in the commit prevents that ambiguity.
        git("push","origin","HEAD:"+ref)
    return ref
