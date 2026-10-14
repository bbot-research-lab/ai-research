"""Consistent per-frame snapshots for research-only SQLite state.

Snapshots are local and untrusted until copied to a durable remote store.
No official V3 checkpoint format or production state is modified.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import tempfile

FILES = ("training_ledger.sqlite3", "training_progress.json")

def snapshot(frame_dir, destination):
    frame_dir, destination = Path(frame_dir), Path(destination)
    if not (frame_dir / FILES[0]).is_file():
        raise ValueError("missing experiment ledger")
    destination.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=destination) as staging:
        stage = Path(staging)
        source = sqlite3.connect(str(frame_dir / FILES[0]))
        target = sqlite3.connect(str(stage / FILES[0]))
        try:
            source.backup(target)
        finally:
            target.close()
            source.close()
        if (frame_dir / FILES[1]).is_file():
            (stage / FILES[1]).write_bytes((frame_dir / FILES[1]).read_bytes())
        entries = {}
        for path in stage.iterdir():
            data = path.read_bytes()
            entries[path.name] = {"sha256": hashlib.sha256(data).hexdigest(), "size": len(data)}
        manifest = {"schema": "BBOT_FRAME_SNAPSHOT_V1", "files": entries}
        (stage / "manifest.json").write_text(json.dumps(manifest, sort_keys=True), encoding="utf-8")
        # Stage each file then atomically replace manifest last. Readers should
        # verify all hashes and treat partial updates as invalid.
        for name in FILES:
            source_path = stage / name
            if source_path.exists():
                os.replace(source_path, destination / name)
        os.replace(stage / "manifest.json", destination / "manifest.json")
    return manifest

def verify_snapshot(directory):
    directory = Path(directory)
    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    entries = manifest.get("files")
    if manifest.get("schema") != "BBOT_FRAME_SNAPSHOT_V1" or not isinstance(entries, dict):
        raise ValueError("invalid snapshot manifest")
    if FILES[0] not in entries or set(entries) - set(FILES):
        raise ValueError("unrecognized snapshot files")
    for name, record in entries.items():
        data = (directory / name).read_bytes()
        if len(data) != record.get("size") or hashlib.sha256(data).hexdigest() != record.get("sha256"):
            raise ValueError("corrupt frame snapshot")
    return manifest

def restore_snapshot(directory, frame_dir):
    verify_snapshot(directory)
    directory, frame_dir = Path(directory), Path(frame_dir)
    frame_dir.mkdir(parents=True, exist_ok=True)
    if any((frame_dir / name).exists() for name in FILES):
        raise ValueError("restore requires empty frame target")
    for name in FILES:
        if (directory / name).is_file():
            data = (directory / name).read_bytes()
            fd, temporary = tempfile.mkstemp(prefix=".restore-", dir=frame_dir)
            with os.fdopen(fd, "wb") as out:
                out.write(data)
                out.flush()
                os.fsync(out.fileno())
            os.replace(temporary, frame_dir / name)
