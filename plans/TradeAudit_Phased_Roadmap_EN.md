# TradeAudit — Phased Implementation Roadmap

This roadmap reorganizes the full TradeAudit implementation plan into practical development phases.

The goal is to make every phase independently implementable, testable, and releasable.

---

# Phase 0 — Project Foundation

## Goal

Create a stable project skeleton and development environment before implementing MT5 or analytics logic.

## Scope

- Python project setup
- virtual environment
- package structure
- dependency management
- logging
- configuration
- SQLite setup
- unit-test framework
- application bootstrap
- basic PySide6 window
- application versioning

## Deliverables

```text
TradeAudit/
│
├── README.md
├── IMPLEMENTATION_PLAN.md
├── pyproject.toml
├── requirements.txt
├── src/
├── tests/
├── resources/
└── scripts/
```

Core modules:

```text
app
domain
infrastructure
ui
tests
```

## Technical Tasks

- configure Python 3.11/3.12;
- create PySide6 application shell;
- initialize SQLAlchemy;
- create SQLite database;
- configure logging;
- define application settings;
- define exception handling;
- configure `pytest`;
- add basic CI-ready test command.

## Definition of Done

- [ ] application starts successfully;
- [ ] main window opens;
- [ ] database initializes;
- [ ] logs are written;
- [ ] tests run successfully;
- [ ] project structure is stable.

---

# Phase 1 — MT5 Connection and Account Settings

## Goal

Allow TradeAudit to connect safely to a user-selected MetaTrader 5 terminal.

## Scope

- MT5 executable path;
- login;
- password;
- server;
- connection status;
- secure password storage;
- account information.

## Deliverables

### Settings Screen

Fields:

```text
MT5 Path
Login
Password
Server
Connection Timeout
```

### Services

```text
MT5ConnectionService
CredentialStore
SettingsRepository
```

## Security

Password must be stored using:

```text
Python keyring
→ Windows Credential Locker
```

Never store passwords in plain text.

## Connection Flow

```text
User Settings
    ↓
Credential Store
    ↓
MT5 initialize()
    ↓
Connection Validation
    ↓
Account Info
```

## Definition of Done

- [ ] user can select `terminal64.exe`;
- [ ] login and server can be saved;
- [ ] password is stored securely;
- [ ] app connects to MT5;
- [ ] connection errors are displayed;
- [ ] account balance/equity/currency are shown;
- [ ] password never appears in logs.

---

# Phase 2 — MT5 History Import and Trade Aggregation

## Goal

Import raw MT5 history and convert it into logical trades.

## Scope

- historical orders;
- historical deals;
- positions;
- duplicate protection;
- partial close support;
- multiple entries;
- scale-in / scale-out;
- local persistence.

## MT5 Functions

```text
history_orders_get()
history_deals_get()
```

## Core Services

```text
MT5HistoryReader
TradeAggregator
TradeNormalizer
SyncService
```

## Important Rule

```text
MT5 Deal != Logical Trade
```

Deals must be grouped using:

```text
position_id
```

where appropriate.

## Database Tables

```text
accounts
trades
trade_deals
sync_state
```

## Sync Workflow

```text
Connect
  ↓
Load Last Sync Timestamp
  ↓
Request MT5 History
  ↓
Normalize Orders/Deals
  ↓
Aggregate Logical Trades
  ↓
Store in SQLite
  ↓
Refresh UI
```

## Definition of Done

- [x] historical MT5 data can be imported;
- [x] duplicate records are prevented;
- [x] trades are grouped correctly;
- [x] partial closes are supported;
- [x] open and close times are correct;
- [x] BUY/SELL direction is correct;
- [x] imported trades persist between application sessions.


---

# Phase 3 — Risk, R-Multiple and Risk/Reward Engine

## Goal

Calculate risk and R consistently for every trade.

## Scope

- initial SL;
- initial TP;
- price risk;
- monetary risk;
- planned R:R;
- realized R;
- risk percentage;
- invalid setups;
- missing SL handling.

## Core Services

```text
RiskCalculator
RMultipleCalculator
TradeValidator
```

## Core Formulas

### Risk

```text
RiskPrice = abs(Entry - InitialSL)
```

### Planned Reward

```text
RewardPrice = abs(InitialTP - Entry)
```

### Planned R:R

```text
PlannedRR = RewardPrice / RiskPrice
```

### 1R

```text
1R = Initial Risk Money
```

### Realized R

```text
RealizedR = NetProfit / InitialRiskMoney
```

## Monetary Risk

Prefer:

```python
mt5.order_calc_profit(...)
```

where possible.

## Important Rules

- R must be based on the **initial SL**;
- final SL must not redefine original risk;
- trades without known initial SL must have:

```text
R = UNKNOWN
```

not an invented value.

## Definition of Done

- [x] BUY risk calculation works;
- [x] SELL risk calculation works;
- [x] monetary risk works;
- [x] risk percentage works;
- [x] planned R:R works;
- [x] realized R works;
- [x] missing SL is handled;
- [x] invalid SL/TP direction is detected;
- [x] unit tests cover calculations.

---

# Phase 4 — Core Performance Analytics

## Goal

Determine whether the historical sample shows a measurable trading edge.

## Scope

- total trades;
- wins;
- losses;
- win rate;
- net P/L;
- Net R;
- average winner;
- average loser;
- expectancy;
- profit factor;
- drawdown;
- losing streaks;
- minimum sample warning.

## Core Service

```text
PerformanceAnalyzer
```

## Key Metrics

### Win Rate

```text
Winning Trades / Closed Trades
```

### Expectancy

```text
ExpectancyR =
(WinRate × AvgWinR)
-
(LossRate × AvgLossR)
```

### Profit Factor

```text
Gross Profit / abs(Gross Loss)
```

### Net R

```text
sum(RealizedR)
```

### Max Drawdown

Calculated from cumulative R.

## Profitability Verdicts

```text
INSUFFICIENT_DATA
NEGATIVE_EXPECTANCY
BREAK_EVEN
POSITIVE_EXPECTANCY
```

## Minimum Sample

Default:

```text
30 trades
```

Configurable later.

## Definition of Done

- [ ] all core metrics are calculated;
- [ ] drawdown curve is correct;
- [ ] losing streak is correct;
- [ ] insufficient sample warnings work;
- [ ] metrics are covered by unit tests;
- [ ] results can be reproduced from the same dataset.

---

# Phase 5 — Analysis Filters and Dashboard

## Goal

Allow the user to analyze a specific subset of trades.

## Scope

### Period

```text
Today
Yesterday
This Week
Last Week
This Month
Last Month
Custom
```

### Direction

```text
BUY
SELL
ALL
```

### Symbols

```text
One
Multiple
All
```

### Results

```text
ALL
WINNERS
LOSERS
BREAKEVEN
```

## Core Model

```text
AnalysisFilter
```

## Dashboard KPIs

```text
Trades
Win Rate
Net P/L
Net R
Average R
Expectancy
Profit Factor
Max Drawdown
Average Risk %
```

## Charts

- cumulative R;
- drawdown;
- performance by symbol;
- BUY vs SELL.

## Definition of Done

- [ ] date filters work;
- [ ] BUY/SELL/ALL works;
- [ ] symbol multi-select works;
- [ ] all-symbol mode works;
- [ ] dashboard recalculates automatically;
- [ ] charts respect active filters.

---

# Phase 6 — Strategy Management and Compliance

## Goal

Separate strategy performance from trader execution quality.

## Scope

- strategy CRUD;
- strategy assignment to trades;
- strategy rules;
- manual compliance review;
- deviation tagging;
- compliance score.

## Strategy Model

```text
Name
Description
Allowed Symbols
Allowed Sessions
Minimum RR
Maximum Risk %
Maximum Trades / Day
Requires SL
Requires TP
Allowed Direction
```

## Rule Engine

```text
StrategyComplianceEngine
```

## Example Rules

```text
MIN_RR
MAX_RISK_PERCENT
REQUIRES_STOP_LOSS
REQUIRES_TAKE_PROFIT
MAX_TRADES_PER_DAY
ALLOWED_SESSION
ALLOWED_DIRECTION
ALLOWED_SYMBOL
```

## Compliance States

```text
COMPLIANT
PARTIAL
DEVIATION
```

## Definition of Done

- [ ] strategies can be created;
- [ ] strategies can be edited;
- [ ] trades can be linked to a strategy;
- [ ] manual compliance can be recorded;
- [ ] automatic rule checks work;
- [ ] deviation reasons are stored;
- [ ] compliant and deviation trades can be analyzed separately.

---

# Phase 7 — Behavioral and Emotional Trade Analysis

## Goal

Identify discipline problems without confusing losing trades with bad trades.

## Scope

- emotional tags;
- FOMO;
- revenge trading;
- overtrading;
- risk escalation;
- SL violations;
- impulsive trades;
- user confirmation of automatic flags.

## Important Rule

```text
Loss != Emotional Trade
```

and:

```text
Win != Good Trade
```

## User Emotion Tags

```text
CALM
FOMO
FEAR
GREED
REVENGE
BOREDOM
FRUSTRATION
OVERCONFIDENCE
IMPULSIVE
OTHER
```

## BehaviorAnalyzer

Input context:

```text
current trade
previous trade
time since previous trade
previous result
average risk
current risk
strategy rules
number of trades today
```

## Automatic Flags

```text
POSSIBLE_REVENGE_TRADE
POSSIBLE_FOMO
OVERTRADING
RISK_ESCALATION
SL_MOVED_AWAY
```

## Confidence

```text
NONE
LOW
MEDIUM
HIGH
```

## User Action

```text
Confirm
Reject
```

## Definition of Done

- [ ] manual emotional tags work;
- [ ] revenge heuristic works;
- [ ] FOMO heuristic works;
- [ ] overtrading detection works;
- [ ] risk escalation works;
- [ ] SL violations work;
- [ ] automatic flags explain their reasons;
- [ ] user can confirm/reject flags.

---

# Phase 8 — Strategy vs Trader Performance

## Goal

Measure whether losses come from the strategy itself or from deviations in execution.

## Scope

### Compliant Performance

```text
Trades
Net R
Expectancy
Profit Factor
Drawdown
```

### Deviation Performance

```text
Trades
Net R
Expectancy
Profit Factor
Drawdown
```

### Emotional Performance

```text
Trades
Net R
Expectancy
```

## Four-Quadrant Analysis

### Good Win

```text
Strategy followed
+
Profitable
```

### Good Loss

```text
Strategy followed
+
Loss
```

### Bad Win

```text
Strategy violated
+
Profitable
```

### Bad Loss

```text
Strategy violated
+
Loss
```

## Key Metric

```text
Deviation Cost R
```

## Example

```text
All Trades:
+4R

Compliant Trades:
+17R

Deviation Trades:
-13R
```

## Definition of Done

- [ ] compliant subset metrics exist;
- [ ] deviation subset metrics exist;
- [ ] emotional subset metrics exist;
- [ ] four-quadrant classification exists;
- [ ] deviation cost in R is visible;
- [ ] reports clearly separate strategy quality from execution quality.

---

# Phase 9 — Advanced Breakdown Analytics

## Goal

Discover where the edge is strongest and weakest.

## Scope

### Direction

```text
BUY
SELL
```

### Symbols

```text
EURUSD
GBPUSD
XAUUSD
...
```

### Time

```text
weekday
hour
session
```

### Context

```text
performance after win
performance after loss
performance by streak
performance by emotion
performance by setup
```

## Reports

### Symbol Breakdown

```text
Trades
Win Rate
Net R
Expectancy
Profit Factor
Max DD
```

### Direction Breakdown

```text
BUY metrics
SELL metrics
```

### Session Breakdown

```text
Asia
London
New York
Overlap
```

## Definition of Done

- [ ] symbol performance works;
- [ ] BUY vs SELL works;
- [ ] weekday analysis works;
- [ ] hourly analysis works;
- [ ] session analysis works;
- [ ] post-win/post-loss behavior can be analyzed.

---

# Phase 10 — Live Trade Journal and Modification Tracking

## Goal

Capture data that cannot always be reconstructed reliably from historical MT5 records.

## Scope

- live position watcher;
- initial SL snapshot;
- initial TP snapshot;
- SL history;
- TP history;
- partial closes;
- position-size changes;
- trade modification timestamps.

## Data Tables

```text
sl_history
tp_history
trade_events
```

## Important Benefit

This phase improves the accuracy of:

- original risk;
- SL-moving analysis;
- TP-moving analysis;
- early exits;
- late exits;
- risk escalation;
- behavioral review.

## Definition of Done

- [ ] new positions are detected;
- [ ] initial SL is captured;
- [ ] initial TP is captured;
- [ ] SL modifications are recorded;
- [ ] TP modifications are recorded;
- [ ] partial closes are recorded;
- [ ] position sizing changes are recorded.

---

# Phase 11 — Markdown and AI-Ready Reporting

## Goal

Generate a structured report that can be uploaded directly to ChatGPT for deeper analysis.

## Scope

### Export Types

```text
Summary
Standard
Full
```

### Filters

The report must respect:

```text
Period
Direction
Symbols
Strategy
Compliance
Result
```

## Main Sections

```text
Executive Summary
Strategy Quality
Behavioral Summary
Cost of Deviations
Direction Analysis
Symbol Analysis
Session Analysis
Risk and Drawdown
Risk Discipline
R Distribution
Trade Table
Deviation Details
Emotional Events
Known Limitations
AI Questions
Suggested AI Prompt
```

## AI Export

Dedicated button:

```text
Export for AI
```

## Privacy

Default behavior:

```text
Mask account number
Never export password
Optionally hide broker/server
Optionally remove ticket IDs
```

## Report Metadata

```yaml
report_version: 1
application: TradeAudit
app_version: ...
schema_version: ...
generated_at: ...
```

## Definition of Done

- [ ] Markdown export works;
- [ ] report respects active filters;
- [ ] report includes all core metrics;
- [ ] report includes compliance metrics;
- [ ] report includes behavioral metrics;
- [ ] report includes known limitations;
- [ ] report includes AI questions;
- [ ] report can be uploaded directly to ChatGPT.

---

# Phase 12 — Production Packaging and Windows EXE

## Goal

Turn the application into a distributable Windows product.

## Scope

- PyInstaller;
- `.spec` file;
- one-folder build;
- application icon;
- version information;
- build scripts;
- local data directories;
- backup;
- installer optional later.

## Recommended First Build

```text
one-folder
```

instead of `--onefile`.

## Build Command

```bash
pyinstaller TradeAudit.spec
```

## Build Script

```bat
@echo off

call .venv\Scripts\activate

pytest

if errorlevel 1 (
    echo Tests failed.
    exit /b 1
)

pyinstaller --clean --noconfirm TradeAudit.spec
```

## App Data

```text
%LOCALAPPDATA%\TradeAudit\
```

Subfolders:

```text
database\
logs\
exports\
config\
backups\
```

## Definition of Done

- [ ] tests pass before build;
- [ ] Windows `.exe` runs without Python installed;
- [ ] MT5 connection works from packaged build;
- [ ] database persists;
- [ ] keyring works;
- [ ] Markdown export works;
- [ ] logs work;
- [ ] backups work.

---

# Phase 13 — Advanced Risk Research

## Goal

Add deeper statistical tools after the core application is stable.

## Scope

- Monte Carlo simulation;
- Risk of Ruin;
- rolling expectancy;
- rolling profit factor;
- rolling drawdown;
- performance stability;
- regime comparison;
- confidence intervals.

## Example

```text
Last 20 Trades Expectancy
Last 50 Trades Expectancy
Last 100 Trades Expectancy
```

## Definition of Done

- [ ] rolling metrics exist;
- [ ] Monte Carlo simulation works;
- [ ] Risk of Ruin is available;
- [ ] confidence warnings are clear;
- [ ] advanced analytics do not alter raw trade data.

---

# Recommended Release Milestones

## Milestone A — Technical Prototype

Includes:

```text
Phase 0
Phase 1
Phase 2
Phase 3
```

Result:

TradeAudit can connect to MT5, import trades, and calculate R.

---

# Milestone B — Usable MVP

Includes:

```text
Phase 0–5
```

Result:

TradeAudit can answer:

```text
Is this historical sample profitable?
What is my expectancy?
What is my Net R?
What is my drawdown?
How does BUY compare with SELL?
How do symbols compare?
```

---

# Milestone C — Trading Journal MVP

Includes:

```text
Phase 0–8
```

Result:

TradeAudit can distinguish:

```text
strategy quality
execution quality
behavioral mistakes
```

This is the first version that delivers the full core product idea.

---

# Milestone D — Professional Analysis Version

Includes:

```text
Phase 0–11
```

Result:

TradeAudit supports:

```text
strategy analytics
behavioral analytics
live trade journal
AI-ready Markdown reports
```

This is the recommended first public beta.

---

# Milestone E — Production Release

Includes:

```text
Phase 0–12
```

Result:

A packaged Windows application distributed as:

```text
TradeAudit.exe
```

with persistent database, secure credentials, reports, backups, and MT5 integration.

---

# Milestone F — Advanced Analytics

Includes:

```text
Phase 13
```

Result:

TradeAudit becomes a deeper quantitative trading-performance research tool.

---

# Recommended Development Priority

If the goal is to reach useful software quickly, implement in this order:

```text
1. Foundation
2. MT5 Connection
3. History Import
4. Risk / R
5. Core Analytics
6. Filters / Dashboard
7. Strategy Compliance
8. Behavioral Analysis
9. Strategy vs Trader Comparison
10. AI Markdown Export
11. Live Journal
12. EXE Packaging
13. Advanced Quant Analytics
```

---

# Recommended MVP Boundary

The best MVP boundary is:

```text
Phase 0
through
Phase 8
```

because this produces the core TradeAudit value proposition:

```text
Does the strategy have an edge?

Am I actually following it?

How much R do my deviations cost?

Are emotional decisions damaging performance?
```

Everything after that improves depth, automation, reporting, and distribution.
