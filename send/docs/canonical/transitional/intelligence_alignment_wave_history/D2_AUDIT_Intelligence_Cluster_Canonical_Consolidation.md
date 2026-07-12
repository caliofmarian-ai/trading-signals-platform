# D2-AUDIT — Intelligence Cluster Canonical Consolidation Audit

Status: Working audit draft
Scope: D2 intelligence document cluster
Date: 2026-03-14

---

## 1. Purpose

Acest audit stabilește cum trebuie consolidat canonic clusterul de documente din zona **Intelligence / Research / AI / Strategy Audit / Statistical Proof** pentru proiectul BinaryBot / DROPi Signals.

Scopul nu este să mai multiplicăm documente, ci să:

* identificăm suprapunerile reale;
* separăm clar arhitectura, operaționalul, research-ul, AI-ul și proof governance;
* decidem ce documente rămân master;
* decidem ce documente devin satelit;
* decidem ce documente trebuie absorbite / unificate / deprecated;
* pregătim terenul pentru patch-uri canonice ulterioare.

---

## 2. D2 Corpus Included

Documentele analizate în clusterul D2 sunt:

1. `AI_STRATEGY_AUDITOR_SPEC.md`
2. `AI_TRADE_PHYSICS_SPACE_MODEL_SPEC.md`
3. `AI_TRADING_INTELLIGENCE_ARCHITECTURE.md`
4. `AUTONOMOUS_STRATEGY_EVOLUTION_SYSTEM.md`
5. `INTELLIGENCE_DATA_PIPELINE_DEFINITION.md`
6. `INTELLIGENCE_FILES_AND_MODULE_MAP.md`
7. `INTELLIGENCE_LAYER_ARCHITECTURE.md`
8. `STRATEGY_INTELLIGENCE_SYSTEM.md`
9. `AI_TRADE_PHYSICS_INTELLIGENCE_SPEC.md`
10. `RESEARCH_AND_LEARNING_FRAMEWORK_SPEC.md`
11. `STATISTICAL_PROOF_LAYER.md`

---

## 3. High-Level Finding

Clusterul D2 este valoros, dar în forma actuală este **prea fragmentat** și are **overlap conceptual major**.

Problema principală nu este lipsa de conținut, ci lipsa unei ierarhii canonice clare între:

* arhitectură de intelligence;
* audit strategic operațional;
* pipeline de date și module;
* research / learning / experimentation;
* proof statistic;
* AI probabilistic / trade physics;
* evolution / recommendation / controlled self-calibration.

Pe scurt:

* există material suficient pentru o bază foarte solidă;
* există prea multe documente care spun parțial același lucru;
* nomenclatura nu este încă stabilizată;
* unele documente sunt mai aproape de “master canon”, altele sunt clar sateliți sau anexe;
* există risc real de contradicții viitoare dacă patch-uim separat fără plan de consolidare.

---

## 4. Macro-Domain Split Proposed

Pentru a evita amestecul de concepte, clusterul D2 trebuie împărțit canonic în 6 domenii mari:

### 4.1 Intelligence Architecture

Definește:

* rolul layerului de intelligence;
* subcomponentele mari;
* relația cu observability, admin, analytics și strategy engine;
* limitele de autoritate;
* flow-ul conceptual end-to-end.

### 4.2 Operational Strategy Audit

Definește:

* strategy auditor;
* bottleneck detection;
* starvation detection;
* reject breakdown;
* heatmap;
* daily / periodic reports pentru operator.

### 4.3 Intelligence Data & Module Topology

Definește:

* surse de date;
* fișiere;
* snapshots;
* JSONL / cache / report artifacts;
* module mapping;
* consumerii interni ai datelor.

### 4.4 Research & Learning Governance

Definește:

* focus history;
* trials;
* outcome validation;
* experiment design;
* symbol rotation;
* buffer mode research;
* strategy drift research;
* learning lifecycle.

### 4.5 Statistical Proof Layer

Definește:

* edge validation;
* sample thresholds;
* confidence intervals;
* multiple testing control;
* readiness states;
* degraded / freeze recommendation governance.

### 4.6 AI / Trade Physics / Calibration Intelligence

Definește:

* probabilistic modeling;
* 4D market model (energie, spațiu, timp, flux);
* TPS / learned probability;
* recommendation-only / bounded auto-adjust;
* calibration engine;
* evolution constraints.

---

## 5. Document-by-Document Classification

## 5.1 Strong Master Candidates

### A. `INTELLIGENCE_LAYER_ARCHITECTURE.md`

Role propus:

* **Master architecture document** pentru întregul layer de intelligence.

De ce:

* numele este corect pentru rol arhitectural;
* ar trebui să stea deasupra tuturor celorlalte;
* este locul potrivit pentru boundaries, ownership, sublayers și authority model.

Problemă actuală:

* există competiție semantică din partea:

  * `AI_TRADING_INTELLIGENCE_ARCHITECTURE.md`
  * `STRATEGY_INTELLIGENCE_SYSTEM.md`

Decizie propusă:

* `INTELLIGENCE_LAYER_ARCHITECTURE.md` rămâne **master**;
* celelalte două trebuie absorbite parțial și reclasificate.

---

### B. `RESEARCH_AND_LEARNING_FRAMEWORK_SPEC.md`

Role propus:

* **Master research governance document**.

De ce:

* este cel mai clar pentru focus dataset + trial dataset + analytics + controlled experimentation;
* separă bine research-ul de execuția live;
* oferă fundație bună pentru optimization governance.

Decizie propusă:

* rămâne master pentru research / learning / experimentation.

---

### C. `STATISTICAL_PROOF_LAYER.md`

Role propus:

* **Master proof / edge validation governance document**.

De ce:

* este distinct conceptual;
* introduce reguli matematice clare;
* definește readiness states și politici de degradare;
* nu trebuie diluat în research generic.

Decizie propusă:

* rămâne master separat.

---

### D. `AI_TRADE_PHYSICS_INTELLIGENCE_SPEC.md`

Role propus:

* **Master AI probabilistic / trade physics intelligence document**, dar numai dacă este patch-uit și aliniat la restul canonului.

De ce:

* formulează bine modelul 4D;
* introduce TPS și calibration engine;
* definește AI-ul ca layer de recomandare controlată.

Problemă actuală:

* overlap serios cu `AI_TRADE_PHYSICS_SPACE_MODEL_SPEC.md`;
* titlul sugerează că acoperă mai mult decât “space”, ceea ce este bine;
* însă trebuie să devină clar că acesta este documentul master, iar “space model” este subcomponentă.

Decizie propusă:

* `AI_TRADE_PHYSICS_INTELLIGENCE_SPEC.md` devine master;
* `AI_TRADE_PHYSICS_SPACE_MODEL_SPEC.md` devine satelit / sub-spec.

---

## 5.2 Strong Satellite Candidates

### E. `AI_STRATEGY_AUDITOR_SPEC.md`

Role propus:

* **Operational audit satellite spec**.

De ce:

* foarte util pentru daily audit behavior, bottlenecks și heatmap;
* dar nu trebuie să devină documentul master pentru întregul intelligence layer.

Decizie propusă:

* rămâne satelit sub domeniul Operational Strategy Audit.

---

### F. `INTELLIGENCE_DATA_PIPELINE_DEFINITION.md`

Role propus:

* **Data pipeline satellite**.

De ce:

* descrie fluxul și artifactele;
* este foarte util tehnic;
* dar nu este document de authority globală.

Decizie propusă:

* rămâne satelit tehnic.

---

### G. `INTELLIGENCE_FILES_AND_MODULE_MAP.md`

Role propus:

* **Module/file mapping satellite**.

De ce:

* foarte bun pentru implementare și navigare;
* nu trebuie amestecat cu arhitectura conceptuală.

Decizie propusă:

* rămâne satelit.

---

### H. `AUTONOMOUS_STRATEGY_EVOLUTION_SYSTEM.md`

Role propus:

* **Future-state / controlled evolution satellite**.

De ce:

* important ca direcție de viitor;
* nu trebuie să domine canonul actual cât timp ai spus clar că mai întâi stabilizăm și aliniem strategia și documentația;
* autonomia trebuie menținută sub governance strictă.

Decizie propusă:

* rămâne satelit de evoluție controlată.

---

## 5.3 Absorb / Merge / Reclassify Candidates

### I. `AI_TRADING_INTELLIGENCE_ARCHITECTURE.md`

Observație:

* titlul intră direct în conflict semantic cu `INTELLIGENCE_LAYER_ARCHITECTURE.md`.

Problemă:

* două documente care pretind arhitectura zonei intelligence;
* risc de dublare a authority model-ului.

Decizie propusă:

* conținutul util se absoarbe în `INTELLIGENCE_LAYER_ARCHITECTURE.md`;
* documentul se reclasifică drept deprecated sau absorbed după patch.

---

### J. `STRATEGY_INTELLIGENCE_SYSTEM.md`

Observație:

* este foarte util ca descriere operațională a subsistemului;
* dar semantic concurează cu documentul de arhitectură și cu auditorul.

Problemă:

* combină architecture overview + strategy heatmap + admin control panel + debug dashboard;
* deci este prea larg și se suprapune cu mai multe documente.

Decizie propusă:

* conținutul lui trebuie împărțit astfel:

  * partea arhitecturală → în `INTELLIGENCE_LAYER_ARCHITECTURE.md`
  * partea auditor / heatmap → în `AI_STRATEGY_AUDITOR_SPEC.md`
  * partea admin/debug UX → în documentele de admin/telegram relevante din alte seturi
* documentul apoi devine deprecated / absorbed.

---

### K. `AI_TRADE_PHYSICS_SPACE_MODEL_SPEC.md`

Observație:

* încă util, dar prea îngust față de `AI_TRADE_PHYSICS_INTELLIGENCE_SPEC.md`.

Problemă:

* dacă îl lăsăm egal ca autoritate cu documentul mai mare, apare confuzie: care e master, “space model” sau “intelligence spec”?

Decizie propusă:

* reclasificat ca sub-spec satelit;
* master devine `AI_TRADE_PHYSICS_INTELLIGENCE_SPEC.md`.

---

## 6. Key Overlaps Identified

## 6.1 Architecture Overlap

Suprapunere majoră între:

* `INTELLIGENCE_LAYER_ARCHITECTURE.md`
* `AI_TRADING_INTELLIGENCE_ARCHITECTURE.md`
* `STRATEGY_INTELLIGENCE_SYSTEM.md`

Tip de overlap:

* component inventory;
* flow definitions;
* operator control concepts;
* relation to observability and analytics.

Risc:

* trei adevăruri paralele despre aceeași zonă.

Rezolvare:

* un singur master de arhitectură;
* restul absorbite / reclasificate.

---

## 6.2 Audit vs Research Overlap

Suprapunere între:

* `AI_STRATEGY_AUDITOR_SPEC.md`
* `STRATEGY_INTELLIGENCE_SYSTEM.md`
* `RESEARCH_AND_LEARNING_FRAMEWORK_SPEC.md`

Tip de overlap:

* reject reason analysis;
* symbol performance;
* diagnostics;
* operator reports.

Distincția corectă:

* **Auditor** = diagnostic operațional și bottleneck insight din engine telemetry;
* **Research framework** = outcome-backed learning și experiment governance;
* **Strategy Intelligence System** = document intermediar care amestecă ambele.

Rezolvare:

* auditorul și research framework-ul rămân separate;
* documentul intermediar se absoarbe.

---

## 6.3 Trade Physics Overlap

Suprapunere între:

* `AI_TRADE_PHYSICS_SPACE_MODEL_SPEC.md`
* `AI_TRADE_PHYSICS_INTELLIGENCE_SPEC.md`

Tip de overlap:

* feasibility / space / reachability;
* trade probability modeling;
* AI scoring concepts.

Distincția corectă:

* `AI_TRADE_PHYSICS_INTELLIGENCE_SPEC.md` = master model;
* `AI_TRADE_PHYSICS_SPACE_MODEL_SPEC.md` = subcomponent / satellite / lower-level model.

---

## 6.4 Evolution vs Governance Overlap

Suprapunere între:

* `AUTONOMOUS_STRATEGY_EVOLUTION_SYSTEM.md`
* `RESEARCH_AND_LEARNING_FRAMEWORK_SPEC.md`
* `STATISTICAL_PROOF_LAYER.md`
* `AI_TRADE_PHYSICS_INTELLIGENCE_SPEC.md`

Tip de overlap:

* strategy improvement;
* recommendation loops;
* recalibration;
* approval boundaries.

Distincția corectă:

* **Research Framework** = produce insight și experimente;
* **Statistical Proof Layer** = validează edge și readiness;
* **Trade Physics Intelligence** = modelează probabilitatea și produce recomandări;
* **Autonomous Evolution** = viziune de orchestrare de nivel superior, dar strict bounded.

---

## 7. Canonical Structure Proposed

Propun structură canonică finală pentru clusterul D2:

### 7.1 Master Documents

1. `INTELLIGENCE_LAYER_ARCHITECTURE.md`

   * master pentru architecture / boundaries / sublayers / authority

2. `RESEARCH_AND_LEARNING_FRAMEWORK_SPEC.md`

   * master pentru learning / trials / experimentation governance

3. `STATISTICAL_PROOF_LAYER.md`

   * master pentru proof / edge validation / readiness states

4. `AI_TRADE_PHYSICS_INTELLIGENCE_SPEC.md`

   * master pentru AI probabilistic model / calibration intelligence

### 7.2 Satellite Documents

5. `AI_STRATEGY_AUDITOR_SPEC.md`

   * satelit operațional de audit și diagnostics

6. `INTELLIGENCE_DATA_PIPELINE_DEFINITION.md`

   * satelit tehnic pentru data pipeline

7. `INTELLIGENCE_FILES_AND_MODULE_MAP.md`

   * satelit tehnic pentru file/module map

8. `AUTONOMOUS_STRATEGY_EVOLUTION_SYSTEM.md`

   * satelit future-state / bounded evolution orchestration

9. `AI_TRADE_PHYSICS_SPACE_MODEL_SPEC.md`

   * satelit submodel / feasibility-space specialization

### 7.3 Absorb / Deprecate After Patch

10. `AI_TRADING_INTELLIGENCE_ARCHITECTURE.md`
11. `STRATEGY_INTELLIGENCE_SYSTEM.md`

Acestea nu trebuie lăsate în aceeași clasă de autoritate cu masterele.

---

## 8. Naming Problems That Must Be Fixed

### 8.1 “AI” vs “Intelligence”

În unele documente “AI” înseamnă:

* analytics;
* recommendation engine;
* ML layer;
* probabilistic trade modeling.

Asta creează confuzie.

Regulă propusă:

* **Intelligence** = umbrella architectural term;
* **AI** = subset specializat pentru learned / probabilistic / recommendation models.

---

### 8.2 “System” vs “Architecture” vs “Framework” vs “Layer”

Trebuie standardizate:

* **Architecture** = structură și boundaries;
* **Framework** = governance process / lifecycle / methodology;
* **Layer** = componentă ierarhică în sistem;
* **System** = termen generic, de evitat când există denumire mai precisă.

Implicație:

* `STRATEGY_INTELLIGENCE_SYSTEM.md` este slab denumit pentru canonul final;
* `INTELLIGENCE_LAYER_ARCHITECTURE.md` este mult mai potrivit ca master.

---

### 8.3 “Autonomous” trebuie limitat semantic

Din moment ce ai cerut control strict și approval/admin boundaries, termenul “autonomous” trebuie reinterpretat ca:

* bounded;
* recommendation-first;
* no unrestricted self-modifying live strategy.

Deci documentul de evolution trebuie patch-uit explicit ca să nu lase impresia unui AI care schimbă live strategia după bunul plac.

---

## 9. Contradiction Risks

### 9.1 Live authority ambiguity

Dacă nu consolidăm, poate apărea întrebarea:

* cine are voie să recomande?
* cine are voie să aprobe?
* cine doar observă?
* cine schimbă params?

Adevărul canonic trebuie să fie:

* observability și auditorul observă;
* research framework analizează;
* proof layer validează edge-ul;
* AI intelligence recomandă;
* admin/owner aprobă;
* strategia live nu se auto-rescrie necontrolat.

---

### 9.2 Dataset duplication risk

Trial data, focus history, engine events și analytics artifacts apar în mai multe locuri.

Fără consolidare, riscăm:

* scheme paralele;
* naming inconsistent;
* multiple “truths” despre aceleași dataseturi.

Trebuie unificate contractele de date și referințele la storage.

---

### 9.3 UX / Admin overlap risk

`STRATEGY_INTELLIGENCE_SYSTEM.md` introduce admin control panel și debug dashboard, dar zona de admin / Telegram / control plane există și în alte seturi de documente.

Asta înseamnă că patch-ul D2 trebuie coordonat cu seturile admin/control/telegram, nu izolat.

---

## 10. Recommended Upgrade Directions While Patching

Conform cerinței tale, în timp ce patch-uim nu doar reparăm, ci și propunem upgrade-uri. Pentru D2, cele mai bune upgrade-uri sunt:

### 10.1 Owner-Centric Governance Layer

Toate documentele D2 ar trebui patch-uite să reflecte explicit:

* Owner suprem;
* admin principal;
* admini funcționali pe rol;
* layer AI/research/reporting sub control uman.

---

### 10.2 Topic-Based Telegram Intelligence UX

Trebuie introdusă o separare clară pe topicuri:

* proof reports;
* daily auditor reports;
* anomaly / degraded alerts;
* recommendation queue;
* research summaries.

Nu toate mesajele intelligence trebuie să intre în același topic admin.

---

### 10.3 Recommendation Queue Instead of Silent Autotune

Orice propunere de schimbare din AI / research / proof trebuie să intre într-o coadă formală:

* recommendation_id
* source layer
* evidence summary
* expected benefit
* risk note
* approval status

---

### 10.4 Decision-Audit Integration

D2 trebuie aliniat explicit cu noua direcție de Decision Audit:

* de ce a murit semnalul;
* în ce strat a murit;
* ce score / gate / feasibility / spike / SR / timing l-a oprit;
* ce pattern repetitiv rezultă.

Asta este important mai ales pentru legătura între auditor, research și proof layer.

---

### 10.5 Strategy Change Governance

Trebuie să existe traseu clar:

* detect insight;
* verify statistically;
* create recommendation;
* admin review;
* bounded patch / param change;
* revalidation;
* proof reset dacă params_hash se schimbă.

---

### 10.6 Human-in-the-Loop AI

În toate documentele care folosesc termenul AI trebuie întărit:

* recommend-only implicit;
* admin approve by default;
* bounded-auto-adjust doar ca mod explicit activat;
* rollback + audit obligatoriu după orice schimbare.

---

## 11. Recommended Wave Order for Canonical Patching

### Wave D2-1 — Architecture Consolidation

Patch target:

* `INTELLIGENCE_LAYER_ARCHITECTURE.md`
* `AI_TRADING_INTELLIGENCE_ARCHITECTURE.md`
* `STRATEGY_INTELLIGENCE_SYSTEM.md`

Scop:

* alegere master;
* absorbție conținut util;
* marcarea documentelor redundante.

### Wave D2-2 — Research / Proof Separation Hardening

Patch target:

* `RESEARCH_AND_LEARNING_FRAMEWORK_SPEC.md`
* `STATISTICAL_PROOF_LAYER.md`

Scop:

* clarificare boundaries;
* legătură cu trials / params_hash / governance.

### Wave D2-3 — Trade Physics Canonicalization

Patch target:

* `AI_TRADE_PHYSICS_INTELLIGENCE_SPEC.md`
* `AI_TRADE_PHYSICS_SPACE_MODEL_SPEC.md`

Scop:

* alegere master;
* degradare space model la sub-spec.

### Wave D2-4 — Operational Audit Alignment

Patch target:

* `AI_STRATEGY_AUDITOR_SPEC.md`
* `INTELLIGENCE_DATA_PIPELINE_DEFINITION.md`
* `INTELLIGENCE_FILES_AND_MODULE_MAP.md`

Scop:

* aliniere artifacts, schemas, outputs și consumeri.

### Wave D2-5 — Evolution Governance

Patch target:

* `AUTONOMOUS_STRATEGY_EVOLUTION_SYSTEM.md`

Scop:

* bounded autonomy;
* owner approval;
* no live unrestricted self-modification.

---

## 12. Final Canonical Recommendation

Recomandarea mea canonică finală pentru clusterul D2 este:

### Keep as canonical masters

* `INTELLIGENCE_LAYER_ARCHITECTURE.md`
* `RESEARCH_AND_LEARNING_FRAMEWORK_SPEC.md`
* `STATISTICAL_PROOF_LAYER.md`
* `AI_TRADE_PHYSICS_INTELLIGENCE_SPEC.md`

### Keep as canonical satellites

* `AI_STRATEGY_AUDITOR_SPEC.md`
* `INTELLIGENCE_DATA_PIPELINE_DEFINITION.md`
* `INTELLIGENCE_FILES_AND_MODULE_MAP.md`
* `AUTONOMOUS_STRATEGY_EVOLUTION_SYSTEM.md`
* `AI_TRADE_PHYSICS_SPACE_MODEL_SPEC.md`

### Absorb then deprecate

* `AI_TRADING_INTELLIGENCE_ARCHITECTURE.md`
* `STRATEGY_INTELLIGENCE_SYSTEM.md`

---

## 13. Short Executive Verdict

D2 nu trebuie tratat ca 11 documente egale.

D2 trebuie tratat ca:

* 4 documente master;
* 5 documente satelit;
* 2 documente de absorbție/deprecation.

Asta reduce haosul, păstrează conținutul valoros, clarifică autoritatea canonică și creează baza corectă pentru patch-uri ulterioare în admin, control panel, telegram UX, research, AI și strategie.

---

## 14. Next Deliverable

Următorul document logic după acest audit este:

**D2-PATCH-PLAN — Intelligence Cluster Canonical Patch Plan**

Acela trebuie să conțină, fișier cu fișier:

* ce se editează;
* ce secțiuni se mută;
* ce se redenumește conceptual;
* ce se marchează “absorbed by”;
* ce adevăruri canonice noi introducem.
