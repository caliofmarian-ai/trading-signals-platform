BINARYBOT CANONICAL SPECIFICATION

SR CORRIDOR ENGINE SPEC

Version: 2.0.0
Status: Canonical
Scope: Corridor Detection / Structural Market Analysis

Dependencies:

- STRATEGY_ENGINE_ARCHITECTURE_MAP_v1.0.0.md
- ALGO_SPEC_v2.0.0.md
- TIME_MODEL_CANON_v1.0.0.md

Supersedes:

- SR_CORRIDOR_ENGINE_SPEC.md (legacy versions)

---

1. PURPOSE OF THIS DOCUMENT

Acest document definește motorul de detecție al corridorului de suport și rezistență utilizat de strategia BinaryBot.

Corridor Engine are rolul de a analiza structura geometrică a pieței și de a determina dacă există un corridor valid pentru setup-ul de tranzacționare.

Corridor Engine nu calculează timp sau expiry.

Responsabilitatea sa este exclusiv analiza structurală a prețului.

---

2. POSITION IN STRATEGY PIPELINE

Corridor Engine funcționează în interiorul Strategy Engine.

Pipeline-ul relevant este:

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

Corridor Engine primește contextul pieței și produce parametrii structurali ai corridorului.

---

3. CORRIDOR CONCEPT

Un corridor reprezintă zona delimitată de nivelele de suport și rezistență în interiorul căreia prețul evoluează.

Corridorul definește:

- limitele structurale ale mișcării prețului
- spațiul disponibil pentru evoluția setup-ului
- calitatea geometrică a setup-ului

---

4. INPUT DATA

Corridor Engine utilizează următoarele date:

current_price
support_levels
resistance_levels
candle_range
volatility_state
structure_context

Aceste date sunt furnizate de Market Model.

---

5. CORRIDOR DETECTION

Primul pas este detectarea unui corridor valid.

Corridorul este identificat prin:

nearest_support
nearest_resistance

unde:

nearest_support < current_price < nearest_resistance

---

6. CORRIDOR WIDTH

Lățimea corridorului reprezintă distanța dintre suport și rezistență.

corridor_width =
nearest_resistance − nearest_support

Această valoare definește spațiul structural disponibil pentru mișcarea prețului.

---

7. CORRIDOR VALIDITY

Un corridor este valid dacă:

corridor_width ≥ minimum_structure_threshold

și dacă nivelurile de suport și rezistență sunt confirmate structural.

Output:

corridor_valid = true | false

---

8. CORRIDOR OPEN CONDITION

Corridorul trebuie să permită execuția setup-ului.

Se verifică:

distance_to_support
distance_to_resistance

și se determină dacă setup-ul are spațiu suficient.

Output:

corridor_open_ok

---

9. CORRIDOR GEOMETRY SCORE

Se calculează scorul geometric al corridorului.

Acesta reflectă:

- stabilitatea nivelurilor
- simetria structurii
- raportul dintre spațiu și volatilitate

Output:

corridor_geometry_score ∈ [0 , 1]

Interpretare:

0 → corridor slab sau invalid
1 → corridor foarte stabil

---

10. CORRIDOR ENGINE OUTPUT

Corridor Engine produce următorii parametri:

corridor_valid
corridor_width
corridor_open_ok
corridor_geometry_score

Acești parametri sunt utilizați de:

SCORING MODEL
DECISION OBJECT BUILDER

---

11. CORRIDOR ENGINE RESTRICTIONS

Corridor Engine nu are voie să calculeze:

expiry
execution time
recommended expiry
signal timing

Aceste calcule aparțin:

TIME MODEL

---

12. RESPONSIBILITY BOUNDARY

Separarea responsabilităților este:

Market Model
→ market context

Time Model
→ temporal feasibility

Corridor Engine
→ structural feasibility

---

13. OBSERVABILITY DATA

Corridor Engine trebuie să furnizeze date pentru audit:

nearest_support
nearest_resistance
corridor_width
corridor_geometry_score
corridor_valid

Aceste date sunt utilizate pentru:

strategy diagnostics
setup quality analysis
decision audit

---

14. FINAL PRINCIPLE

Corridor Engine analizează geometria pieței, nu timpul.

Principiul fundamental este:

Corridor Engine
→ structural feasibility

iar

Time Model
→ temporal feasibility

Separarea acestor două componente garantează:

modular architecture
clear responsibility boundaries
predictable strategy behaviour