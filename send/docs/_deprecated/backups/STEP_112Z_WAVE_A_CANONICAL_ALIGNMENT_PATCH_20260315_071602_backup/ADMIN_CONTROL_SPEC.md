ADMIN_CONTROL_SPEC.md

Admin Control Interface Specification — BinaryBot
Version: 1.0.0
Status: Canonical
Linked Documents: TELEGRAM_UX.md, ALGO_SPEC.md, FSM_SPEC.md, SIGNAL_DISTRIBUTION_SPEC.md, CHANNEL_CONFIG_SPEC.md, PERFORMANCE_ANALYTICS_SPEC.md, OBSERVABILITY_LOGGING_SPEC.md

---

1. PURPOSE

This document defines the Admin Control Panel of BinaryBot.

The Admin Control Panel allows the system operator to:

- Control operational parameters
- Select tradable symbols
- Monitor system state
- Access research statistics
- View internal documentation
- Verify system behavior

The Admin Panel is not visible to public users.

Only the system operator has access.

---

2. ADMIN ACCESS CONTROL (RBAC)

Access to the Admin Control Panel is governed by the Role-Based Access Control model defined in:

ADMIN_OPERATIONS_SPEC.md

Supported roles:

OWNER  
ADMIN  
ANALYST  
MODERATOR

Each role has different permissions inside the Admin Panel.

Example:

OWNER
- full control

ADMIN
- operational control (buffer, symbols, status)

ANALYST
- research access only

MODERATOR
- limited status viewing

Role permissions are enforced by the control layer before executing any command.

Unauthorized users must receive:

Access denied.

No admin information must be exposed.

---

3. ADMIN PANEL ENTRY POINT

The Admin Panel is accessed through a Telegram command:

/admin

This command opens the Admin Control interface.

The interface is displayed as a button-based control panel.

All controls are accessible via inline keyboard buttons.

---

4. CORE CONTROL BUTTONS

The main Admin Panel contains the following core controls:

SET BUFFER
SET SYMBOLS
SYSTEM STATUS
RESEARCH PANEL
VIEW DOCUMENTATION

Each button opens a sub-interface.

---

5. BUFFER CONTROL

Purpose:

Change the active buffer mode used by the trading engine.

Available modes:

SMALL
MEDIUM
LARGE

Example interface:

Select Buffer Mode

[ SMALL ]
[ MEDIUM ]
[ LARGE ]

When selected:

The bot updates the configuration parameter controlling buffer size.

Effect:

- Changes apply only to future signals.
- Active trades are unaffected.

All changes must be logged.

---

6. SYMBOL SELECTION INTERFACE

Purpose:

Define which symbols the bot scans.

The Admin selects symbols based on high broker payout availability.

The bot itself does not know payout values.

The operator manually selects high-payout pairs.

Example interface:

Active Symbols

[EURUSD]  ON/OFF
[GBPUSD]  ON/OFF
[USDJPY]  ON/OFF
[AUDUSD]  ON/OFF
[USDCAD]  ON/OFF

Rules:

- Enabled symbols are scanned in WIDE SCAN mode.
- Disabled symbols produce no signals.
- Removing a symbol clears its WATCHLIST state.

---

7. WIDE SCAN AND FOCUS BEHAVIOR

The bot normally runs in WIDE SCAN mode.

Meaning:

All enabled symbols are scanned continuously.

When a PRE signal is detected:

The symbol enters FOCUS MODE.

Focus behavior:

70% of API resources are directed to the focus symbol.

30% remain on remaining wide-scan symbols.

If a second PRE signal appears:

Resources may split 50% / 50%.

When a trade either:

- reaches OPEN_NOW
- or invalidates

The symbol exits focus and returns to WIDE SCAN.

---

8. SYSTEM STATUS PANEL

Purpose:

Display real-time system state.

Displayed information:

ENGINE STATUS
Running / Stopped

SCAN MODE
Wide Scan / Focus Mode

ACTIVE SYMBOLS
List of enabled pairs

FOCUS SYMBOLS
Current focus targets

API LOAD
Current request rate

WATCHLIST SIZE
Number of tracked setups

This panel allows the operator to verify system health.

---

9. RESEARCH PANEL

Purpose:

Provide statistical insight into trading behavior.

Available research tools:

SIGNAL PERFORMANCE

Displays per-symbol statistics:

- Number of PRE signals
- Number of CONFIRM signals
- Number of OPEN_NOW signals

Helps identify productive pairs.

---

FOCUS HISTORY

Shows historical focus events.

Example data:

EURUSD
PRE signals: 34
CONFIRM: 21
OPEN_NOW: 15

GBPUSD
PRE signals: 19
CONFIRM: 10
OPEN_NOW: 7

This helps determine which pairs generate the most valid signals.

---

10. SIGNAL OUTCOME ANALYTICS

Outcome data collected from ELITE members is analyzed here.

Metrics:

- WIN count
- LOSE count
- MISSED count
- Win rate per symbol
- Win rate per session

Example display:

EURUSD
WIN: 63%
LOSE: 27%
MISSED: 10%
Total trades: 120

This allows algorithm performance evaluation.

---

11. SYSTEM MONITORING

Admin can inspect operational alerts.

Examples:

ENGINE STARTED
ENGINE STOPPED
API ERROR
RESTART DETECTED
COOLDOWN RECOVERY

Logs are pulled from the system observability layer.

---

12. DOCUMENTATION VIEWER

The Admin Panel provides access to system documentation.

Available documents:

VIEW ALGO_SPEC
VIEW FSM_SPEC
VIEW TELEGRAM_UX
VIEW RISK_MODEL
VIEW CHANNEL_CONFIG
VIEW SIGNAL_DISTRIBUTION
VIEW PERFORMANCE_ANALYTICS

When selected:

The bot sends the requested Markdown document to the admin.

Purpose:

Allow the operator to review system rules directly inside Telegram.

---

13. SAFETY RULES

The Admin Panel must never:

- expose sensitive configuration publicly
- allow unauthorized access
- modify active trades
- bypass risk protections

Admin actions affect future signals only.

---

14. OPERATIONAL GUARANTEE

If ADMIN_CONTROL_SPEC is implemented correctly:

The operator gains full control of system behavior without exposing internal mechanisms to users.

This ensures:

- safe configuration management
- transparency of operation
- continuous system monitoring
- long-term strategy improvement

---

15. ROLE-BASED PANEL VISIBILITY

The Admin Panel must dynamically adjust visible controls based on the role of the user.

Examples:

OWNER / ADMIN

Visible buttons:
SET BUFFER
SET SYMBOLS
SYSTEM STATUS
RESEARCH PANEL
VIEW DOCUMENTATION

ANALYST

Visible buttons:
RESEARCH PANEL
SYSTEM STATUS
VIEW DOCUMENTATION

MODERATOR

Visible buttons:
SYSTEM STATUS (limited)

Buttons that the user is not authorized to use must not appear in the interface.

End of ADMIN_CONTROL_SPEC.md