
The canonical downstream handoff remains:

- `Corridor Engine` is before `Time Model`.
- `DecisionObject` is produced before FSM.

# SR_CORRIDOR_ENGINE_SPEC_v2.0.0


Path: /opt/binarybot/docs/canonical/active/SR_CORRIDOR_ENGINE_SPEC_v2.0.0.md  
Version: 2.0.0  
Status: Canonical Active Structural Specification  
Owner: BinaryBot / DROPi Signals  
Scope: Canonical support/resistance and corridor interpretation layer, positioned before time model and before DecisionObject production  

Linked Documents:
- /opt/binarybot/docs/canonical/active/CANONICAL_STRATEGY_STACK_v1.0.0.md
- /opt/binarybot/docs/canonical/active/ALGO_SPEC_v2.0.0.md
- /opt/binarybot/docs/canonical/active/TIME_MODEL_UNIFIED_CANON_v2.0.0.md
- /opt/binarybot/docs/canonical/active/DECISION_OBJECT_CANONICAL_SPEC_v1.0.0.md
- /opt/binarybot/docs/canonical/active/OBSERVABILITY_SPEC_v2.0.0.md


Depends on:
- canonical/active/CANONICAL_STRATEGY_STACK_v1.0.0.md
- canonical/active/ALGO_SPEC_v2.0.0.md
- canonical/active/TIME_MODEL_UNIFIED_CANON_v2.0.0.md
- canonical/active/DECISION_OBJECT_CANONICAL_SPEC_v1.0.0.md
- canonical/active/OBSERVABILITY_SPEC_v2.0.0.md

---

## 1. PURPOSE

Acest document definește specificația canonică a layerului SR / Corridor Engine din BinaryBot.

Acest layer are rolul de a:
- interpreta structura relevantă de support / resistance
- defini corridorul operațional curent
- delimita zona în care setup-ul este fezabil sau nefezabil structural
- furniza adevărul structural folosit ulterior de time model, scoring și `DecisionObject`

Acest document există pentru a separa clar:
- interpretarea structurii
- interpretarea timpului
- verdictul strategic agregat
- verdictul operațional FSM

---

## 2. CORE PRINCIPLE

SR / Corridor Engine este **înainte** de Time Model în pipeline-ul canonic.

Acesta este adevăr de arhitectură blocat.

Ordinea oficială este:
1. market model
2. SR / corridor engine
3. time model
4. scoring
5. `DecisionObject`
6. FSM
7. signal engine

Prin urmare:
- time modelul nu trebuie să inventeze singur structura
- scoringul nu trebuie să ignore adevărul structural
- `DecisionObject` trebuie să primească material structural deja derivat
- FSM-ul nu trebuie să refacă manual logica structurală

---

## 3. ROLE OF SR / CORRIDOR ENGINE

Layerul SR / Corridor Engine are patru responsabilități fundamentale:

1. **identificare structurală**  
   detectează niveluri și zone relevante de support / resistance

2. **definire de corridor**  
   stabilește spațiul operațional în care setup-ul este interpretat

3. **fezabilitate structurală**  
   evaluează dacă setup-ul are loc într-o zonă structural coerentă

4. **livrare de adevăr structural semantic**  
   furnizează output recognoscibil pentru layerele următoare

---

## 4. WHAT SR / CORRIDOR ENGINE IS NOT

Acest layer nu este:
- time model
- scoring engine
- FSM
- signal execution layer
- doar un set de linii desenate vizual
- doar o colecție brută de nivele fără semantică

El nu trebuie să emită singur semnalul final.
El nu trebuie să decidă singur stările FSM.
El nu trebuie să substituie `DecisionObject`.

---

## 5. STRUCTURAL TRUTH PRINCIPLE

SR / Corridor Engine trebuie să producă **adevăr structural recognoscibil**.

Asta înseamnă că outputul său trebuie să poată răspunde semantic la întrebări ca:
- unde este corridorul curent?
- care sunt marginile relevante?
- setup-ul este interior, la margine sau în afara corridorului?
- există spațiu structural suficient?
- există conflict structural evident?
- structura favorizează sau penalizează setup-ul?

Aceste răspunsuri nu trebuie lăsate implicite.

---

## 6. REQUIRED INPUT FAMILIES

Acest layer poate consuma date derivate din market model și alte surse structurale,
dar la nivel canonic trebuie să existe capacitatea de a interpreta minimum:

- niveluri de support relevante
- niveluri de resistance relevante
- zone / bands / ranges structurale
- poziția curentă a prețului față de aceste repere
- direcția setup-ului
- contextul de proximitate structurală

Implementarea exactă poate varia,
dar aceste familii de input trebuie să existe.

---

## 7. CORRIDOR DEFINITION PRINCIPLE

Un corridor este o structură operațională delimitată de repere SR relevante,
în interiorul căreia interpretăm fezabilitatea și spațiul setup-ului.

Corridorul nu este doar o formă geometrică.
Este o abstracție strategică utilizată pentru:
- localizare contextuală
- evaluare de spațiu
- estimare de constrângere
- interpretare înainte de time model

---

## 8. REQUIRED CORRIDOR QUESTIONS

Motorul trebuie să poată răspunde semantic minimum la:

- care este corridorul activ?
- care sunt marginile lui?
- cât de aproape este setup-ul de limită?
- există spațiu de mișcare suficient?
- există compresie structurală?
- există conflict cu direcția dorită?
- setup-ul este încadrat structural sau forțat artificial?

---

## 9. STRUCTURAL FEASIBILITY PRINCIPLE

Fezabilitatea structurală trebuie evaluată înainte de evaluarea temporală completă.

Aceasta este regula canonică blocată.

Asta înseamnă:
- un setup nefezabil structural nu trebuie cosmetizat de time model
- timpul nu poate compensa complet lipsa de sens structural
- scoringul trebuie să reflecte adevărul structural, nu să îl ocolească

---

## 10. RELATION TO TIME MODEL

Time modelul consumă adevărul structural deja produs de SR / Corridor Engine.

Time modelul poate răspunde la întrebări precum:
- există suficient timp în interiorul structurii?
- expiră setup-ul înainte de ieșirea fezabilă?
- presiunea temporală schimbă interpretarea setup-ului?

Dar aceste întrebări sunt **după** definirea structurii, nu înainte.

Prin urmare:
- SR / corridor precede time model
- time model nu definește corridorul
- time model interpretează timpul în interiorul adevărului structural

---

## 11. RELATION TO SCORING

Scoringul trebuie să includă adevărul structural ca ingredient major.

Asta înseamnă că:
- scorul nu poate fi calculat în vid
- setup-urile cu structură slabă trebuie penalizate
- setup-urile bine încadrate structural pot primi avantaj,
  dar nu ignorând celelalte layere

SR / Corridor Engine nu este scorul,
dar este contributor canonic la el.

---

## 12. RELATION TO DECISIONOBJECT

`DecisionObject` trebuie să primească semantica structurală într-o formă stabilă și recognoscibilă.

Asta poate include, la nivel de familie semantică:
- corridor summary
- structural position
- boundary proximity
- structural feasibility
- structural conflict flags
- structural explanation snippets

Numele exacte pot varia,
dar adevărul structural nu trebuie pierdut înainte de `DecisionObject`.

---

## 13. REQUIRED SEMANTIC OUTPUT FAMILIES

Outputul structural trebuie să poată exprima minimum:

- corridor identity / summary
- relevant boundaries
- structural position
- feasibility state
- conflict state
- pressure / compression / constrained-space semantics
- explanation summary

Aceste familii sunt obligatorii la nivel canonic,
chiar dacă reprezentarea exactă diferă.

---

## 14. STRUCTURAL OUTCOME FAMILIES

La nivel semantic, layerul poate clasifica setup-ul structural în familii precum:

- structurally valid
- structurally constrained
- structurally degraded
- structurally conflicted
- structurally invalid

Aceste denumiri pot fi adaptate,
dar conceptul de outcome structural recognoscibil este obligatoriu.

---

## 15. BOUNDARY PROXIMITY PRINCIPLE

Proximitatea față de marginea corridorului este informație strategică esențială.

De aceea sistemul trebuie să poată surprinde semantic:
- aproape de limită favorabilă
- aproape de limită nefavorabilă
- prea aproape pentru fezabilitate sănătoasă
- suficient de central sau liber pentru setup

Nu este obligatoriu un singur format numeric,
dar semantica trebuie să existe.

---

## 16. STRUCTURAL CONFLICT PRINCIPLE

Motorul trebuie să poată identifica când setup-ul intră în conflict cu structura.

Exemple de conflict:
- direcția dorită lovește imediat în rezistență relevantă
- spațiul disponibil este insuficient
- corridorul este comprimat sau ostil
- setup-ul presupune o mișcare neverosimilă structural

Această informație trebuie să fie disponibilă downstream.

---

## 17. STRUCTURAL EXPLANATION REQUIREMENT

Pentru audit și debug,
layerul structural trebuie să poată produce explanation snippets utile.

Exemple:
- "long too close to upper resistance"
- "corridor compressed"
- "insufficient structural room"
- "setup centered within healthy corridor"

Formulările exacte pot varia,
dar explicația semantică este obligatorie.

---

## 18. OBSERVABILITY REQUIREMENT

Observability trebuie să poată urmări:
- ce corridor a fost ales
- ce margini au fost folosite
- ce outcome structural a rezultat
- ce conflict sau constrângere a fost detectată
- cum a influențat asta scoringul, `DecisionObject` și outcome-ul ulterior

Layerul structural nu poate rămâne o cutie neagră.

---

## 19. FORBIDDEN STRUCTURAL PATTERNS

Sunt interzise ca modele canonice active:

- time model care definește corridorul în locul layerului structural
- scoring fără input structural recognoscibil
- `DecisionObject` fără adevăr structural recognoscibil
- FSM care re-derivă manual structura din price action brută
- corridor definit doar informal, fără semnificație semantică auditabilă
- amestecarea structurii cu execuția finală a semnalului

---


## 20A. ANCHOR ARCHITECTURE TRUTHS

This structural specification explicitly adopts the following canonical truths:

1. `Corridor Engine` is before `Time Model` in the strategic pipeline.
2. `DecisionObject` is produced before FSM.

The structural layer therefore exists upstream of both time interpretation and FSM operational interpretation.
Its output must remain compatible with the architecture in which structural truth is derived first, then consumed by time/scoring, then standardized into `DecisionObject`, and only afterwards consumed by FSM.

---
## 20. CODE ALIGNMENT RULE

Orice implementare trebuie să poată răspunde clar la întrebările:

- unde este derivat corridorul?
- ce output structural stabil produce?
- cum ajunge acest output în scoring?
- cum ajunge în `DecisionObject`?
- cum este expus în observability?
- cum se evită duplicarea logicii structurale în FSM sau signal engine?

Dacă aceste răspunsuri nu sunt clare,
alinierea codului este incompletă.

---

## 21. FINAL PRINCIPLE

SR / Corridor Engine este layerul canonic al adevărului structural în BinaryBot.

El trebuie să fie:
- separat de time model
- separat de FSM
- recognoscibil semantic
- util pentru scoring
- util pentru `DecisionObject`
- observabil
- suficient pentru a explica fezabilitatea structurală a setup-ului

Aceasta este specificația canonică activă a layerului SR / Corridor Engine.
