BINARYBOT — CONTROL PANEL HIERARCHY AND INTELLIGENCE SPECIFICATION

Version: 1.0
Status: CANONICAL SPECIFICATION
Location: /opt/binarybot/docs/CONTROL_PANEL_HIERARCHY_AND_INTELLIGENCE_SPEC.md


------------------------------------------------------------
1. PURPOSE
------------------------------------------------------------

Acest document definește arhitectura completă a panoului de control BinaryBot.

Panoul de control este sistemul prin care operatorii umani pot:

- monitoriza sistemul
- controla strategia
- controla distribuția semnalelor
- analiza performanța
- executa operațiuni administrative
- gestiona programul de afiliere
- accesa sistemele de research și AI intelligence

Panoul este proiectat ca un sistem ierarhic cu control strict al accesului
(Role Based Access Control - RBAC) și cu separare clară între niveluri
operaționale, comerciale și de cercetare.

Acest panou devine centrul de control al întregului ecosistem BinaryBot.

Subsystemele controlate prin acest panou includ:

- Signal Engine
- Strategy Configuration
- Channel Distribution
- Observability
- Strategy Intelligence System
- Research Tools
- Affiliate Program


------------------------------------------------------------
2. CONTROL PANEL ARCHITECTURE
------------------------------------------------------------

Panoul de control este structurat pe două axe principale:

AXA 1 — CONTROL HIERARCHY (Cine are voie să controleze)
AXA 2 — INTELLIGENCE LAYER (Ce informații sunt disponibile)

Structura completă este:

CONTROL PANEL

    ├── Owner Layer
    │
    ├── Primary Admin Layer
    │
    ├── Functional Admin Layer
    │     ├── Strategy Admin
    │     ├── Operations Admin
    │     ├── Risk Admin
    │     ├── Channel Admin
    │     └── Research Admin
    │
    ├── Affiliate / Influencer Layer
    │
    └── Intelligence Layer
          ├── Strategy Intelligence
          ├── Signal Debug Dashboard
          └── Research Analytics


------------------------------------------------------------
3. ROLE HIERARCHY
------------------------------------------------------------

BinaryBot utilizează un sistem ierarhic de roluri.

Rolurile sunt definite strict și fiecare rol are limite de acces clare.

ROLURI:

OWNER
PRIMARY_ADMIN
FUNCTIONAL_ADMIN
ANALYST
MODERATOR
AFFILIATE_ADMIN


------------------------------------------------------------
4. OWNER ROLE
------------------------------------------------------------

OWNER este nivelul suprem de control.

Acest rol este rezervat creatorului și proprietarului sistemului.

OWNER are acces nelimitat la:

- toate configurările strategiei
- toate configurările operaționale
- toate datele analitice
- toate datele comerciale
- toate sistemele AI
- toate canalele
- toate logurile
- toate operațiunile administrative

OWNER poate:

- modifica strategia
- modifica pragurile
- modifica buffer SR
- modifica filtrele spike
- modifica simbolurile
- modifica distribuția canalelor
- modifica parametrii AI
- modifica rolurile utilizatorilor
- crea sau șterge admini
- crea sau șterge afiliați
- accesa toate datele comerciale

OWNER poate opri sau porni întregul sistem.


------------------------------------------------------------
5. PRIMARY ADMIN ROLE
------------------------------------------------------------

PRIMARY_ADMIN este administratorul operațional principal.

Acest rol operează sistemul în mod curent.

PRIMARY_ADMIN are acces la:

- control strategie
- control canale
- control distribuție
- control simboluri
- control parametri
- analytics operaționale

PRIMARY_ADMIN NU poate:

- modifica OWNER
- accesa comisioanele afiliaților
- modifica structura RBAC
- modifica sistemele AI interne


------------------------------------------------------------
6. FUNCTIONAL ADMIN LAYER
------------------------------------------------------------

Adminii funcționali sunt specializați pe domenii.

Tipuri de Functional Admin:

STRATEGY_ADMIN
OPERATIONS_ADMIN
RISK_ADMIN
CHANNEL_ADMIN
RESEARCH_ADMIN


------------------------------------------------------------
6.1 STRATEGY ADMIN
------------------------------------------------------------

STRATEGY_ADMIN poate controla parametrii strategiei.

Acces:

- thresholds
- SR buffer
- spike filter
- indicator weights
- signal scoring

Comenzi:

/strategy
/thresholds
/sr
/spike


------------------------------------------------------------
6.2 OPERATIONS ADMIN
------------------------------------------------------------

Responsabil pentru funcționarea sistemului.

Acces:

- system status
- restart engine
- monitoring
- logs

Comenzi:

/status
/system
/restart


------------------------------------------------------------
6.3 RISK ADMIN
------------------------------------------------------------

Responsabil pentru controlul riscului.

Acces:

- daily limits
- cooldown states
- silent tiers


------------------------------------------------------------
6.4 CHANNEL ADMIN
------------------------------------------------------------

Responsabil pentru distribuția semnalelor.

Acces:

- channel config
- tier routing
- publish scheduler


------------------------------------------------------------
6.5 RESEARCH ADMIN
------------------------------------------------------------

Responsabil pentru analiză și cercetare.

Acces:

- strategy reports
- analytics
- signal history
- AI auditor


------------------------------------------------------------
7. AFFILIATE / INFLUENCER ADMIN LAYER
------------------------------------------------------------

Acest layer este destinat influencerilor sau partenerilor
care aduc utilizatori în sistem.

Aceștia nu sunt admini tehnici.

Rolul lor este comercial.

AFFILIATE_ADMIN are acces doar la datele propriei rețele.


------------------------------------------------------------
7.1 Affiliate Permissions
------------------------------------------------------------

Affiliate poate vedea:

- utilizatorii aduși de el
- numărul de utilizatori activi
- conversii
- retenție
- comisioane generate

Affiliate NU poate vedea:

- utilizatorii altor afiliați
- strategia internă
- parametrii sistemului
- loguri interne
- analytics globale


------------------------------------------------------------
7.2 Affiliate Dashboard
------------------------------------------------------------

Affiliate Dashboard include:

MY_REFERRALS
MY_ACTIVE_USERS
MY_CHANNEL_MEMBERS
MY_CONVERSIONS
MY_COMMISSION


------------------------------------------------------------
8. INTELLIGENCE LAYER
------------------------------------------------------------

Intelligence Layer oferă informații analitice despre sistem.

Acest layer include subsistemul:

Strategy Intelligence System


------------------------------------------------------------
8.1 Strategy Heatmap
------------------------------------------------------------

Analizează deciziile strategiei.

Exemplu rezultate:

SR too tight
RSI filter too strict
trend filter too aggressive


------------------------------------------------------------
8.2 Signal Debug Dashboard
------------------------------------------------------------

Permite operatorilor să vadă exact de ce un semnal a fost respins.

Exemplu:

PAIR: EURAUD
TREND: WITH_TREND
SCORE: 66.5
REASON: SR_SPACE_INSUFFICIENT


------------------------------------------------------------
8.3 AI Strategy Auditor
------------------------------------------------------------

Generează rapoarte zilnice automate despre performanța strategiei.


------------------------------------------------------------
9. TELEGRAM CONTROL INTERFACE
------------------------------------------------------------

Panoul de control este expus prin Telegram.

Comenzi principale:

/admin
/status
/strategy
/symbols
/thresholds
/sr
/spike
/research


------------------------------------------------------------
10. SECURITY MODEL
------------------------------------------------------------

Toate acțiunile administrative trebuie să genereze loguri.

Log event type:

admin_change

Fiecare schimbare trebuie să includă:

user_id
role
timestamp
action
old_value
new_value


------------------------------------------------------------
11. AUDIT TRAIL
------------------------------------------------------------

Toate operațiunile administrative sunt înregistrate.

Log location:

/opt/binarybot/observability/admin_events.jsonl


------------------------------------------------------------
12. FUTURE EXTENSIONS
------------------------------------------------------------

Extensii planificate:

- AI Strategy Optimizer
- Automated Parameter Tuning
- Affiliate Performance AI
- Autonomous Research Assistant


------------------------------------------------------------
13. CONCLUSION
------------------------------------------------------------

CONTROL PANEL este centrul de comandă al BinaryBot.

Acesta permite:

- control operațional
- control strategie
- monitorizare
- analiză
- operare comercială

Panoul este proiectat să permită evoluția sistemului către
un sistem autonom de trading bazat pe inteligență artificială.

END OF DOCUMENT