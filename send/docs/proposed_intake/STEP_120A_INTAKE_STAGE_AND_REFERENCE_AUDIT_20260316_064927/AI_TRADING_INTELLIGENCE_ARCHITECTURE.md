BINARYBOT — AI TRADING INTELLIGENCE ARCHITECTURE

Version: 1.0  
Status: CANONICAL SPECIFICATION  
Location: /opt/binarybot/docs/AI_TRADING_INTELLIGENCE_ARCHITECTURE.md


------------------------------------------------------------
1. PURPOSE
------------------------------------------------------------

This document defines the architecture of the AI-powered
strategy intelligence system used by BinaryBot.

The AI Intelligence Layer transforms raw strategy activity
into operational insights and strategic diagnostics.

The system answers questions such as:

• Why are signals not appearing?
• Which filters block most signals?
• Which symbols perform best?
• Which thresholds are too strict?
• Where does the signal lifecycle fail?

The AI layer does NOT trade.

Its responsibility is analysis and explanation.


------------------------------------------------------------
2. POSITION IN SYSTEM ARCHITECTURE
------------------------------------------------------------

The AI Intelligence Layer sits above the operational engine.

System stack:

MARKET DATA
↓
ENGINE
↓
FSM
↓
OBSERVABILITY
↓
AUDIT
↓
AI INTELLIGENCE
↓
ADMIN CONTROL
↓
DISTRIBUTION


------------------------------------------------------------
3. INTELLIGENCE COMPONENTS
------------------------------------------------------------

The AI Intelligence system is composed of several modules.

Core modules:

AI Strategy Auditor  
Strategy Heatmap Generator  
Signal Diagnostic Engine  
Symbol Health Analyzer  
Bottleneck Detector  
Research Engine  


------------------------------------------------------------
4. AI STRATEGY AUDITOR
------------------------------------------------------------

Defined in:

AI_STRATEGY_AUDITOR_SPEC.md

Responsibilities:

• read decision events
• analyze signal conversion
• detect strategy failures
• generate daily reports

Input sources:

engine_events.jsonl  
fsm_events.jsonl  
distribution_events.jsonl  

Outputs:

Daily Strategy Report


------------------------------------------------------------
5. STRATEGY HEATMAP
------------------------------------------------------------

The strategy heatmap analyzes score distributions
and signal conversion across score ranges.

Example heatmap:

Score Range | Decisions | PRE | CONFIRM | OPEN
------------------------------------------------
60-65       | 320       | 110 | 30      | 5
65-70       | 280       | 140 | 70      | 20
70-75       | 200       | 120 | 80      | 35

The heatmap reveals:

• score clustering
• dead score zones
• effective score ranges
• inefficient thresholds


------------------------------------------------------------
6. SIGNAL DIAGNOSTIC ENGINE
------------------------------------------------------------

The signal diagnostic engine explains why signals fail.

Example diagnostics:

SR_SPACE_INSUFFICIENT  
TREND_MISMATCH  
SPIKE_DETECTED  
LOW_SCORE  

These diagnostics feed both:

AI Strategy Auditor  
Signal Debug Dashboard


------------------------------------------------------------
7. SYMBOL HEALTH ANALYZER
------------------------------------------------------------

Symbol health measures how well each symbol performs
within the strategy.

Example metrics:

Symbol | Decisions | PRE | PRE Rate
-----------------------------------
EURUSD | 220       | 3   | 1.3%
GBPUSD | 190       | 2   | 1.0%
BTCUSD | 160       | 40  | 25%

Classification:

HEALTHY  
STARVED  
NOISY  
BLOCKED


------------------------------------------------------------
8. STRATEGY BOTTLENECK DETECTOR
------------------------------------------------------------

Detects dominant failure causes in the signal pipeline.

Example result:

Top Reject Cause:

SR_SPACE_INSUFFICIENT = 64%

Meaning:

Support/Resistance filter blocks most signals.


------------------------------------------------------------
9. SIGNAL LIFECYCLE ANALYSIS
------------------------------------------------------------

Measures how signals progress through the lifecycle.

Example:

Candidates: 120  
PRE Signals: 35  
CONFIRM Signals: 12  
OPEN Signals: 4  

Conversion rates:

PRE Conversion: 29%  
CONFIRM Conversion: 34%  
OPEN Conversion: 33%


------------------------------------------------------------
10. RESEARCH ENGINE
------------------------------------------------------------

The research engine analyzes historical performance
to guide strategy improvement.

Responsibilities:

• long-term signal statistics
• strategy performance evaluation
• threshold sensitivity analysis

The research engine supports the system owner
in making informed decisions about strategy adjustments.


------------------------------------------------------------
11. OPERATOR FEEDBACK LOOP
------------------------------------------------------------

Strategy improvement follows a feedback loop.

Strategy Execution
↓
Observability Logs
↓
Decision Audit
↓
AI Strategy Auditor
↓
Research Engine
↓
Operator Review
↓
Strategy Adjustment


------------------------------------------------------------
12. DATA SOURCES
------------------------------------------------------------

The intelligence system reads structured logs.

Primary sources:

/opt/binarybot/observability/engine_events.jsonl  
/opt/binarybot/observability/fsm_events.jsonl  
/opt/binarybot/observability/distribution_events.jsonl  


------------------------------------------------------------
13. REPORT TYPES
------------------------------------------------------------

The system produces several reports.

Daily Strategy Report

Includes:

• decision counts
• rejection breakdown
• score heatmap
• bottleneck detection

Symbol Health Report

Includes:

• symbol performance
• PRE conversion rates

Lifecycle Report

Includes:

• stage conversions
• lifecycle bottlenecks


------------------------------------------------------------
14. ADMIN INTEGRATION
------------------------------------------------------------

Admins can access intelligence reports via Telegram.

Example commands:

/strategy report  
/strategy heatmap  
/strategy diagnostics  
/symbol health  


------------------------------------------------------------
15. OPERATIONAL BENEFITS
------------------------------------------------------------

The AI Intelligence system provides:

• transparency into strategy behavior
• faster debugging
• improved strategy tuning
• reduced blind parameter adjustments


------------------------------------------------------------
16. FUTURE AI EXTENSIONS
------------------------------------------------------------

Possible upgrades:

• machine learning threshold suggestions
• adaptive score thresholds
• automated strategy tuning
• anomaly detection


------------------------------------------------------------
17. RELATION TO OTHER SPECIFICATIONS
------------------------------------------------------------

Related documents:

AI_STRATEGY_AUDITOR_SPEC.md  
SIGNAL_DEBUG_DASHBOARD_SPEC.md  
DECISION_AUDIT_SPEC.md  
PERFORMANCE_ANALYTICS_SPEC.md  
RESEARCH_AND_LEARNING_FRAMEWORK_SPEC.md  


------------------------------------------------------------
18. FINAL STATEMENT
------------------------------------------------------------

The AI Trading Intelligence Architecture transforms
BinaryBot from a simple signal generator into
a self-analyzing trading system.

This intelligence layer enables continuous
strategy improvement through data-driven insights.