import json, os, time
from pathlib import Path
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes

load_dotenv("/opt/binarybot/.env")

SYMBOLS_PATH = Path("/opt/binarybot/symbols.json")
ACTIVE_PATH  = Path("/opt/binarybot/active_symbols.json")

TOPIC_ALERTS = int(os.getenv("TOPIC_SYSTEM_ALERTS", "0") or "0")
ADMIN_CHAT_ID = os.getenv("TELEGRAM_ADMIN_CHAT_ID")

def load_symbols():
    return json.loads(SYMBOLS_PATH.read_text())

def load_active():
    if not ACTIVE_PATH.exists():
        ACTIVE_PATH.write_text(json.dumps({"forex": [], "crypto": []}, indent=2))
    return json.loads(ACTIVE_PATH.read_text())

def save_active(active):
    ACTIVE_PATH.write_text(json.dumps(active, indent=2))

def build_keyboard(category: str):
    symbols = load_symbols()[category]
    active = load_active()[category]
    rows = []
    row = []
    for s in symbols:
        checked = "✅" if s in active else "⬜"
        row.append(InlineKeyboardButton(f"{checked} {s}", callback_data=f"tg:{category}:{s}"))
        if len(row) == 3:
            rows.append(row); row=[]
    if row: rows.append(row)

    # calculam stare ALL/NONE corect
    all_checked = "✅" if set(active) == set(symbols) and symbols else "⬜"
    none_checked = "✅" if len(active) == 0 else "⬜"

    rows.append([
        InlineKeyboardButton(f"{all_checked} All", callback_data=f"tg:{category}:__ALL__"),
        InlineKeyboardButton(f"{none_checked} None", callback_data=f"tg:{category}:__NONE__"),
        InlineKeyboardButton("🔄 Refresh", callback_data=f"tg:{category}:__REFRESH__"),
    ])
    return InlineKeyboardMarkup(rows)

async def send_panel(chat_id: str, category: str, context: ContextTypes.DEFAULT_TYPE):
    active = load_active()
    text = ("📊 FOREX — Symbol Selector\nBifezi/debifezi simbolurile pe care vrei să le scanez.\n\n"
            f"Active acum: {len(active['forex'])}") if category=="forex" else \
           ("🪙 CRYPTO — Symbol Selector\nBifezi/debifezi simbolurile pe care vrei să le scanez.\n\n"
            f"Active acum: {len(active['crypto'])}")
    await context.bot.send_message(
        chat_id=chat_id,
        text=text,
        reply_markup=build_keyboard(category),
        message_thread_id=TOPIC_ALERTS if TOPIC_ALERTS else None
    )

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # trimite ambele panouri în SYSTEM_ALERTS (ca să fie ușor de găsit)
    await send_panel(update.effective_chat.id, "forex", context)
    await send_panel(update.effective_chat.id, "crypto", context)

async def cmd_forex(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_panel(update.effective_chat.id, "forex", context)

async def cmd_crypto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_panel(update.effective_chat.id, "crypto", context)

async def on_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    data = q.data.split(":")
    # tg:<cat>:<symbol>
    _, cat, sym = data[0], data[1], ":".join(data[2:]) if len(data) > 2 else ""

    symbols_all = load_symbols()[cat]
    active_all = load_active()

    if sym == "__ALL__":
        active_all[cat] = symbols_all[:]
    elif sym == "__NONE__":
        active_all[cat] = []
    elif sym == "__REFRESH__":
        pass
    else:
        if sym in active_all[cat]:
            active_all[cat].remove(sym)
        else:
            active_all[cat].append(sym)

    save_active(active_all)

    # update text + keyboard
    new_count = len(active_all[cat])
    header = ("📊 FOREX — Symbol Selector\nBifezi/debifezi simbolurile pe care vrei să le scanez.\n\n"
              f"Active acum: {new_count}") if cat=="forex" else \
             ("🪙 CRYPTO — Symbol Selector\nBifezi/debifezi simbolurile pe care vrei să le scanez.\n\n"
              f"Active acum: {new_count}")

    await q.edit_message_text(header, reply_markup=build_keyboard(cat))


async def cmd_open(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # /open BTC/USD  -> confirma ca ai executat trade-ul LIVE, elibereaza focus
    try:
        args = context.args or []
        if not args:
            await update.message.reply_text("Usage: /open BTC/USD")
            return
        symbol = " ".join(args).strip().upper()
        from pathlib import Path
        import json
        stp = Path("/opt/binarybot/focus_state.json")
        if not stp.exists():
            stp.write_text(json.dumps({"watchlist": [], "pending_open": {}, "cooldown_until": {}}, indent=2))
        data = json.loads(stp.read_text())
        # marca open pentru symbol (daca era pending)
        pend = data.get("pending_open", {})
        pend[symbol] = True
        data["pending_open"] = pend
        stp.write_text(json.dumps(data, indent=2))
        await update.message.reply_text(f"✅ Confirmed OPEN for {symbol}. Scanner revine la scanare generală când focus se eliberează.")
    except Exception as e:
        await update.message.reply_text(f"ERROR: {e}")



from pathlib import Path as _Path
import json as _json

_SETTINGS_PATH = _Path("/opt/binarybot/settings.json")

def _load_settings():
    if not _SETTINGS_PATH.exists():
        _SETTINGS_PATH.write_text(_json.dumps({"buffer_mode":"medium"}, indent=2))
    try:
        return _json.loads(_SETTINGS_PATH.read_text())
    except Exception:
        return {"buffer_mode":"medium"}

def _save_settings(d):
    _SETTINGS_PATH.write_text(_json.dumps(d, indent=2))

async def cmd_buffer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    st = _load_settings()
    cur = (st.get("buffer_mode") or "medium").lower()
    def mark(name, key):
        # Pad cu NBSP ca toate butoanele sa aiba aceeasi latime (MIC/MARE ca MEDIU)
        label = name + ("\u00A0" * max(0, 5 - len(name)))
        return f"✅ {label}" if cur == key else f"☐ {label}"

    kb = [[
        InlineKeyboardButton(mark("MIC", "small"),  callback_data="buffer_set:small"),
        InlineKeyboardButton(mark("MEDIU", "medium"), callback_data="buffer_set:medium"),
        InlineKeyboardButton(mark("MARE", "large"), callback_data="buffer_set:large"),
    ]]
    await update.message.reply_text("Alege Buffer (Mic / Mediu / Mare):", reply_markup=InlineKeyboardMarkup(kb))

async def cb_buffer_set(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    try:
        await q.answer()
        data = (q.data or "")
        if not data.startswith("buffer_set:"):
            return
        mode = data.split(":",1)[1].strip().lower()
        if mode not in ("small","medium","large"):
            await q.edit_message_text("❌ Buffer invalid.")
            return
        st = _load_settings()
        st["buffer_mode"] = mode
        _save_settings(st)
        # redraw buttons
        cur = mode
        def mark(name, key):
            return f"✅ {name}" if cur == key else f"☐ {name}"
        kb = [[
            InlineKeyboardButton(mark("MIC", "small"),  callback_data="buffer_set:small"),
            InlineKeyboardButton(mark("MEDIU", "medium"), callback_data="buffer_set:medium"),
            InlineKeyboardButton(mark("MARE", "large"), callback_data="buffer_set:large"),
        ]]
        await q.edit_message_text(f"✅ Buffer setat: {mode.upper()}", reply_markup=InlineKeyboardMarkup(kb))
    except Exception as e:
        try:
            await q.edit_message_text(f"ERROR: {e}")
        except Exception:
            pass


def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise SystemExit("Lipsește TELEGRAM_BOT_TOKEN în .env")

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("buffer", cmd_buffer))
    app.add_handler(CommandHandler("forex", cmd_forex))
    app.add_handler(CommandHandler("crypto", cmd_crypto))
    app.add_handler(CommandHandler("open", cmd_open))
    app.add_handler(CallbackQueryHandler(on_toggle, pattern=r"^tg:"))
    app.add_handler(CallbackQueryHandler(cb_buffer_set, pattern=r"^buffer_set:"))
    app.run_polling(close_loop=False)

if __name__ == "__main__":
    main()
