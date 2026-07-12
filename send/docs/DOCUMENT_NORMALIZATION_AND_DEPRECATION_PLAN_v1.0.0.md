# DOCUMENT_NORMALIZATION_AND_DEPRECATION_PLAN_v1.0.0

Status: Satellite / Non-Canonical Reference
Canonical Position: Supporting document only; does not define active canonical truth.
Primary Active Canon: Refer to active canonical documents under /opt/binarybot/docs/canonical/active/

---

# DOCUMENT_NORMALIZATION_AND_DEPRECATION_PLAN_v1.0.0

Version: 1.0.0  
Status: Canonical Active Governance and Migration Plan  
Owner: BinaryBot / DROPi Signals  
Scope: Normalization of canonical document locations, active/deprecated status governance, duplicate reduction, and migration rules for strategy-related documentation before code alignment work  

Depends on:
- canonical/active/CANONICAL_STRATEGY_STACK_v1.0.0.md
- canonical/active/ALGO_SPEC_v2.0.0.md
- canonical/active/TIME_MODEL_UNIFIED_CANON_v2.0.0.md
- canonical/active/SR_CORRIDOR_ENGINE_SPEC_v2.0.0.md
- canonical/active/DECISION_OBJECT_CANONICAL_SPEC_v1.0.0.md
- canonical/active/FSM_DECISION_ENGINE_SPEC_v1.0.0.md
- canonical/active/SIGNAL_ENGINE_EXECUTION_SPEC_v2.0.0.md
- canonical/active/OBSERVABILITY_SPEC_v2.0.0.md

---

## 1. PURPOSE

Acest document definește planul canonic de normalizare a documentației active și de deprecare a documentelor vechi, duplicate, mixed sau istorice.

Scopul lui este:
- să reducă ambiguitatea dintre documente active și documente istorice
- să definească unde trebuie să locuiască documentele canonice active
- să definească ce fel de documente trebuie mutate sau depreciate
- să prevină proliferarea necontrolată de documente paralele
- să pregătească terenul pentru auditul de aliniere cod ↔ documentație

Acest document este plan de guvernanță și migrare,
nu specificație a logicii strategice în sine.

---

## 2. CORE PRINCIPLE

În BinaryBot trebuie să existe **un set mic, clar și recognoscibil de documente canonice active**.

Restul documentelor trebuie clasificate explicit ca:
- supporting
- transitional
- historical
- deprecated
- duplicate
- mixed / superseded

Adevărul canonic nu trebuie distribuit haotic în zeci de fișiere cu autoritate ambiguă.

---

## 3. WHY NORMALIZATION IS REQUIRED

Normalizarea este necesară deoarece, fără ea:
- aceeași logică poate apărea în mai multe fișiere
- path-urile devin inconsistente
- documentele vechi pot părea active
- auditul de cod devine nesigur
- implementarea poate deriva din sursa greșită
- mentenanța devine haotică

Prin urmare, normalizarea documentară este prerechizit pentru patching de cod.

---

## 4. OFFICIAL ACTIVE STRATEGY ROOT SET

Setul activ minim strategic, la momentul acestui document, este:

- canonical/active/CANONICAL_STRATEGY_STACK_v1.0.0.md
- canonical/active/ALGO_SPEC_v2.0.0.md
- canonical/active/TIME_MODEL_UNIFIED_CANON_v2.0.0.md
- canonical/active/SR_CORRIDOR_ENGINE_SPEC_v2.0.0.md
- canonical/active/DECISION_OBJECT_CANONICAL_SPEC_v1.0.0.md
- canonical/active/FSM_DECISION_ENGINE_SPEC_v1.0.0.md
- canonical/active/SIGNAL_ENGINE_EXECUTION_SPEC_v2.0.0.md
- canonical/active/OBSERVABILITY_SPEC_v2.0.0.md

Aceste documente formează lanțul canonic strategic activ.

---

## 5. TARGET NORMALIZED DOCUMENT CLASSES

După normalizare, documentele trebuie să aparțină uneia dintre clasele:

### 5.1 Canonical Active
Documente autoritare active, folosite direct pentru audit și implementare.

### 5.2 Canonical Supporting
Documente de suport active, de exemplu alignment matrix, audit, refactor plan, implementation plan, fără a redefini adevărul strategic principal.

### 5.3 Transitional Migration
Documente temporare folosite pentru migrare, unificare sau curățenie. Acestea nu trebuie să rămână surse de adevăr pe termen lung.

### 5.4 Deprecated / Historical
Documente vechi, înlocuite, păstrate doar pentru trasabilitate istorică.

### 5.5 Duplicate / Mixed / Superseded
Documente care combină mai multe layere, repetă logică deja canonizată sau au fost depășite de setul activ actual.

---

## 6. ACTIVE VS DEPRECATED RULE

Orice document relevant trebuie să aibă statut clar recognoscibil.

Nu trebuie să existe fișiere care:
- par active dar sunt învechite
- par canonice dar sunt doar drafturi istorice
- conțin adevăr amestecat și conflictual fără etichetare
- coexistă cu un document nou fără regulă de precedență clară

Dacă un document nu este activ, rolul lui trebuie clarificat sau documentul trebuie depreciat.

---

## 7. PATH NORMALIZATION PRINCIPLE

Path-urile documentelor canonice trebuie să fie stabile și previzibile.

Reguli:
- documentele root canonice active trebuie să fie ușor de găsit
- referințele dintre documente trebuie să folosească path-uri oficiale
- un document mutat trebuie actualizat în lanțul de referințe relevante
- path-urile istorice nu trebuie lăsate ca referințe primare active

---

## 8. CANONICAL LOCATION PRINCIPLE

Documentele care reprezintă specificații canonice active trebuie să fie grupate coerent și recognoscibil.

Dacă proiectul folosește `canonical/active/` pentru anumite documente root,
atunci această schemă trebuie aplicată coerent, nu arbitrar.

Nu este obligatoriu ca toate fișierele să fie mutate simultan,
dar planul final trebuie să stabilească exact:
- ce rămâne în `docs/`
- ce trebuie mutat în `docs/canonical/active/` sau echivalentul deja existent
- ce trebuie lăsat explicit deprecated

---

## 9. REFERENCE CONSISTENCY RULE

După normalizare:
- fiecare document activ trebuie să refere corect celelalte documente active
- nu trebuie să existe referințe primare către documente deprecated
- documentele supporting trebuie să pointeze către setul canonic activ
- documentele migration trebuie să specifice clar că nu sunt sursa finală de adevăr

Orice inconsistență de referință trebuie tratată ca defect de documentație.

---

## 10. DUPLICATE REDUCTION PRINCIPLE

Când două sau mai multe documente spun același lucru,
nu păstrăm toate ca pseudo-canonice.

Trebuie ales:
- documentul autoritar
- documentele care devin deprecated
- eventual documentele care rămân doar cu rol de mapare sau migrare

Scopul nu este multiplicarea documentelor,
ci reducerea clară a surselor de adevăr.

---

## 11. MIXED DOCUMENT RULE

Documentele mixed sunt fișiere care:
- combină logică de strategie, FSM, execuție, observability sau admin într-un mod confuz
- repetă și amestecă termeni vechi și noi
- nu respectă separarea pe layere canonică

Aceste documente nu trebuie lăsate active ca surse primare.

Ele trebuie:
- fie restructurate
- fie extrase în documente specializate
- fie depreciate dacă sunt deja depășite

---

## 12. DEPRECATION PRINCIPLE

Deprecarea nu înseamnă ștergere oarbă.

Deprecarea canonică înseamnă:
- păstrarea trasabilității
- eliminarea autorității active
- marcarea clară a statutului istoric
- evitarea folosirii accidentale în implementare

Un document deprecated poate exista în continuare,
dar nu trebuie tratat ca sursă activă de adevăr.

---

## 13. MINIMUM DEPRECATION ACTIONS

Pentru un document deprecated trebuie să existe, ideal:
- nume recognoscibil sau prefix de deprecated
- mențiune de înlocuire / supersedare
- dată sau context de deprecare
- referință către documentul activ care l-a înlocuit, unde este posibil

---

## 14. MIGRATION WITHOUT CHAOS RULE

Migrarea documentelor trebuie făcută controlat.

Asta înseamnă:
- backup înainte
- audit după
- referințe actualizate
- mutări explicite, nu implicite
- evitarea rupturii lanțului de documente
- evitarea apariției de noi duplicate în timpul curățeniei

---

## 15. GOVERNANCE BEFORE CODE RULE

Înainte de modificări serioase în Python,
trebuie să fie clar:
- care este setul activ canonic
- care este ordinea de autoritate
- care documente sunt deprecated
- care documente sunt doar supporting sau migration
- ce path-uri sunt oficiale

Fără această claritate,
auditul codului riscă să se alinieze la sursa greșită.

---

## 16. REQUIRED INVENTORY OUTPUT

Normalizarea completă trebuie să producă un inventar explicit cu minimum:

- document activ
- statut
- clasă
- locație curentă
- locație țintă, dacă se mută
- document care îl înlocuiește, dacă e deprecated
- motivul clasificării

Acest inventar poate trăi într-un audit separat,
dar este rezultat obligatoriu al normalizării.

---

## 17. RELATION TO SUPPORTING DOCS

Documente precum:
- alignment matrix
- alignment audit
- refactor plan
- implementation step plan

pot rămâne active ca documente supporting,
dar ele nu trebuie să redefinească adevărul strategic root.

Ele trebuie să derive din setul canonic activ,
nu invers.

---

## 18. RELATION TO ADMIN / OBSERVABILITY / NON-STRATEGY DOCS

Curățenia documentară nu se oprește la strategie pură.

Admin panel, observability, distribuție Telegram și alte funcții ale botului trebuie și ele racordate la noua ordine canonică.

Prin urmare, după normalizarea stack-ului strategic,
următoarele audituri trebuie să extindă aceeași disciplină și în:
- admin / control plane docs
- observability / telemetry docs
- distribution / Telegram docs
- alte docs operaționale relevante

---

## 19. FORBIDDEN DOCUMENTATION PATTERNS

Sunt interzise ca stare țintă:

- mai multe documente active care concurează pentru același adevăr
- documente vechi lăsate fără statut clar
- referințe primare către fișiere supersedate
- mixed docs păstrate ca pseudo-canonice
- drafturi temporare tratate ca surse oficiale
- migrare fără audit și fără trasabilitate

---

## 20. CANONICAL END STATE

Starea țintă după normalizare trebuie să fie:

- set activ mic și clar
- path-uri oficiale coerente
- referințe consistente
- documente deprecated marcate clar
- documente mixed eliminate din lanțul activ
- documentație suficient de curată pentru audit cod ↔ canon

Aceasta este condiția necesară înainte de faza de patching Python pe rând.

---

## 21. FINAL PRINCIPLE

Scopul acestui plan nu este să creeze mai multe documente,
ci să reducă haosul documentar și să consolideze o singură coloană vertebrală canonică.

Documentația trebuie să fie suficient de clară încât codul să poată deriva din ea fără ambiguitate.

Aceasta este regula canonică activă de normalizare și deprecare documentară.

## Non-Canonical Usage Note

This document is retained as a supporting/satellite reference only. It must not be treated as active canonical truth. Where conflict exists, active canonical documents in /opt/binarybot/docs/canonical/active/ take precedence.
