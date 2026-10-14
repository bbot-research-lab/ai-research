# Initial static dependency findings

Source: user-uploaded BBOT_RESEARCH_UPLOAD.zip, inspected offline. This is **not** a certification that the archive is safe to publish.

- 3,648 ZIP entries; Windows `\\` separators are used within archive member names.
- Top-level `strategy_lab` contains at least 78 Python modules.
- Core modules are present: `roadmap_manager.py`, `research_controller.py`, `run_strategy.py`, `v3_governance.py`, `v3_task_queue.py`.
- `roadmap_manager.py` uses `subprocess`, `SERVER_PUSH_HOLD.flag`, and server-push-related state.
- `research_controller.py` conditionally imports `msvcrt`, imports `v3_deployment`, and inspects `SERVER_PUSH_HOLD.flag`.
- `v3_deployment.py` includes file/database updates and should not be copied into a public runnable job without an isolated, audited replacement.
- `run_strategy.py` imports NumPy/Pandas and dynamic import support. Dependencies and data contracts require examination.
- Filename scans alone cannot establish confidentiality. Public publishing is blocked until full security audit and import closure verification.

## Decision
Keep real research execution **disabled** until Linux compatibility, data contracts, side effects and all imported files pass review. Separate candidate discovery from validation, approval and live deployment.
