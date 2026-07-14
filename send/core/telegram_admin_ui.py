from __future__ import annotations

from typing import Optional

CALLBACK_PREFIX = "ADMIN_NAV:"


def _btn(text: str, action: str) -> dict[str, str]:
    return {"text": text, "callback_data": f"{CALLBACK_PREFIX}{action}"}


def _kb(rows: list[list[dict[str, str]]]) -> dict[str, list[list[dict[str, str]]]]:
    return {"inline_keyboard": rows}


def parse_action(callback_data: str) -> Optional[str]:
    if not isinstance(callback_data, str) or not callback_data.startswith(CALLBACK_PREFIX):
        return None
    action = callback_data[len(CALLBACK_PREFIX):].strip()
    return action or None


def admin_home_markup(*, include_roles_reload: bool) -> dict[str, list[list[dict[str, str]]]]:
    rows = [
        [_btn("📡 Status", "STATUS"), _btn("📈 Strategy", "STRATEGY")],
        [_btn("🧩 Symbols", "SYMBOLS"), _btn("⚙️ Engine", "ENGINE")],
        [_btn("🧪 Debug", "DEBUG"), _btn("📊 Report", "REPORT")],
        [_btn("👥 Roles", "ROLES"), _btn("💼 Affiliate", "AFFILIATE")],
    ]
    if include_roles_reload:
        rows.append([_btn("♻️ Reload Roles", "RELOAD_ROLES_CONFIRM")])
    return _kb(rows)


def status_markup() -> dict[str, list[list[dict[str, str]]]]:
    return _kb(
        [
            [_btn("📈 Strategy", "STRATEGY"), _btn("⚙️ Engine", "ENGINE")],
            [_btn("⬅️ Admin", "HOME")],
        ]
    )


def strategy_markup() -> dict[str, list[list[dict[str, str]]]]:
    return _kb(
        [
            [_btn("🎯 Thresholds", "THRESHOLDS"), _btn("📐 SR", "SR")],
            [_btn("⚡ Spike", "SPIKE"), _btn("🧩 Symbols", "SYMBOLS")],
            [_btn("⬅️ Admin", "HOME")],
        ]
    )


def symbols_markup() -> dict[str, list[list[dict[str, str]]]]:
    return _kb(
        [
            [_btn("🔄 Refresh Symbols", "SYMBOLS"), _btn("📈 Strategy", "STRATEGY")],
            [_btn("⬅️ Admin", "HOME")],
        ]
    )


def engine_markup(*, include_roles_reload: bool) -> dict[str, list[list[dict[str, str]]]]:
    rows = [[_btn("🔄 Refresh Engine", "ENGINE"), _btn("📡 Status", "STATUS")]]
    if include_roles_reload:
        rows.append([_btn("♻️ Reload Roles", "RELOAD_ROLES_CONFIRM")])
    rows.append([_btn("⬅️ Admin", "HOME")])
    return _kb(rows)


def standard_back_markup() -> dict[str, list[list[dict[str, str]]]]:
    return _kb([[_btn("⬅️ Admin", "HOME")]])


def reload_confirm_markup() -> dict[str, list[list[dict[str, str]]]]:
    return _kb([[_btn("✅ Confirm Reload", "RELOAD_ROLES_EXEC"), _btn("❌ Cancel", "HOME")]])
