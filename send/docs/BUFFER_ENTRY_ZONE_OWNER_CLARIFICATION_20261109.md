# Buffer band adjacent to entry — Owner clarification, 9 November 2026

Source: the Owner's correction of the V3 report chart on 9 November 2026.
This clarification defines the price region shown as the buffer and how a
settled observation is described. It does not change the frozen width, entry,
expiry, quote eligibility, or ordinary directional result.

## Geometry and expiry meaning

For observed entry E, frozen positive width B, and expiry observation P:

| Position | BUY | SELL | Directional result / quality |
| --- | --- | --- | --- |
| Beyond buffer | P > E+B | P < E-B | WIN, beyond the favorable edge |
| Favorable edge | P = E+B | P = E-B | WIN, exactly on the edge |
| Inside buffer | E < P < E+B | E-B < P < E | WIN, fragile / near failure |
| Entry | P = E | P = E | DRAW |
| Unfavorable side of entry | P < E | P > E | LOSS |

The buffer itself is [E, E+B] for BUY and [E-B, E] for SELL. The chart shades
that band next to entry. A region beyond the favorable edge must not be labeled
as the buffer. Classification uses exact serialized decimal values, without
rounding a shortfall into an edge contact. Missing or invalid inputs remain
unavailable.

The report's 09.11.2026 example has E=1.1222100, B=0.0001858 and
P=1.1223450. Its favorable edge is 1.1223958, and its correct presentation is
**WIN fragile — inside the buffer**. A screenshot alone does not establish
the preceding path or validate the choice of B.

## Relationship with existing measured evidence

`BUFFER_MET_AT_EXPIRY_V1` measures whether favorable movement d >= B. That
persisted metric remains compatible and is displayed as complete margin
obtained / not obtained, rather than confusingly calling the price inside
the buffer ATINS or NEATINS. A fragile WIN retains its WIN directional outcome;
its margin quality remains NOT_MET. At exact equality with the favorable edge,
the existing MET result is retained and the presentation says on the edge.

Historical records, numeric observations, snapshots and calibration cohorts
remain unchanged. Chart and caption share `core.buffer_zone` classification.

## Path evidence is a separate question

The intended path moves favorably out of the band and avoids returning into
it. Starting at entry is the initial state, not a re-entry. Contact with the
favorable edge alone is neither a directional loss nor proof of a later return.
An observed return after an exit must not be erased by a later favorable close.

This correction does not claim continuous path coverage or absence of re-entry.
A recorded edge contact proves only that contact; an OHLC bar does not provide
the ordering of its high and low. Missing ticks or bars cannot be filled with
assumed prices. Final position, historical contact, and directional outcome
must remain distinct observations. No width calibration or protection guarantee
is established by fixing the rendering.
