D2-PATCH-PLAN — Intelligence Cluster Canonical Patch Plan

Status: Canonical working patch plan
Scope: D2 intelligence cluster
Date: 2026-03-14


---

1. Purpose

Acest document definește planul canonic de patch pentru clusterul D2 din BinaryBot / DROPi Signals.

Scopul planului este:

să transforme auditul D2 într-o secvență clară de intervenții documentare;

să evite patch-uri haotice, paralele sau contradictorii;

să stabilească ordinea corectă de consolidare;

să definească, fișier cu fișier, ce se păstrează, ce se mută, ce se absoarbe și ce se depreciază;

să pregătească documentația pentru alinierea viitoare cu admin panel, Telegram UX, observability, decision audit și cod.


Acest plan nu modifică încă documentele. El stabilește exact cum trebuie modificate.


---

2. Governing Canonical Truths

Acest patch plan trebuie executat respectând următoarele adevăruri deja stabilite în proiect:

1. DecisionObject este produs înainte de FSM.


2. Corridor Engine este înainte de Time Model în pipeline-ul strategic.


3. Documentația trebuie curățată și aliniată înainte de patch-uri în cod.


4. AI / research / intelligence sunt sub control uman și nu pot deveni auto-modificare live necontrolată.


5. Ownerul are autoritatea supremă; adminii și layerele de intelligence funcționează sub ierarhie clară.


6. Pentru documente lungi, livrarea se face ca fișier .md, nu ca mesaj lung în chat.




---

3. Scope of This Patch Plan

Documente incluse în D2 patch plan:

3.1 Proposed Master Documents

INTELLIGENCE_LAYER_ARCHITECTURE.md

RESEARCH_AND_LEARNING_FRAMEWORK_SPEC.md

STATISTICAL_PROOF_LAYER.md

AI_TRADE_PHYSICS_INTELLIGENCE_SPEC.md


3.2 Proposed Satellite Documents

AI_STRATEGY_AUDITOR_SPEC.md

INTELLIGENCE_DATA_PIPELINE_DEFINITION.md

INTELLIGENCE_FILES_AND_MODULE_MAP.md

AUTONOMOUS_STRATEGY_EVOLUTION_SYSTEM.md

AI_TRADE_PHYSICS_SPACE_MODEL_SPEC.md


3.3 Proposed Absorb/Deprecate Documents

AI_TRADING_INTELLIGENCE_ARCHITECTURE.md

STRATEGY_INTELLIGENCE_SYSTEM.md



---

4. Target End-State

La finalul patch planului, clusterul D2 trebuie să ajungă într-o stare în care:

există un singur master clar pentru architecture;

există un singur master clar pentru research governance;

există un singur master clar pentru statistical proof;

există un singur master clar pentru AI probabilistic / trade physics intelligence;

documentele satelit sunt clare și subordonate conceptual;

documentele redundante sunt absorbite și marcate deprecated;

toate referințele cross-doc sunt coerente;

vocabularul “AI / intelligence / architecture / system / framework / layer” este stabilizat;

relația cu admin, Telegram UX, observability și decision audit este explicită.



---

5. Patch Strategy Overview

Patch-ul trebuie executat în 5 valuri:

1. Wave D2-1 — Architecture Consolidation


2. Wave D2-2 — Research / Proof Boundary Hardening


3. Wave D2-3 — Trade Physics Canonicalization


4. Wave D2-4 — Operational Audit & Data Topology Alignment


5. Wave D2-5 — Evolution Governance Hardening



Ordinea este importantă. Nu inversăm valurile, pentru că documentele ulterioare depind semantic de cele anterioare.


---

6. Wave D2-1 — Architecture Consolidation

6.1 Objective

Să existe un singur document master de arhitectură pentru întregul cluster intelligence.

6.2 Files involved

Primary target:

INTELLIGENCE_LAYER_ARCHITECTURE.md


Absorb/reclassify sources:

AI_TRADING_INTELLIGENCE_ARCHITECTURE.md

STRATEGY_INTELLIGENCE_SYSTEM.md


6.3 Required actions

A. Patch INTELLIGENCE_LAYER_ARCHITECTURE.md

Trebuie să devină explicit documentul master pentru:

boundaries;

sublayers;

data flow conceptual;

authority model;

interfaces către observability, research, proof, admin și AI.


Trebuie să includă explicit:

Intelligence umbrella definition;

diferența dintre intelligence layer și AI sublayer;

role split între observability, auditor, research, proof, AI, admin;

human approval boundaries;

owner/admin governance chain.


B. Extract useful content from AI_TRADING_INTELLIGENCE_ARCHITECTURE.md

Conținut de absorbit doar dacă este util pentru:

component inventory;

architecture flow;

sublayer decomposition;

model boundaries.


După absorbție:

documentul se marchează absorbed by INTELLIGENCE_LAYER_ARCHITECTURE.md;

se mută în zonă deprecated/superseded, nu rămâne concurent semantic.


C. Extract useful content from STRATEGY_INTELLIGENCE_SYSTEM.md

Conținutul trebuie împărțit:

architecture overview → în INTELLIGENCE_LAYER_ARCHITECTURE.md

strategy heatmap / bottleneck / daily audit → în AI_STRATEGY_AUDITOR_SPEC.md

admin control / debug dashboard references → în documentele relevante din clusterul admin/telegram, nu păstrate aici ca autoritate principală


După absorbție:

documentul se marchează absorbed and decomposed;

se mută la deprecated.


6.4 End-state for Wave D2-1

La finalul acestui val:

INTELLIGENCE_LAYER_ARCHITECTURE.md = single architecture master;

celelalte două nu mai au voie să concureze semantic cu el.



---

7. Wave D2-2 — Research / Proof Boundary Hardening

7.1 Objective

Separarea clară dintre:

learning / experimentation / outcome analytics;

proof of edge / readiness / statistical significance.


7.2 Files involved

RESEARCH_AND_LEARNING_FRAMEWORK_SPEC.md

STATISTICAL_PROOF_LAYER.md


7.3 Required actions

A. Patch RESEARCH_AND_LEARNING_FRAMEWORK_SPEC.md

Trebuie clarificat că acest document guvernează:

focus learning dataset;

trials dataset;

outcome capture;

symbol/session/buffer research;

controlled experimentation;

long-term strategy optimization workflow.


Trebuie adăugat explicit:

că research produce insight și experiment recommendations, nu proof final de edge;

că orice improvement claim semnificativ trebuie trimis spre STATISTICAL_PROOF_LAYER.md pentru validare;

că schimbările de params trebuie legate de params_hash și versiune;

că research findings trebuie integrate într-o recommendation queue formală.


B. Patch STATISTICAL_PROOF_LAYER.md

Trebuie clarificat că acest document guvernează:

edge validation;

readiness states;

Wilson CI / exact binomial / multiple testing;

degraded state;

freeze recommendation.


Trebuie adăugat explicit:

că proof layer nu proiectează experimente și nu produce tuning logic;

doar validează sau respinge susținerea statistică a edge-ului;

că proof state este invalidat / reset când se schimbă params_hash sau algo_version relevant;

legătură formală cu recommendation governance și owner/admin review.


7.4 End-state for Wave D2-2

RESEARCH_AND_LEARNING_FRAMEWORK_SPEC.md = master research governance

STATISTICAL_PROOF_LAYER.md = master statistical validation governance

fără overlap necontrolat între ele



---

8. Wave D2-3 — Trade Physics Canonicalization

8.1 Objective

Stabilirea unui singur document master pentru AI probabilistic / Trade Physics model.

8.2 Files involved

AI_TRADE_PHYSICS_INTELLIGENCE_SPEC.md

AI_TRADE_PHYSICS_SPACE_MODEL_SPEC.md


8.3 Required actions

A. Patch AI_TRADE_PHYSICS_INTELLIGENCE_SPEC.md

Trebuie să devină explicit master pentru:

4D market model;

probabilistic trade feasibility;

TPS / learned probability;

calibration engine;

recommendation-only / bounded auto-adjust governance;

relation to research and proof layers.


Trebuie adăugat explicit:

no live unrestricted auto-modification;

all AI-generated parameter suggestions pass through human approval or explicitly bounded mode;

relation to decision audit, observability and post-outcome learning;

relație cu RESEARCH_AND_LEARNING_FRAMEWORK_SPEC.md și STATISTICAL_PROOF_LAYER.md.


B. Patch AI_TRADE_PHYSICS_SPACE_MODEL_SPEC.md

Trebuie reclasificat conceptual ca:

submodel;

lower-level specialization for structural space / reachability / feasibility.


Trebuie adăugat explicit:

this document is subordinate to AI_TRADE_PHYSICS_INTELLIGENCE_SPEC.md;

nu mai pretinde autoritate totală asupra întregii zone AI trade physics.


8.4 End-state for Wave D2-3

AI_TRADE_PHYSICS_INTELLIGENCE_SPEC.md = master

AI_TRADE_PHYSICS_SPACE_MODEL_SPEC.md = satellite sub-spec



---

9. Wave D2-4 — Operational Audit & Data Topology Alignment

9.1 Objective

Alinierea clară între auditul operațional și documentele tehnice care descriu datele și modulele.

9.2 Files involved

AI_STRATEGY_AUDITOR_SPEC.md

INTELLIGENCE_DATA_PIPELINE_DEFINITION.md

INTELLIGENCE_FILES_AND_MODULE_MAP.md


9.3 Required actions

A. Patch AI_STRATEGY_AUDITOR_SPEC.md

Trebuie clarificat că auditorul este responsabil pentru:

bottleneck detection;

starvation detection;

reject reason clustering;

symbol heatmaps;

operational diagnostics;

daily / periodic reports.


Trebuie adăugat explicit:

auditorul operează în principal pe observability / engine telemetry;

auditorul nu validează singur edge-ul statistic;

auditorul nu aprobă param changes;

auditorul poate produce recommendations, anomaly flags și escalation către research/proof/admin.


Trebuie aliniat cu noua direcție de Decision Audit:

semnalul trebuie urmărit pe straturi de decizie;

trebuie să existe compatibilitate cu motivele pentru care semnalul moare sau este respins.


B. Patch INTELLIGENCE_DATA_PIPELINE_DEFINITION.md

Trebuie clarificat:

care sunt sursele de date canonice;

care sunt artifactele persistente;

care sunt snapshot-urile;

care sunt consumatorii principali;

ce este append-only și ce este derived.


Trebuie adăugat explicit:

mapping clar între engine events, decision audit events, focus history, trials, proof state și analytics reports;

ownership per artifact;

contract boundaries.


C. Patch INTELLIGENCE_FILES_AND_MODULE_MAP.md

Trebuie clarificat:

ce module produc date;

ce module consumă date;

ce fișiere sunt canonical state;

ce fișiere sunt cache/report/generated outputs.


Trebuie adăugat explicit:

cross-reference la pipeline definition;

legătura cu admin topic outputs și dashboards;

naming alignment cu documentele master.


9.4 End-state for Wave D2-4

auditorul, pipeline-ul și module map-ul devin coerente între ele;

nu mai există contradicții despre cine produce / citește / validează ce.



---

10. Wave D2-5 — Evolution Governance Hardening

10.1 Objective

Să redefinim “autonomous evolution” într-o formă compatibilă cu controlul uman și cu politica de schimbare canonică a proiectului.

10.2 File involved

AUTONOMOUS_STRATEGY_EVOLUTION_SYSTEM.md


10.3 Required actions

Trebuie patch-uit explicit că:

autonomia este bounded;

default mode este recommend-only;

auto-adjust nu este implicit și nu poate fi nelimitat;

orice schimbare importantă trece prin governance și approval;

params/version/hash changes implică revalidation;

rollout-ul trebuie să aibă rollback, audit și comparison logic.


Trebuie introdusă o schemă de tip:

detect insight;

quantify evidence;

validate statistically;

prepare recommendation;

owner/admin approval;

bounded deploy;

post-change audit;

proof reset / revalidation.


10.4 End-state for Wave D2-5

documentul nu mai sună ca un layer de self-modifying system necontrolat;

devine o orchestrare de evoluție asistată și guvernată.



---

11. Required Cross-Document Patches

Indiferent de val, următoarele adevăruri trebuie introduse transversal în toate documentele relevante:

11.1 Human Governance Truth

owner supreme authority

principal admin full access

role-based functional admins

intelligence layers do not outrank human governance


11.2 Recommendation Queue Truth

Toate insight-urile cu impact operațional trebuie să poată fi transformate în:

recommendation record

evidence bundle

review status

approval status

implementation link

post-validation result


11.3 Decision Audit Truth

Toate documentele relevante trebuie să se alinieze cu noua direcție de audit al deciziilor strategiei:

unde moare semnalul;

de ce moare;

care gate sau strat l-a oprit;

cum se agregă aceste cauze;

cum se folosesc în auditor, research și AI recommendation.


11.4 Version / Params / Hash Truth

Orice research, proof sau AI recommendation cu valoare operațională trebuie legat de:

algo_version

params_hash

timeframe/symbol scope dacă este relevant


11.5 Telegram Topic Separation Truth

Outputs intelligence trebuie separate pe topicuri sau fluxuri distincte:

operational alerts

daily auditor reports

proof state changes

research summaries

recommendation queue



---

12. File-by-File Patch Matrix

12.1 INTELLIGENCE_LAYER_ARCHITECTURE.md

Patch type:

expand + harden + absorb references


Must add:

umbrella intelligence definition

AI as subset, not synonym

authority boundaries

owner/admin governance chain

interfaces to observability/research/proof/AI/admin


Must receive absorbed concepts from:

AI_TRADING_INTELLIGENCE_ARCHITECTURE.md

STRATEGY_INTELLIGENCE_SYSTEM.md



---

12.2 AI_TRADING_INTELLIGENCE_ARCHITECTURE.md

Patch type:

absorb-useful-content then deprecate


Must do:

preserve any useful conceptual blocks in master

append absorbed-by notice

move to deprecated/superseded after execution



---

12.3 STRATEGY_INTELLIGENCE_SYSTEM.md

Patch type:

decompose then deprecate


Must do:

move architecture content to master architecture doc

move auditor content to auditor spec

move admin/debug references to correct admin/telegram docs later

append absorbed/decomposed note



---

12.4 RESEARCH_AND_LEARNING_FRAMEWORK_SPEC.md

Patch type:

harden boundaries + integrate governance


Must add:

distinction from proof layer

recommendation queue linkage

params/version/hash traceability

explicit experiment governance



---

12.5 STATISTICAL_PROOF_LAYER.md

Patch type:

harden readiness governance


Must add:

explicit relation to research findings

explicit non-authority over tuning design

params/version/hash invalidation rule strengthened

recommendation/freeze governance clarified



---

12.6 AI_TRADE_PHYSICS_INTELLIGENCE_SPEC.md

Patch type:

elevate to master + connect to canon


Must add:

relation to research/proof/decision-audit

bounded autonomy language

recommendation pipeline

admin approval truth



---

12.7 AI_TRADE_PHYSICS_SPACE_MODEL_SPEC.md

Patch type:

downgrade to subordinate sub-spec


Must add:

subordinate-to-master notice

precise scope restriction to structural/space modeling



---

12.8 AI_STRATEGY_AUDITOR_SPEC.md

Patch type:

harden operational scope


Must add:

operational diagnostics boundary

non-proof/non-tuning authority

decision audit integration

escalation outputs



---

12.9 INTELLIGENCE_DATA_PIPELINE_DEFINITION.md

Patch type:

contract clarification


Must add:

ownership per artifact

state vs cache vs report distinction

decision audit linkage

proof/report/admin output mapping



---

12.10 INTELLIGENCE_FILES_AND_MODULE_MAP.md

Patch type:

topology clarification


Must add:

producer/consumer map

canonical vs generated file separation

relation to data pipeline definition



---

12.11 AUTONOMOUS_STRATEGY_EVOLUTION_SYSTEM.md

Patch type:

governance rewrite


Must add:

bounded autonomy

no unrestricted self-modification

human approval chain

rollback/revalidation logic



---

13. Deprecation Rules for D2

Documentele nu se depreciază arbitrar. Pentru D2, regulile corecte sunt:

13.1 Deprecate only after absorption

Un document redundant poate fi deprecated doar după ce:

conținutul util a fost extras;

documentul master a fost patch-uit;

există notă explicită absorbed by ....


13.2 Do not delete

Documentele redundante:

nu se șterg;

se mută în deprecated/superseded;

se păstrează cu context istoric.


13.3 Add deprecation metadata

Documentele absorbite trebuie să conțină:

status: deprecated or superseded

reason

replacement document

date



---

14. Recommended Upgrade Additions Beyond Pure Cleanup

Pe lângă curățare, patch planul recomandă și upgrade-uri reale:

14.1 Intelligence Recommendation Ledger

Un nou concept canonic care ar trebui introdus transversal:

recommendation_id

source_doc/source_layer

evidence summary

linked params_hash

approval state

implementation state

outcome after deployment


14.2 Proof-to-Admin Escalation UX

Când proof state devine DEGRADED sau HARD_PROVEN, trebuie standardizat:

cine primește alerta;

în ce topic;

ce câmpuri sunt trimise;

ce acțiune recomandată se afișează.


14.3 Research-to-Strategy Change Pipeline

Trebuie definit clar circuitul:

research insight → proof check → recommendation → approval → bounded rollout → validation.


14.4 Decision Death Taxonomy

D2 trebuie să sprijine explicit o taxonomie standard pentru motivele de moarte / reject ale semnalului, compatibilă cu:

score

SR

spike

feasibility

focus

PRE/CONFIRM/OPEN_NOW transitions

execution-state death points


14.5 Owner Dashboard Thinking

Deși UI-ul complet este în alt cluster, documentele D2 trebuie să fie scrise astfel încât să poată alimenta un viitor owner dashboard cu:

edge status

current degraded risks

top reject reasons

recommended parameter reviews

strongest / weakest symbols

proof state changes



---

15. Execution Order Recommendation

Ordinea concretă recomandată a fișierelor pentru patch este:

1. INTELLIGENCE_LAYER_ARCHITECTURE.md


2. AI_TRADING_INTELLIGENCE_ARCHITECTURE.md


3. STRATEGY_INTELLIGENCE_SYSTEM.md


4. RESEARCH_AND_LEARNING_FRAMEWORK_SPEC.md


5. STATISTICAL_PROOF_LAYER.md


6. AI_TRADE_PHYSICS_INTELLIGENCE_SPEC.md


7. AI_TRADE_PHYSICS_SPACE_MODEL_SPEC.md


8. AI_STRATEGY_AUDITOR_SPEC.md


9. INTELLIGENCE_DATA_PIPELINE_DEFINITION.md


10. INTELLIGENCE_FILES_AND_MODULE_MAP.md


11. AUTONOMOUS_STRATEGY_EVOLUTION_SYSTEM.md



Motiv:

întâi fixăm arhitectura;

apoi limitele research/proof;

apoi modelul AI;

apoi operaționalul și topologia tehnică;

la final, evolution governance.



---

16. Final Patch Governance Rule

Niciun document din D2 nu trebuie patch-uit izolat “după inspirație”.

Fiecare patch ulterior trebuie să indice explicit:

documentul sursă;

rolul lui în structură;

ce adevăr canonic rezolvă;

ce overlap reduce;

ce documente afectează colateral;

dacă produce absorbție / deprecation.



---

17. Final Executive Summary

D2 trebuie transformat dintr-un cluster bun, dar fragmentat, într-un cluster canonic stabil.

Acest lucru se obține astfel:

alegem 4 documente master;

păstrăm 5 documente satelit;

absorbim și depreciem 2 documente redundante;

introducem governance clară pentru AI, research, proof și audit;

aliniem totul la owner/admin hierarchy, decision audit și future Telegram intelligence UX.



---

18. Next Deliverable

După acest plan, următoarea livrare logică este:

Wave D2-1 Patch Draft

adică documentul de patch concret pentru primul val:

INTELLIGENCE_LAYER_ARCHITECTURE.md

AI_TRADING_INTELLIGENCE_ARCHITECTURE.md

STRATEGY_INTELLIGENCE_SYSTEM.md


Acela trebuie să fie tot în format .md și să conțină textul propus concret pentru editare canonică.