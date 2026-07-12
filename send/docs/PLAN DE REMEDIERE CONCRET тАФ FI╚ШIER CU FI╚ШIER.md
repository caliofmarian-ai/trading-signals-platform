# PLAN DE REMEDIERE CONCRET — FIȘIER CU FIȘIER

Status: Satellite / Non-Canonical Reference
Canonical Position: Supporting document only; does not define active canonical truth.
Primary Active Canon: Refer to active canonical documents under /opt/binarybot/docs/canonical/active/

---

Da. Mai jos ai un plan de remediere concret, fișier cu fișier, în ordinea corectă de lucru, astfel încât să stabilizezi botul fără să strici și mai mult repo-ul.

L-am făcut în stil operațional:

ce fișier atingi,

ce problemă rezolvi,

ce modifici concret,

ce verifici după.



---

PLAN DE REMEDIERE CONCRET — FIȘIER CU FIȘIER

FAZA 0 — REGULĂ DE LUCRU

Înainte de orice modificare:

1. nu mai edita fișierele .bak, Copy, variante vechi


2. stabilește clar că fișierele active sunt doar cele fără sufixe


3. creează un branch sau backup separat de lucru


4. orice patch nou trebuie să respecte:

un singur adevăr pentru config

un singur adevăr pentru state

un singur adevăr pentru schema de evenimente





---

FAZA 1 — STABILIZARE CRITICĂ

1) core/strategy_v2.py

Problemă

Strategia citește ultima lumânare cu [-1], dar adapterul livrează newest-first.

Ce trebuie făcut

Alege una din două variante, dar recomand varianta A.

Varianta A — păstrezi contractul docs + adapter

Păstrezi:

candles[0] = newest


și modifici strategia să folosească:

candles_m1[0] pentru lumânarea curentă

candles_m1[1] pentru lumânarea anterioară


Ce schimbi concret

Caută toate locurile de tip:

candles_m1[-1]
candles_m1[-2]
closes_m1[-1]
closes_m1[-2]
highs_m1[-1]
lows_m1[-1]

și inversează logica la:

candles_m1[0]
candles_m1[1]
closes_m1[0]
closes_m1[1]
highs_m1[0]
lows_m1[0]

Ce trebuie verificat atent

calcul spike

candle timestamp

expiry anchor

signal_id

prev vs current candle

orice slicing de ferestre istorice


După patch, verifici

ultima lumânare procesată este chiar cea mai recentă

timestamp-ul din semnal coincide cu ultima lumânare din feed

nu se inversează accidental serii folosite la medii/statistici


Severitate

Critic — primul lucru de reparat


---

2) core/candle_adapter.py

Problemă

Nu e neapărat bug aici, dar trebuie întărit contractul ca să nu mai existe ambiguitate.

Ce trebuie făcut

Adaugă assert-uri și comentarii canonice.

Ce schimbi concret

În punctul în care returnezi lista normalizată:

confirmi explicit că este sortată descrescător după ts

adaugi validare că candles[0]["ts"] >= candles[1]["ts"]


Adaugă un helper clar

Exemplu logic:

def assert_newest_first(candles):
    if len(candles) >= 2 and candles[0]["ts"] < candles[1]["ts"]:
        raise ValueError("Candles must be newest-first")

După patch, verifici

orice intrare în strategie primește serii newest-first

dacă apare date disorder, engine-ul oprește clar cu eroare utilă


Severitate

Critic indirect — important imediat după strategy


---

3) core/signal_engine.py

Probleme

1. event_type="SIGNAL_EVENT" în loc de signal_event


2. citește config dintr-un loc care nu e aliniat cu restul proiectului


3. probabil folosește fallback-uri tăcute



Ce trebuie făcut

A. repari event type

Înlocuiești:

"SIGNAL_EVENT"

cu:

"signal_event"

B. unifici path-urile

Acest fișier trebuie să citească doar din convenția oficială.

Convenția recomandată

config static/mutabil de admin: /opt/binarybot/config/...

state runtime: /opt/binarybot/state/...

observability: /opt/binarybot/observability/...


Ce schimbi concret

Păstrezi:

ACTIVE_SYMBOLS_PATH = "/opt/binarybot/config/active_symbols.json"
SETTINGS_PATH = "/opt/binarybot/config/settings.json"

dar apoi te asiguri că și celelalte module folosesc exact aceleași căi.

După patch, verifici

engine-ul vede exact aceleași simboluri pe care le modifici din admin

settings.json chiar există în config/

logurile nu mai aruncă eroare pe SIGNAL_EVENT


Severitate

Critic


---

4) core/bot_service.py

Probleme

1. folosește path-uri vechi în root


2. importă outcome_tracker inexistent


3. amestecă logică veche și nouă


4. e cel mai fragil fișier din repo



Ce trebuie făcut acum

Nu îl rescrii complet din prima. Mai întâi îl stabilizezi.


---

4.1 Path-uri

Înlocuiești toate path-urile vechi de tip:

/opt/binarybot/settings.json
/opt/binarybot/symbols.json
/opt/binarybot/focus_state.json

cu convenția unică:

CONFIG_DIR = "/opt/binarybot/config"
STATE_DIR = "/opt/binarybot/state"

SETTINGS_PATH = os.path.join(CONFIG_DIR, "settings.json")
ACTIVE_SYMBOLS_PATH = os.path.join(CONFIG_DIR, "active_symbols.json")
FOCUS_STATE_PATH = os.path.join(STATE_DIR, "focus_state.json")
DIST_STATE_PATH = os.path.join(STATE_DIR, "dist_state.json")

4.2 Eliminarea outcome_tracker

Caută:

from core import outcome_tracker
result = outcome_tracker.register_vote(...)

și scoate complet această ramură.

Înlocuiește cu apel către:

core/outcome_service.py sau

funcția actuală canonică de outcome/voting


4.3 Curățare minimă

Identifică și marchează în comentarii:

blocuri vechi

blocuri de compatibilitate

callback-uri duplicate


Nu le șterge pe toate din prima, dar izolează clar ce rămâne activ.

După patch, verifici

comenzile admin încă răspund

voturile/callback-urile nu mai crapă la import

UI admin modifică exact fișierele citite de engine


Severitate

Critic


---

5) core/admin_commands.py

Problemă

Acesta pare mai aproape de convenția bună decât bot_service.py, dar trebuie aliniat total cu engine-ul.

Ce trebuie făcut

Verifici că folosește exact aceleași fișiere ca signal_engine.py:

config/active_symbols.json

config/settings.json

config/admin_settings.json


Ce schimbi concret

Dacă există referințe la:

symbols.json

fișiere root-level

state care ar trebui să fie config


le normalizezi.

După patch, verifici

/health, /engine, modificarea simbolurilor, focus și buffer merg pe aceleași surse

orice schimbare din admin se vede imediat în runtime


Severitate

Majoră


---

6) core/distribution_router.py

Probleme

1. build_event() este apelat cu argumente invalide


2. aici se poate rupe resetul zilnic și logarea distribuției


3. posibilă logică de tier reset sensibilă



Ce trebuie făcut

Trebuie să repari toate apelurile la:

observability_logger.build_event(...)

Semnătura corectă

Trebuie folosit doar:

build_event(event_type, data, source=None, correlation=None)

Exemplu de remediere

În loc de:

build_event(
    event_type="tier_reset",
    data=...,
    module="distribution_router",
    now_ts=now_ts,
)

faci:

build_event(
    event_type="tier_reset",
    data={
        ...,
        "now_ts": now_ts,
    },
    source={
        "module": "distribution_router",
        "function": "maybe_daily_reset",
    },
)

Verifică toate apelurile similare

tier reset

tier publish

orice event build local


După patch, verifici

resetul zilnic nu mai aruncă excepții

tier_publish și tier_reset intră corect în loguri


Severitate

Critic


---

7) core/observability_logger.py

Probleme

1. whitelist-ul de event types nu corespunde cu ce emit modulele


2. schema reală nu e aliniată cu schema/event_schema.json



Ce trebuie făcut în faza de stabilizare

Ai două opțiuni:

fie restrângi toate modulele la whitelist-ul actual

fie extinzi whitelist-ul conform nevoilor reale


Recomandarea mea: în faza 1 restrângi emiterea, nu extinzi haotic schema.

Ce schimbi concret

Păstrezi lista canonică mică:

engine_start

engine_stop

signal_event

decision

fsm_transition

tier_publish

tier_reset

admin_change

user_outcome

error


și mapezi toate modulele la acestea.

Exemple de mapare

SIGNAL_EVENT → signal_event

OUTCOME_SET → user_outcome

outcome_register_open_now → user_outcome

system_health → fie engine_start/error, fie decision dacă e health snapshot separat

risk_warning → error sau decision cu categorie warning

strategy_optimizer → decision sau eveniment separat doar după ce actualizezi schema oficială


Mai adaugi ceva important

Când respingi un event invalid, mesajul de eroare trebuie să includă:

attempted_event_type

module

payload minim


După patch, verifici

nu mai apar observability_log_failed

error logul scade masiv

toate evenimentele importante ajung în fișierele corecte


Severitate

Critic


---

8) core/outcome_service.py

Probleme

1. log_warning() este apelat greșit


2. evenimentele outcome nu sunt aliniate semantic cu loggerul



Ce trebuie făcut

Schimbi toate apelurile de tip:

observability_logger.log_warning({...})

în:

observability_logger.log_warning(
    warn_type="...",
    message="...",
    context={...},
    source={...},
)

Al doilea pas

Normalizezi outcome events către:

"user_outcome"

nu către event types exotice.

După patch, verifici

voturile nu mai generează erori de logging

toate rezultatele se văd în observability corect


Severitate

Majoră


---

9) intelligence/risk_monitor.py

Problemă

Folosește tot log_warning() greșit și emite risk_warning nealiniat.

Ce trebuie făcut

Exact aceeași corecție:

keyword args la log_warning

mapare event semantică la schema existentă


Recomandare

În loc de risk_warning ca event type separat, folosește:

error cu severity="WARNING" sau

decision cu decision_kind="RISK_WARNING"


După patch, verifici

monitorizarea de risc nu mai rupe observability

warning-urile sunt vizibile și consistente


Severitate

Majoră


---

10) monitoring/restart_guard.py

Problemă

Emite system_health care nu e acceptat de logger și participă la secvența cu dubla numărare.

Ce trebuie făcut

A. normalizezi logging-ul

În faza 1, nu inventa event nou.

Mapează la:

error dacă e anomalie

sau decision dacă e health snapshot logic


B. verifici rolul exact al fișierului

Dacă el doar face freeze detection, atunci evenimentele trebuie să fie minimale și compatibile.

După patch, verifici

la boot nu mai apar event type invalid

health events nu mai sunt respinse


Severitate

Majoră


---

11) runtime/system_boot.py

Problemă

Dublează record_start() prin restart_loop_detected() / should_freeze().

Ce trebuie făcut

Refaci secvența de boot astfel încât record_start() să fie chemat o singură dată.

Model recomandat

start_info = record_start()

if start_info.get("crash_loop"):
    ...
    return

și elimini al doilea record_start() implicit.

Dacă should_freeze() trebuie păstrat

Schimbi funcția astfel încât:

să nu mai scrie din nou în state

doar să citească rezultatul deja calculat


După patch, verifici

un boot = un singur increment

crash loop detection se activează doar real, nu fals


Severitate

Majoră


---

FAZA 2 — UNIFICAREA STATE / CONFIG

12) core/storage.py

Problemă

Trebuie să devină punctul canonic de I/O pentru JSON-urile de config și state.

Ce trebuie făcut

Introdu un strat clar de helperi:

load_config_json(name)

save_config_json(name, data)

load_state_json(name)

save_state_json(name, data)


Beneficiu

Elimini hardcodările repetitive din:

signal_engine.py

bot_service.py

admin_commands.py

distribution_router.py


Convenție oficială

config/ = input controlat de admin/operator

state/ = runtime mutable state

observability/ = loguri/envelope

analytics/ = output-uri derivate


După patch, verifici

nu mai ai căi hardcodate în 10 locuri

toate modulele citesc aceleași fișiere prin storage layer


Severitate

Majoră


---

13) config/

Problemă

Ai inconsistențe de tip:

active_symbols.json

symbols.json

lipsă settings.json


Ce trebuie făcut

Standardizezi setul minim:

În config/ trebuie să existe doar:

active_symbols.json

settings.json

admin_settings.json

alte fișiere strict de config, dacă există


Elimini sau depreciezi

symbols.json dacă dublează active_symbols.json


După patch, verifici

repo-ul pornește fără fallback-uri mute

engine-ul chiar citește fișiere existente


Severitate

Critică la nivel operațional


---

14) state/

Problemă

State-ul trebuie separat complet de config.

Ce trebuie făcut

În state/ mută doar:

focus_state.json

dist_state.json

fsm state

runtime counters

restart state

cache-uri volatile persistate


Nu ține aici

settings

symbol allowlists

admin config


După patch, verifici

resetul de stare nu afectează config-ul operatorului

backup-ul de config e separat de backup-ul runtime


Severitate

Majoră


---

FAZA 3 — CURĂȚARE BOT SERVICE / SEPARARE RESPONSABILITĂȚI

15) core/bot_service.py

Problemă

Fișier prea mare, hibrid, greu de auditat.

Ce trebuie făcut după stabilizare

Îl spargi treptat, nu violent.

Țintă recomandată

Extragi în module separate:

core/admin_handlers.py

core/callback_handlers.py

core/docs_handlers.py

core/outcome_handlers.py

core/command_router.py


În bot_service.py rămâne doar

bootstrap bot

routing principal

wiring între module


Beneficiu

scade riscul de regresie

devine auditabil

poți testa separat


Severitate

Majoră pentru mentenanță


---

FAZA 4 — SCHEMA ȘI OBSERVABILITY OFICIALĂ

16) schema/event_schema.json

Problemă

Schema oficială nu corespunde cu envelope-ul real din logger.

Ce trebuie făcut

Rescrii schema după implementarea reală din core/observability_logger.py.

Trebuie să includă minim

event_id

schema_version

event_type

ts_utc

ts_epoch_ms

service

env

run_id

source

data


Și enum-ul real de event_type

doar cele canonice, stabilite în faza 1.

După patch, verifici

documentația și implementarea vorbesc aceeași limbă

orice validator viitor poate folosi schema oficială


Severitate

Majoră


---

17) observability/ fișiere JSONL

Problemă

Ai nevoie de reguli clare de routing.

Ce trebuie făcut

Documentezi și verifici:

engine_events.jsonl

decision_events.jsonl

error_events.jsonl

fsm_events.jsonl

outcome_events.jsonl

admin_events.jsonl


Recomandare

Routing-ul să fie făcut exclusiv după event_type, nu după presupuneri locale.

După patch, verifici

fiecare event type ajunge într-un singur fișier logic

nu mai ai evenimente importante îngropate în error_events



---

FAZA 5 — DOCUMENTAȚIE CANONICĂ

18) docs/ARCHITECTURE_CODE_MAPPING.md

Problemă

Mapează pe structură veche.

Ce trebuie făcut

Actualizezi toate referințele la:

core/...

config/...

state/...

observability/...

monitoring/...

intelligence/...


Adaugi câmpuri clare

Pentru fiecare document:

module implementatoare

status: implemented / partial / planned

note de deviație


Severitate

Majoră


---

19) docs/BINARYBOT_MASTER_INDEX.md

Problemă

Referă documente lipsă.

Ce trebuie făcut

Ai două opțiuni:

1. ori creezi documentele lipsă,


2. ori scoți referințele și marchezi clar ce este canonic acum.



Recomandare

Mai întâi cureți indexul, nu crea docs fantomă doar ca să umpli lista.

Severitate

Majoră


---

20) docs/SYSTEM_ARCHITECTURE_MAP.md

Problemă

Descrie o bibliotecă de spec-uri mai mare decât ce există.

Ce trebuie făcut

Pentru fiecare document referit:

dacă există → păstrezi

dacă nu există, îl marchezi:

planned

not yet written

superseded by X



Beneficiu

Nu mai pari că ai implementat ceva ce încă nu există.

Severitate

Medie spre majoră


---

21) docs/DECISION_AUDIT_SPEC_v2.0.0.md

Problemă

Spec-ul e mai avansat decât codul actual.

Ce trebuie făcut

Nu îl ștergi. Îl marchezi corect:

target architecture

partial implementation


Adaugi secțiune nouă

Current implementation status

cu mapare la:

intelligence/signal_diagnostics.py

intelligence/bottleneck_detector.py

intelligence/heatmap.py

core/analytics_engine.py


Severitate

Medie, dar importantă pentru guvernanță


---

22) docs/MODULE_INTERFACE_SPEC_v2.0.0.md

Problemă

Aici trebuie aliniat explicit contractul lumânărilor după patch-ul din strategie.

Ce trebuie făcut

Asiguri că scrie fără ambiguitate:

order = newest-first

candles[0] = current/latest closed candle

candles[1] = previous candle


Foarte important

Adaugi exemplu concret de listă.

Severitate

Critică documentar


---

FAZA 6 — IGIENĂ DE REPO

23) core/*.bak, *Copy*

Problemă

Fișiere moarte direct în repo activ.

Ce trebuie făcut

Le scoți din path-ul principal.

Variante

fie le muți într-un folder _archive/legacy/

fie le elimini din deploy package

fie le ignori prin procesul de release


Beneficiu

Reduci confuzia și riscul operațional.

Severitate

Medie


---

24) tools/ și scripts/

Problemă

Trebuie aliniate la noile convenții după schimbările de config/state/schema.

Ce trebuie făcut

Verifici orice script care:

citește symbols.json

citește settings din root

folosește schema veche de event

presupune ordine veche a lumânărilor


Severitate

Majoră, dar după stabilizare


---

ORDINEA EXACTĂ DE IMPLEMENTARE

Sprint 1 — fără discuție, astea primele

1. core/strategy_v2.py


2. core/candle_adapter.py


3. core/signal_engine.py


4. core/distribution_router.py


5. core/observability_logger.py


6. core/outcome_service.py


7. intelligence/risk_monitor.py


8. runtime/system_boot.py


9. monitoring/restart_guard.py


10. core/bot_service.py



Sprint 2 — unificare infrastructură

11. core/storage.py


12. config/


13. state/


14. core/admin_commands.py


15. tools/ și scripts/



Sprint 3 — documentație și guvernanță

16. schema/event_schema.json


17. docs/ARCHITECTURE_CODE_MAPPING.md


18. docs/BINARYBOT_MASTER_INDEX.md


19. docs/SYSTEM_ARCHITECTURE_MAP.md


20. docs/MODULE_INTERFACE_SPEC_v2.0.0.md


21. docs/DECISION_AUDIT_SPEC_v2.0.0.md



Sprint 4 — cleanup

22. .bak


23. Copy


24. legacy dead paths




---

DEFINIȚIA DE GATA PE FIECARE FAZĂ

Faza 1 e gata când

semnalele folosesc lumânarea corectă

admin și engine citesc aceleași fișiere

observability nu mai respinge event types

distribution_router nu mai crapă la build_event

bot_service nu mai importă module inexistente


Faza 2 e gata când

toate fișierele JSON sunt accesate prin convenție unică

nu mai există settings root-level active

symbols.json nu mai dublează active_symbols.json


Faza 3 e gata când

bot_service.py devine router, nu groapă de logică

callback-urile și admin-ul sunt separate


Faza 4 e gata când

schema oficială a evenimentelor = schema reală

docs și cod spun același lucru



---

RECOMANDAREA MEA OPERAȚIONALĂ

Nu încerca să repari tot deodată.

Fă exact așa:

întâi adevărul datelor de piață,

apoi adevărul config/state,

apoi adevărul observability,

apoi adevărul documentației.


Pentru botul tău, asta e ordinea corectă.

În pasul următor îți pot scrie patch plan ultra-concret, cu fragmente de cod exacte, fișier cu fișier, începând cu Sprint 1.


Mai jos ai Patch Plan ultra-concret pentru Sprint 1, cu fragmente exacte, fișier cu fișier, pe baza arhivelor tale reale.

Ordinea este cea corectă de aplicare:

1. core/strategy_v2.py


2. core/candle_adapter.py


3. core/signal_engine.py


4. core/distribution_router.py


5. core/observability_logger.py


6. core/outcome_service.py


7. intelligence/risk_monitor.py


8. runtime/system_boot.py


9. monitoring/restart_guard.py


10. core/bot_service.py




---

0) Backup înainte de patch

În directorul botului:

cd /opt/binarybot
cp core/strategy_v2.py core/strategy_v2.py.bak_sprint1
cp core/candle_adapter.py core/candle_adapter.py.bak_sprint1
cp core/signal_engine.py core/signal_engine.py.bak_sprint1
cp core/distribution_router.py core/distribution_router.py.bak_sprint1
cp core/observability_logger.py core/observability_logger.py.bak_sprint1
cp core/outcome_service.py core/outcome_service.py.bak_sprint1
cp intelligence/risk_monitor.py intelligence/risk_monitor.py.bak_sprint1
cp runtime/system_boot.py runtime/system_boot.py.bak_sprint1
cp monitoring/restart_guard.py monitoring/restart_guard.py.bak_sprint1
cp core/bot_service.py core/bot_service.py.bak_sprint1


---

1) core/strategy_v2.py

Problema

Strategia citește seria ca și cum ar fi oldest-first, dar candle_adapter.py livrează newest-first.

Patch exact

A. Înlocuiește aceste linii:

symbol = _normalize_symbol(str(candles_m1[-1].get("symbol", context.get("symbol", "UNKNOWN"))))

cu:

symbol = _normalize_symbol(str(candles_m1[0].get("symbol", context.get("symbol", "UNKNOWN"))))


---

B. Înlocuiește:

candle_ts = _get_ts(candles_m1[-1])

cu:

candle_ts = _get_ts(candles_m1[0])


---

C. Înlocuiește:

price = closes_m1[-1]
prev_price = closes_m1[-2] if len(closes_m1) >= 2 else price

cu:

price = closes_m1[0]
prev_price = closes_m1[1] if len(closes_m1) >= 2 else price


---

D. Înlocuiește blocul:

m1_n = min(10, len(candles_m1))
m1_ranges = [float(candles_m1[-i]["high"]) - float(candles_m1[-i]["low"]) for i in range(1, m1_n + 1)]

cu:

m1_n = min(10, len(candles_m1))
m1_ranges = [float(candles_m1[i]["high"]) - float(candles_m1[i]["low"]) for i in range(m1_n)]


---

E. Înlocuiește:

last_candle = candles_m1[-1]
prev_candle = candles_m1[-2] if len(candles_m1) >= 2 else candles_m1[-1]
m1_ranges_all = [float(c["high"]) - float(c["low"]) for c in candles_m1[-50:]] if len(candles_m1) >= 50 else m1_ranges

cu:

last_candle = candles_m1[0]
prev_candle = candles_m1[1] if len(candles_m1) >= 2 else candles_m1[0]
m1_ranges_all = [float(c["high"]) - float(c["low"]) for c in candles_m1[:50]] if len(candles_m1) >= 50 else m1_ranges


---

F. Patch important pentru indicatori

Cum ema, rsi, atr sunt scrise să folosească valori cu ultimul element ca cel mai nou, iar tu acum ai newest-first, trebuie să inversezi seriile înainte să le dai indicatorilor.

Înlocuiește blocul:

closes_m1 = [float(c["close"]) for c in candles_m1]
closes_m5 = [float(c["close"]) for c in candles_m5]
highs_m5 = [float(c["high"]) for c in candles_m5]
lows_m5 = [float(c["low"]) for c in candles_m5]

cu:

closes_m1 = [float(c["close"]) for c in candles_m1]
closes_m5 = [float(c["close"]) for c in candles_m5]
highs_m5 = [float(c["high"]) for c in candles_m5]
lows_m5 = [float(c["low"]) for c in candles_m5]

# indicator helpers below expect oldest-first series
closes_m1_ind = list(reversed(closes_m1))
closes_m5_ind = list(reversed(closes_m5))
highs_m5_ind = list(reversed(highs_m5))
lows_m5_ind = list(reversed(lows_m5))


---

G. Înlocuiește:

ema_fast = ema(closes_m5, ema_fast_n)
ema_slow = ema(closes_m5, ema_slow_n)
rsi_val = rsi(closes_m1, rsi_n)
atr_val = atr(highs_m5, lows_m5, closes_m5, 14)

cu:

ema_fast = ema(closes_m5_ind, ema_fast_n)
ema_slow = ema(closes_m5_ind, ema_slow_n)
rsi_val = rsi(closes_m1_ind, rsi_n)
atr_val = atr(highs_m5_ind, lows_m5_ind, closes_m5_ind, 14)


---

Verificare rapidă după patch

grep -n '\[-1\]\|\[-2\]' /opt/binarybot/core/strategy_v2.py

În zona decide() nu ar mai trebui să rămână accesări la candles_m1[-1], candles_m1[-2], closes_m1[-1], closes_m1[-2].


---

2) core/candle_adapter.py

Problema

Contractul e bun, dar trebuie întărit ca să crape clar dacă se rupe ordinea.

Patch exact

Adaugă helperul ăsta sub _pick(...):

def assert_newest_first(candles: List[Dict[str, Any]]) -> None:
    if len(candles) < 2:
        return
    if int(candles[0]["ts"]) < int(candles[1]["ts"]):
        raise ValueError("candles ordering invalid: expected newest-first")


---

Apoi, în normalize(...), după:

out.sort(key=lambda x: x["ts"], reverse=True)

adaugă:

assert_newest_first(out)


---

Apoi, în validate(...), la final, după bucla existentă, adaugă:

assert_newest_first(candles)

și elimină dublarea logicii vechi de ordering dacă vrei să rămână un singur adevăr.

Poți înlocui:

# Newest-first
    for i in range(1, len(candles)):
        if int(candles[i]["ts"]) > int(candles[i - 1]["ts"]):
            raise ValueError("candles ordering invalid: expected newest-first")

cu:

assert_newest_first(candles)


---

3) core/signal_engine.py

Problema

event_type greșit și settings/path-uri fragile.

Patch exact

A. Normalizează event type

În _make_signal_event(...), înlocuiește:

"event_type": "SIGNAL_EVENT",

cu:

"event_type": "signal_event",


---

B. Întărește _load_settings()

Înlocuiește:

def _load_settings() -> Dict[str, Any]:
    return storage.load_json(SETTINGS_PATH, default={"buffer_mode": "MEDIUM"})

cu:

def _load_settings() -> Dict[str, Any]:
    settings = storage.load_json(SETTINGS_PATH, default=None)
    if not isinstance(settings, dict):
        observability_logger.log_warning(
            warn_type="SETTINGS_FALLBACK_DEFAULT",
            message="settings.json missing or invalid, using defaults",
            context={"settings_path": SETTINGS_PATH},
            source={"module": "signal_engine", "function": "_load_settings"},
        )
        return {"buffer_mode": "MEDIUM"}
    return settings


---

C. Întărește excepția din run_once(...)

Înlocuiește:

except Exception as e:
            observability_logger.log_error({
                "event_type": "error",
                "module": "signal_engine",
                "symbol": symbol,
                "error": str(e),
            })
            continue

cu:

except Exception as e:
            observability_logger.log_error({
                "event_type": "error",
                "message": f"signal_engine failed for symbol {symbol}",
                "error_type": type(e).__name__,
                "context": {
                    "module": "signal_engine",
                    "symbol": symbol,
                },
                "trace": repr(e),
                "source": {"module": "signal_engine", "function": "run_once"},
            })
            continue


---

4) core/distribution_router.py

Problema

build_event() este apelat cu argumente invalide.

Patch exact

A. În maybe_daily_reset(...), înlocuiește blocul:

observability_logger.log_event(observability_logger.build_event(
        event_type="tier_reset",
        data={
            "reset_time_london": f"{RESET_HOUR:02d}:{RESET_MINUTE:02d} Europe/London",
            "effective_date_london": today_str,
            "before": before,
            "after": {
                "tier_state": dict(state["tier_state"]),
                "open_signals_today": dict(state["open_signals_today"]),
                "last_reset_london_date": state["last_reset_london_date"],
            },
        },
        module="distribution_router",
        now_ts=now_ts
    ))

cu:

observability_logger.log_event(
        observability_logger.build_event(
            event_type="tier_reset",
            data={
                "reset_time_london": f"{RESET_HOUR:02d}:{RESET_MINUTE:02d} Europe/London",
                "effective_date_london": today_str,
                "before": before,
                "after": {
                    "tier_state": dict(state["tier_state"]),
                    "open_signals_today": dict(state["open_signals_today"]),
                    "last_reset_london_date": state["last_reset_london_date"],
                },
                "now_ts": int(now_ts),
            },
            source={"module": "distribution_router", "function": "maybe_daily_reset"},
        )
    )


---

B. În _log_tier_publish(...), caută apelul similar la build_event(...) și fă aceeași corecție.

Structura corectă trebuie să fie de forma:

observability_logger.log_event(
        observability_logger.build_event(
            event_type="tier_publish",
            data={
                "publish_decision": publish_decision,
                "tier_state_before": tier_state_before,
                "tier_state_after": tier_state_after,
                "limit": limit,
                "counter_before": counter_before,
                "counter_after": counter_after,
                "counted": counted,
                "telegram_ok": telegram_ok,
                "message_id": message_id,
                "error": error,
                "dedup_key": dedup_key,
                "was_duplicate": was_duplicate,
                "dedup_action": dedup_action,
                "chat_id": chat_id,
                "tier": tier,
                "signal_id": event.get("signal_id"),
                "stage": event.get("stage"),
                "symbol": event.get("symbol"),
                "now_ts": int(now_ts),
            },
            source={"module": "distribution_router", "function": "_log_tier_publish"},
            correlation={
                "tier": tier,
                "signal_id": event.get("signal_id"),
                "symbol": event.get("symbol"),
                "timeframe": event.get("timeframe"),
            },
        )
    )


---

5) core/observability_logger.py

Problema

Ai schema bună, dar încă intră evenimente vechi și greșite.

Patch exact

A. Extinde _normalize_event(...) ca să map-eze tipurile vechi la cele canonice

Adaugă sub:

event_type = event.get("event_type")
    if not event_type:
        raise ValueError("event missing event_type")

acest bloc:

event_type = str(event_type).strip()

    event_type_aliases = {
        "SIGNAL_EVENT": "signal_event",
        "OUTCOME_SET": "user_outcome",
        "outcome_register_open_now": "user_outcome",
        "risk_warning": "error",
        "system_health": "decision",
        "strategy_optimizer": "decision",
    }
    event_type = event_type_aliases.get(event_type, event_type)

Și păstrează mai jos:

normalized = build_event(
        event_type=str(event_type),
        data=data,
        source=source,
    )


---

B. Îmbunătățește logarea erorilor de validare

În log_event(...), înlocuiește:

context={"original_event_type": event.get("event_type") if isinstance(event, dict) else None},

cu:

context={
                    "original_event_type": event.get("event_type") if isinstance(event, dict) else None,
                    "source_module": event.get("module") if isinstance(event, dict) else None,
                },


---

C. Nu schimba whitelist-ul încă

Păstrează _ALLOWED_EVENT_TYPES exact cum e acum. Sprint 1 trebuie să normalizeze emiterea, nu să umfle schema.


---

6) core/outcome_service.py

Problema

log_warning() este apelat greșit.

Patch exact

Caută blocul:

observability_logger.log_warning({
            "event_type": "warning",
            "module": "outcome_service",
            "warning": "OUTCOME_REJECTED_NOT_ELITE",
            "user_id": int(user_id),
            "signal_id": signal_id,
            "data": {"reason": member_reason}
        })

și înlocuiește-l cu:

observability_logger.log_warning(
            warn_type="OUTCOME_REJECTED_NOT_ELITE",
            message="Outcome rejected because user is not ELITE member",
            context={
                "user_id": int(user_id),
                "signal_id": signal_id,
                "reason": member_reason,
            },
            source={"module": "outcome_service", "function": "register_vote"},
        )


---

Dacă mai ai și alte log_warning({...}) în fișier, fă aceeași transformare.

Verificare rapidă:

grep -n 'log_warning({' /opt/binarybot/core/outcome_service.py

Rezultatul ideal: nimic.


---

7) intelligence/risk_monitor.py

Problema

Tot log_warning() greșit.

Patch exact

Înlocuiește:

observability_logger.log_warning({
            "event_type": "risk_warning",
            "reason": "low_win_rate",
            "win_rate": win_rate
        })

cu:

observability_logger.log_warning(
            warn_type="LOW_WIN_RATE",
            message="Risk monitor detected low win rate",
            context={
                "reason": "low_win_rate",
                "win_rate": win_rate,
                "threshold": WIN_RATE_MIN,
            },
            source={"module": "risk_monitor", "function": "evaluate_risk"},
        )


---

8) runtime/system_boot.py

Problema

Dublează record_start().

Patch exact

A. Înlocuiește importul:

from monitoring.restart_guard import record_start, should_freeze as restart_loop_detected

cu:

from monitoring.restart_guard import record_start


---

B. În start_system(), înlocuiește blocul:

# record restart early
    record_start()

    # crash-loop protection (boot-level)
    if restart_loop_detected():
        log_event({
            "event_type": "error",
            "severity": "CRITICAL",
            "message": "CRASH_LOOP_DETECTED — system boot blocked",
        })
        return

cu:

# record restart once and evaluate crash-loop from same result
    start_info = record_start()

    if start_info.get("crash_loop"):
        log_event({
            "event_type": "error",
            "message": "CRASH_LOOP_DETECTED — system boot blocked",
            "data": {
                "severity": "CRITICAL",
                "restart_count": start_info.get("restart_count"),
                "window_seconds": start_info.get("window_seconds"),
                "max_restarts": start_info.get("max_restarts"),
            },
            "source": {"module": "system_boot", "function": "start_system"},
        })
        return


---

9) monitoring/restart_guard.py

Problema

Emite system_health, care nu este permis de logger.

Patch exact

În record_start(...), înlocuiește blocul:

else:
        log_event({
            "event_type": "system_health",
            "message": "Restart guard start recorded",
            "data": {
                "restart_count": restart_count,
                "window_seconds": WINDOW_SECONDS,
                "max_restarts": MAX_RESTARTS,
            }
        })

cu:

else:
        log_event({
            "event_type": "decision",
            "data": {
                "decision_kind": "SYSTEM_HEALTH",
                "message": "Restart guard start recorded",
                "restart_count": restart_count,
                "window_seconds": WINDOW_SECONDS,
                "max_restarts": MAX_RESTARTS,
            },
            "source": {"module": "restart_guard", "function": "record_start"},
        })


---

Important

Nu folosi should_freeze() în boot după patch-ul din system_boot.py.
Îl poți lăsa temporar pentru compatibilitate, dar să nu mai fie folosit acolo.


---

10) core/bot_service.py

Probleme

Path-uri vechi, outcome_tracker inexistent, eveniment OUTCOME_SET necanonic.

Patch exact

A. Înlocuiește constantele de path:

SETTINGS_PATH = os.path.join(BASE_DIR, "settings.json")              # existing in root
ACTIVE_SYMBOLS_PATH = os.path.join(BASE_DIR, "symbols.json")         # existing in root (your current)
FOCUS_STATE_PATH = os.path.join(BASE_DIR, "focus_state.json")        # existing in root
DIST_STATE_PATH = os.path.join(STATE_DIR, "dist_state.json")         # new state location
OUTCOMES_PATH = os.path.join(STATE_DIR, "outcomes.json")         # admin outcomes store

cu:

SETTINGS_PATH = os.path.join(CONFIG_DIR, "settings.json")
ACTIVE_SYMBOLS_PATH = os.path.join(CONFIG_DIR, "active_symbols.json")
FOCUS_STATE_PATH = os.path.join(STATE_DIR, "focus_state.json")
DIST_STATE_PATH = os.path.join(STATE_DIR, "dist_state.json")
OUTCOMES_PATH = os.path.join(STATE_DIR, "outcomes.json")


---

B. Normalizează _load_active_symbols()

Înlocuiește funcția întreagă cu:

def _load_active_symbols() -> List[str]:
    data = storage.load_json(ACTIVE_SYMBOLS_PATH, default={})

    out: List[str] = []
    if isinstance(data, dict):
        if isinstance(data.get("symbols"), list):
            out = [str(x).strip() for x in data["symbols"] if str(x).strip()]
        else:
            for k in ("forex", "crypto"):
                if isinstance(data.get(k), list):
                    out.extend([str(x).strip() for x in data[k] if str(x).strip()])
    elif isinstance(data, list):
        out = [str(x).strip() for x in data if str(x).strip()]

    seen = set()
    cleaned: List[str] = []
    for s in out:
        if s not in seen:
            seen.add(s)
            cleaned.append(s)
    return cleaned


---

C. Normalizează _save_active_symbols()

Înlocuiește funcția cu:

def _save_active_symbols(symbols: List[str]) -> None:
    storage.save_json_atomic(ACTIVE_SYMBOLS_PATH, {"symbols": symbols})

Asta îți dă un format unic imediat.


---

D. Repară evenimentul OUTCOME_SET

În _record_outcome(...), înlocuiește:

observability_logger.log_event({
        "event_type": "OUTCOME_SET",
        "data": {
            "signal_id": signal_id,
            "outcome": outcome,
            "previous_outcome": previous_outcome,
            "user_id": user_id,
            "symbol": symbol,
            "tier": "admin"
        }
    })

cu:

observability_logger.log_event({
        "event_type": "user_outcome",
        "signal_id": signal_id,
        "tier": "admin",
        "symbol": symbol,
        "data": {
            "signal_id": signal_id,
            "outcome": outcome,
            "previous_outcome": previous_outcome,
            "user_id": user_id,
            "symbol": symbol,
            "accepted": True,
            "source_flow": "admin_manual_outcome",
        },
        "source": {"module": "bot_service", "function": "_record_outcome"},
    })


---

E. Elimină ramura cu outcome_tracker

În handle_callback(...), șterge complet blocul:

# ---- Outcome voting (public buttons) ----
    if data.startswith("VOTE_"):
        from core import outcome_tracker
        signal_id, outcome = data.split("|")[1:]
        result = outcome_tracker.register_vote(signal_id, outcome, user_id, chat_id)
        return {"text": result, "reply_markup": None}

Lasă doar ramura deja existentă și validă:

if data.startswith("VOTE_|"):


---

F. Întărește _load_settings()

Înlocuiește:

def _load_settings() -> Dict[str, Any]:
    # settings.json exists in /opt/binarybot (your current)
    return storage.load_json(SETTINGS_PATH, default={"buffer_mode": "MEDIUM"})

cu:

def _load_settings() -> Dict[str, Any]:
    settings = storage.load_json(SETTINGS_PATH, default=None)
    if not isinstance(settings, dict):
        observability_logger.log_warning(
            warn_type="SETTINGS_FALLBACK_DEFAULT",
            message="bot_service settings.json missing or invalid, using defaults",
            context={"settings_path": SETTINGS_PATH},
            source={"module": "bot_service", "function": "_load_settings"},
        )
        return {"buffer_mode": "MEDIUM"}
    return settings


---

Test minim după Sprint 1

Rulează astea:

cd /opt/binarybot
python3 -m compileall core intelligence monitoring runtime

Apoi:

grep -R "SIGNAL_EVENT" core intelligence monitoring runtime
grep -R "OUTCOME_SET" core intelligence monitoring runtime
grep -R "system_health" core intelligence monitoring runtime
grep -R "log_warning({" core intelligence monitoring runtime
grep -R "outcome_tracker" core intelligence monitoring runtime

Rezultatul ideal:

nimic pentru SIGNAL_EVENT

nimic pentru OUTCOME_SET

nimic pentru system_health

nimic pentru log_warning({

nimic pentru outcome_tracker



---

Smoke test după restart

După deploy:

tail -n 50 /opt/binarybot/observability/


Mai jos ai Sprint 2 la același nivel de granularitate, cu patch-uri exacte, orientat pe:

unificare totală config/ și state/

introducerea unui strat canonic în core/storage.py

eliminarea hardcodărilor repetitive

alinierea modulelor admin/runtime la aceeași convenție

pregătirea pentru curățarea mare din Sprint 3


Obiectivul Sprint 2 este simplu:

orice modul care citește/scrie JSON trebuie să o facă prin același strat și pe aceleași directoare.


---

SPRINT 2 — ȚINTĂ FINALĂ

La finalul Sprint 2 trebuie să fie adevărat:

tot config-ul operatorului este în config/

tot runtime state-ul mutabil este în state/

modulele nu mai folosesc direct 10 path-uri hardcodate diferit

symbols.json nu mai este sursa activă

settings.json există clar în config/

active_symbols.json devine singura sursă de adevăr pentru simbolurile active



---

0) Backup înainte de Sprint 2

cd /opt/binarybot
cp core/storage.py core/storage.py.bak_sprint2
cp core/admin_commands.py core/admin_commands.py.bak_sprint2
cp core/bot_service.py core/bot_service.py.bak_sprint2
cp core/signal_engine.py core/signal_engine.py.bak_sprint2
cp core/distribution_router.py core/distribution_router.py.bak_sprint2
cp core/outcome_service.py core/outcome_service.py.bak_sprint2
cp core/params_loader.py core/params_loader.py.bak_sprint2


---

1) core/storage.py

Problema

Momentan este doar un helper generic. Trebuie să devină stratul canonic de filesystem JSON pentru tot proiectul.

Patch exact

A. Adaugă constante canonice sus în fișier

Sub importuri, adaugă:

import os
import json
import tempfile
from typing import Any, Dict, Optional

BASE_DIR = "/opt/binarybot"
CONFIG_DIR = os.path.join(BASE_DIR, "config")
STATE_DIR = os.path.join(BASE_DIR, "state")
OBSERVABILITY_DIR = os.path.join(BASE_DIR, "observability")
ANALYTICS_DIR = os.path.join(BASE_DIR, "analytics")


---

B. Adaugă helper de directory ensure

Sub constante, adaugă:

def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


---

C. Adaugă resolveri canonici de path

Adaugă:

def config_path(name: str) -> str:
    ensure_dir(CONFIG_DIR)
    return os.path.join(CONFIG_DIR, name)

def state_path(name: str) -> str:
    ensure_dir(STATE_DIR)
    return os.path.join(STATE_DIR, name)

def observability_path(name: str) -> str:
    ensure_dir(OBSERVABILITY_DIR)
    return os.path.join(OBSERVABILITY_DIR, name)

def analytics_path(name: str) -> str:
    ensure_dir(ANALYTICS_DIR)
    return os.path.join(ANALYTICS_DIR, name)


---

D. Dacă nu există deja, păstrează sau normalizează load_json(...)

Funcția trebuie să fie exact de forma:

def load_json(path: str, default: Any = None) -> Any:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return default
    except Exception:
        return default


---

E. Dacă nu există deja, normalizează save_json_atomic(...)

Folosește exact varianta asta:

def save_json_atomic(path: str, data: Any) -> None:
    parent = os.path.dirname(path) or "."
    ensure_dir(parent)

    fd, tmp_path = tempfile.mkstemp(prefix=".tmp_", dir=parent, text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as tmp:
            json.dump(data, tmp, ensure_ascii=False, indent=2, sort_keys=True)
            tmp.flush()
            os.fsync(tmp.fileno())
        os.replace(tmp_path, path)
    finally:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass


---

F. Adaugă helperi canonici de nivel înalt

Adaugă exact:

def load_config_json(name: str, default: Any = None) -> Any:
    return load_json(config_path(name), default=default)

def save_config_json(name: str, data: Any) -> None:
    save_json_atomic(config_path(name), data)

def load_state_json(name: str, default: Any = None) -> Any:
    return load_json(state_path(name), default=default)

def save_state_json(name: str, data: Any) -> None:
    save_json_atomic(state_path(name), data)


---

G. Adaugă helper de migrare controlată

Adaugă:

def migrate_json_file(old_path: str, new_path: str, *, default: Any = None) -> Any:
    data = load_json(new_path, default=None)
    if data is not None:
        return data

    old_data = load_json(old_path, default=None)
    if old_data is not None:
        save_json_atomic(new_path, old_data)
        return old_data

    if default is not None:
        save_json_atomic(new_path, default)
        return default

    return None

Asta va fi util pentru trecerea de la root-level la config/ și state/.


---

2) core/signal_engine.py

Problema

Încă folosește path-uri hardcodate. Sprint 2 îl trece pe helperii canonici.

Patch exact

A. Înlocuiește constantele:

ACTIVE_SYMBOLS_PATH = "/opt/binarybot/config/active_symbols.json"
SETTINGS_PATH = "/opt/binarybot/config/settings.json"

cu:

ACTIVE_SYMBOLS_FILE = "active_symbols.json"
SETTINGS_FILE = "settings.json"


---

B. Înlocuiește _load_settings()

În loc de:

def _load_settings() -> Dict[str, Any]:
    settings = storage.load_json(SETTINGS_PATH, default=None)
    if not isinstance(settings, dict):
        observability_logger.log_warning(
            warn_type="SETTINGS_FALLBACK_DEFAULT",
            message="settings.json missing or invalid, using defaults",
            context={"settings_path": SETTINGS_PATH},
            source={"module": "signal_engine", "function": "_load_settings"},
        )
        return {"buffer_mode": "MEDIUM"}
    return settings

pune:

def _load_settings() -> Dict[str, Any]:
    settings = storage.load_config_json(SETTINGS_FILE, default=None)
    if not isinstance(settings, dict):
        observability_logger.log_warning(
            warn_type="SETTINGS_FALLBACK_DEFAULT",
            message="settings.json missing or invalid, using defaults",
            context={"settings_file": SETTINGS_FILE},
            source={"module": "signal_engine", "function": "_load_settings"},
        )
        return {"buffer_mode": "MEDIUM"}
    return settings


---

C. Dacă există _load_active_symbols(), înlocuiește-o cu:

def _load_active_symbols() -> list[str]:
    data = storage.load_config_json(ACTIVE_SYMBOLS_FILE, default={})

    out: list[str] = []
    if isinstance(data, dict):
        if isinstance(data.get("symbols"), list):
            out = [str(x).strip() for x in data["symbols"] if str(x).strip()]
        else:
            for k in ("forex", "crypto"):
                if isinstance(data.get(k), list):
                    out.extend([str(x).strip() for x in data[k] if str(x).strip()])
    elif isinstance(data, list):
        out = [str(x).strip() for x in data if str(x).strip()]

    seen = set()
    cleaned: list[str] = []
    for s in out:
        if s not in seen:
            seen.add(s)
            cleaned.append(s)
    return cleaned


---

3) core/bot_service.py

Problema

Trebuie să citească/scrie exclusiv prin storage.

Patch exact

A. Înlocuiește blocul de constante de path

În loc de:

BASE_DIR = "/opt/binarybot"
CONFIG_DIR = os.path.join(BASE_DIR, "config")
STATE_DIR = os.path.join(BASE_DIR, "state")

SETTINGS_PATH = os.path.join(CONFIG_DIR, "settings.json")
ACTIVE_SYMBOLS_PATH = os.path.join(CONFIG_DIR, "active_symbols.json")
FOCUS_STATE_PATH = os.path.join(STATE_DIR, "focus_state.json")
DIST_STATE_PATH = os.path.join(STATE_DIR, "dist_state.json")
OUTCOMES_PATH = os.path.join(STATE_DIR, "outcomes.json")

pune:

SETTINGS_FILE = "settings.json"
ACTIVE_SYMBOLS_FILE = "active_symbols.json"
FOCUS_STATE_FILE = "focus_state.json"
DIST_STATE_FILE = "dist_state.json"
OUTCOMES_FILE = "outcomes.json"


---

B. Înlocuiește _load_settings()

Cu:

def _load_settings() -> Dict[str, Any]:
    settings = storage.load_config_json(SETTINGS_FILE, default=None)
    if not isinstance(settings, dict):
        observability_logger.log_warning(
            warn_type="SETTINGS_FALLBACK_DEFAULT",
            message="bot_service settings.json missing or invalid, using defaults",
            context={"settings_file": SETTINGS_FILE},
            source={"module": "bot_service", "function": "_load_settings"},
        )
        return {"buffer_mode": "MEDIUM"}
    return settings


---

C. Înlocuiește _save_settings(...)

Dacă ai ceva de forma:

def _save_settings(data: Dict[str, Any]) -> None:
    storage.save_json_atomic(SETTINGS_PATH, data)

înlocuiește cu:

def _save_settings(data: Dict[str, Any]) -> None:
    storage.save_config_json(SETTINGS_FILE, data)


---

D. Înlocuiește _load_active_symbols()

Folosește exact aceeași funcție ca în Sprint 1, dar prin storage.load_config_json(...):

def _load_active_symbols() -> List[str]:
    data = storage.load_config_json(ACTIVE_SYMBOLS_FILE, default={})

    out: List[str] = []
    if isinstance(data, dict):
        if isinstance(data.get("symbols"), list):
            out = [str(x).strip() for x in data["symbols"] if str(x).strip()]
        else:
            for k in ("forex", "crypto"):
                if isinstance(data.get(k), list):
                    out.extend([str(x).strip() for x in data[k] if str(x).strip()])
    elif isinstance(data, list):
        out = [str(x).strip() for x in data if str(x).strip()]

    seen = set()
    cleaned: List[str] = []
    for s in out:
        if s not in seen:
            seen.add(s)
            cleaned.append(s)
    return cleaned


---

E. Înlocuiește _save_active_symbols(...)

Cu:

def _save_active_symbols(symbols: List[str]) -> None:
    storage.save_config_json(ACTIVE_SYMBOLS_FILE, {"symbols": symbols})


---

F. Înlocuiește orice încărcare de focus state

Caută ceva de forma:

focus_state = storage.load_json(FOCUS_STATE_PATH, default={})

și înlocuiește cu:

focus_state = storage.load_state_json(FOCUS_STATE_FILE, default={})


---

G. Înlocuiește orice salvare de focus state

Din:

storage.save_json_atomic(FOCUS_STATE_PATH, focus_state)

în:

storage.save_state_json(FOCUS_STATE_FILE, focus_state)


---

H. Înlocuiește orice încărcare de dist state

Din:

dist_state = storage.load_json(DIST_STATE_PATH, default={})

în:

dist_state = storage.load_state_json(DIST_STATE_FILE, default={})


---

I. Înlocuiește orice salvare de dist state

Din:

storage.save_json_atomic(DIST_STATE_PATH, dist_state)

în:

storage.save_state_json(DIST_STATE_FILE, dist_state)


---

J. Înlocuiește outcomes store

Din:

outcomes = storage.load_json(OUTCOMES_PATH, default={})
storage.save_json_atomic(OUTCOMES_PATH, outcomes)

în:

outcomes = storage.load_state_json(OUTCOMES_FILE, default={})
storage.save_state_json(OUTCOMES_FILE, outcomes)


---

4) core/admin_commands.py

Problema

Trebuie aliniat pe aceeași convenție cu bot_service.py și signal_engine.py.

Patch exact

A. Înlocuiește orice bloc de constante hardcodate

Dacă ai ceva de forma:

BASE_DIR = "/opt/binarybot"
CONFIG_DIR = os.path.join(BASE_DIR, "config")
ADMIN_SETTINGS_PATH = os.path.join(CONFIG_DIR, "admin_settings.json")
ACTIVE_SYMBOLS_PATH = os.path.join(CONFIG_DIR, "active_symbols.json")
SETTINGS_PATH = os.path.join(CONFIG_DIR, "settings.json")

înlocuiește cu:

ADMIN_SETTINGS_FILE = "admin_settings.json"
ACTIVE_SYMBOLS_FILE = "active_symbols.json"
SETTINGS_FILE = "settings.json"


---

B. Înlocuiește încărcarea de admin settings

Din:

admin_settings = storage.load_json(ADMIN_SETTINGS_PATH, default={})

în:

admin_settings = storage.load_config_json(ADMIN_SETTINGS_FILE, default={})


---

C. Înlocuiește salvarea de admin settings

Din:

storage.save_json_atomic(ADMIN_SETTINGS_PATH, admin_settings)

în:

storage.save_config_json(ADMIN_SETTINGS_FILE, admin_settings)


---

D. Înlocuiește load/save pentru active symbols

Load:

symbols_data = storage.load_config_json(ACTIVE_SYMBOLS_FILE, default={})

Save:

storage.save_config_json(ACTIVE_SYMBOLS_FILE, {"symbols": symbols})


---

E. Înlocuiește load/save pentru settings

Load:

settings = storage.load_config_json(SETTINGS_FILE, default={"buffer_mode": "MEDIUM"})

Save:

storage.save_config_json(SETTINGS_FILE, settings)


---

5) core/distribution_router.py

Problema

Trebuie să folosească state/ prin storage, nu path-uri dispersate.

Patch exact

A. Înlocuiește constante de tip:

DIST_STATE_PATH = "/opt/binarybot/state/dist_state.json"

cu:

DIST_STATE_FILE = "dist_state.json"


---

B. Înlocuiește _load_state() dacă există

Din ceva de forma:

def _load_state():
    return storage.load_json(DIST_STATE_PATH, default=_default_state())

în:

def _load_state():
    state = storage.load_state_json(DIST_STATE_FILE, default=None)
    if not isinstance(state, dict):
        state = _default_state()
        storage.save_state_json(DIST_STATE_FILE, state)
    return state


---

C. Înlocuiește _save_state(...)

Din:

storage.save_json_atomic(DIST_STATE_PATH, state)

în:

storage.save_state_json(DIST_STATE_FILE, state)


---

6) core/outcome_service.py

Problema

Outcomes trebuie să stea canonic în state/.

Patch exact

A. Înlocuiește orice constantă de path outcomes

Din:

OUTCOMES_PATH = "/opt/binarybot/state/outcomes.json"

sau altă variantă hardcodata, în:

OUTCOMES_FILE = "outcomes.json"


---

B. Înlocuiește încărcarea

Din:

outcomes = storage.load_json(OUTCOMES_PATH, default={})

în:

outcomes = storage.load_state_json(OUTCOMES_FILE, default={})


---

C. Înlocuiește salvarea

Din:

storage.save_json_atomic(OUTCOMES_PATH, outcomes)

în:

storage.save_state_json(OUTCOMES_FILE, outcomes)


---

7) core/params_loader.py

Problema

Fișierul de parametri trebuie tratat ca config, nu ca state.

Patch exact

A. Înlocuiește orice path hardcodat către params

Dacă ai ceva de forma:

PARAMS_PATH = "/opt/binarybot/config/params.json"

poți păstra ideea, dar treci pe:

PARAMS_FILE = "params.json"


---

B. Înlocuiește încărcarea

Din:

params = storage.load_json(PARAMS_PATH, default={})

în:

params = storage.load_config_json(PARAMS_FILE, default={})


---

C. Dacă există salvare, folosește:

storage.save_config_json(PARAMS_FILE, params)


---

8) Migrare controlată a fișierelor reale

Aici nu mai modifici doar codul; faci și migrarea fișierelor existente.


---

A. Verifică structura actuală

cd /opt/binarybot
find config -maxdepth 2 -type f | sort
find state -maxdepth 2 -type f | sort
find . -maxdepth 1 -type f | sort


---

B. Creează config/settings.json dacă lipsește

Dacă nu există, rulează:

python3 - <<'PY'
import os, json
path = "/opt/binarybot/config/settings.json"
os.makedirs(os.path.dirname(path), exist_ok=True)
if not os.path.exists(path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"buffer_mode": "MEDIUM"}, f, ensure_ascii=False, indent=2)
print(path)
PY


---

C. Normalizează active_symbols.json

Dacă ai încă symbols.json sau formate mixte, rulează:

python3 - <<'PY'
import json, os

config_path = "/opt/binarybot/config/active_symbols.json"
legacy_paths = [
    "/opt/binarybot/config/symbols.json",
    "/opt/binarybot/symbols.json",
    "/opt/binarybot/state/active_symbols.json",
]

data = None
if os.path.exists(config_path):
    with open(config_path, "r", encoding="utf-8") as f:
        data = json.load(f)

if data is None:
    for p in legacy_paths:
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
            break

symbols = []
if isinstance(data, dict):
    if isinstance(data.get("symbols"), list):
        symbols = [str(x).strip() for x in data["symbols"] if str(x).strip()]
    else:
        for k in ("forex", "crypto"):
            if isinstance(data.get(k), list):
                symbols.extend([str(x).strip() for x in data[k] if str(x).strip()])
elif isinstance(data, list):
    symbols = [str(x).strip() for x in data if str(x).strip()]

seen = set()
cleaned = []
for s in symbols:
    if s not in seen:
        seen.add(s)
        cleaned.append(s)

os.makedirs("/opt/binarybot/config", exist_ok=True)
with open(config_path, "w", encoding="utf-8") as f:
    json.dump({"symbols": cleaned}, f, ensure_ascii=False, indent=2, sort_keys=True)

print("normalized:", config_path, "count=", len(cleaned))
PY


---

D. Mută root-level focus state în state/ dacă există

Rulează:

python3 - <<'PY'
import os, json, shutil
old_path = "/opt/binarybot/focus_state.json"
new_path = "/opt/binarybot/state/focus_state.json"
os.makedirs("/opt/binarybot/state", exist_ok=True)

if os.path.exists(new_path):
    print("already exists:", new_path)
elif os.path.exists(old_path):
    shutil.copy2(old_path, new_path)
    print("copied:", old_path, "->", new_path)
else:
    with open(new_path, "w", encoding="utf-8") as f:
        json.dump({}, f, ensure_ascii=False, indent=2)
    print("created empty:", new_path)
PY


---

E. Mută outcomes în state/ dacă există altundeva

Dacă ai fișiere vechi, normalizează similar:

python3 - <<'PY'
import os, json, shutil

candidates = [
    "/opt/binarybot/state/outcomes.json",
    "/opt/binarybot/outcomes.json",
]

target = "/opt/binarybot/state/outcomes.json"
os.makedirs("/opt/binarybot/state", exist_ok=True)

for p in candidates:
    if os.path.exists(p):
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
        with open(target, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, sort_keys=True)
        print("normalized from:", p)
        break
else:
    with open(target, "w", encoding="utf-8") as f:
        json.dump({}, f, ensure_ascii=False, indent=2, sort_keys=True)
    print("created empty:", target)
PY


---

9) Verificări de cod după Sprint 2

A. Compile check

cd /opt/binarybot
python3 -m compileall core intelligence monitoring runtime


---

B. Caută hardcodări vechi de path

grep -R '"/opt/binarybot/settings.json"' core intelligence monitoring runtime
grep -R '"/opt/binarybot/symbols.json"' core intelligence monitoring runtime
grep -R '"/opt/binarybot/focus_state.json"' core intelligence monitoring runtime
grep -R '"/opt/binarybot/config/active_symbols.json"' core intelligence monitoring runtime
grep -R '"/opt/binarybot/config/settings.json"' core intelligence monitoring runtime
grep -R '"/opt/binarybot/state/dist_state.json"' core intelligence monitoring runtime

Ținta bună după Sprint 2:

cât mai puține rezultate

ideal, în modulele patch-uite: zero



---

C. Caută folosirea helperilor canonici

grep -R "load_config_json\|save_config_json\|load_state_json\|save_state_json" core intelligence monitoring runtime

Aici vrei să vezi modulele principale.


---

10) Smoke test operațional după restart

După ce repornești botul, verifici:

cat /opt/binarybot/config/settings.json
cat /opt/binarybot/config/active_symbols.json
cat /opt/binarybot/state/focus_state.json
cat /opt/binarybot/state/dist_state.json
cat /opt/binarybot/state/outcomes.json

Trebuie să existe toate.


---

Test logic important

Schimbă simbolurile din admin și verifică imediat dacă engine-ul le vede.

Pas 1

Folosești comanda ta admin pentru simboluri.

Pas 2

Verifici:

cat /opt/binarybot/config/active_symbols.json

Pas 3

Verifici logs/runtime că engine-ul citește aceleași simboluri.

Dacă ai log pe startup/run_once, trebuie să vezi exact aceeași listă.


---

11) Definiția de gata pentru Sprint 2

Sprint 2 este gata când:

core/storage.py este stratul canonic de acces JSON

signal_engine.py, bot_service.py, admin_commands.py, distribution_router.py, outcome_service.py, params_loader.py folosesc helperii canonici

config/settings.json există clar și este folosit

config/active_symbols.json este singura sursă reală pentru simboluri active

state/focus_state.json, state/dist_state.json, state/outcomes.json sunt singurele surse reale pentru stările respective

hardcodările vechi root-level sunt eliminate din fluxurile active



---

12) Ce NU facem încă în Sprint 2

Nu facem încă:

split mare în bot_service.py

rescriere schema event_schema.json

cleanup .bak

cleanup documentație

redesign analytics


Astea intră în Sprint 3 și Sprint 4.


---

Ordinea exactă de aplicare Sprint 2

1. core/storage.py


2. core/signal


Mai jos ai Sprint 3 la același nivel de granularitate, cu patch-uri exacte pentru:

curățarea și spargerea core/bot_service.py

schema oficială de observability

alinierea schema/event_schema.json

curățarea logicii de callback/admin/outcome


Scopul Sprint 3 este:

să scoți logica amestecată din bot_service.py, să ai routing clar, evenimente canonice și un flux curat pentru admin / callback / outcome.


---

SPRINT 3 — ȚINTĂ FINALĂ

La finalul Sprint 3 trebuie să fie adevărat:

core/bot_service.py devine orchestrator, nu groapă de logică

callback-urile sunt separate de comenzile text

admin flow este separat de outcome flow

nu mai există ramuri moarte sau duplicate pentru voting

schema reală de observability este documentată și validabilă

schema/event_schema.json reflectă implementarea actuală



---

0) Backup înainte de Sprint 3

cd /opt/binarybot
cp core/bot_service.py core/bot_service.py.bak_sprint3
cp core/observability_logger.py core/observability_logger.py.bak_sprint3
cp core/outcome_service.py core/outcome_service.py.bak_sprint3
cp schema/event_schema.json schema/event_schema.json.bak_sprint3


---

1) Creezi noile module pentru separarea lui bot_service.py

Vom extrage 4 module noi:

core/command_router.py

core/callback_handlers.py

core/outcome_handlers.py

core/admin_state_helpers.py


Astea sunt module de stabilizare. Nu redesign complet, ci separare sigură.


---

2) core/admin_state_helpers.py

Rol

Mută aici helperii de config/state pe care îi folosește UI-ul Telegram, ca să nu mai stea îngropați în bot_service.py.

Fișier nou

Creează core/admin_state_helpers.py cu acest conținut:

from __future__ import annotations

from typing import Any, Dict, List
from core import storage

SETTINGS_FILE = "settings.json"
ACTIVE_SYMBOLS_FILE = "active_symbols.json"
FOCUS_STATE_FILE = "focus_state.json"
DIST_STATE_FILE = "dist_state.json"
OUTCOMES_FILE = "outcomes.json"


def load_settings() -> Dict[str, Any]:
    data = storage.load_config_json(SETTINGS_FILE, default=None)
    return data if isinstance(data, dict) else {"buffer_mode": "MEDIUM"}


def save_settings(data: Dict[str, Any]) -> None:
    storage.save_config_json(SETTINGS_FILE, data)


def load_active_symbols() -> List[str]:
    data = storage.load_config_json(ACTIVE_SYMBOLS_FILE, default={})

    out: List[str] = []
    if isinstance(data, dict):
        if isinstance(data.get("symbols"), list):
            out = [str(x).strip() for x in data["symbols"] if str(x).strip()]
        else:
            for k in ("forex", "crypto"):
                if isinstance(data.get(k), list):
                    out.extend([str(x).strip() for x in data[k] if str(x).strip()])
    elif isinstance(data, list):
        out = [str(x).strip() for x in data if str(x).strip()]

    seen = set()
    cleaned: List[str] = []
    for s in out:
        if s not in seen:
            seen.add(s)
            cleaned.append(s)
    return cleaned


def save_active_symbols(symbols: List[str]) -> None:
    storage.save_config_json(ACTIVE_SYMBOLS_FILE, {"symbols": symbols})


def load_focus_state() -> Dict[str, Any]:
    data = storage.load_state_json(FOCUS_STATE_FILE, default={})
    return data if isinstance(data, dict) else {}


def save_focus_state(data: Dict[str, Any]) -> None:
    storage.save_state_json(FOCUS_STATE_FILE, data)


def load_dist_state() -> Dict[str, Any]:
    data = storage.load_state_json(DIST_STATE_FILE, default={})
    return data if isinstance(data, dict) else {}


def save_dist_state(data: Dict[str, Any]) -> None:
    storage.save_state_json(DIST_STATE_FILE, data)


def load_outcomes() -> Dict[str, Any]:
    data = storage.load_state_json(OUTCOMES_FILE, default={})
    return data if isinstance(data, dict) else {}


def save_outcomes(data: Dict[str, Any]) -> None:
    storage.save_state_json(OUTCOMES_FILE, data)


---

3) core/outcome_handlers.py

Rol

Mută aici outcome-ul manual/admin și orice logică de înregistrare locală care nu trebuie să stea în bot_service.py.

Fișier nou

Creează core/outcome_handlers.py cu acest conținut:

from __future__ import annotations

from typing import Any, Dict, Optional
from core import observability_logger
from core.admin_state_helpers import load_outcomes, save_outcomes


def record_manual_outcome(
    *,
    signal_id: str,
    outcome: str,
    user_id: Optional[int] = None,
    symbol: Optional[str] = None,
) -> Dict[str, Any]:
    outcomes = load_outcomes()

    row = outcomes.get(signal_id, {})
    previous_outcome = row.get("outcome")

    row["signal_id"] = signal_id
    row["outcome"] = outcome
    row["user_id"] = user_id
    if symbol:
        row["symbol"] = symbol

    outcomes[signal_id] = row
    save_outcomes(outcomes)

    observability_logger.log_event({
        "event_type": "user_outcome",
        "signal_id": signal_id,
        "symbol": symbol,
        "data": {
            "signal_id": signal_id,
            "outcome": outcome,
            "previous_outcome": previous_outcome,
            "user_id": user_id,
            "symbol": symbol,
            "accepted": True,
            "source_flow": "admin_manual_outcome",
        },
        "source": {"module": "outcome_handlers", "function": "record_manual_outcome"},
    })

    return {
        "ok": True,
        "signal_id": signal_id,
        "outcome": outcome,
        "previous_outcome": previous_outcome,
    }


---

4) core/callback_handlers.py

Rol

Mută aici logica de callback Telegram, astfel încât bot_service.py doar deleagă.

Fișier nou

Creează core/callback_handlers.py cu acest conținut:

from __future__ import annotations

from typing import Any, Dict, Optional

from core import outcome_service
from core import observability_logger
from core.outcome_handlers import record_manual_outcome


def handle_vote_callback(
    *,
    data: str,
    user_id: int,
    chat_id: Optional[int] = None,
) -> Dict[str, Any]:
    result = outcome_service.register_vote(
        callback_data=data,
        user_id=user_id,
        chat_id=chat_id,
    )
    return {
        "text": result.get("message", "Vote processed."),
        "reply_markup": None,
    }


def handle_manual_outcome_callback(
    *,
    data: str,
    user_id: int,
) -> Dict[str, Any]:
    # Expected format: SET_OUTCOME|<signal_id>|<WIN/LOSS/BREAKEVEN>|<symbol?>
    parts = data.split("|")
    if len(parts) < 3:
        return {"text": "Invalid outcome payload.", "reply_markup": None}

    signal_id = parts[1].strip()
    outcome = parts[2].strip().upper()
    symbol = parts[3].strip() if len(parts) >= 4 and parts[3].strip() else None

    res = record_manual_outcome(
        signal_id=signal_id,
        outcome=outcome,
        user_id=user_id,
        symbol=symbol,
    )
    return {
        "text": f"Outcome saved: {res['signal_id']} → {res['outcome']}",
        "reply_markup": None,
    }


def route_callback(
    *,
    data: str,
    user_id: int,
    chat_id: Optional[int] = None,
) -> Dict[str, Any]:
    if data.startswith("VOTE_|"):
        return handle_vote_callback(data=data, user_id=user_id, chat_id=chat_id)

    if data.startswith("SET_OUTCOME|"):
        return handle_manual_outcome_callback(data=data, user_id=user_id)

    observability_logger.log_warning(
        warn_type="UNKNOWN_CALLBACK",
        message="Unknown callback payload received",
        context={"data": data, "user_id": user_id, "chat_id": chat_id},
        source={"module": "callback_handlers", "function": "route_callback"},
    )
    return {"text": "Unknown action.", "reply_markup": None}


---

5) core/command_router.py

Rol

Acesta separă comenzile text de restul.

Fișier nou

Creează core/command_router.py cu acest conținut:

from __future__ import annotations

from typing import Any, Dict, Optional

from core import admin_commands
from core import observability_logger


def route_text_command(
    *,
    text: str,
    user_id: int,
    chat_id: Optional[int] = None,
) -> Optional[Dict[str, Any]]:
    if not text:
        return None

    text = text.strip()
    if not text.startswith("/"):
        return None

    try:
        response = admin_commands.handle_admin_command_v2(
            text=text,
            user_id=user_id,
            chat_id=chat_id,
        )
        return response
    except Exception as e:
        observability_logger.log_error({
            "event_type": "error",
            "message": "Admin command routing failed",
            "error_type": type(e).__name__,
            "context": {
                "text": text,
                "user_id": user_id,
                "chat_id": chat_id,
            },
            "trace": repr(e),
            "source": {"module": "command_router", "function": "route_text_command"},
        })
        return {"text": "Command failed.", "reply_markup": None}


---

6) core/bot_service.py — curățare și spargere

Rol nou

Acest fișier trebuie să rămână doar:

bootstrap bot

parse update

route message text

route callback

fallback safe


Nu trebuie să mai țină local:

logică de settings

logică de active symbols

logică de outcomes

logică duplicată de callback voting



---

Patch exact

A. Înlocuiește importurile vechi / adaugă importurile noi

Adaugă sus:

from core.command_router import route_text_command
from core.callback_handlers import route_callback

Adaugă și, dacă există importuri locale vechi pentru outcome/path helpers, le vei scoate.


---

B. Elimină helperii locali mutați în admin_state_helpers.py

Șterge din bot_service.py funcțiile locale de tip:

def _load_settings(...)
def _save_settings(...)
def _load_active_symbols(...)
def _save_active_symbols(...)
def _record_outcome(...)

Astea nu mai trebuie să stea aici.

Dacă vrei să nu ștergi brutal, comentează-le temporar și apoi elimină complet după test.


---

C. Elimină complet ramura moartă cu outcome_tracker

Caută și șterge complet:

if data.startswith("VOTE_"):
    from core import outcome_tracker
    signal_id, outcome = data.split("|")[1:]
    result = outcome_tracker.register_vote(signal_id, outcome, user_id, chat_id)
    return {"text": result, "reply_markup": None}

Această ramură trebuie să dispară definitiv.


---

D. Înlocuiește handle_callback(...)

Dacă ai o funcție de tip:

def handle_callback(data, user_id, chat_id=None):
    ...

înlocuiește conținutul ei cu:

def handle_callback(data, user_id, chat_id=None):
    return route_callback(data=data, user_id=user_id, chat_id=chat_id)


---

E. Înlocuiește routing-ul pentru mesaje text

Dacă ai în process_update(...) sau funcția echivalentă ceva de forma:

if text.startswith("/"):
    ...
    # multă logică directă aici

înlocuiește blocul cu:

routed = route_text_command(text=text, user_id=user_id, chat_id=chat_id)
    if routed is not None:
        return routed


---

F. Adaugă fallback clar pentru mesaj non-command

Dacă nu există deja, după routing-ul de command, adaugă:

return {"text": "Unsupported message.", "reply_markup": None}

ca să nu rămână ramuri fără return clar.


---

G. Patch model pentru process_update(...)

Dacă vrei un model curat minim, structura ar trebui să arate așa:

def process_update(update: Dict[str, Any]) -> Dict[str, Any]:
    message = update.get("message") or {}
    callback_query = update.get("callback_query") or {}

    if callback_query:
        data = callback_query.get("data", "")
        from_user = callback_query.get("from", {}) or {}
        user_id = int(from_user.get("id", 0) or 0)
        msg = callback_query.get("message", {}) or {}
        chat = msg.get("chat", {}) or {}
        chat_id = chat.get("id")
        return handle_callback(data=data, user_id=user_id, chat_id=chat_id)

    if message:
        text = str(message.get("text", "") or "")
        from_user = message.get("from", {}) or {}
        user_id = int(from_user.get("id", 0) or 0)
        chat = message.get("chat", {}) or {}
        chat_id = chat.get("id")

        routed = route_text_command(text=text, user_id=user_id, chat_id=chat_id)
        if routed is not None:
            return routed

        return {"text": "Unsupported message.", "reply_markup": None}

    return {"text": "Unsupported update.", "reply_markup": None}


---

7) core/outcome_service.py — curățare contract pentru callback voting

Problema

Trebuie să aibă o interfață clară, folosită de callback_handlers.py.

Patch exact

A. Adaugă o funcție publică stabilă dacă nu există

În core/outcome_service.py, adaugă:

from __future__ import annotations

from typing import Any, Dict, Optional

și adaugă o funcție publică de forma:

def register_vote(*, callback_data: str, user_id: int, chat_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Expected callback_data format:
    VOTE_|<signal_id>|<WIN/LOSS/BREAKEVEN>
    """
    parts = callback_data.split("|")
    if len(parts) < 3:
        return {"ok": False, "message": "Invalid vote payload."}

    signal_id = parts[1].strip()
    outcome = parts[2].strip().upper()

    # if you already have a canonical internal vote handler, call it here:
    result = handle_vote_callback(
        signal_id=signal_id,
        outcome=outcome,
        user_id=user_id,
        chat_id=chat_id,
    )

    if isinstance(result, dict):
        return result

    return {"ok": True, "message": str(result)}


---

B. Normalizează rezultatul funcției interne

Dacă handle_vote_callback(...) sau echivalentul returnează string simplu, standardizează-l să returneze dict:

Model bun:

return {
    "ok": True,
    "message": "Vote registered.",
    "signal_id": signal_id,
    "outcome": outcome,
}

și pentru erori:

return {
    "ok": False,
    "message": "Vote rejected.",
    "signal_id": signal_id,
    "outcome": outcome,
    "reason": member_reason,
}

Asta elimină ambiguitatea din callback flow.


---

8) core/observability_logger.py — oficializare schemă

Scop

Acum transformăm schema reală într-un contract oficial.


---

A. Adaugă EVENT_SCHEMA_VERSION

Sub constante, adaugă:

EVENT_SCHEMA_VERSION = "2.0"


---

B. În build_event(...), înlocuiește orice versiune hardcodată

Dacă ai:

"schema_version": "1.0",

sau altceva similar, înlocuiește cu:

"schema_version": EVENT_SCHEMA_VERSION,


---

C. Adaugă validare strictă minimă pentru source

În build_event(...), înainte de a construi event, adaugă:

if source is not None and not isinstance(source, dict):
        raise ValueError("source must be dict or None")


---

D. Adaugă validare strictă minimă pentru data

Tot în build_event(...), adaugă:

if data is None:
        data = {}
    if not isinstance(data, dict):
        raise ValueError("data must be dict")


---

E. Adaugă helper public pentru schema curentă

Adaugă funcția:

def current_event_schema_meta() -> Dict[str, Any]:
    return {
        "schema_version": EVENT_SCHEMA_VERSION,
        "allowed_event_types": sorted(_ALLOWED_EVENT_TYPES),
        "required_top_level_fields": [
            "event_id",
            "schema_version",
            "event_type",
            "ts_utc",
            "ts_epoch_ms",
            "service",
            "env",
            "run_id",
            "host",
            "source",
            "data",
        ],
    }

Asta va ajuta și documentația, și debugging-ul.


---

9) schema/event_schema.json — alinierea oficială

Problema

Schema veche nu mai descrie ce emite efectiv loggerul.

Patch exact

Înlocuiește conținutul fișierului schema/event_schema.json cu acest JSON:

{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "BinaryBot Observability Event Envelope",
  "type": "object",
  "additionalProperties": true,
  "required": [
    "event_id",
    "schema_version",
    "event_type",
    "ts_utc",
    "ts_epoch_ms",
    "service",
    "env",
    "run_id",
    "host",
    "source",
    "data"
  ],
  "properties": {
    "event_id": {
      "type": "string",
      "minLength": 1
    },
    "schema_version": {
      "type": "string",
      "enum": ["2.0"]
    },
    "event_type": {
      "type": "string",
      "enum": [
        "engine_start",
        "engine_stop",
        "signal_event",
        "decision",
        "fsm_transition",
        "tier_publish",
        "tier_reset",
        "admin_change",
        "user_outcome",
        "error"
      ]
    },
    "ts_utc": {
      "type": "string",
      "minLength": 1
    },
    "ts_epoch_ms": {
      "type": "integer"
    },
    "service": {
      "type": "string",
      "minLength": 1
    },
    "env": {
      "type": "string",
      "minLength": 1
    },
    "run_id": {
      "type": "string",
      "minLength": 1
    },
    "host": {
      "type": "string",
      "minLength": 1
    },
    "source": {
      "type": "object",
      "additionalProperties": true
    },
    "correlation": {
      "type": "object",
      "additionalProperties": true
    },
    "data": {
      "type": "object",
      "additionalProperties": true
    },
    "signal_id": {
      "type": ["string", "null"]
    },
    "symbol": {
      "type": ["string", "null"]
    },
    "timeframe": {
      "type": ["string", "null"]
    }
  }
}


---

10) Creezi documentul nou pentru schema observability

Fișier nou

Creează docs/OBSERVABILITY_EVENT_ENVELOPE_SPEC.md

Conținut exact:

# OBSERVABILITY EVENT ENVELOPE SPEC

## Status
implemented

## Canonical producer
`core/observability_logger.py`

## Canonical schema
`schema/event_schema.json`

## Schema version
`2.0`

## Required top-level fields

- `event_id`
- `schema_version`
- `event_type`
- `ts_utc`
- `ts_epoch_ms`
- `service`
- `env`
- `run_id`
- `host`
- `source`
- `data`

## Allowed canonical event types

- `engine_start`
- `engine_stop`
- `signal_event`
- `decision`
- `fsm_transition`
- `tier_publish`
- `tier_reset`
- `admin_change`
- `user_outcome`
- `error`

## Notes

Legacy aliases may be normalized by `core/observability_logger.py`, but producers should emit canonical event types directly.

## Source contract

`source` should be an object and should usually include:

- `module`
- `function`

## Data contract

`data` must be an object.
Event-specific payloads belong inside `data`.


---

11) Curățarea logicii callback/admin/outcome în bot_service.py

Checklist exact

După patch, în core/bot_service.py nu trebuie să mai existe:

A. path helpers

Caută și elimină:

grep -n "_load_settings\|_save_settings\|_load_active_symbols\|_save_active_symbols\|_record_outcome" /opt/binarybot/core/bot_service.py

Ținta: zero rezultate.


---

B. ramuri duplicate de callback

Caută:

grep -n 'startswith("VOTE_' /opt/binarybot/core/bot_service.py
grep -n 'startswith("SET_OUTCOME|' /opt/binarybot/core/bot_service.py

Ținta:

callback-urile să fie rutate doar prin route_callback(...)

nu să mai fie implementate direct aici



---

C. admin command direct handling mare

Caută:

grep -n 'handle_admin_command_v2\|text.startswith("/")' /opt/binarybot/core/bot_service.py

Ținta:

route_text_command(...) să fie singurul punct principal de delegare



---

12) Validare de structură după Sprint 3

A. Compile check

cd /opt/binarybot
python3 -m compileall core intelligence monitoring runtime


---

B. Caută importuri noi și ramuri vechi

grep -R "outcome_tracker" core
grep -R "_record_outcome" core/bot_service.py
grep -R "VOTE_" core/bot_service.py
grep -R "SET_OUTCOME|" core/bot_service.py

Ținta:

nimic relevant în bot_service.py, în afară de delegare



---

C. Confirmă noile module

ls -l /opt/binarybot/core/command_router.py
ls -l /opt/binarybot/core/callback_handlers.py
ls -l /opt/binarybot/core/outcome_handlers.py
ls -l /opt/binarybot/core/admin_state_helpers.py


---

13) Smoke test funcțional după Sprint 3

Test 1 — command routing

Trimite o comandă admin, de exemplu:

/health

/engine

o comandă de symbols


Trebuie să meargă prin route_text_command(...).


---

Test 2 — callback vote

Apasă un buton de vote.

Trebuie să intre:

bot_service.process_update(...)

handle_callback(...)

route_callback(...)

outcome_service.register_vote(...)


și să răspundă fără excepții.


---

Test 3 — manual outcome callback

Dacă ai callback de tip:

SET_OUTCOME|abc123|WIN|EURUSD

trebuie să intre în:

route_callback(...)

record_manual_outcome(...)


și să salveze în state/outcomes.json.


---

Test 4 — observability schema

Verifică ultimele linii din loguri:

tail -n 5 /opt/binarybot/observability/error_events.jsonl
tail -n 5 /opt/binarybot/observability/engine_events.jsonl
tail -n 5 /opt/binarybot/observability/outcome_events.jsonl

Trebuie să vezi evenimente cu:

schema_version: "2.0"

source dict

data dict

event_type canonic



---

14) Definiția de gata pentru Sprint 3

Sprint 3 este gata când:

core/bot_service.py nu mai conține logică de state/config/outcome duplicată

command routing este mutat în core/command_router.py

callback routing este mutat în core/callback_handlers.py

outcome manual/admin este mutat în core/outcome_handlers.py

core/outcome_service.py are interfață publică stabilă pentru vote callbacks

schema/event_schema.json descrie schema reală

există document canonic nou pentru event envelope

flow-urile admin/callback/outcome nu mai sunt amestecate



---

15) Ce intră în Sprint 4

După Sprint 3, următorul pas bun este Sprint 4:

cleanup .bak, Copy, fișiere legacy

actualizare docs canonice:

ARCHITECTURE_CODE_MAPPING.md

BINARYBOT_MASTER_INDEX.md

SYSTEM_ARCHITECTURE_MAP.md

MODULE_INTERFACE_SPEC_v2.0.0.md


marcarea documentelor cu:

implemented

partial

planned

deprecated


audit final doc ↔ cod


Dacă vrei, îți scriu și Sprint 4 la același nivel, tot cu patch-uri exacte și ordine de execuție.


Mai jos ai Sprint 4 la același nivel, cu patch-uri exacte și ordine de execuție.

Sprint 4 este despre:

cleanup de repo

alinierea documentației canonice la codul real

marcarea documentelor cu status

eliminarea referințelor false sau depășite

pregătirea unui repo mai sigur pentru mentenanță și audit viitor


Obiectivul este:

să faci repo-ul credibil ca sursă de adevăr, atât pentru cod, cât și pentru docs.


---

SPRINT 4 — ȚINTĂ FINALĂ

La finalul Sprint 4 trebuie să fie adevărat:

fișierele .bak, Copy, variantele moarte nu mai stau în calea runtime-ului

documentele canonice nu mai trimit la fișiere inexistente fără să spună asta

ARCHITECTURE_CODE_MAPPING.md reflectă structura reală

BINARYBOT_MASTER_INDEX.md devine index real, nu listă aspiratională

SYSTEM_ARCHITECTURE_MAP.md separă clar:

implemented

partial

planned


MODULE_INTERFACE_SPEC_v2.0.0.md este sincronizat cu contractul real al lumânărilor și cu structura reală a modulelor

există o guvernanță minimă a documentației



---

0) Backup înainte de Sprint 4

cd /opt/binarybot
cp docs/ARCHITECTURE_CODE_MAPPING.md docs/ARCHITECTURE_CODE_MAPPING.md.bak_sprint4
cp docs/BINARYBOT_MASTER_INDEX.md docs/BINARYBOT_MASTER_INDEX.md.bak_sprint4
cp docs/SYSTEM_ARCHITECTURE_MAP.md docs/SYSTEM_ARCHITECTURE_MAP.md.bak_sprint4
cp docs/MODULE_INTERFACE_SPEC_v2.0.0.md docs/MODULE_INTERFACE_SPEC_v2.0.0.md.bak_sprint4

Dacă unele fișiere nu există exact cu aceste nume, adaptezi la numele reale din repo.


---

1) Cleanup repo — fișiere moarte și backup-uri

Problema

În core/ și posibil și în alte directoare ai fișiere de tip:

.bak_*

Copy

variante vechi


Astea nu trebuie să rămână în zona activă.


---

A. Creează folderul de arhivă internă

mkdir -p /opt/binarybot/_archive/legacy_core
mkdir -p /opt/binarybot/_archive/legacy_docs
mkdir -p /opt/binarybot/_archive/legacy_misc


---

B. Mută backup-urile din core/

Rulează:

find /opt/binarybot/core -maxdepth 1 \( -name "*.bak*" -o -name "*Copy*" -o -name "* - Copy.py" \) -print

Verifici lista.

Apoi:

find /opt/binarybot/core -maxdepth 1 \( -name "*.bak*" -o -name "*Copy*" -o -name "* - Copy.py" \) -exec mv {} /opt/binarybot/_archive/legacy_core/ \;


---

C. Mută backup-urile din docs/ dacă există

find /opt/binarybot/docs -maxdepth 1 \( -name "*.bak*" -o -name "*Copy*" \) -print
find /opt/binarybot/docs -maxdepth 1 \( -name "*.bak*" -o -name "*Copy*" \) -exec mv {} /opt/binarybot/_archive/legacy_docs/ \;


---

D. Verificare după cleanup

find /opt/binarybot/core -maxdepth 1 \( -name "*.bak*" -o -name "*Copy*" -o -name "* - Copy.py" \)
find /opt/binarybot/docs -maxdepth 1 \( -name "*.bak*" -o -name "*Copy*" \)

Ținta: nimic.


---

2) Creezi documentul de status al documentației

Fișier nou

Creează docs/DOCUMENT_STATUS_POLICY.md

Conținut exact:

# DOCUMENT STATUS POLICY

## Purpose

This document defines the allowed lifecycle status values for documentation in the BinaryBot repository.

## Allowed status values

- `implemented`
- `partial`
- `planned`
- `deprecated`

## Meanings

### implemented
The document matches the current production-oriented code structure closely enough to be used as an operational reference.

### partial
The document describes a mix of implemented behavior and target architecture. It cannot be treated as a complete source of truth without code verification.

### planned
The document describes intended architecture or future modules that are not yet fully implemented.

### deprecated
The document has been superseded or no longer reflects the active structure. It is retained only for historical reference.

## Placement

Each major document should contain a `Status` section near the top.

## Additional recommendation

Each major document should also include:

- canonical owner module(s)
- last reviewed date
- notes about gaps between spec and implementation


---

3) docs/ARCHITECTURE_CODE_MAPPING.md

Problema

Maparea este depășită și probabil încă arată către /opt/binarybot/*.py direct.

Ținta

Acest document trebuie să spună exact care fișier implementează ce, în structura actuală.


---

Patch exact — înlocuire recomandată

Dacă documentul este foarte vechi, cel mai bine este să îl rescrii complet.

Înlocuiește conținutul cu:

# ARCHITECTURE CODE MAPPING

## Status
implemented

## Purpose

This document maps the active BinaryBot architecture layers to the current repository structure.

## Active repository structure

- `core/` — core runtime logic
- `config/` — operator-controlled configuration
- `state/` — mutable runtime state
- `observability/` — JSONL event logs
- `monitoring/` — runtime health / restart protection
- `intelligence/` — diagnostics / analysis helpers
- `schema/` — formal schema artifacts
- `docs/` — canonical and supporting documentation

## Core runtime mapping

### Signal engine
- Spec: `docs/MODULE_INTERFACE_SPEC_v2.0.0.md`
- Code: `core/signal_engine.py`

### Strategy logic
- Spec: `docs/MODULE_INTERFACE_SPEC_v2.0.0.md`
- Code: `core/strategy_v2.py`

### Candle normalization
- Spec: `docs/MODULE_INTERFACE_SPEC_v2.0.0.md`
- Code: `core/candle_adapter.py`

### FSM runtime
- Spec: `docs/FSM_DECISION_ENGINE_SPEC_v1.0.0.md`
- Code: `core/fsm_runtime.py`

### Signal distribution
- Spec: `docs/SIGNAL_DISTRIBUTION_SPEC_v2.0.0.md`
- Code: `core/distribution_router.py`

### Telegram command routing
- Spec: `docs/TELEGRAM_UX_v2.0.0.md`
- Code:
  - `core/bot_service.py`
  - `core/command_router.py`
  - `core/callback_handlers.py`

### Outcome registration
- Spec: `docs/OUTCOME_TRACKING_SPEC_v2.0.0.md`
- Code:
  - `core/outcome_service.py`
  - `core/outcome_handlers.py`

### Admin config/state helpers
- Code:
  - `core/admin_state_helpers.py`
  - `core/admin_commands.py`

## Storage mapping

### Config layer
- Directory: `config/`
- Access layer: `core/storage.py`

### Runtime state layer
- Directory: `state/`
- Access layer: `core/storage.py`

## Observability mapping

### Event envelope producer
- Spec:
  - `docs/OBSERVABILITY_LOGGING_SPEC_v2.0.0.md`
  - `docs/OBSERVABILITY_EVENT_ENVELOPE_SPEC.md`
- Schema:
  - `schema/event_schema.json`
- Code:
  - `core/observability_logger.py`

## Monitoring mapping

### Restart protection
- Spec: `docs/FAILURE_RECOVERY_SPEC_v2.0.0.md`
- Code:
  - `runtime/system_boot.py`
  - `monitoring/restart_guard.py`

## Intelligence / analytics mapping

### Diagnostics and analysis
- Spec: partial / distributed across docs
- Code:
  - `intelligence/risk_monitor.py`
  - `intelligence/signal_diagnostics.py`
  - `intelligence/bottleneck_detector.py`
  - `intelligence/heatmap.py`
  - `core/analytics_engine.py`

## Notes

- Root-level legacy paths should no longer be treated as canonical runtime locations for active config/state.
- `config/active_symbols.json` is the canonical source for active symbols.
- `config/settings.json` is the canonical source for operator settings.
- `state/` holds mutable runtime state such as focus state, distribution state, and outcomes.


---

4) docs/BINARYBOT_MASTER_INDEX.md

Problema

Indexul probabil referă documente lipsă sau documente fără status clar.

Ținta

Indexul trebuie să fie simplu, clar și sincer:

ce e implementat

ce e parțial

ce e planificat

ce e deprecated



---

Patch exact — înlocuire recomandată

Înlocuiește conținutul cu:

# BINARYBOT MASTER INDEX

## Status
implemented

## Purpose

This is the high-level documentation index for the active BinaryBot repository.

## Canonical operational documents

### Implemented
- `ARCHITECTURE_CODE_MAPPING.md`
- `MODULE_INTERFACE_SPEC_v2.0.0.md`
- `FSM_DECISION_ENGINE_SPEC_v1.0.0.md`
- `SIGNAL_DISTRIBUTION_SPEC_v2.0.0.md`
- `OUTCOME_TRACKING_SPEC_v2.0.0.md`
- `OBSERVABILITY_LOGGING_SPEC_v2.0.0.md`
- `OBSERVABILITY_EVENT_ENVELOPE_SPEC.md`
- `FAILURE_RECOVERY_SPEC_v2.0.0.md`
- `TELEGRAM_UX_v2.0.0.md`

### Partial
- `DECISION_AUDIT_SPEC_v2.0.0.md`
- `PERFORMANCE_ANALYTICS_SPEC_v2.0.0.md`
- `RISK_MODEL.md`
- `SYSTEM_ARCHITECTURE_MAP.md`

### Planned
- documents referenced by architecture notes but not yet written as standalone canonical specs should be marked explicitly inside `SYSTEM_ARCHITECTURE_MAP.md`

### Governance
- `DOCUMENT_STATUS_POLICY.md`

## Formal / reference documents
- `FORMAL_SPEC.md`
- `ALGO_SPEC_v2.0.0.md`
- `SYSTEM_INVARIANTS_v2.0.0.md`
- `PARAMS_REFERENCE.md`

## Notes

- A document should not be treated as canonical just because it exists.
- The `Status` section inside each document takes precedence over assumptions.
- If a document describes future architecture, it must be marked `planned` or `partial`.


---

5) docs/SYSTEM_ARCHITECTURE_MAP.md

Problema

Este foarte probabil să enumere mult mai multe documente/spec-uri decât există efectiv.

Ținta

Păstrezi viziunea, dar o faci sinceră:

implemented

partial

planned

not yet written



---

Patch exact — structură de rescriere

Dacă documentul este complex și vrei să păstrezi mult din el, nu îl șterge complet; rescrie primele secțiuni și normalizează referințele.

Începutul documentului trebuie înlocuit cu:

# SYSTEM ARCHITECTURE MAP

## Status
partial

## Purpose

This document describes the target architecture and the current implementation map of BinaryBot.

## Reading rule

This document includes both:
- current implemented architecture
- target architecture not yet fully implemented

It must not be treated as a pure implementation guarantee unless a section is explicitly marked implemented.

## Current implemented layers

- signal engine
- strategy runtime
- candle normalization
- FSM runtime
- distribution routing
- Telegram command/callback handling
- outcome registration
- observability event envelope
- restart protection
- config/state separation

## Partial layers

- analytics layer
- strategy decision audit
- advanced risk intelligence
- reporting / performance aggregation

## Planned or not yet written standalone specs

The following items may exist as architecture concepts without standalone complete specs yet:

- parameter surface governance
- strategy decision proof layer
- channel routing expansion
- risk and limits expansion
- daily reset policy standalone spec
- user feedback analytics standalone spec
- affiliate admin layer standalone spec

These should be treated as planned unless mapped to active code and a specific implemented document.


---

Apoi, în restul documentului:

Înlocuiește formulări de tip:

“defined in X.md”

“see Y.md”


când fișierul nu există, cu:

“planned standalone spec”

“not yet written as standalone doc”

“currently covered partially by …”


Exemple exacte de înlocuire

Dacă apare:

See `CHANNEL_ROUTING_SPEC.md`

și acel fișier nu există, înlocuiești cu:

Planned standalone spec: `CHANNEL_ROUTING_SPEC.md` (not yet written). Current behavior is partially covered by `SIGNAL_DISTRIBUTION_SPEC_v2.0.0.md` and `core/distribution_router.py`.

Dacă apare:

See `USER_FEEDBACK_AND_VOTING_SPEC.md`

înlocuiești cu:

Planned standalone spec: `USER_FEEDBACK_AND_VOTING_SPEC.md` (not yet written). Current implemented flow is partially covered by `OUTCOME_TRACKING_SPEC_v2.0.0.md`, `core/outcome_service.py`, and `core/callback_handlers.py`.


---

6) docs/MODULE_INTERFACE_SPEC_v2.0.0.md

Problema

Aici trebuie să fie clar contractul real pentru:

candles newest-first

responsabilitatea modulelor

ce e input și ce e output


Ținta

Acest document trebuie să fie utilizabil direct la debug.


---

Patch exact — secțiune nouă obligatorie

Adaugă aproape de început, după titlu:

## Status
implemented


---

Patch exact — secțiunea Candle Ordering Contract

Adaugă sau înlocuiește secțiunea relevantă cu exact:

## Candle Ordering Contract

All normalized candle arrays used by the active runtime must be `newest-first`.

### Canonical rule

- `candles[0]` = latest / most recent candle
- `candles[1]` = previous candle
- timestamps must be non-increasing across the array

### Example

```python
[
    {"ts": 1710000120, "open": 1.10, "high": 1.12, "low": 1.09, "close": 1.11},
    {"ts": 1710000060, "open": 1.09, "high": 1.11, "low": 1.08, "close": 1.10},
    {"ts": 1710000000, "open": 1.08, "high": 1.10, "low": 1.07, "close": 1.09}
]

Implementation notes

core/candle_adapter.py is responsible for normalization and ordering enforcement.

core/strategy_v2.py must treat index 0 as the current/latest candle.

Any indicator helper that expects oldest-first series must receive a reversed copy explicitly.


---

## Patch exact — secțiune nouă despre config/state
Adaugă:

```md
## Config and State Contract

### Config
Operator-controlled configuration must be stored in `config/`.

Examples:
- `config/settings.json`
- `config/active_symbols.json`
- `config/admin_settings.json`

### State
Mutable runtime state must be stored in `state/`.

Examples:
- `state/focus_state.json`
- `state/dist_state.json`
- `state/outcomes.json`

### Access layer
Modules should access these files through `core/storage.py`, not through inconsistent ad-hoc path definitions.


---

Patch exact — secțiune nouă despre Telegram routing

Adaugă:

## Telegram Routing Contract

### Command flow
- `core/bot_service.py` receives updates
- text commands are delegated to `core/command_router.py`
- admin command execution is handled by `core/admin_commands.py`

### Callback flow
- `core/bot_service.py` receives callback updates
- callback routing is delegated to `core/callback_handlers.py`

### Outcome flow
- vote callbacks are handled via `core/outcome_service.py`
- manual/admin outcomes are handled via `core/outcome_handlers.py`


---

7) docs/DECISION_AUDIT_SPEC_v2.0.0.md

Problema

Documentul descrie mai mult decât există.

Ținta

Nu îl ștergi. Îl faci sincer și util.


---

Patch exact

Adaugă aproape de început:

## Status
partial


---

Adaugă secțiunea:

## Current implementation status

The full target decision-audit architecture is not yet completely implemented as standalone analytics modules.

### Currently implemented or partially implemented components
- `intelligence/signal_diagnostics.py`
- `intelligence/bottleneck_detector.py`
- `intelligence/heatmap.py`
- `core/analytics_engine.py`

### Not yet fully implemented as dedicated standalone modules
- conversion funnel analytics
- focus analysis aggregation
- rejection statistics module
- symbol performance aggregation
- timeframe performance aggregation

These should be treated as target architecture until mapped to dedicated active code modules.


---

8) docs/OBSERVABILITY_LOGGING_SPEC_v2.0.0.md

Problema

Acum ai document nou pentru envelope, dar acest document trebuie să trimită clar la el.

Patch exact

Adaugă sau înlocuiește începutul cu:

## Status
implemented

și apoi adaugă:

## Canonical envelope reference

The active event envelope structure is defined by:

- `docs/OBSERVABILITY_EVENT_ENVELOPE_SPEC.md`
- `schema/event_schema.json`
- `core/observability_logger.py`

If this document conflicts with the event envelope spec, the envelope spec and active logger implementation take precedence.


---

9) docs/OUTCOME_TRACKING_SPEC_v2.0.0.md

Problema

Trebuie să reflecte noua separare:

callback vote flow

manual outcome flow


Patch exact

Adaugă aproape de început:

## Status
implemented


---

Adaugă secțiunea:

## Current routing implementation

### Vote callbacks
Vote callbacks are routed through:
- `core/bot_service.py`
- `core/callback_handlers.py`
- `core/outcome_service.py`

### Manual/admin outcomes
Manual outcome actions are routed through:
- `core/bot_service.py`
- `core/callback_handlers.py`
- `core/outcome_handlers.py`

### State persistence
Outcome data is stored in:
- `state/outcomes.json`

via:
- `core/storage.py`


---

10) docs/TELEGRAM_UX_v2.0.0.md

Problema

Trebuie să reflecte noul command/callback routing.

Patch exact

Adaugă aproape de început:

## Status
implemented


---

Adaugă secțiunea:

## Active routing architecture

### Text commands
Incoming Telegram text commands are received by `core/bot_service.py` and delegated to `core/command_router.py`.

### Callback actions
Incoming Telegram callbacks are received by `core/bot_service.py` and delegated to `core/callback_handlers.py`.

This separation is intentional and is part of the current active architecture.


---

11) Creezi matricea minimă doc ↔ cod ↔ status

Fișier nou

Creează docs/DOCUMENT_IMPLEMENTATION_MATRIX.md

Conținut exact:

# DOCUMENT IMPLEMENTATION MATRIX

## Status
implemented

| Document | Status | Primary Code Modules | Notes |
|---|---|---|---|
| `ARCHITECTURE_CODE_MAPPING.md` | implemented | multiple | Current repo structure mapping |
| `MODULE_INTERFACE_SPEC_v2.0.0.md` | implemented | `core/candle_adapter.py`, `core/strategy_v2.py`, `core/signal_engine.py` | Includes candle ordering contract |
| `FSM_DECISION_ENGINE_SPEC_v1.0.0.md` | implemented | `core/fsm_runtime.py` | Active FSM layer |
| `SIGNAL_DISTRIBUTION_SPEC_v2.0.0.md` | partial | `core/distribution_router.py` | Code is simpler than full target architecture |
| `OUTCOME_TRACKING_SPEC_v2.0.0.md` | implemented | `core/outcome_service.py`, `core/outcome_handlers.py`, `core/callback_handlers.py` | Active outcome routing |
| `OBSERVABILITY_LOGGING_SPEC_v2.0.0.md` | implemented | `core/observability_logger.py` | See also envelope spec |
| `OBSERVABILITY_EVENT_ENVELOPE_SPEC.md` | implemented | `core/observability_logger.py` | Canonical envelope contract |
| `FAILURE_RECOVERY_SPEC_v2.0.0.md` | partial | `runtime/system_boot.py`, `monitoring/restart_guard.py` | Needs periodic review after restart logic changes |
| `TELEGRAM_UX_v2.0.0.md` | implemented | `core/bot_service.py`, `core/command_router.py`, `core/callback_handlers.py` | Active routing documented |
| `DECISION_AUDIT_SPEC_v2.0.0.md` | partial | `intelligence/signal_diagnostics.py`, `intelligence/bottleneck_detector.py`, `intelligence/heatmap.py`, `core/analytics_engine.py` | Full target not yet complete |
| `PERFORMANCE_ANALYTICS_SPEC_v2.0.0.md` | partial | `core/analytics_engine.py` | Target ahead of code |
| `RISK_MODEL.md` | partial | `core/strategy_v2.py`, `intelligence/risk_monitor.py` | Needs alignment review |


---

12) Verificare automată minimă pentru docs inexistente referite

Comandă utilă

Rulează:

cd /opt/binarybot
grep -Rho '`[^`]\+\.md`' docs | sort | uniq

Apoi verifici manual dacă fiecare fișier există.


---

Comandă mai bună

Rulează:

python3 - <<'PY'
import os, re

docs_dir = "/opt/binarybot/docs"
existing = set(os.listdir(docs_dir))
refs = {}

for fn in os.listdir(docs_dir):
    if not fn.endswith(".md"):
        continue
    path = os.path.join(docs_dir, fn)
    with open(path, "r", encoding="utf-8") as f:
        txt = f.read()
    found = re.findall(r'`([^`]+\.md)`', txt)
    refs[fn] = found

missing = []
for fn, found in refs.items():
    for ref in found:
        base = os.path.basename(ref)
        if base not in existing:
            missing.append((fn, ref))

for src, ref in sorted(missing):
    print(f"{src} -> MISSING: {ref}")
PY

Ținta după Sprint 4:

ori zero lipsuri,

ori doar lipsuri marcate explicit ca planned/not yet written în documentele respective



---

13) Verificare automată minimă pentru Status în docs

Comandă

python3 - <<'PY'
import os, re

docs_dir = "/opt/binarybot/docs"
for fn in sorted(os.listdir(docs_dir)):
    if not fn.endswith(".md"):
        continue
    path = os.path.join(docs_dir, fn)
    with open(path, "r", encoding="utf-8") as f:
        txt = f.read()
    ok = bool(re.search(r'^## Status\s*$', txt, flags=re.MULTILINE))
    print(f"{fn}: {'OK' if ok else 'MISSING_STATUS'}")
PY

Ținta:

toate documentele majore să aibă ## Status



---

14) Ordinea exactă de execuție Sprint 4

Pasul 1

Cleanup repo:

1. creezi _archive/


2. muți .bak, Copy, variante moarte



Pasul 2

Guvernanță docs: 3. creezi DOCUMENT_STATUS_POLICY.md 4. creezi DOCUMENT_IMPLEMENTATION_MATRIX.md

Pasul 3

Core docs: 5. rescrii ARCHITECTURE_CODE_MAPPING.md 6. rescrii BINARYBOT_MASTER_INDEX.md 7. normalizezi SYSTEM_ARCHITECTURE_MAP.md 8. normalizezi MODULE_INTERFACE_SPEC_v2.0.0.md

Pasul 4

Support docs: 9. normalizezi DECISION_AUDIT_SPEC_v2.0.0.md 10. normalizezi OBSERVABILITY_LOGGING_SPEC_v2.0.0.md 11. normalizezi OUTCOME_TRACKING_SPEC_v2.0.0.md 12. normalizezi TELEGRAM_UX_v2.0.0.md

Pasul 5

Validări: 13. rulezi verificarea de refs lipsă 14. rulezi verificarea de status 15. compile check pentru siguranță, deși Sprint 4 e predominant docs


---

15) Verificări finale după Sprint 4
A. Compile sanity
Bash
Copiază codul
cd /opt/binarybot
python3 -m compileall core intelligence monitoring runtime
B. Verifică structura curată
Bash
Copiază codul
find /opt/binarybot/core -maxdepth 1 \( -name "*.bak*" -o -name "*Copy*" -o -name "* - Copy.py" \)
Ținta: nimic.
C. Verifică documentele-cheie
Bash
Copiază codul
grep -n "^## Status" /opt/binarybot/docs/ARCHITECTURE_CODE_MAPPING.md
grep -n "^## Status" /opt/binarybot/docs/BINARYBOT_MASTER_INDEX.md
grep -n "^## Status" /opt/binarybot/docs/SYSTEM_ARCHITECTURE_MAP.md
grep -n "^## Status" /opt/binarybot/docs/MODULE_INTERFACE_SPEC_v2.0.0.md
grep -n "^## Status" /opt/binarybot/docs/DECISION_AUDIT_SPEC_v2.0.0.md
D. Verifică existența documentelor noi
Bash
Copiază codul
ls -l /opt/binarybot/docs/DOCUMENT_STATUS_POLICY.md
ls -l /opt/binarybot/docs/DOCUMENT_IMPLEMENTATION_MATRIX.md
ls -l /opt/binarybot/docs/OBSERVABILITY_EVENT_ENVELOPE_SPEC.md

---

16) Definiția de gata pentru Sprint 4
Sprint 4 este gata când:
repo-ul activ nu mai e poluat de backup-uri și copii în directoarele de runtime
documentele canonice mari au ## Status
master index-ul nu mai minte despre starea documentației
architecture mapping reflectă structura reală
system architecture map separă clar implementat vs țintă
module interface spec spune clar contractul real pentru candles/config/state/routing
există o matrice minimă doc ↔ cod ↔ status
referințele la docs lipsă sunt fie eliminate, fie marcate explicit ca planned

17) Ce urmează după Sprint 4
După Sprint 4, ai două direcții bune:
Direcția A — hardening tehnic
teste de integrare
validator pentru schema de evenimente
script de audit automat doc ↔ cod
verificări de startup pentru config/state
Direcția B — audit și implementare funcțională
layer real de analytics
decision audit complet
un dashboard real /health
cleanup avansat în bot_service.py și admin panel

Pasul cel mai util acum este să transform toate cele 4 sprinturi într-un master execution playbook, cu comenzi în ordine exactă, ca să le poți rula una după alta fără să te încurci.


Da. Mai jos ai Master Execution Playbook pentru toate cele 4 sprinturi, pus în ordine exactă de execuție, astfel încât să-l poți urma cap-coadă fără să te încurci.

L-am scris ca procedură operațională reală:

ce faci,

în ce ordine,

ce modifici,

ce comenzi rulezi,

ce verifici înainte să treci mai departe.



---

MASTER EXECUTION PLAYBOOK — BINARYBOT

Regula de bază

Execută strict în ordinea asta:

1. Pregătire și backup


2. Sprint 1 — stabilizare critică


3. Sprint 2 — unificare config/state


4. Sprint 3 — spargere bot_service.py + observability schema


5. Sprint 4 — cleanup repo + guvernanță docs


6. Verificare finală




---

FAZA 0 — PREGĂTIRE

0.1 Intrare în proiect

cd /opt/binarybot
pwd
find core -maxdepth 1 -type f | sort
find docs -maxdepth 1 -type f | sort


---

0.2 Backup general înainte de orice

mkdir -p /opt/binarybot/_backup_pre_playbook

cp -r core /opt/binarybot/_backup_pre_playbook/core
cp -r docs /opt/binarybot/_backup_pre_playbook/docs
cp -r config /opt/binarybot/_backup_pre_playbook/config 2>/dev/null || true
cp -r state /opt/binarybot/_backup_pre_playbook/state 2>/dev/null || true
cp -r schema /opt/binarybot/_backup_pre_playbook/schema 2>/dev/null || true
cp -r monitoring /opt/binarybot/_backup_pre_playbook/monitoring 2>/dev/null || true
cp -r runtime /opt/binarybot/_backup_pre_playbook/runtime 2>/dev/null || true
cp -r intelligence /opt/binarybot/_backup_pre_playbook/intelligence 2>/dev/null || true


---

0.3 Snapshot textual rapid

python3 -m compileall core intelligence monitoring runtime

Dacă aici ai erori de sintaxă, oprești și le notezi înainte să continui.


---

SPRINT 1 — STABILIZARE CRITICĂ

Obiectiv:

corectarea ordinii lumânărilor

repararea event types

repararea distribution_router

repararea restart_guard

eliminarea ramurii moarte outcome_tracker



---

1.1 Backup local Sprint 1

cp core/strategy_v2.py core/strategy_v2.py.bak_sprint1
cp core/candle_adapter.py core/candle_adapter.py.bak_sprint1
cp core/signal_engine.py core/signal_engine.py.bak_sprint1
cp core/distribution_router.py core/distribution_router.py.bak_sprint1
cp core/observability_logger.py core/observability_logger.py.bak_sprint1
cp core/outcome_service.py core/outcome_service.py.bak_sprint1
cp intelligence/risk_monitor.py intelligence/risk_monitor.py.bak_sprint1
cp runtime/system_boot.py runtime/system_boot.py.bak_sprint1
cp monitoring/restart_guard.py monitoring/restart_guard.py.bak_sprint1
cp core/bot_service.py core/bot_service.py.bak_sprint1


---

1.2 Patch core/strategy_v2.py

Aici faci manual exact modificările deja definite:

candles_m1[-1] → candles_m1[0]

candles_m1[-2] → candles_m1[1]

closes_m1[-1] → closes_m1[0]

indicatorii primesc versiuni reversed(...)


Verificare după patch

grep -n '\[-1\]\|\[-2\]' /opt/binarybot/core/strategy_v2.py

Ținta: în zona decide() să nu mai existe accesările greșite.


---

1.3 Patch core/candle_adapter.py

Adaugi helperul assert_newest_first(...) și îl chemi în:

normalize(...)

validate(...)


Verificare

grep -n "assert_newest_first" /opt/binarybot/core/candle_adapter.py


---

1.4 Patch core/signal_engine.py

Fă:

SIGNAL_EVENT → signal_event

normalizează _load_settings()

îmbunătățește logging-ul pe excepții


Verificare

grep -n 'SIGNAL_EVENT\|signal_event' /opt/binarybot/core/signal_engine.py

Ținta: doar signal_event.


---

1.5 Patch core/distribution_router.py

Corectezi toate apelurile build_event(...) astfel încât să folosească:

event_type

data

source

correlation


nu module=..., now_ts=... direct.

Verificare

grep -n "build_event(" /opt/binarybot/core/distribution_router.py

Verifici manual fiecare apel.


---

1.6 Patch core/observability_logger.py

Adaugi alias mapping în _normalize_event(...):

SIGNAL_EVENT → signal_event

OUTCOME_SET → user_outcome

outcome_register_open_now → user_outcome

risk_warning → error

system_health → decision

strategy_optimizer → decision


Verificare

grep -n "event_type_aliases" /opt/binarybot/core/observability_logger.py


---

1.7 Patch core/outcome_service.py

Transformi toate apelurile greșite:

log_warning({...}) în

log_warning(warn_type=..., message=..., context=..., source=...)


Verificare

grep -n 'log_warning({' /opt/binarybot/core/outcome_service.py

Ținta: nimic.


---

1.8 Patch intelligence/risk_monitor.py

Exact aceeași corecție pentru log_warning(...).

Verificare

grep -n 'log_warning({' /opt/binarybot/intelligence/risk_monitor.py

Ținta: nimic.


---

1.9 Patch runtime/system_boot.py

Scoți:

should_freeze as restart_loop_detected


și faci:

start_info = record_start()

verifici start_info.get("crash_loop")


Verificare

grep -n "record_start\|restart_loop_detected\|should_freeze" /opt/binarybot/runtime/system_boot.py

Ținta: fără restart_loop_detected.


---

1.10 Patch monitoring/restart_guard.py

Transformi system_health în event canonic, de exemplu:

decision cu decision_kind="SYSTEM_HEALTH"


Verificare

grep -n 'system_health\|SYSTEM_HEALTH' /opt/binarybot/monitoring/restart_guard.py

Ținta: fără event_type: system_health.


---

1.11 Patch core/bot_service.py

Faci minimul critic:

path-uri pe convenția nouă

OUTCOME_SET → user_outcome

ștergi complet ramura outcome_tracker


Verificare

grep -n 'outcome_tracker\|OUTCOME_SET' /opt/binarybot/core/bot_service.py

Ținta: nimic.


---

1.12 Verificare completă Sprint 1

cd /opt/binarybot
python3 -m compileall core intelligence monitoring runtime

grep -R "SIGNAL_EVENT" core intelligence monitoring runtime
grep -R "OUTCOME_SET" core intelligence monitoring runtime
grep -R "system_health" core intelligence monitoring runtime
grep -R "log_warning({" core intelligence monitoring runtime
grep -R "outcome_tracker" core intelligence monitoring runtime

Ținta:

zero rezultate la toate



---

SPRINT 2 — UNIFICARE CONFIG / STATE

Obiectiv:

core/storage.py devine strat canonic

toate modulele principale citesc/scriu prin storage

config/settings.json și config/active_symbols.json devin surse unice

state/... devine locul unic pentru stare runtime



---

2.1 Backup local Sprint 2

cp core/storage.py core/storage.py.bak_sprint2
cp core/admin_commands.py core/admin_commands.py.bak_sprint2
cp core/bot_service.py core/bot_service.py.bak_sprint2
cp core/signal_engine.py core/signal_engine.py.bak_sprint2
cp core/distribution_router.py core/distribution_router.py.bak_sprint2
cp core/outcome_service.py core/outcome_service.py.bak_sprint2
cp core/params_loader.py core/params_loader.py.bak_sprint2


---

2.2 Patch core/storage.py

Adaugi:

CONFIG_DIR

STATE_DIR

OBSERVABILITY_DIR

ANALYTICS_DIR

ensure_dir(...)

config_path(...)

state_path(...)

load_config_json(...)

save_config_json(...)

load_state_json(...)

save_state_json(...)

migrate_json_file(...)


Verificare

grep -n 'CONFIG_DIR\|STATE_DIR\|load_config_json\|save_state_json\|migrate_json_file' /opt/binarybot/core/storage.py


---

2.3 Patch core/signal_engine.py

Treci pe:

ACTIVE_SYMBOLS_FILE = "active_symbols.json"

SETTINGS_FILE = "settings.json"


și pe:

storage.load_config_json(...)


Verificare

grep -n 'load_config_json\|ACTIVE_SYMBOLS_FILE\|SETTINGS_FILE' /opt/binarybot/core/signal_engine.py


---

2.4 Patch core/bot_service.py

Treci complet pe:

SETTINGS_FILE

ACTIVE_SYMBOLS_FILE

FOCUS_STATE_FILE

DIST_STATE_FILE

OUTCOMES_FILE


și pe:

load_config_json(...)

save_config_json(...)

load_state_json(...)

save_state_json(...)


Verificare

grep -n 'load_config_json\|save_config_json\|load_state_json\|save_state_json' /opt/binarybot/core/bot_service.py


---

2.5 Patch core/admin_commands.py

Exact aceeași trecere pe storage.

Verificare

grep -n 'load_config_json\|save_config_json' /opt/binarybot/core/admin_commands.py


---

2.6 Patch core/distribution_router.py

Treci pe:

DIST_STATE_FILE = "dist_state.json"

load_state_json(...)

save_state_json(...)


Verificare

grep -n 'DIST_STATE_FILE\|load_state_json\|save_state_json' /opt/binarybot/core/distribution_router.py


---

2.7 Patch core/outcome_service.py

Treci pe:

OUTCOMES_FILE = "outcomes.json"

load_state_json(...)

save_state_json(...)


Verificare

grep -n 'OUTCOMES_FILE\|load_state_json\|save_state_json' /opt/binarybot/core/outcome_service.py


---

2.8 Patch core/params_loader.py

Treci pe:

PARAMS_FILE = "params.json"

load_config_json(...)

save_config_json(...)


Verificare

grep -n 'PARAMS_FILE\|load_config_json\|save_config_json' /opt/binarybot/core/params_loader.py


---

2.9 Migrare fișiere reale

Creezi config/settings.json dacă lipsește

python3 - <<'PY'
import os, json
path = "/opt/binarybot/config/settings.json"
os.makedirs(os.path.dirname(path), exist_ok=True)
if not os.path.exists(path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"buffer_mode": "MEDIUM"}, f, ensure_ascii=False, indent=2)
print(path)
PY


---

Normalizezi config/active_symbols.json

python3 - <<'PY'
import json, os

config_path = "/opt/binarybot/config/active_symbols.json"
legacy_paths = [
    "/opt/binarybot/config/symbols.json",
    "/opt/binarybot/symbols.json",
    "/opt/binarybot/state/active_symbols.json",
]

data = None
if os.path.exists(config_path):
    with open(config_path, "r", encoding="utf-8") as f:
        data = json.load(f)

if data is None:
    for p in legacy_paths:
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
            break

symbols = []
if isinstance(data, dict):
    if isinstance(data.get("symbols"), list):
        symbols = [str(x).strip() for x in data["symbols"] if str(x).strip()]
    else:
        for k in ("forex", "crypto"):
            if isinstance(data.get(k), list):
                symbols.extend([str(x).strip() for x in data[k] if str(x).strip()])
elif isinstance(data, list):
    symbols = [str(x).strip() for x in data if str(x).strip()]

seen = set()
cleaned = []
for s in symbols:
    if s not in seen:
        seen.add(s)
        cleaned.append(s)

os.makedirs("/opt/binarybot/config", exist_ok=True)
with open(config_path, "w", encoding="utf-8") as f:
    json.dump({"symbols": cleaned}, f, ensure_ascii=False, indent=2, sort_keys=True)

print("normalized:", config_path, "count=", len(cleaned))
PY


---

Migrezi focus_state.json

python3 - <<'PY'
import os, json, shutil
old_path = "/opt/binarybot/focus_state.json"
new_path = "/opt/binarybot/state/focus_state.json"
os.makedirs("/opt/binarybot/state", exist_ok=True)

if os.path.exists(new_path):
    print("already exists:", new_path)
elif os.path.exists(old_path):
    shutil.copy2(old_path, new_path)
    print("copied:", old_path, "->", new_path)
else:
    with open(new_path, "w", encoding="utf-8") as f:
        json.dump({}, f, ensure_ascii=False, indent=2)
    print("created empty:", new_path)
PY


---

Normalizezi outcomes.json

python3 - <<'PY'
import os, json

candidates = [
    "/opt/binarybot/state/outcomes.json",
    "/opt/binarybot/outcomes.json",
]

target = "/opt/binarybot/state/outcomes.json"
os.makedirs("/opt/binarybot/state", exist_ok=True)

for p in candidates:
    if os.path.exists(p):
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
        with open(target, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, sort_keys=True)
        print("normalized from:", p)
        break
else:
    with open(target, "w", encoding="utf-8") as f:
        json.dump({}, f, ensure_ascii=False, indent=2, sort_keys=True)
    print("created empty:", target)
PY


---

2.10 Verificare completă Sprint 2

cd /opt/binarybot
python3 -m compileall core intelligence monitoring runtime

grep -R '"/opt/binarybot/settings.json"' core intelligence monitoring runtime
grep -R '"/opt/binarybot/symbols.json"' core intelligence monitoring runtime
grep -R '"/opt/binarybot/focus_state.json"' core intelligence monitoring runtime
grep -R "load_config_json\|save_config_json\|load_state_json\|save_state_json" core intelligence monitoring runtime


---

SPRINT 3 — SPARGERE bot_service.py + OBSERVABILITY SCHEMA

Obiectiv:

bot_service.py devine orchestrator

callback-urile și comenzile se separă

outcome flow se separă

schema de evenimente devine oficială



---

3.1 Backup local Sprint 3

cp core/bot_service.py core/bot_service.py.bak_sprint3
cp core/observability_logger.py core/observability_logger.py.bak_sprint3
cp core/outcome_service.py core/outcome_service.py.bak_sprint3
cp schema/event_schema.json schema/event_schema.json.bak_sprint3


---

3.2 Creezi fișierul core/admin_state_helpers.py

Conținutul este cel definit în Sprint 3.

Verificare

ls -l /opt/binarybot/core/admin_state_helpers.py
python3 -m py_compile /opt/binarybot/core/admin_state_helpers.py


---

3.3 Creezi fișierul core/outcome_handlers.py

Conținutul este cel definit în Sprint 3.

Verificare

ls -l /opt/binarybot/core/outcome_handlers.py
python3 -m py_compile /opt/binarybot/core/outcome_handlers.py


---

3.4 Creezi fișierul core/callback_handlers.py

Conținutul este cel definit în Sprint 3.

Verificare

ls -l /opt/binarybot/core/callback_handlers.py
python3 -m py_compile /opt/binarybot/core/callback_handlers.py


---

3.5 Creezi fișierul core/command_router.py

Conținutul este cel definit în Sprint 3.

Verificare

ls -l /opt/binarybot/core/command_router.py
python3 -m py_compile /opt/binarybot/core/command_router.py


---

3.6 Patch core/bot_service.py

Faci:

import route_text_command

import route_callback

ștergi helperii locali de settings/symbols/outcome

ștergi ramura outcome_tracker

înlocuiești handle_callback(...)

simplifici process_update(...)


Verificare

grep -n "_load_settings\|_save_settings\|_load_active_symbols\|_save_active_symbols\|_record_outcome" /opt/binarybot/core/bot_service.py
grep -n 'outcome_tracker' /opt/binarybot/core/bot_service.py
grep -n 'route_text_command\|route_callback' /opt/binarybot/core/bot_service.py

Ținta:

zero la primele două

importuri și apeluri pentru route_text_command și route_callback



---

3.7 Patch core/outcome_service.py

Adaugi interfața publică:

register_vote(callback_data=..., user_id=..., chat_id=...)


și normalizezi return-ul către dict.

Verificare

grep -n "def register_vote" /opt/binarybot/core/outcome_service.py


---

3.8 Patch core/observability_logger.py

Adaugi:

EVENT_SCHEMA_VERSION = "2.0"

validare source

validare data

current_event_schema_meta()


Verificare

grep -n 'EVENT_SCHEMA_VERSION\|current_event_schema_meta' /opt/binarybot/core/observability_logger.py


---

3.9 Înlocuiești schema/event_schema.json

Pui schema envelope v2 exact cum a fost definită.

Verificare

cat /opt/binarybot/schema/event_schema.json


---

3.10 Creezi docs/OBSERVABILITY_EVENT_ENVELOPE_SPEC.md

Conținutul exact din Sprint 3.

Verificare

ls -l /opt/binarybot/docs/OBSERVABILITY_EVENT_ENVELOPE_SPEC.md


---

3.11 Verificare completă Sprint 3

cd /opt/binarybot
python3 -m compileall core intelligence monitoring runtime

grep -R "outcome_tracker" core
grep -R "_record_outcome" core/bot_service.py
grep -R 'startswith("VOTE_' core/bot_service.py
grep -R 'startswith("SET_OUTCOME|' core/bot_service.py

Ținta:

fără logică duplicată în bot_service.py



---

SPRINT 4 — CLEANUP REPO + DOCS GOVERNANCE

Obiectiv:

repo curat

documentație sinceră și aliniată la codul real

status pe documente

matrice doc ↔ cod ↔ status



---

4.1 Backup local Sprint 4

cp docs/ARCHITECTURE_CODE_MAPPING.md docs/ARCHITECTURE_CODE_MAPPING.md.bak_sprint4 2>/dev/null || true
cp docs/BINARYBOT_MASTER_INDEX.md docs/BINARYBOT_MASTER_INDEX.md.bak_sprint4 2>/dev/null || true
cp docs/SYSTEM_ARCHITECTURE_MAP.md docs/SYSTEM_ARCHITECTURE_MAP.md.bak_sprint4 2>/dev/null || true
cp docs/MODULE_INTERFACE_SPEC_v2.0.0.md docs/MODULE_INTERFACE_SPEC_v2.0.0.md.bak_sprint4 2>/dev/null || true


---

4.2 Creezi arhiva internă pentru legacy

mkdir -p /opt/binarybot/_archive/legacy_core
mkdir -p /opt/binarybot/_archive/legacy_docs
mkdir -p /opt/binarybot/_archive/legacy_misc


---

4.3 Muți backup-urile și copiile moarte din core/

find /opt/binarybot/core -maxdepth 1 \( -name "*.bak*" -o -name "*Copy*" -o -name "* - Copy.py" \) -print
find /opt/binarybot/core -maxdepth 1 \( -name "*.bak*" -o -name "*Copy*" -o -name "* - Copy.py" \) -exec mv {} /opt/binarybot/_archive/legacy_core/ \;


---

4.4 Muți backup-urile și copiile moarte din docs/

find /opt/binarybot/docs -maxdepth 1 \( -name "*.bak*" -o -name "*Copy*" \) -print
find /opt/binarybot/docs -maxdepth 1 \( -name "*.bak*" -o -name "*Copy*" \) -exec mv {} /opt/binarybot/_archive/legacy_docs/ \;


---

4.5 Creezi docs/DOCUMENT_STATUS_POLICY.md

Conținutul exact din Sprint 4.

Verificare

ls -l /opt/binarybot/docs/DOCUMENT_STATUS_POLICY.md


---

4.6 Creezi docs/DOCUMENT_IMPLEMENTATION_MATRIX.md

Conținutul exact din Sprint 4.

Verificare

ls -l /opt/binarybot/docs/DOCUMENT_IMPLEMENTATION_MATRIX.md


---

4.7 Rescrii docs/ARCHITECTURE_CODE_MAPPING.md

Pui conținutul exact din Sprint 4.

Verificare

grep -n "^## Status" /opt/binarybot/docs/ARCHITECTURE_CODE_MAPPING.md


---

4.8 Rescrii docs/BINARYBOT_MASTER_INDEX.md

Pui conținutul exact din Sprint 4.

Verificare

grep -n "^## Status" /opt/binarybot/docs/BINARYBOT_MASTER_INDEX.md


---

4.9 Normalizezi docs/SYSTEM_ARCHITECTURE_MAP.md

Adaugi:

## Status

reguli clare implemented / partial / planned

înlocuiești referințele false la docs lipsă


Verificare

grep -n "^## Status" /opt/binarybot/docs/SYSTEM_ARCHITECTURE_MAP.md


---

4.10 Normalizezi docs/MODULE_INTERFACE_SPEC_v2.0.0.md

Adaugi:

## Status

Candle Ordering Contract

Config and State Contract

Telegram Routing Contract


Verificare

grep -n "^## Status\|Candle Ordering Contract\|Config and State Contract\|Telegram Routing Contract" /opt/binarybot/docs/MODULE_INTERFACE_SPEC_v2.0.0.md


---

4.11 Normalizezi docs/DECISION_AUDIT_SPEC_v2.0.0.md

Adaugi:

## Status

Current implementation status


Verificare

grep -n "^## Status\|Current implementation status" /opt/binarybot/docs/DECISION_AUDIT_SPEC_v2.0.0.md


---

4.12 Normalizezi docs/OBSERVABILITY_LOGGING_SPEC_v2.0.0.md

Adaugi:

## Status

referință către event envelope spec și schema reală


Verificare

grep -n "^## Status\|Canonical envelope reference" /opt/binarybot/docs/OBSERVABILITY_LOGGING_SPEC_v2.0.0.md


---

4.13 Normalizezi docs/OUTCOME_TRACKING_SPEC_v2.0.0.md

Adaugi:

## Status

Current routing implementation


Verificare

grep -n "^## Status\|Current routing implementation" /opt/binarybot/docs/OUTCOME_TRACKING_SPEC_v2.0.0.md


---

4.14 Normalizezi docs/TELEGRAM_UX_v2.0.0.md

Adaugi:

## Status

Active routing architecture


Verificare

grep -n "^## Status\|Active routing architecture" /opt/binarybot/docs/TELEGRAM_UX_v2.0.0.md


---

4.15 Verificare docs lipsă referite

python3 - <<'PY'
import os, re

docs_dir = "/opt/binarybot/docs"
existing = set(os.listdir(docs_dir))
refs = {}

for fn in os.listdir(docs_dir):
    if not fn.endswith(".md"):
        continue
    path = os.path.join(docs_dir, fn)
    with open(path, "r", encoding="utf-8") as f:
        txt = f.read()
    found = re.findall(r'`([^`]+\.md)`', txt)
    refs[fn] = found

missing = []
for fn, found in refs.items():
    for ref in found:
        base = os.path.basename(ref)
        if base not in existing:
            missing.append((fn, ref))

for src, ref in sorted(missing):
    print(f"{src} -> MISSING: {ref}")
PY

Ținta:

zero sau doar referințe marcate explicit ca planned standalone spec



---

4.16 Verificare status în docs

python3 - <<'PY'
import os, re

docs_dir = "/opt/binarybot/docs"
for fn in sorted(os.listdir(docs_dir)):
    if not fn.endswith(".md"):
        continue
    path = os.path.join(docs_dir, fn)
    with open(path, "r", encoding="utf-8") as f:
        txt = f.read()
    ok = bool(re.search(r'^## Status\s*$', txt, flags=re.MULTILINE))
    print(f"{fn}: {'OK' if ok else 'MISSING_STATUS'}")
PY


---

FAZA FINALĂ — VERIFICARE GLOBALĂ

5.1 Compile final

cd /opt/binarybot
python3 -m compileall core intelligence monitoring runtime


---

5.2 Verificare repo curat
Bash
Copiază codul
find /opt/binarybot/core -maxdepth 1 \( -name "*.bak*" -o -name "*Copy*" -o -name "* - Copy.py" \)
find /opt/binarybot/docs -maxdepth 1 \( -name "*.bak*" -o -name "*Copy*" \)
Ținta: nimic.
5.3 Verificare config/state finale
Bash
Copiază codul
cat /opt/binarybot/config/settings.json
cat /opt/binarybot/config/active_symbols.json
cat /opt/binarybot/state/focus_state.json
cat /opt/binarybot/state/dist_state.json
cat /opt/binarybot/state/outcomes.json
5.4 Verificare routing nou
Bash
Copiază codul
ls -l /opt/binarybot/core/command_router.py
ls -l /opt/binarybot/core/callback_handlers.py
ls -l /opt/binarybot/core/outcome_handlers.py
ls -l /opt/binarybot/core/admin_state_helpers.py
5.5 Verificare observability finală
Bash
Copiază codul
tail -n 20 /opt/binarybot/observability/error_events.jsonl
tail -n 20 /opt/binarybot/observability/engine_events.jsonl
tail -n 20 /opt/binarybot/observability/outcome_events.jsonl 2>/dev/null || true
Ce vrei să NU mai vezi:
observability_log_failed
invalid event_type
unexpected keyword argument 'module'
import error pentru outcome_tracker
ORDINEA SCURTĂ, PE O SINGURĂ PAGINĂ
Etapa 1
Rulezi backup general.
Etapa 2
Aplici Sprint 1:
strategy_v2.py
candle_adapter.py
signal_engine.py
distribution_router.py
observability_logger.py
outcome_service.py
risk_monitor.py
system_boot.py
restart_guard.py
bot_service.py
Etapa 3
Verifici compile + grep checks.
Etapa 4
Aplici Sprint 2:
storage.py
signal_engine.py
bot_service.py
admin_commands.py
distribution_router.py
outcome_service.py
params_loader.py
migrare fișiere reale
Etapa 5
Verifici compile + config/state checks.
Etapa 6
Aplici Sprint 3:
creezi admin_state_helpers.py
creezi outcome_handlers.py
creezi callback_handlers.py
creezi command_router.py
cureți bot_service.py
normalizezi outcome_service.py
oficializezi observability_logger.py
înlocuiești schema/event_schema.json
creezi OBSERVABILITY_EVENT_ENVELOPE_SPEC.md
Etapa 7
Verifici compile + routing checks.
Etapa 8
Aplici Sprint 4:
cureți .bak și Copy
creezi DOCUMENT_STATUS_POLICY.md
creezi DOCUMENT_IMPLEMENTATION_MATRIX.md
rescrii docs canonice mari
rulezi verificarea de docs lipsă și status
Etapa 9
Verificare finală globală.
CRITERIUL DE SUCCES
Playbook-ul este executat corect când:
botul compilează fără erori
nu mai există ramuri moarte de outcome
config și state sunt separate clar
event schema oficială corespunde loggerului real
bot_service.py este doar orchestrator
documentația nu mai pretinde lucruri inexistente
repo-ul activ nu mai e plin de backup-uri moarte
Dacă vrei, în pasul următor pot să transform acest playbook într-un document canonic gata de lipit în repo, de tip docs/MASTER_REMEDIATION_PLAYBOOK.md, scris complet curat, ca document oficial de execuție.

## Non-Canonical Usage Note

This document is retained as a supporting/satellite reference only. It must not be treated as active canonical truth. Where conflict exists, active canonical documents in /opt/binarybot/docs/canonical/active/ take precedence.
