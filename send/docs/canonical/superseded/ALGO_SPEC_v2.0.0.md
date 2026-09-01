# ALGO_SPEC_v2.0.0


Path: /opt/binarybot/docs/canonical/active/ALGO_SPEC_v2.0.0.md  
Version: 2.0.0  
Status: Canonical Active Strategy Specification  
Owner: BinaryBot / DROPi Signals  
Scope: Strategic market model, corridor-first decision pipeline, scoring semantics, DecisionObject production contract  

Linked Documents:
- /opt/binarybot/docs/canonical/active/CANONICAL_STRATEGY_STACK_v1.0.0.md
- /opt/binarybot/docs/canonical/active/TIME_MODEL_UNIFIED_CANON_v2.0.0.md
- /opt/binarybot/docs/canonical/active/SR_CORRIDOR_ENGINE_SPEC_v2.0.0.md
- /opt/binarybot/docs/canonical/active/DECISION_OBJECT_CANONICAL_SPEC_v1.0.0.md
- /opt/binarybot/docs/canonical/active/FSM_DECISION_ENGINE_SPEC_v1.0.0.md
- /opt/binarybot/docs/canonical/active/SIGNAL_ENGINE_EXECUTION_SPEC_v2.0.0.md
- /opt/binarybot/docs/canonical/active/OBSERVABILITY_SPEC_v2.0.0.md


Depends on:
- canonical/active/CANONICAL_STRATEGY_STACK_v1.0.0.md
- canonical/active/TIME_MODEL_UNIFIED_CANON_v2.0.0.md
- canonical/active/SR_CORRIDOR_ENGINE_SPEC_v2.0.0.md
- canonical/active/DECISION_OBJECT_CANONICAL_SPEC_v1.0.0.md
- canonical/active/FSM_DECISION_ENGINE_SPEC_v1.0.0.md
- canonical/active/SIGNAL_ENGINE_EXECUTION_SPEC_v2.0.0.md
- canonical/active/OBSERVABILITY_SPEC_v2.0.0.md

---

## 1. PURPOSE

Acest document definește specificația canonică a modelului strategic principal din BinaryBot.

El descrie:
- cum este interpretată starea pieței
- cum este identificat corridorul structural relevant
- cum se combină modelul structural cu modelul temporal
- cum se formează scorul strategic
- cum este produs `DecisionObject`
- cum se separă matematica strategiei de decizia operațională FSM

Acest document nu definește în detaliu toate formulele time model.
Acele formule sunt autoritative în:
`canonical/active/TIME_MODEL_UNIFIED_CANON_v2.0.0.md`

Acest document nu definește în detaliu toate stările FSM.
Acele reguli sunt autoritative în:
`canonical/active/FSM_DECISION_ENGINE_SPEC_v1.0.0.md`

---

## 2. CORE ARCHITECTURAL PRINCIPLE

Strategia BinaryBot este corridor-first și DecisionObject-first.

Asta înseamnă:

1. mai întâi se stabilește contextul de piață
2. apoi se identifică structura SR / corridor relevantă
3. apoi se evaluează fezabilitatea temporală în interiorul structurii
4. apoi se calculează scorul setup-ului
5. apoi se produce `DecisionObject`
6. abia după aceea FSM-ul decide semnificația operațională
7. semnalul este emis numai după layerul FSM

Acest principiu este blocat canonic.

---

## 3. OFFICIAL PIPELINE

Pipeline-ul oficial este:

```text
MARKET DATA
   ↓
MARKET MODEL
   ↓
SR / CORRIDOR ENGINE
   ↓
TIME MODEL
   ↓
SCORING MODEL
   ↓
DECISION OBJECT
   ↓
FSM DECISION
   ↓
SIGNAL ENGINE
```

Ordinea aceasta este obligatorie.

Sunt interzise explicit următoarele inversări:
- Time Model înainte de Corridor Engine
- FSM înainte de `DecisionObject`
- Signal emission direct din strategy output necontractat
- folosirea exclusivă a `expiry_minutes` drept adevăr final

---

## 4. STRATEGIC RESPONSIBILITY OF THIS SPEC

Acest document este autoritar pentru:
- market model inputs
- context derivation
- structure-first interpretation
- scoring semantics
- strategic gating înainte de FSM
- producerea contractului `DecisionObject`

Acest document nu este autoritar unic pentru:
- matematica detaliată a timpului
- stările FSM
- execuția de semnal
- formatul complet de observability

---

## 5. MARKET MODEL INPUTS

Strategia operează asupra unui set de inputuri de piață extrase din runtime.

Inputurile pot include, dar nu sunt limitate la:
- latest price
- candle context
- support levels
- resistance levels
- local structure landmarks
- volatility indicators
- trend indicators
- momentum indicators
- distance to nearest structural target
- buffer distance
- market noise / instability markers

Aceste inputuri sunt transformate în parametri operaționali, nu folosite brut.

---

## 6. MARKET CONTEXT DERIVATION

Layerul market model trebuie să derive cel puțin următoarele concepte:

- `price_speed`
- `buffer_distance`
- `trend_context`
- `volatility_state`
- `structure_context`
- `target_distance_context`
- `noise_context`

Aceste concepte sunt folosite pentru a interpreta fezabilitatea setup-ului.

Regula canonică:
nu există decizie strategică validă fără context, structură și timp.

---

## 7. SR / CORRIDOR FIRST PRINCIPLE

Înainte de orice concluzie temporală, strategia trebuie să identifice corridorul relevant.

Asta înseamnă:
- localizarea setup-ului în raport cu suporturi și rezistențe
- identificarea țintei structurale celei mai relevante
- măsurarea distanței utile de deplasare
- validarea că există o geometrie de piață coerentă

Fără corridor relevant:
- nu există setup strategic valid
- time model nu trebuie interpretat izolat
- scorul final trebuie degradat sau setup-ul respins

Detaliile structurale normative sunt definite în:
`canonical/active/SR_CORRIDOR_ENGINE_SPEC_v2.0.0.md`

---

## 8. TIME MODEL INTEGRATION

După ce corridorul a fost stabilit, strategia trebuie să integreze time modelul unificat.

Conceptele canonice obligatorii sunt:
- `t_needed`
- `t_needed_adjusted`
- `model_expiry`
- `model_time_reach_ratio`
- `corridor_time_pressure`
- `time_state`

Acest document consumă aceste concepte.
Nu le redefinește matematic.

Matematica autoritară este în:
`canonical/active/TIME_MODEL_UNIFIED_CANON_v2.0.0.md`

Sunt interzise ca termeni canonici primari:
- `expiry_reach_ratio`
- `buffer_price` ca substitut al `buffer_distance`
- `expiry_minutes` ca verdict suficient în sine

---

## 9. TIME-STRUCTURE INTERPRETATION RULE

Time modelul nu este interpretat izolat de structură.

Interpretarea corectă este:
- întâi există corridor valid
- apoi se calculează fezabilitatea temporală în raport cu acel corridor
- apoi se derivă presiunea de timp
- apoi aceste rezultate intră în scor

Aceasta este regula canonică:
**corridor first, time second, score third**.

---

## 10. SCORING MODEL ROLE

Scoring modelul agregă informația strategică și produce o evaluare sintetică a setup-ului.

Scorul trebuie să reflecte:
- calitatea contextului de piață
- claritatea structurii
- fezabilitatea temporală
- riscul de instabilitate
- apropierea de ținta structurală relevantă
- coerența totală a setup-ului

Scorul nu este singurul adevăr final.
Dar scorul este mecanismul principal de agregare strategică înainte de `DecisionObject`.

---

## 11. REQUIRED SCORE COMPONENT FAMILIES

Familiile minime de componente de scor trebuie să acopere:

- context / trend quality
- structure / corridor quality
- time feasibility quality
- volatility / instability penalty
- target realism
- buffer realism
- confidence synthesis

Numele exacte ale subcomponentelor pot evolua,
dar aceste familii conceptuale trebuie să rămână recognoscibile.

---

## 12. STRATEGIC GATING BEFORE DECISIONOBJECT

Înainte de producerea `DecisionObject`, strategia trebuie să aplice gating strategic.

Asta poate include:
- lipsa unei structuri valide
- lipsa unei ținte structurale relevante
- infezabilitate temporală severă
- instabilitate excesivă
- contradicții între context, structură și timp

Dacă gatingul strategic eșuează:
- setup-ul poate fi respins înainte de FSM
sau
- poate fi produs un `DecisionObject` explicit degradat / rejectable, conform contractului oficial

Detaliul formatului este definit de:
`canonical/active/DECISION_OBJECT_CANONICAL_SPEC_v1.0.0.md`

---

## 13. DECISIONOBJECT PRODUCTION CONTRACT

Outputul strategic oficial nu este un dict legacy informal.

Outputul strategic oficial este `DecisionObject`.

`DecisionObject` trebuie produs:
- după corridor
- după time model
- după scoring
- înainte de FSM

Acest adevăr este blocat canonic.

`DecisionObject` trebuie să conțină suficient context pentru:
- a explica starea strategică
- a permite FSM-ului să facă decizia operațională
- a alimenta observability și rejection audit

Detaliile contractului sunt autoritare în:
`canonical/active/DECISION_OBJECT_CANONICAL_SPEC_v1.0.0.md`

---

## 14. RELATION TO FSM

FSM-ul nu produce adevărul matematic strategic.

FSM-ul consumă adevărul strategic standardizat prin `DecisionObject`
și îl transformă în semnificație operațională.

Separarea canonică este:
- strategia produce
- FSM interpretează operațional
- signal engine execută

Această separare este obligatorie pentru auditabilitate.

---

## 15. REQUIRED STRATEGIC STATES OR OUTCOMES

La nivel strategic, înainte de FSM, sistemul trebuie să poată distinge cel puțin:

- setup structural valid
- setup structural slab
- setup temporal fezabil
- setup temporal tensionat
- setup temporal infezabil
- score puternic
- score marginal
- reject strategic

Acestea nu sunt neapărat stările finale FSM,
dar trebuie să existe semantic în layerul strategic sau în `DecisionObject`.

---

## 16. FORBIDDEN LEGACY PATTERNS

Sunt interzise ca modele canonice active:

- strategy output direct în format legacy dict fără contract `DecisionObject`
- time-first interpretation fără corridor
- decizie finală bazată doar pe expiry
- amestecarea scoringului strategic cu stările FSM într-un singur pas opac
- semnal emis direct din layerul matematic fără intermediere FSM

Aceste pattern-uri pot exista doar în:
- compat layer temporar
- documente de migrare
- secțiuni istorice / deprecated

---

## 17. MINIMUM EXPLANATION REQUIREMENT

Orice decizie strategică importantă trebuie să poată fi explicată prin minimum:

- context
- structure
- time
- score
- decision contract result

Dacă sistemul nu poate explica una dintre aceste dimensiuni,
atunci observability este incompletă.

Acest principiu leagă strategia de audit și observability.

---

## 18. OBSERVABILITY RELATION

Strategia trebuie să emită suficientă semnificație semantică pentru ca observability să poată înregistra:

- de ce setup-ul a fost acceptat
- de ce setup-ul a fost degradat
- de ce setup-ul a fost respins
- unde s-a rupt: context, structure, time, score sau FSM

Aceasta este fundația pentru auditul de decizie și rejection analytics.

---

## 19. CODE ALIGNMENT RULE

Orice patch de cod derivat din această specificație trebuie să respecte:

- corridor înainte de time
- `DecisionObject` înainte de FSM
- time vocabulary din canonul unificat
- separarea strategy / FSM / signal engine

Dacă implementarea curentă contrazice aceste reguli,
implementarea trebuie refactorizată,
nu reinterpretată documentația.

---

## 20. PATCH PRIORITIES DERIVED FROM THIS SPEC

Din această specificație derivă următoarele priorități de patch:

1. eliminarea referințelor canonice vechi la superseded time-model documents și alinierea exclusivă la `TIME_MODEL_UNIFIED_CANON_v2.0.0.md`
2. înlocuirea vocabularului legacy de tip `expiry_reach_ratio`
3. garantarea producerii `DecisionObject` înainte de FSM
4. separarea clară dintre scoring și FSM semantics
5. eliminarea fluxurilor runtime care sar peste contractul strategic oficial

---

## 21. FINAL PRINCIPLE

BinaryBot nu decide pe bază de expiry simplu.

BinaryBot decide pe baza unui stack strategic în care:
- piața este interpretată contextual
- corridorul este identificat structural
- timpul este evaluat în interiorul structurii
- scorul agregă fezabilitatea setup-ului
- `DecisionObject` standardizează adevărul strategic
- FSM decide semnificația operațională
- signal engine emite rezultatul final

Aceasta este specificația canonică activă a modelului strategic principal.

## 27. Adaptive Activity Gate Canonicalization

This section absorbs bounded content from ADAPTIVE_ACTIVITY_GATE_SPEC.md.

### 27.1 Canonical gate model
The activity gate must use normalized activity logic rather than fixed absolute inactivity thresholds whenever adaptive market-scale comparison is available.

### 27.2 Interpretation rule
Activity should be evaluated relative to context-sensitive movement scale so that low-volatility live conditions are not incorrectly rejected as inactive by a rigid fixed filter.

### 27.3 Governance boundary
Adaptive gate truth belongs to active strategy canon and may inform scoring eligibility, but any future refinements must still pass through canonical change control.
