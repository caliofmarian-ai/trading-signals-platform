# Startup Import Order Audit

## Verified startup chain
1. `railway.json` runs `python -m scripts.railway_start`.
2. `scripts.railway_start.main()` resolves `BINARYBOT_BASE_DIR` and applies the Railway path contract.
3. `initialize_for_railway()` prepares runtime directories.
4. `readiness_report()` imports runtime modules.
5. `runtime.system_boot.start_system()` starts runtime threads.

## Root-cause finding
- PR #32 loaded Telegram active UI state via a module-import side effect in `send/core/telegram_app_nav.py`.
- That load happened only once.
- If the module was imported before the final runtime path contract was established, persisted state was not reloaded later.
- Reproduction confirmed: importing `core.telegram_app_nav` before `BINARYBOT_BASE_DIR` was set left active UI recovery empty even after the variable was set later.

## Correction
- Import-time load side effect was removed as the only recovery mechanism.
- An explicit, idempotent `initialize_active_ui_state()` contract now performs loading after runtime path resolution and before Telegram polling starts.
