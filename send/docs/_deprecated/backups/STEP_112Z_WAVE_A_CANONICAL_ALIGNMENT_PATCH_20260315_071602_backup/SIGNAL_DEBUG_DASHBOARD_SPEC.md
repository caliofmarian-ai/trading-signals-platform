BINARYBOT — SIGNAL DEBUG DASHBOARD SPECIFICATION

Version: 1.0  
Status: CANONICAL SPECIFICATION  
Location: /opt/binarybot/docs/SIGNAL_DEBUG_DASHBOARD_SPEC.md  


------------------------------------------------------------
1. PURPOSE
------------------------------------------------------------

The Signal Debug Dashboard provides real-time diagnostic
visibility into the signal decision pipeline.

Its primary goal is to help operators understand:

• why signals are not produced
• which gates block signals
• how strategy scores behave
• where signals die in the lifecycle

The dashboard must allow operators to debug the system
without inspecting raw logs or modifying code.


------------------------------------------------------------
2. SYSTEM ROLE
------------------------------------------------------------

The debug dashboard belongs to the following architecture layers:

INTELLIGENCE  
ADMIN  

It consumes data from:

ENGINE  
FSM  
OBSERVABILITY  
AUDIT  


------------------------------------------------------------
3. CORE PROBLEM IT SOLVES
------------------------------------------------------------

Without diagnostics, an operator cannot determine whether:

• the engine is running
• market data is available
• strategy gates are too strict
• SR filters are blocking signals
• score thresholds are too high
• signals are dying between PRE and CONFIRM

The debug dashboard makes these problems visible instantly.


------------------------------------------------------------
4. DASHBOARD ACCESS
------------------------------------------------------------

The dashboard is accessible via Telegram admin commands.

Access roles:

OWNER  
PRIMARY_ADMIN  
FUNCTIONAL_ADMIN  
ANALYST  

Unauthorized users must receive:

Unauthorized command.


------------------------------------------------------------
5. TELEGRAM COMMANDS
------------------------------------------------------------

Example commands:

/debug symbol EURUSD

/debug last

/debug stats

/debug gates

/debug scores


------------------------------------------------------------
6. DEBUG SIGNAL VIEW
------------------------------------------------------------

The main diagnostic view shows the most recent signal evaluation.

Example output:

PAIR: EURAUD
TIMEFRAME: 1m

TREND: WITH_TEND
SCORE: 66.4

SR_DISTANCE: 0.00042
SR_REQUIRED: 0.00060

SPIKE_FILTER: PASS
TREND_FILTER: PASS

FINAL_DECISION: REJECT

REJECT_REASON: SR_SPACE_INSUFFICIENT


------------------------------------------------------------
7. ENGINE DIAGNOSTICS
------------------------------------------------------------

The dashboard must confirm engine health.

Example output:

ENGINE STATUS

Market Data: OK  
Candles Retrieved: 50  
Last Candle Time: 18:42:00  

Engine Loop: ACTIVE  
Engine Tick Interval: 2 seconds


------------------------------------------------------------
8. STRATEGY SCORE DIAGNOSTICS
------------------------------------------------------------

Score diagnostics show score distribution
for the latest evaluations.

Example:

Score Breakdown

RSI Score: 18  
Trend Score: 20  
Momentum Score: 12  
Structure Score: 16  

Total Score: 66

PRE Threshold: 70


------------------------------------------------------------
9. GATE DIAGNOSTICS
------------------------------------------------------------

Strategy gates determine whether signals are allowed.

Example gate output:

Gate Status

Trend Filter: PASS
Spike Filter: PASS
Structure Filter: FAIL

Fail Reason

SR_SPACE_INSUFFICIENT


------------------------------------------------------------
10. SIGNAL LIFECYCLE DIAGNOSTICS
------------------------------------------------------------

Shows where signals die in the lifecycle.

Example:

Signal Lifecycle

Candidates: 120
PRE Signals: 35
CONFIRM Signals: 12
OPEN Signals: 4


------------------------------------------------------------
11. SYMBOL HEALTH DIAGNOSTICS
------------------------------------------------------------

Shows signal production per symbol.

Example:

Symbol Health

EURUSD  
Decisions: 140  
PRE: 8  

GBPUSD  
Decisions: 160  
PRE: 3  

BTCUSD  
Decisions: 100  
PRE: 30


------------------------------------------------------------
12. SR FILTER DEBUG
------------------------------------------------------------

Support/Resistance filters are a major source of signal rejection.

Example diagnostic:

Price: 1.07340  
Nearest Resistance: 1.07380  

Distance: 0.00040  
Required Distance: 0.00060  

Result: REJECT


------------------------------------------------------------
13. DECISION AUDIT LINK
------------------------------------------------------------

Each debug output must reference the decision audit system.

Example:

Decision ID: 8f93c7

Audit Event Available.


------------------------------------------------------------
14. SIGNAL HEATMAP LINK
------------------------------------------------------------

Debug dashboard should integrate with:

AI_STRATEGY_AUDITOR_SPEC.md

Operators must be able to view:

• score heatmaps  
• rejection distribution  
• strategy bottlenecks  


------------------------------------------------------------
15. TELEGRAM DEBUG FORMAT
------------------------------------------------------------

Example Telegram message:

SIGNAL DEBUG

PAIR: EURAUD  
SCORE: 66.4  

TREND: WITH_TREND  
SPIKE: PASS  

SR DISTANCE: 0.00042  
REQUIRED: 0.00060  

RESULT: REJECT  
REASON: SR_SPACE_INSUFFICIENT


------------------------------------------------------------
16. DEBUG LOG SOURCES
------------------------------------------------------------

The dashboard reads from observability logs.

Primary sources:

/opt/binarybot/observability/engine_events.jsonl  
/opt/binarybot/observability/fsm_events.jsonl  


------------------------------------------------------------
17. FUTURE EXTENSIONS
------------------------------------------------------------

Possible improvements:

• graphical dashboards  
• signal replay  
• strategy simulation  
• historical diagnostics  


------------------------------------------------------------
18. FINAL STATEMENT
------------------------------------------------------------

The Signal Debug Dashboard is the primary operational
tool for diagnosing strategy behavior.

It allows the system owner and administrators to understand
signal production dynamics in real time without reading raw logs
or inspecting source code.

This greatly improves maintainability and operational control.