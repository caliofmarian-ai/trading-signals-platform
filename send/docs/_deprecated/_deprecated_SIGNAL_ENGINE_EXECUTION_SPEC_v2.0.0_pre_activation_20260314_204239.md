BINARYBOT CANONICAL SPECIFICATION

SIGNAL ENGINE EXECUTION SPEC

Version: 2.0.0
Status: Canonical
Scope: Signal Engine / Signal Delivery Layer

Dependencies:

- STRATEGY_ENGINE_ARCHITECTURE_MAP_v1.0.0.md
- DECISION_OBJECT_CANONICAL_SPEC_v1.0.0.md
- FSM_DECISION_ENGINE_SPEC_v1.0.0.md
- ALGO_SPEC_v2.0.0.md

Supersedes:

- SIGNAL_ENGINE_SPEC.md (legacy versions)

---

1. PURPOSE OF THIS DOCUMENT

Acest document definește Signal Engine, componenta responsabilă de livrarea semnalelor către utilizatori.

Signal Engine nu face calcule strategice.

Responsabilitatea sa este exclusiv:

interpret DecisionObject
format signal message
deliver signal

---

2. POSITION IN STRATEGY PIPELINE

Signal Engine se află la finalul pipeline-ului strategiei.

Pipeline-ul complet:

MARKET DATA
      ↓
MARKET MODEL
      ↓
TIME MODEL
      ↓
CORRIDOR ENGINE
      ↓
SCORING MODEL
      ↓
DECISION OBJECT
      ↓
FSM DECISION ENGINE
      ↓
SIGNAL ENGINE
      ↓
USER DELIVERY

Signal Engine consumă rezultatul final al strategiei.

---

3. SIGNAL ENGINE INPUT

Inputul principal este:

DecisionObject

Structura obiectului este definită în:

DECISION_OBJECT_CANONICAL_SPEC_v1.0.0.md

---

4. DECISION OBJECT FIELDS USED

Signal Engine utilizează următoarele câmpuri:

decision_state
execution_parameters
market_context
identity
observability

În special:

execution_parameters

care conțin informațiile necesare execuției.

---

5. SIGNAL STATES

Signal Engine reacționează la stările FSM:

PRE
CONFIRM
OPEN_NOW

Stările:

NO_SIGNAL
REJECT

nu generează mesaje către utilizator.

---

6. PRE STATE HANDLING

În starea PRE:

Signal Engine poate livra alertă de pregătire.

Mesajul poate conține:

symbol
direction
setup detected
market context

PRE nu conține expiry.

Scopul acestei stări este informarea utilizatorului despre posibilul setup.

---

7. CONFIRM STATE HANDLING

În starea CONFIRM se livrează semnalul confirmat.

Signal Engine utilizează:

confirm_expiry_min_minutes
confirm_expiry_max_minutes

Aceste valori provin din:

DecisionObject.execution_parameters

Mesajul transmis utilizatorului include:

symbol
direction
entry_context
expiry_range
confidence

---

8. OPEN_NOW STATE HANDLING

În starea OPEN_NOW se livrează semnalul executabil imediat.

Signal Engine utilizează:

open_now_expiry_minutes

Această valoare poate fi:

fractional value

și trebuie transmisă exact utilizatorului.

Mesajul include:

symbol
direction
entry instruction
exact expiry
confidence level

---

9. MESSAGE FORMATTING

Signal Engine este responsabil de formatarea mesajului pentru platforma de livrare.

Acesta poate include:

text formatting
icons
labels
visual markers

Dar nu modifică valorile strategiei.

---

10. SIGNAL DELIVERY CHANNELS

Signal Engine poate livra semnale prin:

telegram
web interface
api
dashboard

Indiferent de canal, conținutul deciziei trebuie să rămână identic.

---

11. SIGNAL ENGINE RESTRICTIONS

Signal Engine nu are voie să recalculze:

expiry
score
corridor width
model_time_reach_ratio

Signal Engine nu modifică DecisionObject.

El doar interpretează rezultatul strategiei.

---

12. ERROR HANDLING

Dacă DecisionObject conține inconsistențe:

execution parameters missing
expiry range invalid
state mismatch

Signal Engine trebuie să înregistreze eroarea și să blocheze livrarea.

---

13. OBSERVABILITY

Signal Engine trebuie să înregistreze:

DecisionObject identity
signal_state
delivery timestamp
execution parameters
delivery channel

Aceste informații sunt utilizate pentru:

performance monitoring
delivery diagnostics
signal tracking

---

14. RESPONSIBILITY BOUNDARY

Separarea responsabilităților este:

Strategy Engine
→ produce DecisionObject

FSM Decision Engine
→ decide state transition

Signal Engine
→ livrează semnalul

---

15. FINAL PRINCIPLE

Signal Engine este un layer de livrare, nu un layer strategic.

Principiul fundamental este:

DecisionObject
→ interpret
→ deliver

Această separare garantează:

strategy integrity
consistent signal delivery
clear architecture boundaries