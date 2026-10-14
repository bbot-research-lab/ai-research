"""Authenticated encrypted transport for per-frame snapshots.

Ciphertext may be stored externally; plaintext, keys and strategy evidence must
not be committed to the public GitHub repository.
"""
from __future__ import annotations
import base64
import hashlib
import io
import json
from pathlib import Path
import secrets
import zipfile

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from .frame_snapshot import verify_snapshot, restore_snapshot

SCHEMA = "BBOT_FRAME_ENCRYPTED_SNAPSHOT_V1"
AAD_PREFIX = b"BBOT_FRAME_SNAPSHOT_V1:"

def _key(encoded):
    key = base64.b64decode(encoded, validate=True)
    if len(key) != 32:
        raise ValueError("expected 32-byte snapshot key")
    return key

def seal(frame, snapshot_directory, encoded_key):
    if not frame or "/" in frame or ".." in frame:
        raise ValueError("invalid frame")
    source = Path(snapshot_directory)
    manifest = verify_snapshot(source)
    names = sorted([*manifest["files"].keys(), "manifest.json"])
    with io.BytesIO() as buffer:
        with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for name in names:
                archive.write(source / name, arcname=name)
        nonce = secrets.token_bytes(12)
        ciphertext = nonce + AESGCM(_key(encoded_key)).encrypt(
            nonce, buffer.getvalue(), AAD_PREFIX + frame.encode("utf-8"))
    return ciphertext

def unseal(frame, ciphertext, encoded_key, target):
    if not frame or "/" in frame or ".." in frame:
        raise ValueError("invalid frame")
    target = Path(target)
    if target.exists() and any(target.iterdir()):
        raise ValueError("restore target must be empty")
    if len(ciphertext) < 29:
        raise ValueError("invalid encrypted snapshot")
    try:
        plaintext = AESGCM(_key(encoded_key)).decrypt(
            ciphertext[:12], ciphertext[12:], AAD_PREFIX + frame.encode("utf-8"))
    except Exception as exc:
        raise ValueError("snapshot authentication failed") from exc
    with zipfile.ZipFile(io.BytesIO(plaintext)) as archive:
        allowed = {"training_ledger.sqlite3", "training_progress.json", "manifest.json"}
        names = archive.namelist()
        if not names or len(names) != len(set(names)) or set(names) - allowed:
            raise ValueError("unrecognized snapshot archive")
        if sum(item.file_size for item in archive.infolist()) > 500 * 1024**2:
            raise ValueError("snapshot too large")
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            staging = Path(tmp)
            for name in names:
                (staging / name).write_bytes(archive.read(name))
            verify_snapshot(staging)
            restore_snapshot(staging, target)

def file_identity(ciphertext):
    return {"schema": SCHEMA, "sha256": hashlib.sha256(ciphertext).hexdigest(),
            "size": len(ciphertext)}
