from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence


@dataclass(frozen=True)
class CommandSpec:
    command: str
    usage: str
    description: str
    access: str
    mutation: bool = False
    permission_note: str = ""


_COMMANDS: tuple[CommandSpec, ...] = (
    CommandSpec("/start", "/start", "Confirm that the bot is online.", "public"),
    CommandSpec("/help", "/help", "Show the active command inventory.", "public"),
    CommandSpec("/status", "/status", "Show runtime health and safe-mode state.", "public"),
    CommandSpec("/admin", "/admin", "Show admin identity and command overview.", "admin", permission_note="admin.view"),
    CommandSpec("/strategy", "/strategy", "View strategy configuration.", "admin", permission_note="strategy.view"),
    CommandSpec("/thresholds", "/thresholds", "View score thresholds.", "admin", permission_note="strategy.view"),
    CommandSpec("/thresholds", "/thresholds PRE|CONFIRM|OPEN <value>", "Update score thresholds.", "admin", mutation=True, permission_note="strategy.thresholds.write"),
    CommandSpec("/sr", "/sr", "View SR multiplier.", "admin", permission_note="strategy.view"),
    CommandSpec("/sr", "/sr <multiplier>", "Update SR multiplier.", "admin", mutation=True, permission_note="strategy.sr.write"),
    CommandSpec("/spike", "/spike", "View spike-filter settings.", "admin", permission_note="strategy.view"),
    CommandSpec("/spike", "/spike wick_body_ratio_max|range_z_max|jump_vs_atr_max <value>", "Update spike-filter settings.", "admin", mutation=True, permission_note="strategy.spike.write"),
    CommandSpec("/symbols", "/symbols list", "List active symbols.", "admin", permission_note="strategy.view"),
    CommandSpec("/symbols", "/symbols add SYMBOL", "Add an active symbol.", "admin", mutation=True, permission_note="strategy.symbols.write"),
    CommandSpec("/symbols", "/symbols remove SYMBOL", "Remove an active symbol.", "admin", mutation=True, permission_note="strategy.symbols.write"),
    CommandSpec("/engine", "/engine", "View engine status.", "admin", permission_note="engine.view"),
    CommandSpec("/debug", "/debug", "View the latest decision debug snapshot.", "admin", permission_note="debug.view"),
    CommandSpec("/report", "/report", "View the latest strategy report.", "admin", permission_note="reports.view"),
    CommandSpec("/roles", "/roles", "View configured roles.", "admin", permission_note="roles.view"),
    CommandSpec("/affiliate", "/affiliate", "View affiliate scope.", "admin", permission_note="affiliate.view"),
    CommandSpec("/roles_reload", "/roles_reload", "Reload role and permission config.", "admin", mutation=True, permission_note="roles.write"),
)


def command_registry() -> Sequence[CommandSpec]:
    return _COMMANDS


def admin_command_names() -> set[str]:
    return {spec.command for spec in _COMMANDS if spec.access == "admin"}


def public_command_names() -> set[str]:
    return {spec.command for spec in _COMMANDS if spec.access == "public"}


def _render_section(title: str, specs: Iterable[CommandSpec]) -> list[str]:
    items = list(specs)
    if not items:
        return []
    lines = [title]
    for spec in items:
        permission = f" [{spec.permission_note}]" if spec.permission_note else ""
        lines.append(f"{spec.usage} — {spec.description}{permission}")
    lines.append("")
    return lines


def render_help_text() -> str:
    lines: list[str] = ["BinaryBot Commands", ""]
    lines.extend(_render_section("Read-only commands", [spec for spec in _COMMANDS if not spec.mutation]))
    lines.extend(_render_section("Mutation commands", [spec for spec in _COMMANDS if spec.mutation]))
    lines.extend(
        [
            "Restrictions",
            "Public commands are available in any chat context.",
            "Admin commands require the configured admin control topic and canonical role permissions.",
            "Owner private-chat access is allowed only for: /admin /strategy /thresholds /sr /spike /symbols /engine /debug /report /roles /affiliate.",
            "Mutation commands stay fail-closed outside the admin context or without the required permission.",
        ]
    )
    return "\n".join(line for line in lines if line is not None).strip()


def render_start_text(*, shadow_mode: bool) -> str:
    mode = "SHADOW_MODE is active." if shadow_mode else "Shadow mode is disabled."
    return "\n".join(
        [
            "BinaryBot is online.",
            mode,
            "Use /help to view available commands.",
        ]
    )


def render_status_text(snapshot: dict[str, object]) -> str:
    lines = [
        "BinaryBot Status",
        "",
        f"Overall: {snapshot.get('overall_state', 'UNKNOWN')}",
        f"Runtime phase: {snapshot.get('runtime_phase', 'unknown')}",
        f"Health: {snapshot.get('runtime_message', 'unknown')}",
        f"Recovery: {snapshot.get('recovery_state', 'UNKNOWN')}",
        f"Market data: {snapshot.get('market_data_state', 'UNKNOWN')}",
        f"Telegram: {snapshot.get('telegram_state', 'UNKNOWN')}",
        f"FSM: {snapshot.get('fsm_state', 'UNKNOWN')}",
        f"Shadow mode: {snapshot.get('shadow_mode', 'OFF')}",
        f"Broker execution: {snapshot.get('broker_state', 'NOT AVAILABLE')}",
    ]
    note = snapshot.get("market_data_note")
    if isinstance(note, str) and note.strip():
        lines.append(f"Market note: {note.strip()}")
    return "\n".join(lines)
