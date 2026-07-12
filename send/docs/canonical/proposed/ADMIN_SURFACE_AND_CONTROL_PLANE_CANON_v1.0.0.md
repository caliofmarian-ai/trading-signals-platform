# ADMIN_SURFACE_AND_CONTROL_PLANE_CANON_v1.0.0

Version: 1.0.0  
Status: Proposed Canonical Root Document  
Owner: BinaryBot / DROPi Signals  
Scope: Canonical definition of the human/operator control plane, including Owner authority, hierarchical admin layers, Telegram admin interface relation, observability consumption, affiliate/admin segmentation, and separation between truth, control, and execution surfaces

Depends on:
- canonical/active/CANONICAL_STRATEGY_STACK_v1.0.0.md
- canonical/active/ALGO_SPEC_v2.0.0.md
- canonical/active/DECISION_OBJECT_CANONICAL_SPEC_v1.0.0.md
- canonical/active/FSM_DECISION_ENGINE_SPEC_v1.0.0.md
- canonical/active/SR_CORRIDOR_ENGINE_SPEC_v2.0.0.md
- canonical/active/TIME_MODEL_UNIFIED_CANON_v2.0.0.md
- canonical/active/SIGNAL_ENGINE_EXECUTION_SPEC_v2.0.0.md
- canonical/active/OBSERVABILITY_SPEC_v2.0.0.md
- canonical/active/GOVERNANCE_AND_CHANGE_CONTROL.md
- canonical/active/AFFILIATE_SIGNAL_DISTRIBUTION_MODEL.md

---

## 1. PURPOSE

Acest document definește canonul root pentru suprafața umană de control și operare din BinaryBot / DROPi Signals.

Scopul lui este să stabilească, într-o singură sursă de adevăr:

- cine deține autoritatea supremă
- ce layere administrative există
- ce poate vedea fiecare layer
- ce poate controla fiecare layer
- cum se separă suprafețele de adevăr, control și execuție
- cum consumă admin surface datele din observability
- cum se integrează Telegram admin ca interfață operațională
- cum se integrează affiliate / influencer admin
- cum se integrează research / AI / reporting tooling
- cum se evită amestecarea necanonică dintre strategie, execuție și control uman

Acest document nu redefinește strategia, FSM-ul, Signal Engine-ul sau Observability.
El definește **cum sunt consumate, expuse și controlate uman** aceste adevăruri și capabilități.

---

## 2. WHY THIS DOCUMENT EXISTS

În documentația istorică au apărut separat și uneori suprapus:

- admin control specs
- admin operations specs
- Telegram UX / command docs
- dashboard / debug specs
- distribution / channel control docs
- affiliate distribution notes

Aceste documente pot rămâne utile,
dar fără un root canon pentru control plane apar inevitabil:

- suprapuneri de autoritate
- roluri neclare
- acces excesiv
- interfețe inconsecvente
- amestec între truth display și command execution
- confuzie între observability și chat notifications
- lipsa unei ierarhii canonice pentru Owner, admins și affiliate roles

Prin urmare, acest document există pentru a unifica și bloca adevărul de arhitectură al suprafeței de control uman.

---

## 3. FUNDAMENTAL PRINCIPLE

BinaryBot are două lumi distincte, dar conectate:

1. **machine truth plane**
2. **human control plane**

Machine truth plane conține adevărul sistemului:
- market model
- corridor engine
- time model
- scoring
- `DecisionObject`
- FSM
- signal engine
- observability traces

Human control plane conține:
- suprafețe de vizualizare
- controale operaționale
- guvernanță administrativă
- audit views
- tooling de analiză și reporting

Control plane-ul uman nu are voie să rescrie informal adevărul canonic produs de machine truth plane.

El poate:
- să îl citească
- să îl filtreze
- să îl expună
- să îl controleze la nivel de policy și operations
- să îl investigheze
- să aplice override-uri explicit permise

Dar nu poate deveni o sursă paralelă de adevăr strategic.

---

## 4. CORE CANONICAL SEPARATION

Începând cu acest document, separarea canonică obligatorie este:

### 4.1 Truth Layer
Aici trăiește adevărul semantic și operațional al sistemului:
- strategy outputs
- structural truth
- time truth
- score truth
- `DecisionObject`
- FSM operational truth
- execution truth
- observability truth

### 4.2 Display Layer
Aici trăiesc suprafețele care afișează adevărul:
- admin dashboard
- Telegram admin views
- health summaries
- debug drilldown
- audit summaries
- affiliate stats surfaces
- reporting surfaces

### 4.3 Control Layer
Aici trăiesc comenzile și politicile:
- channel enable / disable
- routing rules
- admin permissions
- role-based controls
- operational cooldowns
- maintenance mode
- guardrails
- symbol activation policies
- distribution controls

### 4.4 Delivery Layer
Aici trăiește emiterea efectivă către destinații:
- signal engine delivery
- channel orchestration
- outbound notification surfaces
- affiliate delivery segmentation

### 4.5 Governance Layer
Aici trăiesc regulile de schimbare și autoritate:
- Owner authority
- approval rules
- change control
- audit requirements
- rollback authority
- protected controls

Aceste layere sunt conectate, dar nu trebuie confundate.

---

## 5. OWNER PRINCIPLE

Owner-ul este nivelul suprem al sistemului.

În contextul acestui proiect, Owner-ul este autoritatea finală umană asupra:

- strategiei aprobate
- documentației canonice
- control plane governance
- activării sau dezactivării unor mari capabilități
- structurii administrative
- programului affiliate
- politicilor de distribuție
- priorităților de research și AI
- direcției produsului

Owner-ul nu este doar un admin „mai mare”.
Owner-ul este instanța finală de autoritate.

Orice model ierarhic trebuie să pornească de la acest adevăr.

---

## 6. CANONICAL HUMAN CONTROL HIERARCHY

Ierarhia canonică a control plane-ului este:

1. **Owner**
2. **Primary Admin**
3. **Functional Admins**
4. **Affiliate / Influencer Admin**
5. **Research / AI / Reporting Operators**
6. **Read-only / Audit Observers** (opțional, dacă sistemul cere)

Această ordine definește ierarhia oficială a suprafeței umane de control.

---

## 7. OWNER LAYER

## 7.1 Role

Owner-ul este sursa supremă de autoritate umană.

## 7.2 Minimum Authority

Owner-ul trebuie să poată:

- vedea toate suprafețele
- aproba sau bloca schimbări majore
- vedea toate audit trails
- vedea observability global
- controla rolurile și permisiunile
- controla distribuția pe canale
- controla afilierea și regulile programului affiliate
- accesa raportarea strategică și operațională
- activa sau dezactiva sisteme majore
- controla override-urile critice
- impune freeze / rollback / maintenance

## 7.3 Protected Nature

Nicio altă categorie administrativă nu poate depăși sau ocoli autoritatea Owner-ului.

Acesta este adevăr canonic blocat.

---

## 8. PRIMARY ADMIN LAYER

## 8.1 Role

Primary Admin este administratorul principal operațional sub Owner.

## 8.2 Purpose

Acest layer există pentru a conduce operațiunile zilnice fără a înlocui Owner-ul.

## 8.3 Minimum Authority

Primary Admin poate avea acces complet la:

- health monitoring
- operational dashboards
- admin panel controls
- routing and channel controls
- symbol activation tooling
- observability drilldown
- debug workflows
- incident handling
- affiliate operations oversight
- reporting workflows

## 8.4 Limits

Primary Admin nu trebuie să aibă autoritate implicită de a:
- rescrie canonul fără proces de governance
- schimba structura fundamentală a rolurilor fără aprobare
- altera programul affiliate la nivel constituțional fără aprobare
- redefini adevărul strategic al sistemului

---

## 9. FUNCTIONAL ADMIN LAYER

## 9.1 Role

Functional Admins sunt admini specializați pe domenii.

## 9.2 Example Domains

Exemple tipice:
- distribution admin
- observability admin
- incident admin
- support/admin comms
- symbol universe admin
- payout/affiliate ops admin
- moderation/admin channel admin
- quality/review admin

## 9.3 Principle

Functional Admins trebuie să aibă acces strict pe domeniul lor,
nu acces complet implicit la întreg sistemul.

## 9.4 Minimum Rule

Orice Functional Admin trebuie definit prin:
- scope
- allowed views
- allowed controls
- forbidden controls
- audit trail requirements

---

## 10. AFFILIATE / INFLUENCER ADMIN LAYER

## 10.1 Role

Affiliate / Influencer Admin este un layer administrativ limitat,
dedicat programului de afiliere și distribuție asociată.

## 10.2 Purpose

Acest layer există pentru a permite operarea programului affiliate
fără a expune adevărul complet al sistemului intern.

## 10.3 Allowed Access

Affiliate / Influencer Admin poate avea acces la:
- utilizatorii aduși de acel afiliat
- statistici despre conversii / activitate relevante programului
- performanță de canal afiliat
- payout visibility relevantă
- materiale promo / distribution resources permise
- starea programului propriu
- coduri / linkuri / referințe aferente

## 10.4 Forbidden Access

Affiliate / Influencer Admin nu trebuie să aibă acces la:
- full observability internă
- truth strategic complet
- debug intern complet
- signals outside permitted segmentation
- alți afiliați fără drept explicit
- controale operaționale globale
- FSM intern complet
- date sensibile din afara programului affiliate

## 10.5 Canonical Principle

Affiliate layer este un layer de business-admin limitat,
nu un layer de core admin.

---

## 11. RESEARCH / AI / REPORTING LAYER

## 11.1 Role

Acest layer grupează operatorii și uneltele orientate spre:
- research
- analiză
- raportare
- insight generation
- quality review
- optimization support

## 11.2 Purpose

Acest layer există pentru a transforma adevărul observabil în:
- rapoarte utile
- insight-uri strategice
- rezumate operaționale
- analize de rejection/degradation
- propuneri de optimizare

## 11.3 Limits

Acest layer nu trebuie să aibă implicit:
- comenzi de livrare directă
- autoritate de distribuție
- override operațional global
- autoritate de schimbare canonică fără governance

## 11.4 Importance

Acest layer este canonic important pentru viziunea BinaryBot,
deoarece sistemul nu este doar de execuție,
ci și de învățare, explicabilitate și optimizare continuă.

---

## 12. READ-ONLY / AUDIT OBSERVER LAYER

Acest layer este opțional, dar recomandat.

El poate exista pentru:
- audit intern
- review extern
- compliance internă
- verificare de incidente
- consultare limitată

Acest layer are acces la view-uri controlate și nu la comenzi active.

---

## 13. ROLE DESIGN PRINCIPLE

Orice rol din control plane trebuie definit prin patru întrebări:

1. ce poate vedea?
2. ce poate controla?
3. ce nu poate controla?
4. ce audit produce când acționează?

Dacă aceste întrebări nu au răspuns clar,
rolul nu este canonic definit suficient.

---

## 14. LEAST PRIVILEGE RULE

Control plane-ul trebuie să respecte principul de minimum access necesar.

Aceasta înseamnă:
- nu oferim acces total din comoditate
- nu amestecăm affiliate cu core admin
- nu oferim debug complet unde nu este necesar
- nu oferim control de distribuție fără scop operațional valid
- nu expunem date interne mai mult decât cere rolul

Aceasta este regula canonică de securitate și claritate operațională.

---

## 15. DISPLAY VS CONTROL RULE

Trebuie să existe separare clară între:

- **a vedea**
- **a acționa**

Faptul că un rol poate vedea un status, un trace sau un summary
nu înseamnă automat că poate modifica policy, routing, channel state sau override.

Această separare este obligatorie în panou și în Telegram admin interface.

---

## 16. TELEGRAM RELATION PRINCIPLE

Telegram admin este o suprafață de control și expunere operațională,
dar nu este sursa fundamentală de adevăr a sistemului.

Truth-ul rămâne în:
- strategy pipeline
- `DecisionObject`
- FSM
- signal engine traces
- observability storage / semantic event model

Telegram poate:
- afișa rezumate
- primi comenzi
- expune health views
- expune alerting
- expune drilldowns scurte
- declanșa controale permise

Dar nu trebuie tratat ca storage canonic și nici ca adevăr primar.

Această regulă este aliniată cu Observability canon.

---

## 17. ADMIN DASHBOARD RELATION PRINCIPLE

Panoul admin este suprafața principală de vizualizare și control structurată.

Acesta trebuie să poată consuma, în mod canonic:
- health views
- rejection summaries
- stage-of-death summaries
- signal flow summaries
- debug drilldown
- role-specific operational controls
- affiliate monitoring surfaces
- reporting and insight surfaces

Panoul admin nu redefinește adevărul;
îl consumă și îl organizează pentru uz uman.

---

## 18. OBSERVABILITY CONSUMPTION RULE

Control plane-ul trebuie să consume observability,
nu să inventeze propriile explicații paralele.

Minimum, control plane-ul trebuie să poată consuma:
- correlation id
- symbol
- direction
- stage identifier
- outcome family
- decision summaries
- reject reasons
- degrade path
- stage-of-death
- execution outcome
- explanation snippets

Acestea trebuie prezentate diferențiat pe roluri și contexte.

---

## 19. REQUIRED HUMAN VIEWS

Control plane-ul trebuie să poată oferi, în forme adecvate rolului, minimum următoarele familii de view:

- system health view
- live signal flow view
- rejection analytics view
- stage-of-death view
- execution outcome view
- symbol activity view
- channel status view
- affiliate program view
- incident / anomaly view
- strategy performance review summaries
- audit / history view

Nu toate view-urile sunt pentru toate rolurile.

---

## 20. REQUIRED HUMAN CONTROLS

Control plane-ul trebuie să poată găzdui, în mod controlat, minimum următoarele familii de comenzi:

- channel enable / disable
- routing and distribution controls
- symbol activation / deactivation
- maintenance controls
- flood/cooldown controls
- affiliate program operational controls
- admin role assignment controls
- observability filtering tools
- incident acknowledgment / escalation tools
- report generation triggers
- protected critical controls pentru Owner / Primary Admin

Orice control trebuie auditat.

---

## 21. PROTECTED CONTROLS PRINCIPLE

Există controale care trebuie protejate special.

Exemple:
- emergency global stop
- enable/disable distribuție majoră
- modificarea routingului critic
- schimbări de roluri de nivel înalt
- modificarea guardrail-urilor critice
- maintenance mode global
- resetarea unor stări critice

Aceste controale trebuie să fie:
- limitate pe rol
- clar marcate
- auditabile
- ideal confirmate explicit
- ușor de investigat post-action

---

## 22. AUDITABILITY RULE FOR HUMAN ACTIONS

Orice acțiune umană relevantă din control plane trebuie să poată lăsa urme auditabile.

Minimum:
- actor role
- actor identity
- action type
- target
- timestamp
- pre-state summary
- post-state summary
- outcome
- reason/context dacă este cazul

Fără acest layer, control plane-ul devine opac și periculos.

---

## 23. NO SHADOW TRUTH RULE

Este interzisă apariția unui “shadow truth” în control plane.

Sunt interzise:
- statusuri manuale care contrazic observability truth
- explicații umane salvate ca și cum ar fi truth strategic
- folosirea Telegram message history ca substitut de audit canonic
- interpretări locale de admin tratate ca verdict oficial al FSM
- payload-ul final tratat ca adevăr strategic complet

Adevărul canonic rămâne în sistemul de truth și observability.

---

## 24. OVERRIDE PRINCIPLE

Override-urile umane pot exista,
dar trebuie tratate ca excepții controlate.

Un override trebuie să fie:
- explicit
- limitat
- auditat
- justificabil
- recognoscibil downstream
- separat de truth-ul produs automat de strategie/FSM

Override-ul nu trebuie să falsifice retrospectiv adevărul sistemului.
Trebuie să fie înregistrat ca intervenție umană.

---

## 25. INCIDENT MANAGEMENT RELATION

Control plane-ul trebuie să includă sau să poată susține fluxuri de incident management.

Acestea pot include:
- detectare anomalie
- alertare
- triage
- ack/nack
- escaladare
- freeze / maintenance
- rollback operational
- post-incident review

Acest document nu definește playbook-ul complet de incidente,
dar definește că incident management este parte legitimă din control plane.

---

## 26. AFFILIATE SEGMENTATION RULE

Programul affiliate trebuie să fie integrat în control plane fără a compromite ierarhia principală.

Regulile canonice sunt:
- affiliate data este segmentată
- affiliate controls sunt limitate
- affiliate visibility este scoped
- affiliate reporting este permis doar în limitele programului
- affiliate layer nu poate accesa complet observability internă
- affiliate layer nu poate executa core admin actions

---

## 27. RESEARCH / AI INTEGRATION RULE

Control plane-ul trebuie să poată include componente de research și AI,
dar acestea nu trebuie să devină autoritate informală necontrolată.

Aceste componente pot:
- sumariza observability
- detecta pattern-uri
- genera rapoarte
- semnala anomalii
- propune optimizări
- grupa reject reasons
- analiza stage-of-death trends

Dar:
- nu rescriu canonul singure
- nu emit politici singure
- nu devin sursă autonomă de distribuție fără reguli explicite
- nu înlocuiesc governance-ul uman

---

## 28. SIGNAL DISTRIBUTION RELATION

Control plane-ul poate controla politicile de distribuție,
dar nu execută el însuși delivery-ul efectiv.

Signal Engine rămâne layerul de execuție finală.

Control plane-ul poate:
- activa/dezactiva canale
- schimba politici permise
- seta guardrail-uri
- controla segmentarea affiliate
- vedea delivery outcomes

Dar nu trebuie să ocolească:
- FSM verdict
- execution gating
- execution outcome model

---

## 29. SYMBOL CONTROL RELATION

Control plane-ul poate include suprafețe de administrare pentru universul de simboluri.

Acestea pot include:
- activare/dezactivare simboluri
- grupare pe liste
- prioritizare
- policies pe simbol
- observability pe simbol
- summary de performanță / rejection per simbol

Dar aceste controale sunt politici de operare,
nu rescriere a logicii canonice interne.

---

## 30. HEALTH MODEL RELATION

Health view-ul uman trebuie să fie derivat din semnale observabile reale,
nu din impresii sau mesaje disparate.

Minimum, health-ul trebuie să poată reflecta:
- starea pipeline-ului
- starea distribuției
- starea observability
- starea canalelor
- starea componentelor administrative critice
- anomalii sau backlog
- incidente active

Health nu este echivalent cu „botul răspunde la comenzi”.
Health este stare operațională semantică.

---

## 31. DASHBOARD / TELEGRAM CONSISTENCY RULE

Dacă aceeași informație este expusă în dashboard și în Telegram admin,
ea trebuie să fie consistentă semantic.

Diferențele permise sunt:
- nivel de detaliu
- format
- compactare
- drepturi de acces

Nu sunt permise:
- definiții diferite ale aceluiași outcome
- taxonomii diferite de reject reasons
- statusuri contradictorii
- timpuri interpretate diferit față de canon

---

## 32. REQUIRED TAXONOMY ALIGNMENT

Control plane-ul trebuie să respecte taxonomiile canonice venite din domeniile sursă.

Minimum:
- outcome families din observability
- outcome families din signal execution
- structural semantics din corridor engine
- time semantics din unified time canon
- verdict semantics din FSM
- `DecisionObject` semantic families

Control plane-ul nu are voie să inventeze etichete UI care distrug sau amestecă aceste taxonomii.

---

## 33. DOCUMENT RELATION PRINCIPLE

Toate documentele de mai jos trebuie să fie subordinate sau aliniate acestui canon root:

- ADMIN_CONTROL_SPEC
- ADMIN_OPERATIONS_SPEC
- ADMIN_UX_V2_SPEC
- ADMIN_TREE_MAP
- ADMIN_CALLBACK_MAP
- TELEGRAM_UX
- SIGNAL_DEBUG_DASHBOARD_SPEC
- SIGNAL_DISTRIBUTION_SPEC
- CHANNEL_CONFIG_SPEC
- AFFILIATE_SIGNAL_DISTRIBUTION_MODEL

Aceste documente pot detalia implementarea,
dar nu pot contrazice acest root canon.

---

## 34. FORBIDDEN CONTROL PLANE PATTERNS

Sunt interzise ca modele canonice active:

- Telegram tratat ca sursă principală de adevăr
- panou admin tratat ca loc unde se “redefinește” semnalul
- affiliate admin cu acces global complet
- roluri fără limită clară de autoritate
- view-uri care combină strategic truth cu execuție într-un blob opac
- lipsa audit trail pentru controale critice
- override-uri ascunse sau neexplicate
- health definit doar prin “bot răspunde”
- shadow truth produs manual în locul observability
- comenzi de control fără rol clar și fără logging

---

## 35. CODE ALIGNMENT RULE

Orice implementare a control plane-ului trebuie să poată răspunde clar la întrebările:

- unde este definită ierarhia rolurilor?
- ce poate vedea fiecare rol?
- ce poate controla fiecare rol?
- cum este separată afișarea de control?
- cum consumă dashboard-ul și Telegram observability truth?
- cum sunt protejate comenzile critice?
- cum este auditată fiecare acțiune relevantă?
- cum este segmentat affiliate layer?
- cum este integrat research / AI / reporting layer?
- cum se evită shadow truth?

Dacă aceste răspunsuri nu sunt clare,
alinierea codului este incompletă.

---

## 36. IMPLEMENTATION PRINCIPLE

De la această versiune înainte:

- orice patch pe panou admin trebuie ancorat în acest document
- orice patch pe Telegram admin interface trebuie ancorat în acest document
- orice patch pe affiliate admin trebuie ancorat în acest document
- orice patch pe health / debug / audit surfaces trebuie ancorat în acest document
- orice nou rol administrativ trebuie definit explicit aici sau într-un document subordonat aliniat

Niciun document nou nu are voie să redefinească separat ierarhia umană principală fără referință explicită la acest canon.

---

## 37. FINAL PRINCIPLE

BinaryBot / DROPi Signals nu este doar un bot de semnale.
Este un sistem cu adevăr semantic intern și cu suprafețe umane de control, audit și guvernanță.

Prin urmare, control plane-ul canonic trebuie să fie:

- ierarhic clar
- separat de truth plane
- separat de delivery plane
- auditabil
- rol-based
- compatibil cu observability
- compatibil cu affiliate segmentation
- compatibil cu research / AI / reporting
- sigur din perspectiva privilegiilor
- suficient de structurat pentru panou admin și Telegram admin

Acesta este canonul root pentru Admin Surface și Human Control Plane.