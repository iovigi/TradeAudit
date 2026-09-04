# ⚡ TradeAudit

[![Python Version](https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.13-blue.svg)](https://www.python.org/)
[![GUI Framework](https://img.shields.io/badge/GUI-PySide6%20%28Qt6%29-41cd52.svg)](https://doc.qt.io/qtforpython/)
[![Database](https://img.shields.io/badge/Database-SQLite%20%2B%20SQLAlchemy-003B57.svg)](https://www.sqlalchemy.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows-0078D6.svg)](https://microsoft.com/windows)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**TradeAudit** is a professional desktop performance auditing, risk analytics, and behavioral intelligence platform built for **MetaTrader 5 (MT5)** traders.

Unlike standard trading journals that only calculate raw dollar gains, TradeAudit evaluates your trading through strict **R-Multiple** mathematics, separates **Strategy Quality** from **Trader Execution Quality**, detects emotional discipline breaches (FOMO, revenge trading, risk escalation), runs deep **Quantitative Research** (Monte Carlo simulations, Risk of Ruin), and reconstructs trades on **Interactive Candlestick Charts** with bar-by-bar trade replay.

---

## 💡 The Core Problem TradeAudit Solves

Every trader needs definitive answers to four fundamental questions:

1. **Does my strategy actually have a positive expectancy edge?**
2. **Am I executing the strategy rules with discipline?**
3. **How much R (risk units) do my execution mistakes and deviations cost me?**
4. **Are emotional impulses (FOMO, Revenge, Overtrading) draining my account?**

TradeAudit answers all four quantitatively and automatically.

---

## ✨ Key Features & Capabilities

### 📈 1. Performance Dashboard & Real-Time Analytics
- **Standardized R Accounting:** Realized R, Planned R:R, Win Rate, Expectancy (R per trade), Profit Factor, and Max Drawdown in R and currency.
- **Dynamic QtCharts:** Cumulative R equity curves, drawdown trajectories, symbol rankings, and BUY vs SELL performance comparisons.
- **Interactive Multi-Filters:** Filter seamlessly by custom date ranges, symbol multi-selection, trade direction, or outcome.

### ⚖️ 2. Strategy vs Trader Analysis (The 4-Quadrant Matrix)
- **Quadrant Categorization:** Classifies trades into **Good Wins** (Compliant + Profitable), **Good Losses** (Compliant + Loss), **Bad Wins** (Deviation + Profitable), and **Bad Losses** (Deviation + Loss).
- **Deviation Cost in R:** Quantifies the exact statistical cost of breaking your rules (e.g. `Compliant: +17.2R` vs `Deviations: -13.5R`).

### 🎯 3. Strategy Management & Compliance Engine
- Define custom strategies with explicit execution rules: Minimum R:R, Maximum Risk %, Allowed Symbols, Allowed Trading Sessions (Asia/London/NY), and Required SL/TP.
- Automatically audits historical trades against assigned strategies with clear compliance verdicts (`COMPLIANT`, `PARTIAL`, `DEVIATION`).

### 🧠 4. Behavioral & Emotional Trade Analysis
- Automated heuristics detect psychological mistakes:
  - 🚨 **Revenge Trading:** Rapid re-entries following losing trades.
  - 🌪️ **FOMO:** Chasing impulsive momentum without confirmed setups.
  - 📈 **Risk Escalation:** Unplanned position size inflation.
  - 🛑 **Stop-Loss Moving Away:** Widening risk mid-trade.
  - ⏱️ **Overtrading:** Exceeding disciplined daily trade limits.
- Supports emotional state tagging (`CALM`, `FEAR`, `GREED`, `FRUSTRATION`, `OVERCONFIDENCE`).

### 🕯️ 5. Interactive Candlestick Charts & Trade Replay
- High-resolution OHLC candlestick charting across multiple timeframes (**M1**, **M5**, **M15**, **M30**, **H1**, **H4**, **D1**).
- **Execution Overlays:** Visual markers for entry price, initial Stop Loss, Take Profit, trailing SL adjustment steps, and final exits.
- **Trade Replay Engine:** Step-by-step bar replay player with speed control (0.5x, 1x, 2x, 4x) to re-live execution dynamics.

### 📝 6. Live Trade Journal & Modification Tracking
- Real-time MT5 position polling that captures initial Stop-Loss and Take-Profit snapshots at the moment of order placement.
- Audit trail logging every mid-trade Stop-Loss and Take-Profit modification.

### 🔬 7. Quantitative Risk Research & Simulation
- **Monte Carlo Simulation:** 1,000+ iteration trade sequence reshuffling to discover worst-case drawdown distributions and 5th/50th/95th percentile equity curves.
- **Risk of Ruin Calculation:** Quantitative probability of experiencing 20%, 30%, or 50% drawdowns based on your empirical edge.
- **Rolling Metrics & Bootstrap Confidence Intervals:** Rolling 20/50/100-trade expectancy curves to measure edge degradation over time.

### 📄 8. Markdown & AI-Ready Reporting
- Export comprehensive audit dossiers ready for ChatGPT analysis with structured performance metrics, deviation breakdowns, and tailored diagnostic prompts.
- Built-in privacy controls: One-click account number and broker masking.

### 🔒 9. Security, Backups & Portability
- Passwords stored securely in the **Windows Credential Locker** using the Python `keyring` API (passwords are never logged or stored in plaintext).
- Automated SQLite database snapshot backups with one-click restore.

---

## 🚀 Quick Start

### Prerequisites
- **Windows 10 / 11** (64-bit)
- **Python 3.11+**
- **MetaTrader 5 Desktop Terminal** (optional for viewing existing datasets)

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/iovigi/TradeAudit.git
   cd TradeAudit
   ```

2. **Create and activate a virtual environment:**
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   pip install -e .[dev]
   ```

4. **Launch the application:**
   ```bash
   python -m tradeaudit
   ```

---

## 🧪 Running Tests

The test suite includes **150+ unit and integration tests** covering domain calculations, MT5 adapters, compliance rules, analytics, and UI components:

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v
```

---

## 📦 Building Windows Executable & Installer

### 1. Build Standalone Folder (`TradeAudit.exe`)
Packages TradeAudit using PyInstaller:
```powershell
.\scripts\build_exe.ps1
```
Output: `dist/TradeAudit/TradeAudit.exe`

### 2. Build Release Package & Setup Installer
Runs all automated tests, packages the PyInstaller distribution, creates a portable `.zip` archive, and compiles the Windows Setup installer via **Inno Setup**:
```powershell
.\scripts\build_installer.ps1
```
Output: `dist/installer/TradeAudit-Setup-v1.0.0.exe`

---

## 🏛️ Project Architecture

```text
src/tradeaudit/
├── app/                  # Application services (Analytics, Sync, Compliance, Quant, Charting)
├── domain/               # Domain entities (Trade, Strategy, Metrics, Candles, Enums)
├── infrastructure/       # MT5 adapters, SQLite repositories, Credential locker
└── ui/                   # PySide6 GUI views, dialogs, custom charts & widgets
```

For full architectural guidelines and developer references, see [CLAUDE.md](CLAUDE.md) and the [Phased Roadmap](plans/TradeAudit_Phased_Roadmap_EN.md).

---

## 📜 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
