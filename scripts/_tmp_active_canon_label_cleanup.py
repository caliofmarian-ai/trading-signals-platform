from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ACTIVE = ROOT / "send" / "docs" / "canonical" / "active"

replacements = (
    ("Linked proposed/current authorities:", "Linked authorities:"),
    ("Linked proposed/current documents:", "Linked documents:"),
    ("Linked proposed/current authority:", "Linked authority:"),
    ("Supersession intent:", "Supersedes:"),
    ("- Root Strategy Stack successor", "- `CANONICAL_STRATEGY_STACK_v2.0.0.md`"),
    ("- `CANONICAL_STRATEGY_STACK` successor", "- `CANONICAL_STRATEGY_STACK_v2.0.0.md`"),
)

changed_files = 0
changed_lines = 0
for path in sorted(ACTIVE.glob("*.md")):
    text = path.read_text(encoding="utf-8")
    original = text
    for old, new in replacements:
        count = text.count(old)
        if count:
            text = text.replace(old, new)
            changed_lines += count
    if text != original:
        path.write_text(text, encoding="utf-8")
        changed_files += 1

print(f"FILES_REPAIRED={changed_files}")
print(f"LABEL_REPLACEMENTS={changed_lines}")
