from pathlib import Path

path = Path(__file__).resolve().parents[1] / "send/core/bot_service.py"
text = path.read_bytes().decode("utf-8")

replacements = [
    ('"Profiles: NOT AVAILABLE\n"', '"Profiles: NOT AVAILABLE\\n"'),
    ('f"Current profile state: {current_observation}\n\n"', 'f"Current profile state: {current_observation}\\n\\n"'),
]

for old, new in replacements:
    if text.count(old) != 1:
        raise SystemExit(f"expected exactly one generated escape target, found {text.count(old)}")
    text = text.replace(old, new, 1)

path.write_bytes(text.encode("utf-8"))
