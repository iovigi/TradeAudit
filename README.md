# TradeAudit

TradeAudit is a desktop application for MetaTrader 5 (MT5) trade auditing, risk management, performance metrics, and behavioral analysis.

## Features

- **MT5 Integration**: Secure connection to MT5 terminal and account synchronization.
- **Risk & R-Multiple Engine**: Automatic risk calculations, planned R:R, and realized R.
- **Core Performance Analytics**: Win rate, expectancy, drawdown, profit factor, losing streak tracking.
- **Strategy & Compliance**: Rule engine to verify strategy adherence vs deviations.
- **Behavioral Analysis**: Detection of emotional trading (revenge trading, FOMO, overtrading).

## Installation & Setup

1. **Clone repository**:
   ```bash
   git clone https://github.com/your-org/TradeAudit.git
   cd TradeAudit
   ```

2. **Create & activate virtual environment**:
   ```bash
   python -m venv .venv
   # Windows PowerShell:
   .venv\Scripts\Activate.ps1
   # Linux/macOS:
   source .venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   # Or install editable package:
   pip install -e .[dev]
   ```

## Running the Application

Launch TradeAudit with Python module entry point:
```bash
python -m tradeaudit
```
Or via script:
```bash
tradeaudit
```

## Running Tests

Run unit test suite using `pytest`:
```bash
pytest
```
