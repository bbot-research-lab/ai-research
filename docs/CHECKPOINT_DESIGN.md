# Durable trial checkpoints — implementation stage

Added `research_addon/checkpoint_store.py`:
- JSON schema version; SHA-256 fingerprints of parameter dictionaries for duplicate prevention.
- Saves via temporary file + fsync + atomic replace.
- Rejects unknown schemas, invalid records and approval/deployment status.
- A checkpoint is **research-only**, without order or strategy promotion authority.

**Important operational limitation:** GitHub-hosted runners are ephemeral. Atomic local checkpoint writing is **not persistence across Actions jobs**. A secure durable remote store (e.g., restricted Git branch/artifact cache with explicit retention, or S3 with read/write boundary) and concurrency coordination is required before scheduled research can resume. GitHub Actions artifacts are retained for a finite period and are not suitable as the sole authoritative ledger.

**Not yet integrated:** real V3 research controller, GA/Optuna objectives, sealed verification or AWS synchronizer. No scheduled research and no live deployment are enabled.
