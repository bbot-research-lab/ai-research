# Uploaded research archive audit — 2026-10-14

- Source: user-provided BBOT_RESEARCH_UPLOAD.zip (~84 MiB), **not published**.
- 3,648 ZIP entries; 1,023 Python files and 2,549 JSON files. Many JSON files are research outputs, not necessarily public market candles.
- Preliminary content screening of 1,666 files smaller than 200 KB identified 21 files containing keywords associated with credentials, private host paths or account/Telegram metadata (14 .py, 2 .json, 5 .ps1). These are **potential matches, not confirmed exposed secrets**. Larger files and remaining items were not completely audited.
- The ZIP also includes server_exchange_snapshot.json and local/Windows scripts, which must not be uploaded blindly.
- No raw market-data dataset can be assumed safe for public release without inspecting content and source/license.
- Core research entrypoints exist: roadmap_manager.py, research_controller.py, run_strategy.py; exact runtime dependency closure, environment compatibility and side effects not yet established.
- Existing live execution and trading server are not modified.

## Publication decision
**BLOCK whole-archive upload.** Publish only audited research-only modules and redacted configuration, while retaining the full research import locally for review.

## Next acceptance gates
1. Complete source/config scanning including large files and nested import closure.
2. Identify stateful writes, deploy hooks and credential-bearing code before selecting module list.
3. Build isolated Linux research job with zero exchange order side effects.
4. Run actual single research cycle (dry-run) with official validation.
5. Only enable periodic research once checkpoint persistence is proven.

Preliminary screening is not a guarantee of secrecy. Do not publish any data or source simply because it passes a filename pattern.
