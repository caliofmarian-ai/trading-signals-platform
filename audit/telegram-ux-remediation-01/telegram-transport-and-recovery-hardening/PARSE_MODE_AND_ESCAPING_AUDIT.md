# PARSE MODE AND ESCAPING AUDIT

## Before Fix

### edit_message — HTML parse_mode

```python
if text:
    payload["text"] = text
    payload["parse_mode"] = "HTML"
```

### send_message — no parse_mode

```python
payload = {"chat_id": chat_id, "text": text}
# parse_mode absent → Telegram default (plain text)
```

## Inconsistency consequence

Pages produced by `render_admin_home()` include command-help strings from the command registry:

```
/thresholds PRE|CONFIRM|OPEN <value>
/sr <multiplier>
/spike wick_body_ratio_max|range_z_max|jump_vs_atr_max <value>
/download <dir> <filename>
/symbols add SYMBOL
/symbols remove SYMBOL
```

These strings contain `<` and `>` characters.  Under `parse_mode="HTML"`, Telegram's parser
treats `<value>`, `<dir>`, `<filename>`, `<multiplier>` as HTML start tags and returns:

```
400 Bad Request: can't parse entities: Unsupported start tag "value" at byte offset N
```

This exception was caught by `_edit_interactive_message`, classified as "unexpected"
(not "stale"), logged internally, and the function returned `False`.
`_send_interactive_page` then fell through to `send_message` (no parse_mode) which succeeded
— sending a **new message** instead of editing the existing one.  This is the primary cause
of the observed single-message contract violation.

## Page text format

All interactive page renderers (`telegram_app_nav.py`, `admin_views.py`) produce plain text.
Some pages use Markdown-style `*bold*` and `_italic_` syntax.  Neither Telegram Markdown nor
Telegram MarkdownV2 is explicitly set, so these markers render literally under the default
(no parse_mode) mode.  This is acceptable; the single-message navigation behaviour is
restored without needing to re-render all pages.

If rich formatting is desired in a future cycle, the correct approach is to:
1. Choose exactly one parse_mode (recommend MarkdownV2).
2. Apply it consistently to both `send_message` and `edit_message`.
3. Escape all dynamic content using the appropriate escape helper.

## After Fix

`parse_mode` is absent from both `send_message` and `edit_message`.  Telegram renders all
text literally.  No parse errors are possible from `<>` characters in admin command-help
strings.  Both call paths are consistent.

## Escaping requirement

No escaping is required for the default (no parse_mode) mode because Telegram renders all
characters literally.  `_sanitize()` in `telegram_publisher` performs token redaction on
error strings only and is unrelated to message-text escaping.
