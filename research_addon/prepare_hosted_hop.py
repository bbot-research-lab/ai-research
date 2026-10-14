"""Bind a synthetic workflow hop to the authenticated restored frame state.

The restored hop advances only by one, never rewinds, and never silently
reinitializes legacy checkpoints. The next frame snapshot encrypts the receipt.
"""
from __future__ import annotations
import argparse
from pathlib import Path
from .continuation_receipt import read_hop,write_hop
from .structure_proposals import FRAMES

def prepare_hop(frame,root,requested):
    directory=Path(root)/frame
    existing=read_hop(directory,frame,require_existing=True)
    if type(requested) is not int or requested < 0 or requested > 48:
        raise ValueError("invalid requested hop")
    if requested == existing:
        # Retries of a failed job do not create a new hop.
        return {"frame":frame,"hop":existing,"advanced":False}
    if requested != existing+1:
        raise ValueError("checkpoint hop mismatch: refusing rewind or skip")
    write_hop(directory,frame,requested,expected_previous=existing)
    return {"frame":frame,"hop":requested,"advanced":True}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--frame",required=True,choices=FRAMES)
    p.add_argument("--root",required=True)
    p.add_argument("--hop",required=True,type=int)
    a=p.parse_args()
    print(prepare_hop(a.frame,a.root,a.hop))
if __name__=="__main__":
    main()
