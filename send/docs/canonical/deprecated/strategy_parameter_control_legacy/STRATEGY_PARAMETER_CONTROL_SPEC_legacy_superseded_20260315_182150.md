BINARYBOT — STRATEGY PARAMETER CONTROL SPECIFICATION

Version: 1.0
Status: CANONICAL SPECIFICATION
Location: /opt/binarybot/docs/STRATEGY_PARAMETER_CONTROL_SPEC.md


------------------------------------------------------------
1. PURPOSE
------------------------------------------------------------

This document defines the system used to control
BinaryBot strategy parameters without modifying source code.

The Strategy Parameter Control system allows operators
to adjust strategy behavior dynamically via the admin
control interface.

These parameters include:

• score thresholds
• support/resistance buffers
• spike detection filters
• trend filters
• symbol selection

The goal is to allow strategy tuning without code deployment.


------------------------------------------------------------
2. POSITION IN SYSTEM ARCHITECTURE
------------------------------------------------------------

The strategy parameter control system belongs to
the ADMIN layer and influences the ENGINE layer.

System architecture:

ADMIN CONTROL PANEL
↓
STRATEGY PARAMETER CONFIGURATION
↓
ENGINE STRATEGY LOGIC
↓
SIGNAL DECISIONS


------------------------------------------------------------
3. CONTROL METHODS
------------------------------------------------------------

Strategy parameters can be modified through:

Telegram Admin Commands

Admin Control Panel

Configuration File Updates


Primary control interface:

Telegram commands.


------------------------------------------------------------
4. PARAMETER GROUPS
------------------------------------------------------------

Strategy parameters are grouped into the following categories.

Threshold Parameters

Score thresholds for signal stages.


Support / Resistance Parameters

Distance buffers from support or resistance levels.


Spike Detection Parameters

Detection of abnormal candles.


Trend Filter Parameters

Trend confirmation rules.


Symbol Parameters

Control of which markets are traded.


------------------------------------------------------------
5. SIGNAL THRESHOLDS
------------------------------------------------------------

Thresholds determine when signals advance
through the signal lifecycle.

Signal states:

PRE
CONFIRM
OPEN_NOW


Example thresholds:

PRE_THRESHOLD = 70
CONFIRM_THRESHOLD = 75
OPEN_THRESHOLD = 80


Example command:

/thresholds PRE 68
/thresholds CONFIRM 72
/thresholds OPEN 78


------------------------------------------------------------
6. SUPPORT / RESISTANCE BUFFER CONTROL
------------------------------------------------------------

Support / resistance filters prevent trades too close
to important price levels.

Example parameter:

SR_BUFFER


Example values:

Small buffer

0.0003


Medium buffer

0.0006


Large buffer

0.0010


Example command:

/sr 0.0006


------------------------------------------------------------
7. BUFFER PROFILES
------------------------------------------------------------

Instead of numeric buffers, operators may select profiles.

Example profiles:

SMALL_BUFFER
MEDIUM_BUFFER
LARGE_BUFFER


Example command:

/buffer_profile SMALL


These profiles map to predefined values.


------------------------------------------------------------
8. SPIKE FILTER PARAMETERS
------------------------------------------------------------

Spike filters detect abnormal candles
that indicate unstable market conditions.

Example parameters:

WICK_RATIO_LIMIT

ATR_JUMP_LIMIT


Example values:

WICK_RATIO_LIMIT = 5.0
ATR_JUMP_LIMIT = 2.2


Example commands:

/spike wick_ratio 5.5
/spike atr_jump 2.0


------------------------------------------------------------
9. TREND FILTER PARAMETERS
------------------------------------------------------------

Trend filters ensure trades follow the market direction.

Example parameters:

EMA_DISTANCE_MIN
TREND_CONFIRMATION_BARS


Example commands:

/trend ema_gap 0.0004
/trend confirm_bars 3


------------------------------------------------------------
10. SYMBOL CONTROL
------------------------------------------------------------

The system must allow dynamic control of
which symbols are traded.

Example commands:

/symbols list

/symbols add EURAUD

/symbols remove GBPJPY


------------------------------------------------------------
11. PARAMETER STORAGE
------------------------------------------------------------

Strategy parameters must be stored persistently.

Recommended storage location:

/opt/binarybot/config/strategy_params.json


Example structure:

{
  "thresholds": {
    "pre": 70,
    "confirm": 75,
    "open": 80
  },
  "sr_buffer": 0.0006,
  "spike": {
    "wick_ratio": 5.0,
    "atr_jump": 2.2
  }
}


------------------------------------------------------------
12. ENGINE PARAMETER LOADING
------------------------------------------------------------

The signal engine must load parameters
from the configuration file at runtime.

Loading points:

Engine startup

Periodic refresh

Admin parameter update


------------------------------------------------------------
13. LIVE PARAMETER UPDATE
------------------------------------------------------------

When an admin changes parameters:

the configuration file is updated

the engine reloads parameters

the new settings take effect immediately


------------------------------------------------------------
14. PARAMETER VALIDATION
------------------------------------------------------------

All parameter updates must be validated.

Examples:

Threshold values must remain between:

50 and 95


SR buffer must remain within:

0.0001 and 0.002


Invalid parameters must be rejected.


------------------------------------------------------------
15. PARAMETER CHANGE LOGGING
------------------------------------------------------------

All parameter changes must be logged.

Log location:

/opt/binarybot/observability/admin_proofs.jsonl


Example event:

event_type: admin_change

data:

parameter: SR_BUFFER
old_value: 0.0006
new_value: 0.0008
admin: OWNER


------------------------------------------------------------
16. ROLE PERMISSIONS
------------------------------------------------------------

Parameter modification permissions are defined in:

ROLE_AND_PERMISSION_MATRIX_SPEC.md


Example roles:

OWNER

Full control.


PRIMARY_ADMIN

May change thresholds and symbols.


ANALYST

Read-only access.


------------------------------------------------------------
17. SAFETY MECHANISMS
------------------------------------------------------------

Strategy control must include safety protections.

Examples:

Maximum parameter change limits

Parameter rollback capability

Emergency reset to default strategy


------------------------------------------------------------
18. FUTURE EXTENSIONS
------------------------------------------------------------

Possible improvements include:

Automatic parameter tuning

Strategy optimization suggestions

Machine learning threshold adjustments


------------------------------------------------------------
19. RELATION TO OTHER SPECIFICATIONS
------------------------------------------------------------

Related documents:

CONTROL_PANEL_HIERARCHY_AND_INTELLIGENCE_SPEC.md
ROLE_AND_PERMISSION_MATRIX_SPEC.md
AI_STRATEGY_AUDITOR_SPEC.md
SIGNAL_DEBUG_DASHBOARD_SPEC.md


------------------------------------------------------------
20. FINAL STATEMENT
------------------------------------------------------------

The Strategy Parameter Control system enables
safe and flexible management of the trading strategy.

By separating strategy logic from parameter control,
BinaryBot can evolve and adapt without requiring
frequent code changes or system redeployment.