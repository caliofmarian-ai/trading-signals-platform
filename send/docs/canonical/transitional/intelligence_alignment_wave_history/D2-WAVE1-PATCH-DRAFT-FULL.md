# D2-WAVE1-PATCH-DRAFT — Intelligence Cluster Wave 1 Canonical Patch Draft

**Document Type:** Canonical patch draft  
**Status:** Draft for review and save  
**Scope:** D2 Wave 1 — architecture backbone cleanup  
**Date:** 2026-03-14  
**Project:** BinaryBot / DROPi Signals  
**Language:** RO  

---

# 1. Purpose

Acest document conține draftul complet de patch pentru **Wave 1** din clusterul D2.
Wave 1 atacă cele trei documente care formează backbone-ul conceptual al zonei de intelligence:
- `INTELLIGENCE_LAYER_ARCHITECTURE.md`
- `AI_TRADING_INTELLIGENCE_ARCHITECTURE.md`
- `STRATEGY_INTELLIGENCE_SYSTEM.md`
Scopul este să clarifice root-ul, delimitările semantice și integrarea cu strategy stack, observability, decision audit, admin panel și Telegram admin surfaces.

---

# 2. Why Wave 1 Must Be Deep, Not Cosmetic

Wave 1 nu poate fi tratat ca operațiune cosmetică.
Trebuie eliminată competiția semantică dintre cele trei documente, fixată ierarhia și tăiată pseudo-autonomia semantică a AI-ului.

---

# 3. Canonical Intent of Wave 1

La finalul Wave 1 trebuie să existe:
- un root clar pentru D2;
- un sub-spec AI clar și guvernat;
- un strategy-intelligence bridge clar;
- vocabular stabil pentru valurile următoare.

---

# 4. Canonical Decision for Wave 1

Final role assignment:
- `INTELLIGENCE_LAYER_ARCHITECTURE.md` = D2 root architecture authority
- `AI_TRADING_INTELLIGENCE_ARCHITECTURE.md` = AI sub-architecture under Intelligence Layer
- `STRATEGY_INTELLIGENCE_SYSTEM.md` = Strategy-to-intelligence operational bridge
Niciunul dintre cele trei documente nu are voie să pretindă singur că reprezintă întreaga zonă de intelligence.

---

# 5. Shared Canonical Truths That Must Appear in All Three Documents

DecisionObject este produs înainte de FSM.
Corridor Engine este înainte de Time Model în pipeline-ul strategic.
Truth-ul strategic este produs în stack-ul canonic upstream, nu în intelligence layer.
Intelligence Layer este downstream și interpretiv.
Observability și Decision Audit sunt sursele semantice principale pentru analiza post-decizie.
Owner-ul este autoritatea supremă umană.
AI nu poate schimba strategia live fără proces explicit separat, aprobat și auditabil.

---

# 6. Detailed Patch Draft per Document

## 6.1 `INTELLIGENCE_LAYER_ARCHITECTURE.md`

### Proposed role
- Document root al clusterului D2.

### Mandatory patch directions
- Trebuie să definească ce este și ce nu este Intelligence Layer.
- Trebuie să descrie poziția canonică downstream de strategy stack, după observability și decision audit.
- Trebuie să enumere sublayerele majore: audit intelligence, research intelligence, proof support, AI assistance, trade physics interpretation, admin rendering.
- Trebuie să definească input families și output families.
- Trebuie să aibă secțiune clară de non-goals.
- Trebuie să interzică shadow truth, auto-authority și live unsupervised mutation.
- Trebuie să definească relația cu admin surface și cu code alignment.

### Title block recommendation
```md
# INTELLIGENCE_LAYER_ARCHITECTURE.md

Version: 2.0.0  
Status: Canonical patched draft  
Owner: BinaryBot / DROPi Signals  
Scope: To be rewritten according to Wave 1 canonical rules
```

### Must-have sections
- `PURPOSE`
- `WHY THIS DOCUMENT EXISTS`
- `CANONICAL ROLE`
- `INPUT FAMILIES`
- `OUTPUT FAMILIES`
- `BOUNDARIES`
- `RELATION TO OBSERVABILITY`
- `RELATION TO DECISION AUDIT`
- `RELATION TO ADMIN SURFACE`
- `NON-GOALS`
- `FINAL PRINCIPLE`

### Must remove / downgrade
- marketing-sounding AI language
- claims of autonomous authority
- duplicate root-architecture wording
- vague promises without input/output contracts

---

## 6.2 `AI_TRADING_INTELLIGENCE_ARCHITECTURE.md`

### Proposed role
- Document subordonat root-ului.

### Mandatory patch directions
- Trebuie să definească funcțiile permise ale AI-ului: summarization, anomaly detection, clustering, recommendation drafting, contradiction flags.
- Trebuie să definească funcțiile interzise: no direct live strategy mutation, no direct parameter change execution, no bypass of owner/admin approval.
- Trebuie să definească confidence / uncertainty labeling.
- Trebuie să definească relația cu research, proof și audit.
- Trebuie să definească relația cu admin panel și Telegram fără a transforma AI-ul în authority layer.

### Title block recommendation
```md
# AI_TRADING_INTELLIGENCE_ARCHITECTURE.md

Version: 2.0.0  
Status: Canonical patched draft  
Owner: BinaryBot / DROPi Signals  
Scope: To be rewritten according to Wave 1 canonical rules
```

### Must-have sections
- `PURPOSE`
- `WHY THIS DOCUMENT EXISTS`
- `CANONICAL ROLE`
- `INPUT FAMILIES`
- `OUTPUT FAMILIES`
- `BOUNDARIES`
- `RELATION TO OBSERVABILITY`
- `RELATION TO DECISION AUDIT`
- `RELATION TO ADMIN SURFACE`
- `NON-GOALS`
- `FINAL PRINCIPLE`

### Must remove / downgrade
- marketing-sounding AI language
- claims of autonomous authority
- duplicate root-architecture wording
- vague promises without input/output contracts

---

## 6.3 `STRATEGY_INTELLIGENCE_SYSTEM.md`

### Proposed role
- Document punte între runtime truth și intelligence support.

### Mandatory patch directions
- Trebuie să definească upstream truth sources: DecisionObject, FSM outcomes, signal execution outcomes, observability traces, decision audit evidence.
- Trebuie să definească downstream uses: diagnostics, bottlenecks, reject clustering, symbol health, proof preparation, recommendation drafting, dashboard summaries.
- Trebuie să definească mapping-ul dintre lifecycle-ul strategiei și lifecycle-ul intelligence.
- Trebuie să includă dead signal / reject / promotion interpretation.
- Trebuie să delimiteze clar relația cu research și cu proof.

### Title block recommendation
```md
# STRATEGY_INTELLIGENCE_SYSTEM.md

Version: 2.0.0  
Status: Canonical patched draft  
Owner: BinaryBot / DROPi Signals  
Scope: To be rewritten according to Wave 1 canonical rules
```

### Must-have sections
- `PURPOSE`
- `WHY THIS DOCUMENT EXISTS`
- `CANONICAL ROLE`
- `INPUT FAMILIES`
- `OUTPUT FAMILIES`
- `BOUNDARIES`
- `RELATION TO OBSERVABILITY`
- `RELATION TO DECISION AUDIT`
- `RELATION TO ADMIN SURFACE`
- `NON-GOALS`
- `FINAL PRINCIPLE`

### Must remove / downgrade
- marketing-sounding AI language
- claims of autonomous authority
- duplicate root-architecture wording
- vague promises without input/output contracts

---

# 7. Cross-Document Alignment Changes Required in Wave 1

## 7.1 Terminology lock

- Intelligence Layer = umbrella architecture
- AI Trading Intelligence = AI sublayer within Intelligence
- Strategy Intelligence System = operational bridge layer

## 7.2 Governance lock

- Owner is supreme
- Primary Admin reviews and operates
- AI is subordinate
- no self-authorized live change

## 7.3 Truth hierarchy lock

- truth is produced upstream in canonical strategy stack
- intelligence is downstream and interpretive
- no shadow truth

## 7.4 Decision audit linkage

- decision audit is a core evidence source
- intelligence uses it, not replaces it

## 7.5 Observability linkage

- observability provides semantic traceability
- intelligence aggregates and interprets that traceability

---

# 8. Expected Outcome of Wave 1

- un root clar pentru D2
- un AI sub-spec clar și guvernat
- o punte clară între strategie și intelligence
- zero competiție semantică între cele trei documente
- un vocabular stabil pentru valurile următoare
- o bază solidă pentru Wave 2 și Wave 3

---

# 9. What Must Wait for Later Waves

- research workflow complet
- statistical proof thresholds
- module/file mapping final
- trade physics intern detaliat
- bounded evolution workflow complet
- Telegram UX concret
- dashboard branch design detaliat

---

# 10. Review Checklist for This Draft

- [ ] root vs sub-spec vs bridge sunt clar separate
- [ ] AI nu pare autoritate autonomă
- [ ] intelligence nu pare upstream față de strategy stack
- [ ] relation to observability and decision audit este explicită
- [ ] owner/admin governance este explicită
- [ ] documentele nu dublează aceleași roluri

---

# 11. Next Deliverable

## `D2-WAVE2-PATCH-DRAFT.md`

- `AI_STRATEGY_AUDITOR_SPEC.md`
- `RESEARCH_AND_LEARNING_FRAMEWORK_SPEC.md`
- `AUTONOMOUS_STRATEGY_EVOLUTION_SYSTEM.md`

---

# Appendix A — Acceptance Criteria by Theme
## A.1 Authority clarity

- criterion 1: section language must be explicit and testable
- criterion 2: section language must be explicit and testable
- criterion 3: section language must be explicit and testable
- criterion 4: section language must be explicit and testable
- criterion 5: section language must be explicit and testable
- criterion 6: section language must be explicit and testable
- criterion 7: section language must be explicit and testable
- criterion 8: section language must be explicit and testable
- criterion 9: section language must be explicit and testable
- criterion 10: section language must be explicit and testable

## A.2 Boundary clarity

- criterion 1: section language must be explicit and testable
- criterion 2: section language must be explicit and testable
- criterion 3: section language must be explicit and testable
- criterion 4: section language must be explicit and testable
- criterion 5: section language must be explicit and testable
- criterion 6: section language must be explicit and testable
- criterion 7: section language must be explicit and testable
- criterion 8: section language must be explicit and testable
- criterion 9: section language must be explicit and testable
- criterion 10: section language must be explicit and testable

## A.3 AI limitation clarity

- criterion 1: section language must be explicit and testable
- criterion 2: section language must be explicit and testable
- criterion 3: section language must be explicit and testable
- criterion 4: section language must be explicit and testable
- criterion 5: section language must be explicit and testable
- criterion 6: section language must be explicit and testable
- criterion 7: section language must be explicit and testable
- criterion 8: section language must be explicit and testable
- criterion 9: section language must be explicit and testable
- criterion 10: section language must be explicit and testable

## A.4 Observability linkage

- criterion 1: section language must be explicit and testable
- criterion 2: section language must be explicit and testable
- criterion 3: section language must be explicit and testable
- criterion 4: section language must be explicit and testable
- criterion 5: section language must be explicit and testable
- criterion 6: section language must be explicit and testable
- criterion 7: section language must be explicit and testable
- criterion 8: section language must be explicit and testable
- criterion 9: section language must be explicit and testable
- criterion 10: section language must be explicit and testable

## A.5 Decision audit linkage

- criterion 1: section language must be explicit and testable
- criterion 2: section language must be explicit and testable
- criterion 3: section language must be explicit and testable
- criterion 4: section language must be explicit and testable
- criterion 5: section language must be explicit and testable
- criterion 6: section language must be explicit and testable
- criterion 7: section language must be explicit and testable
- criterion 8: section language must be explicit and testable
- criterion 9: section language must be explicit and testable
- criterion 10: section language must be explicit and testable

## A.6 Admin surface linkage

- criterion 1: section language must be explicit and testable
- criterion 2: section language must be explicit and testable
- criterion 3: section language must be explicit and testable
- criterion 4: section language must be explicit and testable
- criterion 5: section language must be explicit and testable
- criterion 6: section language must be explicit and testable
- criterion 7: section language must be explicit and testable
- criterion 8: section language must be explicit and testable
- criterion 9: section language must be explicit and testable
- criterion 10: section language must be explicit and testable

## A.7 Terminology consistency

- criterion 1: section language must be explicit and testable
- criterion 2: section language must be explicit and testable
- criterion 3: section language must be explicit and testable
- criterion 4: section language must be explicit and testable
- criterion 5: section language must be explicit and testable
- criterion 6: section language must be explicit and testable
- criterion 7: section language must be explicit and testable
- criterion 8: section language must be explicit and testable
- criterion 9: section language must be explicit and testable
- criterion 10: section language must be explicit and testable

## A.8 No shadow truth

- criterion 1: section language must be explicit and testable
- criterion 2: section language must be explicit and testable
- criterion 3: section language must be explicit and testable
- criterion 4: section language must be explicit and testable
- criterion 5: section language must be explicit and testable
- criterion 6: section language must be explicit and testable
- criterion 7: section language must be explicit and testable
- criterion 8: section language must be explicit and testable
- criterion 9: section language must be explicit and testable
- criterion 10: section language must be explicit and testable

## A.9 No pseudo-autonomy

- criterion 1: section language must be explicit and testable
- criterion 2: section language must be explicit and testable
- criterion 3: section language must be explicit and testable
- criterion 4: section language must be explicit and testable
- criterion 5: section language must be explicit and testable
- criterion 6: section language must be explicit and testable
- criterion 7: section language must be explicit and testable
- criterion 8: section language must be explicit and testable
- criterion 9: section language must be explicit and testable
- criterion 10: section language must be explicit and testable

## A.10 Code alignment readiness

- criterion 1: section language must be explicit and testable
- criterion 2: section language must be explicit and testable
- criterion 3: section language must be explicit and testable
- criterion 4: section language must be explicit and testable
- criterion 5: section language must be explicit and testable
- criterion 6: section language must be explicit and testable
- criterion 7: section language must be explicit and testable
- criterion 8: section language must be explicit and testable
- criterion 9: section language must be explicit and testable
- criterion 10: section language must be explicit and testable

---

# Appendix B — Editorial Prompts
## B.1 Editorial prompt block

- Ce afirmă această secțiune?
- Ce interzice această secțiune?
- La ce documente se leagă?
- Ce risc de confuzie elimină?
- Cum ajută owner/admin în practică?
- Ce formulări trebuie tăiate dacă sună prea autonome?

## B.2 Editorial prompt block

- Ce afirmă această secțiune?
- Ce interzice această secțiune?
- La ce documente se leagă?
- Ce risc de confuzie elimină?
- Cum ajută owner/admin în practică?
- Ce formulări trebuie tăiate dacă sună prea autonome?

## B.3 Editorial prompt block

- Ce afirmă această secțiune?
- Ce interzice această secțiune?
- La ce documente se leagă?
- Ce risc de confuzie elimină?
- Cum ajută owner/admin în practică?
- Ce formulări trebuie tăiate dacă sună prea autonome?

## B.4 Editorial prompt block

- Ce afirmă această secțiune?
- Ce interzice această secțiune?
- La ce documente se leagă?
- Ce risc de confuzie elimină?
- Cum ajută owner/admin în practică?
- Ce formulări trebuie tăiate dacă sună prea autonome?

## B.5 Editorial prompt block

- Ce afirmă această secțiune?
- Ce interzice această secțiune?
- La ce documente se leagă?
- Ce risc de confuzie elimină?
- Cum ajută owner/admin în practică?
- Ce formulări trebuie tăiate dacă sună prea autonome?

## B.6 Editorial prompt block

- Ce afirmă această secțiune?
- Ce interzice această secțiune?
- La ce documente se leagă?
- Ce risc de confuzie elimină?
- Cum ajută owner/admin în practică?
- Ce formulări trebuie tăiate dacă sună prea autonome?

## B.7 Editorial prompt block

- Ce afirmă această secțiune?
- Ce interzice această secțiune?
- La ce documente se leagă?
- Ce risc de confuzie elimină?
- Cum ajută owner/admin în practică?
- Ce formulări trebuie tăiate dacă sună prea autonome?

## B.8 Editorial prompt block

- Ce afirmă această secțiune?
- Ce interzice această secțiune?
- La ce documente se leagă?
- Ce risc de confuzie elimină?
- Cum ajută owner/admin în practică?
- Ce formulări trebuie tăiate dacă sună prea autonome?

## B.9 Editorial prompt block

- Ce afirmă această secțiune?
- Ce interzice această secțiune?
- La ce documente se leagă?
- Ce risc de confuzie elimină?
- Cum ajută owner/admin în practică?
- Ce formulări trebuie tăiate dacă sună prea autonome?

## B.10 Editorial prompt block

- Ce afirmă această secțiune?
- Ce interzice această secțiune?
- La ce documente se leagă?
- Ce risc de confuzie elimină?
- Cum ajută owner/admin în practică?
- Ce formulări trebuie tăiate dacă sună prea autonome?

## B.11 Editorial prompt block

- Ce afirmă această secțiune?
- Ce interzice această secțiune?
- La ce documente se leagă?
- Ce risc de confuzie elimină?
- Cum ajută owner/admin în practică?
- Ce formulări trebuie tăiate dacă sună prea autonome?

## B.12 Editorial prompt block

- Ce afirmă această secțiune?
- Ce interzice această secțiune?
- La ce documente se leagă?
- Ce risc de confuzie elimină?
- Cum ajută owner/admin în practică?
- Ce formulări trebuie tăiate dacă sună prea autonome?

## B.13 Editorial prompt block

- Ce afirmă această secțiune?
- Ce interzice această secțiune?
- La ce documente se leagă?
- Ce risc de confuzie elimină?
- Cum ajută owner/admin în practică?
- Ce formulări trebuie tăiate dacă sună prea autonome?

## B.14 Editorial prompt block

- Ce afirmă această secțiune?
- Ce interzice această secțiune?
- La ce documente se leagă?
- Ce risc de confuzie elimină?
- Cum ajută owner/admin în practică?
- Ce formulări trebuie tăiate dacă sună prea autonome?

## B.15 Editorial prompt block

- Ce afirmă această secțiune?
- Ce interzice această secțiune?
- La ce documente se leagă?
- Ce risc de confuzie elimină?
- Cum ajută owner/admin în practică?
- Ce formulări trebuie tăiate dacă sună prea autonome?

## B.16 Editorial prompt block

- Ce afirmă această secțiune?
- Ce interzice această secțiune?
- La ce documente se leagă?
- Ce risc de confuzie elimină?
- Cum ajută owner/admin în practică?
- Ce formulări trebuie tăiate dacă sună prea autonome?

## B.17 Editorial prompt block

- Ce afirmă această secțiune?
- Ce interzice această secțiune?
- La ce documente se leagă?
- Ce risc de confuzie elimină?
- Cum ajută owner/admin în practică?
- Ce formulări trebuie tăiate dacă sună prea autonome?

## B.18 Editorial prompt block

- Ce afirmă această secțiune?
- Ce interzice această secțiune?
- La ce documente se leagă?
- Ce risc de confuzie elimină?
- Cum ajută owner/admin în practică?
- Ce formulări trebuie tăiate dacă sună prea autonome?

## B.19 Editorial prompt block

- Ce afirmă această secțiune?
- Ce interzice această secțiune?
- La ce documente se leagă?
- Ce risc de confuzie elimină?
- Cum ajută owner/admin în practică?
- Ce formulări trebuie tăiate dacă sună prea autonome?

## B.20 Editorial prompt block

- Ce afirmă această secțiune?
- Ce interzice această secțiune?
- La ce documente se leagă?
- Ce risc de confuzie elimină?
- Cum ajută owner/admin în practică?
- Ce formulări trebuie tăiate dacă sună prea autonome?

## B.21 Editorial prompt block

- Ce afirmă această secțiune?
- Ce interzice această secțiune?
- La ce documente se leagă?
- Ce risc de confuzie elimină?
- Cum ajută owner/admin în practică?
- Ce formulări trebuie tăiate dacă sună prea autonome?

## B.22 Editorial prompt block

- Ce afirmă această secțiune?
- Ce interzice această secțiune?
- La ce documente se leagă?
- Ce risc de confuzie elimină?
- Cum ajută owner/admin în practică?
- Ce formulări trebuie tăiate dacă sună prea autonome?

## B.23 Editorial prompt block

- Ce afirmă această secțiune?
- Ce interzice această secțiune?
- La ce documente se leagă?
- Ce risc de confuzie elimină?
- Cum ajută owner/admin în practică?
- Ce formulări trebuie tăiate dacă sună prea autonome?

## B.24 Editorial prompt block

- Ce afirmă această secțiune?
- Ce interzice această secțiune?
- La ce documente se leagă?
- Ce risc de confuzie elimină?
- Cum ajută owner/admin în practică?
- Ce formulări trebuie tăiate dacă sună prea autonome?

## B.25 Editorial prompt block

- Ce afirmă această secțiune?
- Ce interzice această secțiune?
- La ce documente se leagă?
- Ce risc de confuzie elimină?
- Cum ajută owner/admin în practică?
- Ce formulări trebuie tăiate dacă sună prea autonome?

## B.26 Editorial prompt block

- Ce afirmă această secțiune?
- Ce interzice această secțiune?
- La ce documente se leagă?
- Ce risc de confuzie elimină?
- Cum ajută owner/admin în practică?
- Ce formulări trebuie tăiate dacă sună prea autonome?

## B.27 Editorial prompt block

- Ce afirmă această secțiune?
- Ce interzice această secțiune?
- La ce documente se leagă?
- Ce risc de confuzie elimină?
- Cum ajută owner/admin în practică?
- Ce formulări trebuie tăiate dacă sună prea autonome?

## B.28 Editorial prompt block

- Ce afirmă această secțiune?
- Ce interzice această secțiune?
- La ce documente se leagă?
- Ce risc de confuzie elimină?
- Cum ajută owner/admin în practică?
- Ce formulări trebuie tăiate dacă sună prea autonome?

## B.29 Editorial prompt block

- Ce afirmă această secțiune?
- Ce interzice această secțiune?
- La ce documente se leagă?
- Ce risc de confuzie elimină?
- Cum ajută owner/admin în practică?
- Ce formulări trebuie tăiate dacă sună prea autonome?

## B.30 Editorial prompt block

- Ce afirmă această secțiune?
- Ce interzice această secțiune?
- La ce documente se leagă?
- Ce risc de confuzie elimină?
- Cum ajută owner/admin în practică?
- Ce formulări trebuie tăiate dacă sună prea autonome?

## B.31 Editorial prompt block

- Ce afirmă această secțiune?
- Ce interzice această secțiune?
- La ce documente se leagă?
- Ce risc de confuzie elimină?
- Cum ajută owner/admin în practică?
- Ce formulări trebuie tăiate dacă sună prea autonome?

## B.32 Editorial prompt block

- Ce afirmă această secțiune?
- Ce interzice această secțiune?
- La ce documente se leagă?
- Ce risc de confuzie elimină?
- Cum ajută owner/admin în practică?
- Ce formulări trebuie tăiate dacă sună prea autonome?

## B.33 Editorial prompt block

- Ce afirmă această secțiune?
- Ce interzice această secțiune?
- La ce documente se leagă?
- Ce risc de confuzie elimină?
- Cum ajută owner/admin în practică?
- Ce formulări trebuie tăiate dacă sună prea autonome?

## B.34 Editorial prompt block

- Ce afirmă această secțiune?
- Ce interzice această secțiune?
- La ce documente se leagă?
- Ce risc de confuzie elimină?
- Cum ajută owner/admin în practică?
- Ce formulări trebuie tăiate dacă sună prea autonome?

## B.35 Editorial prompt block

- Ce afirmă această secțiune?
- Ce interzice această secțiune?
- La ce documente se leagă?
- Ce risc de confuzie elimină?
- Cum ajută owner/admin în practică?
- Ce formulări trebuie tăiate dacă sună prea autonome?

## B.36 Editorial prompt block

- Ce afirmă această secțiune?
- Ce interzice această secțiune?
- La ce documente se leagă?
- Ce risc de confuzie elimină?
- Cum ajută owner/admin în practică?
- Ce formulări trebuie tăiate dacă sună prea autonome?

## B.37 Editorial prompt block

- Ce afirmă această secțiune?
- Ce interzice această secțiune?
- La ce documente se leagă?
- Ce risc de confuzie elimină?
- Cum ajută owner/admin în practică?
- Ce formulări trebuie tăiate dacă sună prea autonome?

## B.38 Editorial prompt block

- Ce afirmă această secțiune?
- Ce interzice această secțiune?
- La ce documente se leagă?
- Ce risc de confuzie elimină?
- Cum ajută owner/admin în practică?
- Ce formulări trebuie tăiate dacă sună prea autonome?

## B.39 Editorial prompt block

- Ce afirmă această secțiune?
- Ce interzice această secțiune?
- La ce documente se leagă?
- Ce risc de confuzie elimină?
- Cum ajută owner/admin în practică?
- Ce formulări trebuie tăiate dacă sună prea autonome?

## B.40 Editorial prompt block

- Ce afirmă această secțiune?
- Ce interzice această secțiune?
- La ce documente se leagă?
- Ce risc de confuzie elimină?
- Cum ajută owner/admin în practică?
- Ce formulări trebuie tăiate dacă sună prea autonome?

## B.41 Editorial prompt block

- Ce afirmă această secțiune?
- Ce interzice această secțiune?
- La ce documente se leagă?
- Ce risc de confuzie elimină?
- Cum ajută owner/admin în practică?
- Ce formulări trebuie tăiate dacă sună prea autonome?

## B.42 Editorial prompt block

- Ce afirmă această secțiune?
- Ce interzice această secțiune?
- La ce documente se leagă?
- Ce risc de confuzie elimină?
- Cum ajută owner/admin în practică?
- Ce formulări trebuie tăiate dacă sună prea autonome?

## B.43 Editorial prompt block

- Ce afirmă această secțiune?
- Ce interzice această secțiune?
- La ce documente se leagă?
- Ce risc de confuzie elimină?
- Cum ajută owner/admin în practică?
- Ce formulări trebuie tăiate dacă sună prea autonome?

## B.44 Editorial prompt block

- Ce afirmă această secțiune?
- Ce interzice această secțiune?
- La ce documente se leagă?
- Ce risc de confuzie elimină?
- Cum ajută owner/admin în practică?
- Ce formulări trebuie tăiate dacă sună prea autonome?

## B.45 Editorial prompt block

- Ce afirmă această secțiune?
- Ce interzice această secțiune?
- La ce documente se leagă?
- Ce risc de confuzie elimină?
- Cum ajută owner/admin în practică?
- Ce formulări trebuie tăiate dacă sună prea autonome?

## B.46 Editorial prompt block

- Ce afirmă această secțiune?
- Ce interzice această secțiune?
- La ce documente se leagă?
- Ce risc de confuzie elimină?
- Cum ajută owner/admin în practică?
- Ce formulări trebuie tăiate dacă sună prea autonome?

## B.47 Editorial prompt block

- Ce afirmă această secțiune?
- Ce interzice această secțiune?
- La ce documente se leagă?
- Ce risc de confuzie elimină?
- Cum ajută owner/admin în practică?
- Ce formulări trebuie tăiate dacă sună prea autonome?

## B.48 Editorial prompt block

- Ce afirmă această secțiune?
- Ce interzice această secțiune?
- La ce documente se leagă?
- Ce risc de confuzie elimină?
- Cum ajută owner/admin în practică?
- Ce formulări trebuie tăiate dacă sună prea autonome?

## B.49 Editorial prompt block

- Ce afirmă această secțiune?
- Ce interzice această secțiune?
- La ce documente se leagă?
- Ce risc de confuzie elimină?
- Cum ajută owner/admin în practică?
- Ce formulări trebuie tăiate dacă sună prea autonome?

## B.50 Editorial prompt block

- Ce afirmă această secțiune?
- Ce interzice această secțiune?
- La ce documente se leagă?
- Ce risc de confuzie elimină?
- Cum ajută owner/admin în practică?
- Ce formulări trebuie tăiate dacă sună prea autonome?

## B.51 Editorial prompt block

- Ce afirmă această secțiune?
- Ce interzice această secțiune?
- La ce documente se leagă?
- Ce risc de confuzie elimină?
- Cum ajută owner/admin în practică?
- Ce formulări trebuie tăiate dacă sună prea autonome?

## B.52 Editorial prompt block

- Ce afirmă această secțiune?
- Ce interzice această secțiune?
- La ce documente se leagă?
- Ce risc de confuzie elimină?
- Cum ajută owner/admin în practică?
- Ce formulări trebuie tăiate dacă sună prea autonome?

## B.53 Editorial prompt block

- Ce afirmă această secțiune?
- Ce interzice această secțiune?
- La ce documente se leagă?
- Ce risc de confuzie elimină?
- Cum ajută owner/admin în practică?
- Ce formulări trebuie tăiate dacă sună prea autonome?

## B.54 Editorial prompt block

- Ce afirmă această secțiune?
- Ce interzice această secțiune?
- La ce documente se leagă?
- Ce risc de confuzie elimină?
- Cum ajută owner/admin în practică?
- Ce formulări trebuie tăiate dacă sună prea autonome?

## B.55 Editorial prompt block

- Ce afirmă această secțiune?
- Ce interzice această secțiune?
- La ce documente se leagă?
- Ce risc de confuzie elimină?
- Cum ajută owner/admin în practică?
- Ce formulări trebuie tăiate dacă sună prea autonome?

## B.56 Editorial prompt block

- Ce afirmă această secțiune?
- Ce interzice această secțiune?
- La ce documente se leagă?
- Ce risc de confuzie elimină?
- Cum ajută owner/admin în practică?
- Ce formulări trebuie tăiate dacă sună prea autonome?

## B.57 Editorial prompt block

- Ce afirmă această secțiune?
- Ce interzice această secțiune?
- La ce documente se leagă?
- Ce risc de confuzie elimină?
- Cum ajută owner/admin în practică?
- Ce formulări trebuie tăiate dacă sună prea autonome?

## B.58 Editorial prompt block

- Ce afirmă această secțiune?
- Ce interzice această secțiune?
- La ce documente se leagă?
- Ce risc de confuzie elimină?
- Cum ajută owner/admin în practică?
- Ce formulări trebuie tăiate dacă sună prea autonome?

## B.59 Editorial prompt block

- Ce afirmă această secțiune?
- Ce interzice această secțiune?
- La ce documente se leagă?
- Ce risc de confuzie elimină?
- Cum ajută owner/admin în practică?
- Ce formulări trebuie tăiate dacă sună prea autonome?

## B.60 Editorial prompt block

- Ce afirmă această secțiune?
- Ce interzice această secțiune?
- La ce documente se leagă?
- Ce risc de confuzie elimină?
- Cum ajută owner/admin în practică?
- Ce formulări trebuie tăiate dacă sună prea autonome?

## B.61 Editorial prompt block

- Ce afirmă această secțiune?
- Ce interzice această secțiune?
- La ce documente se leagă?
- Ce risc de confuzie elimină?
- Cum ajută owner/admin în practică?
- Ce formulări trebuie tăiate dacă sună prea autonome?

## B.62 Editorial prompt block

- Ce afirmă această secțiune?
- Ce interzice această secțiune?
- La ce documente se leagă?
- Ce risc de confuzie elimină?
- Cum ajută owner/admin în practică?
- Ce formulări trebuie tăiate dacă sună prea autonome?

## B.63 Editorial prompt block

- Ce afirmă această secțiune?
- Ce interzice această secțiune?
- La ce documente se leagă?
- Ce risc de confuzie elimină?
- Cum ajută owner/admin în practică?
- Ce formulări trebuie tăiate dacă sună prea autonome?

## B.64 Editorial prompt block

- Ce afirmă această secțiune?
- Ce interzice această secțiune?
- La ce documente se leagă?
- Ce risc de confuzie elimină?
- Cum ajută owner/admin în practică?
- Ce formulări trebuie tăiate dacă sună prea autonome?

## B.65 Editorial prompt block

- Ce afirmă această secțiune?
- Ce interzice această secțiune?
- La ce documente se leagă?
- Ce risc de confuzie elimină?
- Cum ajută owner/admin în practică?
- Ce formulări trebuie tăiate dacă sună prea autonome?

## B.66 Editorial prompt block

- Ce afirmă această secțiune?
- Ce interzice această secțiune?
- La ce documente se leagă?
- Ce risc de confuzie elimină?
- Cum ajută owner/admin în practică?
- Ce formulări trebuie tăiate dacă sună prea autonome?

## B.67 Editorial prompt block

- Ce afirmă această secțiune?
- Ce interzice această secțiune?
- La ce documente se leagă?
- Ce risc de confuzie elimină?
- Cum ajută owner/admin în practică?
- Ce formulări trebuie tăiate dacă sună prea autonome?

## B.68 Editorial prompt block

- Ce afirmă această secțiune?
- Ce interzice această secțiune?
- La ce documente se leagă?
- Ce risc de confuzie elimină?
- Cum ajută owner/admin în practică?
- Ce formulări trebuie tăiate dacă sună prea autonome?

## B.69 Editorial prompt block

- Ce afirmă această secțiune?
- Ce interzice această secțiune?
- La ce documente se leagă?
- Ce risc de confuzie elimină?
- Cum ajută owner/admin în practică?
- Ce formulări trebuie tăiate dacă sună prea autonome?

## B.70 Editorial prompt block

- Ce afirmă această secțiune?
- Ce interzice această secțiune?
- La ce documente se leagă?
- Ce risc de confuzie elimină?
- Cum ajută owner/admin în practică?
- Ce formulări trebuie tăiate dacă sună prea autonome?

## B.71 Editorial prompt block

- Ce afirmă această secțiune?
- Ce interzice această secțiune?
- La ce documente se leagă?
- Ce risc de confuzie elimină?
- Cum ajută owner/admin în practică?
- Ce formulări trebuie tăiate dacă sună prea autonome?

## B.72 Editorial prompt block

- Ce afirmă această secțiune?
- Ce interzice această secțiune?
- La ce documente se leagă?
- Ce risc de confuzie elimină?
- Cum ajută owner/admin în practică?
- Ce formulări trebuie tăiate dacă sună prea autonome?

## B.73 Editorial prompt block

- Ce afirmă această secțiune?
- Ce interzice această secțiune?
- La ce documente se leagă?
- Ce risc de confuzie elimină?
- Cum ajută owner/admin în practică?
- Ce formulări trebuie tăiate dacă sună prea autonome?

## B.74 Editorial prompt block

- Ce afirmă această secțiune?
- Ce interzice această secțiune?
- La ce documente se leagă?
- Ce risc de confuzie elimină?
- Cum ajută owner/admin în practică?
- Ce formulări trebuie tăiate dacă sună prea autonome?

## B.75 Editorial prompt block

- Ce afirmă această secțiune?
- Ce interzice această secțiune?
- La ce documente se leagă?
- Ce risc de confuzie elimină?
- Cum ajută owner/admin în practică?
- Ce formulări trebuie tăiate dacă sună prea autonome?

## B.76 Editorial prompt block

- Ce afirmă această secțiune?
- Ce interzice această secțiune?
- La ce documente se leagă?
- Ce risc de confuzie elimină?
- Cum ajută owner/admin în practică?
- Ce formulări trebuie tăiate dacă sună prea autonome?

## B.77 Editorial prompt block

- Ce afirmă această secțiune?
- Ce interzice această secțiune?
- La ce documente se leagă?
- Ce risc de confuzie elimină?
- Cum ajută owner/admin în practică?
- Ce formulări trebuie tăiate dacă sună prea autonome?

## B.78 Editorial prompt block

- Ce afirmă această secțiune?
- Ce interzice această secțiune?
- La ce documente se leagă?
- Ce risc de confuzie elimină?
- Cum ajută owner/admin în practică?
- Ce formulări trebuie tăiate dacă sună prea autonome?

## B.79 Editorial prompt block

- Ce afirmă această secțiune?
- Ce interzice această secțiune?
- La ce documente se leagă?
- Ce risc de confuzie elimină?
- Cum ajută owner/admin în practică?
- Ce formulări trebuie tăiate dacă sună prea autonome?

## B.80 Editorial prompt block

- Ce afirmă această secțiune?
- Ce interzice această secțiune?
- La ce documente se leagă?
- Ce risc de confuzie elimină?
- Cum ajută owner/admin în practică?
- Ce formulări trebuie tăiate dacă sună prea autonome?

## B.81 Editorial prompt block

- Ce afirmă această secțiune?
- Ce interzice această secțiune?
- La ce documente se leagă?
- Ce risc de confuzie elimină?
- Cum ajută owner/admin în practică?
- Ce formulări trebuie tăiate dacă sună prea autonome?

## B.82 Editorial prompt block

- Ce afirmă această secțiune?
- Ce interzice această secțiune?
- La ce documente se leagă?
- Ce risc de confuzie elimină?
- Cum ajută owner/admin în practică?
- Ce formulări trebuie tăiate dacă sună prea autonome?

## B.83 Editorial prompt block

- Ce afirmă această secțiune?
- Ce interzice această secțiune?
- La ce documente se leagă?
- Ce risc de confuzie elimină?
- Cum ajută owner/admin în practică?
- Ce formulări trebuie tăiate dacă sună prea autonome?

## B.84 Editorial prompt block

- Ce afirmă această secțiune?
- Ce interzice această secțiune?
- La ce documente se leagă?
- Ce risc de confuzie elimină?
- Cum ajută owner/admin în practică?
- Ce formulări trebuie tăiate dacă sună prea autonome?

## B.85 Editorial prompt block

- Ce afirmă această secțiune?
- Ce interzice această secțiune?
- La ce documente se leagă?
- Ce risc de confuzie elimină?
- Cum ajută owner/admin în practică?
- Ce formulări trebuie tăiate dacă sună prea autonome?

## B.86 Editorial prompt block

- Ce afirmă această secțiune?
- Ce interzice această secțiune?
- La ce documente se leagă?
- Ce risc de confuzie elimină?
- Cum ajută owner/admin în practică?
- Ce formulări trebuie tăiate dacă sună prea autonome?

## B.87 Editorial prompt block

- Ce afirmă această secțiune?
- Ce interzice această secțiune?
- La ce documente se leagă?
- Ce risc de confuzie elimină?
- Cum ajută owner/admin în practică?
- Ce formulări trebuie tăiate dacă sună prea autonome?

## B.88 Editorial prompt block

- Ce afirmă această secțiune?
- Ce interzice această secțiune?
- La ce documente se leagă?
- Ce risc de confuzie elimină?
- Cum ajută owner/admin în practică?
- Ce formulări trebuie tăiate dacă sună prea autonome?

## B.89 Editorial prompt block

- Ce afirmă această secțiune?
- Ce interzice această secțiune?
- La ce documente se leagă?
- Ce risc de confuzie elimină?
- Cum ajută owner/admin în practică?
- Ce formulări trebuie tăiate dacă sună prea autonome?

## B.90 Editorial prompt block

- Ce afirmă această secțiune?
- Ce interzice această secțiune?
- La ce documente se leagă?
- Ce risc de confuzie elimină?
- Cum ajută owner/admin în practică?
- Ce formulări trebuie tăiate dacă sună prea autonome?

## B.91 Editorial prompt block

- Ce afirmă această secțiune?
- Ce interzice această secțiune?
- La ce documente se leagă?
- Ce risc de confuzie elimină?
- Cum ajută owner/admin în practică?
- Ce formulări trebuie tăiate dacă sună prea autonome?

## B.92 Editorial prompt block

- Ce afirmă această secțiune?
- Ce interzice această secțiune?
- La ce documente se leagă?
- Ce risc de confuzie elimină?
- Cum ajută owner/admin în practică?
- Ce formulări trebuie tăiate dacă sună prea autonome?

## B.93 Editorial prompt block

- Ce afirmă această secțiune?
- Ce interzice această secțiune?
- La ce documente se leagă?
- Ce risc de confuzie elimină?
- Cum ajută owner/admin în practică?
- Ce formulări trebuie tăiate dacă sună prea autonome?

## B.94 Editorial prompt block

- Ce afirmă această secțiune?
- Ce interzice această secțiune?
- La ce documente se leagă?
- Ce risc de confuzie elimină?
- Cum ajută owner/admin în practică?
- Ce formulări trebuie tăiate dacă sună prea autonome?

## B.95 Editorial prompt block

- Ce afirmă această secțiune?
- Ce interzice această secțiune?
- La ce documente se leagă?
- Ce risc de confuzie elimină?
- Cum ajută owner/admin în practică?
- Ce formulări trebuie tăiate dacă sună prea autonome?

## B.96 Editorial prompt block

- Ce afirmă această secțiune?
- Ce interzice această secțiune?
- La ce documente se leagă?
- Ce risc de confuzie elimină?
- Cum ajută owner/admin în practică?
- Ce formulări trebuie tăiate dacă sună prea autonome?

## B.97 Editorial prompt block

- Ce afirmă această secțiune?
- Ce interzice această secțiune?
- La ce documente se leagă?
- Ce risc de confuzie elimină?
- Cum ajută owner/admin în practică?
- Ce formulări trebuie tăiate dacă sună prea autonome?

## B.98 Editorial prompt block

- Ce afirmă această secțiune?
- Ce interzice această secțiune?
- La ce documente se leagă?
- Ce risc de confuzie elimină?
- Cum ajută owner/admin în practică?
- Ce formulări trebuie tăiate dacă sună prea autonome?

## B.99 Editorial prompt block

- Ce afirmă această secțiune?
- Ce interzice această secțiune?
- La ce documente se leagă?
- Ce risc de confuzie elimină?
- Cum ajută owner/admin în practică?
- Ce formulări trebuie tăiate dacă sună prea autonome?

## B.100 Editorial prompt block

- Ce afirmă această secțiune?
- Ce interzice această secțiune?
- La ce documente se leagă?
- Ce risc de confuzie elimină?
- Cum ajută owner/admin în practică?
- Ce formulări trebuie tăiate dacă sună prea autonome?

---

# Appendix C — Forbidden Phrase Matrix
## C.1 `AI decides`

- status: forbidden or must be heavily qualified
- action: rewrite with governance language
- reason: creates semantic overreach

## C.2 `AI governs`

- status: forbidden or must be heavily qualified
- action: rewrite with governance language
- reason: creates semantic overreach

## C.3 `autonomous live optimization`

- status: forbidden or must be heavily qualified
- action: rewrite with governance language
- reason: creates semantic overreach

## C.4 `self-changing strategy without review`

- status: forbidden or must be heavily qualified
- action: rewrite with governance language
- reason: creates semantic overreach

## C.5 `AI proves edge by itself`

- status: forbidden or must be heavily qualified
- action: rewrite with governance language
- reason: creates semantic overreach

## C.6 `dashboard truth`

- status: forbidden or must be heavily qualified
- action: rewrite with governance language
- reason: creates semantic overreach

## C.7 `Telegram truth`

- status: forbidden or must be heavily qualified
- action: rewrite with governance language
- reason: creates semantic overreach

## C.8 `intelligence overrides strategy`

- status: forbidden or must be heavily qualified
- action: rewrite with governance language
- reason: creates semantic overreach

## C.9 `AI final verdict`

- status: forbidden or must be heavily qualified
- action: rewrite with governance language
- reason: creates semantic overreach

## C.10 `automatic threshold rewrite`

- status: forbidden or must be heavily qualified
- action: rewrite with governance language
- reason: creates semantic overreach

---

# Appendix D — Patch Execution Checklist Per Document
## D — `INTELLIGENCE_LAYER_ARCHITECTURE.md`

- [ ] title corrected
- [ ] status corrected
- [ ] scope corrected
- [ ] depends-on corrected
- [ ] purpose rewritten
- [ ] canonical role declared
- [ ] boundaries added
- [ ] inputs added
- [ ] outputs added
- [ ] observability linkage added
- [ ] decision audit linkage added
- [ ] admin surface linkage added
- [ ] non-goals added
- [ ] final principle added
- [ ] forbidden language removed

## D — `AI_TRADING_INTELLIGENCE_ARCHITECTURE.md`

- [ ] title corrected
- [ ] status corrected
- [ ] scope corrected
- [ ] depends-on corrected
- [ ] purpose rewritten
- [ ] canonical role declared
- [ ] boundaries added
- [ ] inputs added
- [ ] outputs added
- [ ] observability linkage added
- [ ] decision audit linkage added
- [ ] admin surface linkage added
- [ ] non-goals added
- [ ] final principle added
- [ ] forbidden language removed

## D — `STRATEGY_INTELLIGENCE_SYSTEM.md`

- [ ] title corrected
- [ ] status corrected
- [ ] scope corrected
- [ ] depends-on corrected
- [ ] purpose rewritten
- [ ] canonical role declared
- [ ] boundaries added
- [ ] inputs added
- [ ] outputs added
- [ ] observability linkage added
- [ ] decision audit linkage added
- [ ] admin surface linkage added
- [ ] non-goals added
- [ ] final principle added
- [ ] forbidden language removed
