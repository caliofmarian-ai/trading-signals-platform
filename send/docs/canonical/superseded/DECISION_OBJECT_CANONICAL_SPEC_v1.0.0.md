# DECISION_OBJECT_CANONICAL_SPEC_v1.0.0


Path: /opt/binarybot/docs/canonical/active/DECISION_OBJECT_CANONICAL_SPEC_v1.0.0.md  
Version: 1.0.0  
Status: Canonical Active Contract Specification  
Owner: BinaryBot / DROPi Signals  
Scope: Official strategic output contract between strategy stack and FSM decision engine  

Linked Documents:
- /opt/binarybot/docs/canonical/active/CANONICAL_STRATEGY_STACK_v1.0.0.md
- /opt/binarybot/docs/canonical/active/ALGO_SPEC_v2.0.0.md
- /opt/binarybot/docs/canonical/active/TIME_MODEL_UNIFIED_CANON_v2.0.0.md
- /opt/binarybot/docs/canonical/active/FSM_DECISION_ENGINE_SPEC_v1.0.0.md
- /opt/binarybot/docs/canonical/active/OBSERVABILITY_SPEC_v2.0.0.md
- /opt/binarybot/docs/canonical/active/DECISION_AUDIT_SPEC_v2.0.0.md


Depends on:
- canonical/active/CANONICAL_STRATEGY_STACK_v1.0.0.md
- canonical/active/ALGO_SPEC_v2.0.0.md
- canonical/active/TIME_MODEL_UNIFIED_CANON_v2.0.0.md
- canonical/active/FSM_DECISION_ENGINE_SPEC_v1.0.0.md
- canonical/active/OBSERVABILITY_SPEC_v2.0.0.md

---

## 1. PURPOSE

Acest document definește contractul canonic oficial al obiectului `DecisionObject`.

`DecisionObject` este outputul strategic standardizat al stack-ului BinaryBot.
El reprezintă puntea formală dintre:
- layerul de strategie
- layerul FSM
- layerul de observability / audit

Acest document există pentru a elimina:
- outputuri strategice informale
- dict-uri legacy instabile
- ambiguități despre ce primește FSM-ul
- confuzia dintre adevărul strategic și verdictul operațional

---

## 2. CORE PRINCIPLE

`DecisionObject` este produs **înainte** de FSM.

Acesta este adevăr canonic blocat.

Ordinea oficială este:
1. market model
2. corridor engine
3. time model
4. scoring
5. `DecisionObject`
6. FSM
7. signal engine

Prin urmare:
- strategia nu emite direct semnalul final
- FSM-ul nu inventează adevărul strategic
- `DecisionObject` este contractul standardizat dintre ele

---

## 3. ROLE OF DECISIONOBJECT

`DecisionObject` are trei roluri fundamentale:

1. **standardizare strategică**  
   transformă outputul intern al strategiei într-o formă coerentă, consumabilă și auditabilă

2. **interfață pentru FSM**  
   oferă FSM-ului o reprezentare clară a stării strategice, fără ca FSM-ul să reconstruiască matematica

3. **fundație pentru observability**  
   permite explicarea acceptării, degradării sau respingerii unui setup

---

## 4. WHAT DECISIONOBJECT IS NOT

`DecisionObject` nu este:
- verdictul final de execuție
- starea FSM
- payload-ul final de Telegram
- doar un scor numeric
- doar un `expiry_minutes`
- doar un wrapper peste un dict legacy fără semnificație semantică

---

## 5. REQUIRED CONTRACT FAMILIES

Orice `DecisionObject` canonic trebuie să conțină familii de informații suficiente pentru următoarele dimensiuni:

- identitatea setup-ului
- contextul strategic
- structura / corridorul relevant
- fezabilitatea temporală
- scorul și semantica scorului
- gating / reject semantics
- readiness pentru FSM
- readiness pentru observability

Nu toate câmpurile trebuie să fie plate.
Structura internă poate evolua.
Dar aceste familii semantice trebuie să existe recognoscibil.

---

## 6. MINIMUM REQUIRED SEMANTIC DOMAINS

Un `DecisionObject` valid trebuie să poată exprima cel puțin:

- ce setup este evaluat
- în ce context de piață se află
- care este corridorul / ținta structurală relevantă
- cât de fezabil este setup-ul temporal
- ce scor strategic a rezultat
- dacă există degradare strategică
- dacă există motiv de reject
- ce material semantic primește FSM-ul

Dacă unul dintre aceste domenii lipsește,
contractul este incomplet.

---

## 7. RECOMMENDED TOP-LEVEL CONTRACT SHAPE

Forma recomandată este una semantică, nu un dict opac.

Exemplu de familii top-level:

```text
DecisionObject
├── setup
├── market_context
├── structure
├── time
├── score
├── strategic_flags
├── reject_reason
├── fsm_inputs
├── observability
└── metadata
```

Aceasta este o formă canonică recomandată.
Implementarea poate varia,
dar nu are voie să piardă familiile semantice.

---

## 8. SETUP DOMAIN

Domeniul `setup` trebuie să identifice setup-ul evaluat.

Poate include:
- symbol
- side / direction
- timestamp de evaluare
- timeframe relevant
- source context
- run identifier sau cycle identifier

Scopul este ca fiecare `DecisionObject` să poată fi corelat univoc cu evaluarea sa.

---

## 9. MARKET CONTEXT DOMAIN

Domeniul `market_context` trebuie să descrie contextul strategic minim al pieței.

Poate include:
- trend context
- volatility state
- price speed
- noise state
- target distance context
- buffer distance context

Acest domeniu nu trebuie să repete toate calculele brute,
ci adevărul contextual relevant pentru decizie.

---

## 10. STRUCTURE DOMAIN

Domeniul `structure` trebuie să descrie componenta structurală.

Poate include:
- support / resistance landmarks
- corridor validity
- chosen corridor side
- target structural reference
- available movement distance
- structural confidence
- structural warnings

Acest domeniu este obligatoriu pentru că BinaryBot este corridor-first.

---

## 11. TIME DOMAIN

Domeniul `time` trebuie să consume vocabularul canonic din time modelul unificat.

Conceptele recomandate includ:
- `t_needed`
- `t_needed_adjusted`
- `model_expiry`
- `model_time_reach_ratio`
- `corridor_time_pressure`
- `time_state`

Acest document nu redefinește matematica acestor concepte.
Matematica autoritară este în:
`canonical/active/TIME_MODEL_UNIFIED_CANON_v2.0.0.md`

Sunt interzise ca adevăr primar în contract:
- `expiry_reach_ratio` ca termen canonic
- interpretarea exclusivă bazată pe `expiry_minutes`

---

## 12. SCORE DOMAIN

Domeniul `score` trebuie să exprime rezultatul agregării strategice.

Poate include:
- score total
- subscore-uri
- confidence bands
- penalties
- score tier
- score explanation snippets

Scorul trebuie să fie suficient de expresiv pentru:
- FSM
- observability
- rejection analytics

---

## 13. STRATEGIC FLAGS DOMAIN

Domeniul `strategic_flags` trebuie să exprime semnale booleene sau categorice relevante strategic.

Exemple:
- valid_structure
- feasible_time
- degraded_setup
- unstable_market
- low_confidence
- rejectable
- borderline

Aceste flag-uri ajută FSM-ul să interpreteze rapid starea fără a rederiva toată matematica.

---

## 14. REJECT SEMANTICS DOMAIN

`DecisionObject` trebuie să poată exprima reject semantics explicit.

Asta poate include:
- `reject_reason`
- `reject_category`
- `reject_stage`
- `degradation_reason`
- `hard_blockers`
- `soft_blockers`

Sistemul nu trebuie să folosească exclusiv absența unui semnal ca dovadă de reject.
Reject-ul trebuie să fie exprimabil semantic.

Această cerință este esențială pentru auditul deciziilor.

---

## 15. FSM INPUT READINESS DOMAIN

`DecisionObject` trebuie să conțină suficient context standardizat pentru ca FSM-ul:
- să decidă starea operațională
- să facă tranziții coerente
- să diferențieze accept, wait, degrade, reject
- să emită explicații observabile

FSM-ul nu trebuie să depindă de parsingul ad-hoc al unui dict informal.

---

## 16. OBSERVABILITY DOMAIN

`DecisionObject` trebuie să conțină sau să poată alimenta datele necesare pentru observability.

Acestea pot include:
- explanations
- tags
- stage markers
- scoring explanations
- timing explanations
- reject explanations
- audit correlation IDs

Scopul este:
orice decizie majoră să poată fi reconstruită semantic.

---

## 17. METADATA DOMAIN

Domeniul `metadata` poate include:
- schema version
- producer module
- compatibility mode markers
- migration markers
- trace identifiers
- debug references

Acest domeniu este util, dar nu poate substitui domeniile semantice principale.

---


## 18A. ANCHOR ARCHITECTURE TRUTHS


The canonical upstream order remains:

- `Corridor Engine` is before `Time Model`.
- `DecisionObject` is produced before FSM.



This document explicitly adopts the following anchor truths from the canonical strategy stack:

1. `DecisionObject` is produced before FSM.
2. `Corridor Engine` is before `Time Model` in the strategic pipeline.

`DecisionObject` is the output contract produced after structural and temporal evaluation, but before operational FSM interpretation.
Therefore this contract must remain compatible with the architecture in which corridor/structure evaluation precedes time evaluation, and the standardized `DecisionObject` precedes FSM consumption.

---
## 18. REQUIRED CANONICAL TRUTHS

Acest document blochează oficial următoarele adevăruri:

1. `DecisionObject` este produs înainte de FSM
2. `DecisionObject` este outputul strategic oficial
3. Time vocabulary trebuie să fie compatibil cu canonul unificat
4. Reject semantics trebuie să fie expresabile explicit
5. Observability trebuie alimentat din contract, nu reconstruit arbitrar

---

## 19. FORBIDDEN CONTRACT PATTERNS

Sunt interzise următoarele pattern-uri ca formă canonică activă:

- dict legacy fără schemă semantică
- output strategic redus la `score + expiry`
- output strategic redus la verdict textual brut
- lipsa totală a structurii
- lipsa totală a semanticii de reject
- lipsa oricărei legături explicite cu FSM readiness

Aceste pattern-uri pot exista doar temporar în layere de compatibilitate.

---

## 20. FSM RELATION RULE

FSM-ul consumă `DecisionObject`, nu îl înlocuiește.

FSM-ul poate:
- interpreta
- clasifica
- decide operațional
- amâna
- respinge
- confirma

Dar FSM-ul nu trebuie:
- să reinventeze contractul strategic
- să derive singur toate câmpurile strategice din inputuri brute
- să decidă pe bază de informație insuficient standardizată

---

## 21. SIGNAL ENGINE RELATION RULE

Signal engine-ul nu trebuie să consume direct output strategic brut.

Signal engine-ul trebuie să consume rezultatul post-FSM,
într-un flux în care `DecisionObject` a existat deja ca adevăr strategic intermediar.

Această separare este esențială pentru:
- audit
- debug
- replay
- refactor sigur

---

## 22. OBSERVABILITY AND REJECTION ANALYTICS RULE

Orice design viitor pentru auditul deciziilor și rejection analytics trebuie să poată folosi `DecisionObject` ca sursă primară de semnificație.

Asta înseamnă că obiectul trebuie să poată explica:
- de ce setup-ul era promițător
- de ce a fost degradat
- de ce a fost blocat
- în ce etapă a murit

Acest document este fundație directă pentru componenta de decision audit.

---

## 23. MIGRATION RULE

Dacă runtime-ul curent produce încă outputuri legacy,
acestea trebuie migrate către `DecisionObject`
prin compat layers temporare,
nu prin păstrarea vechiului model ca adevăr canonic.

Direcția oficială este:
legacy output -> normalized `DecisionObject` -> FSM.

---

## 24. CODE ALIGNMENT RULE

Orice patch de cod trebuie să poată răspunde clar la întrebările:

- unde este produs `DecisionObject`?
- ce câmpuri canonice conține?
- ce parte din FSM îl consumă?
- cum ajunge informația în observability?
- cum este exprimat reject-ul?

Dacă aceste răspunsuri nu există clar,
alinierea codului este incompletă.

---

## 25. FINAL PRINCIPLE

`DecisionObject` este contractul canonic care separă matematica strategică de decizia operațională.

El trebuie să fie:
- standardizat
- semantic
- auditabil
- compatibil cu time canonul unificat
- suficient pentru FSM
- suficient pentru observability

Acesta este contractul oficial dintre strategie și FSM în BinaryBot.
