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

## Building Windows Executable and Installer

### 1. Build Standalone Executable
To package TradeAudit into a standalone Windows folder build (`dist/TradeAudit/TradeAudit.exe`):
```powershell
.\scripts\build_exe.ps1
```

### 2. Build Release Package and Setup Installer
To run tests, build the PyInstaller executable, create a portable `.zip` archive, and compile the Windows Setup installer (`TradeAudit-Setup-vX.X.X.exe` via Inno Setup):
```powershell
.\scripts\build_installer.ps1
```
or run `scripts\build_installer.bat`.

