# send/core/jsonl_parser.py
# BinaryBot — Canonical JSONL / JSON parsing helper for analytics and research.
#
# Rules:
# - Never silently convert malformed JSON to an empty valid structure.
# - Every failure produces a typed ParseError with source path and line number.
# - JSONL iteration supports record-level isolation: one bad line does not
#   invalidate the entire file, but the failure is explicitly surfaced.
# - Blank lines are skipped; they do not count as errors.
# - No network access, threads, or live-service side effects.

from __future__ import annotations

import json
from typing import Any, Dict, Iterator, Optional, Tuple


class ParseError(ValueError):
    """Raised when a JSON line cannot be parsed or is not a dict."""

    def __init__(
        self,
        message: str,
        *,
        source_path: str = "<unknown>",
        line_number: int = 0,
        raw: str = "",
    ) -> None:
        super().__init__(message)
        self.source_path = source_path
        self.line_number = line_number
        self.raw = raw

    def __str__(self) -> str:
        loc = f"{self.source_path}:{self.line_number}"
        return f"ParseError({loc}): {super().__str__()}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_path": self.source_path,
            "line_number": self.line_number,
            "message": super().__str__(),
            "raw_prefix": self.raw[:200],
        }


def parse_json_line(
    line: str,
    *,
    source_path: str = "<unknown>",
    line_number: int = 0,
) -> Dict[str, Any]:
    """
    Parse a single JSON line.

    Returns a dict on success.
    Raises ParseError on empty input, malformed JSON, or non-dict JSON values.
    Never returns {} for malformed input.
    """
    stripped = line.strip()
    if not stripped:
        raise ParseError(
            "empty line",
            source_path=source_path,
            line_number=line_number,
            raw=line,
        )
    try:
        obj = json.loads(stripped)
    except json.JSONDecodeError as exc:
        raise ParseError(
            f"invalid JSON: {exc}",
            source_path=source_path,
            line_number=line_number,
            raw=stripped[:200],
        ) from exc
    if not isinstance(obj, dict):
        raise ParseError(
            f"expected JSON object, got {type(obj).__name__}",
            source_path=source_path,
            line_number=line_number,
            raw=stripped[:200],
        )
    return obj


def iter_jsonl(
    path: str,
) -> Iterator[Tuple[Optional[Dict[str, Any]], Optional[ParseError]]]:
    """
    Iterate a JSONL file, yielding (record, None) or (None, error) per line.

    Blank lines are skipped without yielding.
    Raises FileNotFoundError if the file does not exist.
    Each call is independent; partial files are processed record-by-record.
    """
    with open(path, "r", encoding="utf-8") as fh:
        for line_number, raw_line in enumerate(fh, start=1):
            stripped = raw_line.rstrip("\n")
            if not stripped.strip():
                continue
            try:
                record = parse_json_line(stripped, source_path=path, line_number=line_number)
                yield record, None
            except ParseError as exc:
                yield None, exc
