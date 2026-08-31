# FSM_DECISION_ENGINE_SPEC_v2.0.0

Path: /opt/binarybot/docs/canonical/proposed/FSM_DECISION_ENGINE_SPEC_v2.0.0.md  
Version: 2.0.0  
Status: PROPOSED COMPLETE SUCCESSOR — NOT ACTIVE CANONICAL  
Owner: BinaryBot / DROPi Signals  
Scope: Operational interpretation of strategic truth through FSM, after DecisionObject production and before signal execution, including explicit exact-stage handoff semantics

Supersession Intent: FSM_DECISION_ENGINE_SPEC_v1.0.0.md

Linked Documents:
- CANONICAL_STRATEGY_STACK_v2.0.0.md
- ALGO_SPEC_v2.0.0.md
- DECISION_OBJECT_CANONICAL_SPEC_v1.0.0.md
- SIGNAL_ENGINE_EXECUTION_SPEC_v3.0.0.md
- MODULE_INTERFACE_SPEC_v3.0.0.md
- OBSERVABILITY_SPEC_v3.0.0.md
- EVENT_SCHEMA_SPEC_v3.0.0.md
- DECISION_AUDIT_SPEC_v2.0.0.md

Depends on:
- CANONICAL_STRATEGY_STACK_v2.0.0.md
- ALGO_SPEC_v2.0.0.md
- DECISION_OBJECT_CANONICAL_SPEC_v1.0.0.md
- SYSTEM_INVARIANTS_v2.0.0.md

---

## 0. AUTHORITY AND PROMOTION STATUS

This document is a complete proposed successor. It contains the full intended FSM authority and does not depend normatively on the superseded v1 document for omitted rules.

Until an explicit canonical promotion is approved and completed, `FSM_DECISION_ENGINE_SPEC_v1.0.0.md` remains the active FSM authority. Merge of this proposed file alone does not authorize runtime code changes.

---

## 1. PURPOSE

Acest document definește specificația canonică propusă a layerului FSM din BinaryBot.

FSM-ul are rolul de a:
- consuma `DecisionObject`
- interpreta operațional starea strategică
- decide dacă setup-ul este acceptat, amânat, degradat, blocat sau respins
- controla progresia lifecycle
- furniza ieșirea operațională necesară pentru signal engine și observability
- expune explicit dacă exact stadiul PRE / CONFIRM / OPEN_NOW este eliberat către signal engine

FSM-ul nu definește matematica strategiei.  
FSM-ul nu înlocuiește scoringul.  
FSM-ul nu produce `DecisionObject`.  
FSM-ul nu publică semnale și nu deține distribuția.

---

## 2. CORE PRINCIPLE

FSM-ul este **consumerul operațional** al adevărului strategic standardizat.

Ordinea canonică blocată este:
1. market model
2. corridor engine
3. time model
4. scoring
5. `DecisionObject`
6. FSM
7. signal engine
8. SignalEvent candidate / execution result
9. distribution / publication

Prin urmare:
- FSM-ul este după `DecisionObject`
- FSM-ul nu trebuie să reconstruiască matematica strategică din inputuri brute
- FSM-ul nu trebuie să emită direct payload-ul final de semnal
- existența unui transition event nu este, singură, permisiune de handoff

---

## 3. ROLE OF FSM

FSM-ul are cinci responsabilități fundamentale:

1. **clasificare operațională** — transformă starea strategică într-o stare operațională utilizabilă;
2. **control de tranziție** — stabilește dacă sistemul intră în wait, prepare, confirm, open-now, reject, degraded sau blocked;
3. **stabilizare comportamentală** — previne reacțiile haotice prin reguli explicite de tranziție;
4. **control de continuitate lifecycle** — păstrează ordinea PRE → CONFIRM → OPEN_NOW și identitatea semnalului;
5. **handoff pentru execuție și audit** — produce semnificația operațională necesară signal engine-ului și observability.

---

## 4. WHAT FSM IS NOT

FSM-ul nu este:
- motorul matematic principal al strategiei
- calculatorul primar de timp
- producătorul corridorului
- contractul strategic canonic
- sistemul final de distribuire a semnalului
- substitutul pentru observability
- dovadă de publicare externă
- broker execution authority

---

## 5. REQUIRED INPUT CONTRACT

Inputul canonic pentru FSM este `DecisionObject`.

FSM-ul poate consuma metadata auxiliară de runtime, dar adevărul strategic principal trebuie să vină prin `DecisionObject`.

Sunt interzise ca pattern canonic primar:
- FSM care pornește doar din score brut
- FSM care pornește doar din `expiry_minutes`
- FSM care parsează un dict informal legacy fără contract semantic clar
- FSM care rederivă strategia pentru a înlocui `DecisionObject`

---

## 6. INPUT EXPECTATION FAMILIES

FSM-ul trebuie să poată consuma din `DecisionObject` cel puțin:
- setup identity
- signal identity unde există
- market context
- structure state
- time feasibility
- score semantics
- strategic flags
- stage semantics
- reject / degrade semantics
- observability-ready explanations

Dacă aceste familii lipsesc, FSM-ul funcționează pe un contract incomplet și trebuie să eșueze fail-closed acolo unde lipsa afectează lifecycle sau handoff.

---

## 7. OPERATIONAL PURPOSE OF FSM STATES

Stările FSM nu descriu întreaga matematică a strategiei. Ele descriu **cum trebuie tratat operațional** un setup într-un anumit moment.

- strategia spune ce este setup-ul;
- FSM-ul spune ce facem cu el acum;
- signal engine-ul decide ce candidat de semnal poate fi materializat după handoff;
- distribution decide unde și dacă acel candidat poate fi publicat.

Această separare este obligatorie.

---

## 8. CANONICAL FSM OUTCOME FAMILIES

FSM-ul trebuie să poată exprima cel puțin:
- `REJECT`
- `WAIT`
- `PREPARE`
- `CONFIRM`
- `OPEN_NOW`
- `DEGRADED`
- `BLOCKED`

Numele interne pot evolua doar prin migrare controlată; familiile semantice trebuie să rămână recognoscibile.

---

## 9. REJECT FAMILY

`REJECT` înseamnă că setup-ul nu trebuie să continue spre execuție.

Cauzele pot include:
- structură invalidă
- fezabilitate temporală insuficientă
- score inacceptabil
- conflict major între context și setup
- hard blockers strategici

`REJECT` trebuie să fie explicit și explicabil, nu dedus doar din lipsa unui semnal.

---

## 10. WAIT FAMILY

`WAIT` înseamnă că setup-ul nu este încă executabil, dar nici respins definitiv.

Exemple:
- context încă neclar
- setup promițător dar incomplet
- nevoie de confirmare suplimentară
- timing insuficient matur

`WAIT` trebuie diferențiat clar de `REJECT` și nu eliberează automat un stage actionable.

---

## 11. PREPARE FAMILY

`PREPARE` descrie starea în care setup-ul a devenit relevant operațional, dar nu este în punctul final de execuție.

Este utilă pentru:
- pre-alerting
- focus handling
- staged monitoring
- pregătirea observability și distribution

PRE / PREPARE poate participa la lifecycle numai după aplicarea regulilor explicite de acceptare și handoff definite mai jos.

---

## 12. CONFIRM FAMILY

`CONFIRM` descrie o fază avansată de validare operațională.

Nu înseamnă execuție finală imediată. Un CONFIRM acceptat poate fi eliberat către signal engine pentru SignalEvent lifecycle candidate, dar `trade_execution_ready` trebuie să rămână false.

---

## 13. OPEN_NOW FAMILY

`OPEN_NOW` descrie starea în care setup-ul este considerat executabil imediat conform regulilor operaționale active.

Este cea mai apropiată stare FSM de emiterea efectivă a semnalului, dar:
- SignalEvent construction rămâne responsabilitatea signal engine-ului;
- publication rămâne responsabilitatea distribution/publisher;
- broker execution nu este autorizat de această stare.

---

## 14. DEGRADED FAMILY

`DEGRADED` descrie un setup recognoscibil cu încredere redusă sau condiții deteriorate.

Exemple:
- score marginal
- presiune temporală crescută
- context instabil
- target realism slab

Această familie evită binaritatea falsă accept/reject.

---

## 15. BLOCKED FAMILY

`BLOCKED` descrie o oprire operațională prin regulă explicită, chiar dacă setup-ul strategic poate părea promițător.

Exemple:
- cooldown
- focus gating
- watchlist capacity fără replacement valid
- policy conflict
- runtime guardrail
- invariant failure

Un rezultat BLOCKED nu eliberează stage-ul downstream.

---

## 16. TRANSITION PRINCIPLE

Tranzițiile FSM trebuie să fie:
- explicite
- auditabile
- reproductibile
- bazate pe semnificație strategică standardizată
- corelate cu identitatea setup/signal

Sunt interzise tranzițiile opace bazate pe combinații ad-hoc greu de urmărit.

**Un transition event existent nu constituie singur dovadă că stage-ul cerut a fost acceptat.**

---

## 17. FSM MUST NOT RE-DERIVE STRATEGY

FSM-ul nu trebuie să rederive complet:
- corridorul
- time modelul
- score-ul strategic
- reject semantics strategice de bază

FSM-ul poate interpreta aceste date, dar nu trebuie să fie sursa lor primară de adevăr.

---

## 18. ANCHOR ARCHITECTURE TRUTHS

Adevărurile upstream rămân:
1. Corridor Engine este înainte de Time Model.
2. `DecisionObject` este produs înainte de FSM.
3. FSM este înainte de signal engine.
4. Distribution este downstream de SignalEvent candidate.

FSM consumă un `DecisionObject` care reflectă deja interpretarea structurală și temporală în ordinea canonică.

---

## 19. RELATION TO DECISIONOBJECT

Relația corectă este:
- strategia produce `DecisionObject`;
- FSM citește și interpretează `DecisionObject`;
- FSM produce verdict operațional standardizat și handoff explicit;
- FSM nu rescrie arbitrar contractul strategic.

---

## 20. REQUIRED OUTPUT SEMANTICS OF FSM

Outputul FSM trebuie să poată exprima cel puțin:
- state / outcome
- reason / reason family
- requested_stage: `PRE | CONFIRM | OPEN_NOW | null`
- accepted_stage: `PRE | CONFIRM | OPEN_NOW | null`
- signal_id unde este aplicabil
- state_changed
- transition evidence unde există
- degradation status
- rejection / blocked status
- explanation snippets
- `stage_handoff_ready`
- `trade_execution_ready`
- observability handoff metadata

Outputul nu trebuie redus la un string textual simplu.

---

## 21. EXACT-STAGE HANDOFF CONTRACT

Pentru fiecare `DecisionObject` actionable PRE, CONFIRM sau OPEN_NOW, FSM trebuie să expună explicit dacă **exact acel stage** este acceptat și eliberat către signal engine.

### 21.1 `stage_handoff_ready`

`stage_handoff_ready=true` înseamnă cumulativ:
- requested_stage este actionable;
- accepted_stage == requested_stage;
- lifecycle continuity este validă;
- signal identity continuity este validă unde este cerută;
- focus/watchlist/cooldown/invariant rules permit stage-ul;
- stage-ul nu este duplicate-suppressed;
- nu există blocker activ;
- FSM eliberează explicit stage-ul downstream.

Poate fi true pentru PRE, CONFIRM sau OPEN_NOW.

### 21.2 `trade_execution_ready`

`trade_execution_ready` este un adevăr separat:
- MUST fi false pentru PRE;
- MUST fi false pentru CONFIRM;
- MAY fi true numai pentru OPEN_NOW acceptat, cu lifecycle/focus/actionability valide;
- MUST fi false dacă `stage_handoff_ready=false`.

`stage_handoff_ready` nu poate fi interpretat ca sinonim pentru `trade_execution_ready`.

---

## 22. FAIL-CLOSED HANDOFF RULE

`stage_handoff_ready=false` este obligatoriu pentru:
- `cooldown_active`
- `watchlist_full` fără replacement acceptat
- duplicate stage/candle suppression
- signal identity continuity failure
- invalid PRE/CONFIRM/OPEN_NOW lifecycle path
- FSM reject/block
- invariant failure
- no-op transition care nu eliberează stage-ul cerut
- orice rezultat ambiguu care nu dovedește acceptarea exactă

Normal function return, `accepted=true` generic sau simpla existență a `transition_event` nu sunt suficiente dacă nu exprimă exact stage release.

---

## 23. PRE HANDOFF

PRE poate fi eliberat când watchlist/focus rules permit lifecycle entry sau refresh și niciun blocker nu îl suprimă.

Pentru PRE acceptat:
- accepted_stage = PRE
- stage_handoff_ready = true
- trade_execution_ready = false

Identitatea semnalului trebuie păstrată stabil pentru progresia ulterioară CONFIRM / OPEN_NOW.

---

## 24. CONFIRM HANDOFF

CONFIRM poate fi eliberat numai când lifecycle continuity și focus/watchlist state permit confirmarea aceleiași identități.

Pentru CONFIRM acceptat:
- accepted_stage = CONFIRM
- stage_handoff_ready = true
- trade_execution_ready = false

---

## 25. OPEN_NOW HANDOFF

OPEN_NOW poate fi eliberat numai printr-un PRE path valid, cu focus/actionability context valid și stable signal identity.

Pentru OPEN_NOW acceptat și actionable:
- accepted_stage = OPEN_NOW
- stage_handoff_ready = true
- trade_execution_ready = true

Această acceptare nu dovedește publicarea externă și nu autorizează broker execution.

---

## 26. STATE VS EXTERNAL VISIBILITY

Stări interne precum WATCHLIST sau CONFIRMED nu sunt dovadă că PRE/CONFIRM au fost publicate extern.

External visibility este truth domain downstream și trebuie demonstrată prin distribution/publisher observability.

---

## 27. RELATION TO SIGNAL ENGINE

Signal engine consumă verdictul operațional post-FSM.

Semnalul nu este emis direct din `DecisionObject` sau scoring. Signal engine poate considera un SignalEvent pentru PRE/CONFIRM/OPEN_NOW numai când `stage_handoff_ready=true` și `accepted_stage` corespunde stage-ului strategic cerut.

`trade_execution_ready` nu este necesar pentru PRE/CONFIRM lifecycle candidates și nu poate fi folosit pentru a exclude în mod artificial aceste două stage-uri din lifecycle.

---

## 28. RELATION TO OBSERVABILITY

Observability trebuie să poată vedea:
- ce `DecisionObject` a intrat în FSM
- requested_stage
- accepted_stage
- state/outcome rezultat
- reason / blocker
- transition evidence
- lifecycle continuity
- stage_handoff_ready
- trade_execution_ready
- dacă setup-ul a progresat sau a fost suprimat/blocat

FSM trebuie să emită semantică suficientă pentru audit fără a inventa publication truth.

---

## 29. REJECTION / SUPPRESSION ANALYTICS REQUIREMENT

FSM trebuie să contribuie semantic la analiza:
- reject stage/reason
- degradation path
- blocked path
- duplicate suppression
- cooldown suppression
- wait path care nu a progresat
- identity/lifecycle continuity failure

Acest document susține direct decision audit și execution observability.

---

## 30. FORBIDDEN FSM PATTERNS

Sunt interzise:
- FSM care produce singur adevărul strategic din brut
- FSM care decide doar pe `expiry_minutes`
- FSM care amestecă scoring, contract strategic și execuție într-un singur blob
- FSM fără stare semantică explicită
- FSM care transmite direct Telegram payload
- FSM care nu poate explica reject/block/suppression
- transition-event existence tratată ca stage release
- generic function success tratat ca stage release
- PRE/CONFIRM marcate `trade_execution_ready=true`
- FSM state tratat ca dovadă de external visibility

---

## 31. CODE ALIGNMENT RULE

Orice implementare FSM trebuie să poată răspunde clar:
- unde primește `DecisionObject`?
- care sunt stările/outcomes canonice?
- cum sunt definite tranzițiile majore?
- cum exprimă reject/block/suppression?
- cum exprimă requested_stage și accepted_stage?
- cum calculează `stage_handoff_ready`?
- cum separă `trade_execution_ready`?
- cum păstrează stable signal identity?
- cum ajunge outputul la signal engine și observability?

Dacă aceste răspunsuri nu sunt clare, alinierea codului este incompletă.

---

## 32. PROMOTION AND MIGRATION RULE

La promovare:
- această versiune trebuie să devină singura autoritate FSM activă;
- v1 trebuie eliminat din `canonical/active` și păstrat în `canonical/superseded` cu trasabilitate;
- toate active references către v1 trebuie reparate atomic;
- root manifest și master index trebuie actualizate;
- runtime code rămâne neschimbat până după re-auditul canonului promovat.

---

## 33. FINAL PRINCIPLE

FSM este layerul care transformă adevărul strategic standardizat în adevăr operațional standardizat.

El trebuie să fie:
- dependent de `DecisionObject`
- separat de matematica strategică
- separat de signal engine
- explicit în exact-stage handoff
- fail-closed la ambiguity/block/suppression
- capabil să distingă lifecycle handoff de final trade readiness
- auditabil și explicabil

Aceasta este specificația completă propusă pentru FSM decision engine v2.