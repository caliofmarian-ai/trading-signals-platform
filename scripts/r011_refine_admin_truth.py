from __future__ import annotations

from pathlib import Path


repo = Path(__file__).resolve().parents[1]
path = repo / "send/core/admin_views.py"
with path.open("r", encoding="utf-8", newline="") as handle:
    text = handle.read()

old_source = '''    def _limit_source(tier: str) -> str:\n        if str(os.getenv(f"{tier}_LIMIT") or "").strip():\n            return "ENV"\n        if f"{tier}_LIMIT" in raw or tier in raw_limits:\n            return "PERSISTED_CONFIG"\n        route_cfg = raw_routes.get(tier)\n        if isinstance(route_cfg, dict) and "daily_open_now_limit" in route_cfg:\n            return "PERSISTED_CONFIG"\n        return "CANONICAL_DEFAULT"\n'''
new_source = '''    def _explicit_limit(value: Any) -> tuple[bool, Optional[int]]:\n        if value is None:\n            return False, None\n        normalized = str(value).strip()\n        if not normalized:\n            return False, None\n        if normalized.upper() in {"UNLIMITED", "NONE", "INF"}:\n            return True, None\n        try:\n            return True, int(normalized)\n        except (TypeError, ValueError):\n            return False, None\n\n    def _limit_source(tier: str) -> str:\n        effective_limit = limits.get(tier)\n        env_valid, env_limit = _explicit_limit(os.getenv(f"{tier}_LIMIT"))\n        if env_valid and env_limit == effective_limit:\n            return "ENV"\n\n        route_cfg = raw_routes.get(tier)\n        persisted_candidates: List[Any] = []\n        if f"{tier}_LIMIT" in raw:\n            persisted_candidates.append(raw.get(f"{tier}_LIMIT"))\n        if tier in raw_limits:\n            persisted_candidates.append(raw_limits.get(tier))\n        if isinstance(route_cfg, dict) and "daily_open_now_limit" in route_cfg:\n            persisted_candidates.append(route_cfg.get("daily_open_now_limit"))\n\n        for candidate in persisted_candidates:\n            valid, parsed = _explicit_limit(candidate)\n            if valid and parsed == effective_limit:\n                return "PERSISTED_CONFIG"\n        return "CANONICAL_DEFAULT"\n'''

if text.count(old_source) != 1:
    raise SystemExit(f"expected one exact _limit_source block, found {text.count(old_source)}")
text = text.replace(old_source, new_source, 1)

old_counter = '        counter_text = str(counter) if limit is not None else "unlimited"\n'
new_counter = '        counter_text = str(counter)\n'
if text.count(old_counter) != 1:
    raise SystemExit(f"expected one exact counter_text line, found {text.count(old_counter)}")
text = text.replace(old_counter, new_counter, 1)

with path.open("w", encoding="utf-8", newline="") as handle:
    handle.write(text)
