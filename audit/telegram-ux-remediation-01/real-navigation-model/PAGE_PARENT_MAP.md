# Page Parent Map

## APP parent contract
- Home is the APP root.
- Status, Help, and Admin root entry derive their parent from live APP history.
- Back pops one validated parent and never pushes the page being left.

## Admin parent map

| Child | Parent |
|---|---|
| OPERATIONS | HOME |
| STRATEGY | OPERATIONS |
| SYMBOLS | STRATEGY |
| PROFILE_HOME | STRATEGY |
| THRESHOLDS / SR / SPIKE | STRATEGY |
| SYMBOLS_COV / DECISION_VIS / DISTRIBUTION / RESEARCH / INTELLIGENCE / AFFILIATE / ROLES / SYSHEALTH / GOVDOCS / SECAUDIT / FILES_HOME / STATUS / ENGINE | HOME |
| OPS_ENGINE / OPS_DIAGNOSE | OPERATIONS |
| SH_ENGINE / SH_DIAGNOSE / SH_AUDIT | SYSHEALTH |
| SECAUDIT_AUDIT | SECAUDIT |
| RELOAD_ROLES_CONFIRM | ROLES |

## Context-bearing callbacks
- Strategy symbol mutations encode `STRATEGY` in the callback so the refreshed page still returns to Strategy.
- Diagnose audit callbacks encode the originating branch where needed so failures return to the correct diagnose or health surface instead of jumping to admin root.
