# LiquidityIQ — Short-Term Liquidity Forecasting & Scenario Analysis

LiquidityIQ is a Python-based liquidity forecasting system designed to calculate daily cash positions, evaluate liquidity scenarios, and compare forecasted cash flows with actual ledger activity.

## Key Features

- Relational data model covering nine core financial entities.
- Seeded synthetic data generation.
- Base, delayed-receipt, and stress liquidity scenarios.
- FX rate lookup and reporting-currency conversion.
- Daily cash position calculations.
- Forecast-to-actual comparison.
- Dataset validation and CSV/JSON exports.
- Ground-truth definitions for five financial data-quality edge cases.

## Technology Stack

- Python
- SQLAlchemy
- PostgreSQL
- Pandas
- NumPy
- FastAPI dependencies included in the project environment

## Core Data Entities

1. LegalEntity
2. BankAccount
3. LedgerEntry
4. Receivable
5. Payable
6. CurrencyRate
7. LiquidityScenario
8. ForecastRun
9. CashFlowForecast

## Project Structure

```text
LiquidityIQ/
├── backend/
│   ├── app/
│   │   ├── models/
│   │   ├── services/
│   │   └── routes/
│   └── tests/
├── data/
│   ├── generated/
│   └── ground_truth/
├── docs/
|   ├── database_schema.md
│   ├── data_dictionary.md
│   └── AI_PROMPT_HISTORY.md
├── scripts/
├── .env.example
├── .gitignore
└── requirements.txt
```

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/dileepkumar-valluri/LiquidityIQ.git
cd LiquidityIQ
```

### 2. Create and activate a virtual environment

Windows PowerShell:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
pip install -r requirements.txt
```

### 4. Configure PostgreSQL

Create a PostgreSQL database named `liquidityiq`.

Configure the database connection in a local `.env` file:

```env
DATABASE_URL=postgresql+psycopg://USERNAME:PASSWORD@localhost:5432/liquidityiq
```

Do not commit `.env` or database credentials.

### 5. Configure the Python module path

```powershell
$env:PYTHONPATH = (Get-Location).Path
```

## Data Generation and Verification

The synthetic data generator supports starter and baseline configurations. The current verified local dataset uses the starter configuration and seed `20261022`.

Run validation:

```powershell
python -m backend.app.services.validation
```

Export database tables to CSV and JSON:

```powershell
python -m backend.app.services.export_data
```

Generated exports are written to:

```text
data/generated/
```

Ground-truth definitions for the documented edge cases are generated with:

```powershell
python -m backend.app.services.edge_cases
```

## Current Starter Dataset

| Entity | Records |
|---|---:|
| LegalEntity | 3 |
| BankAccount | 15 |
| LedgerEntry | 1,000 |
| Receivable | 200 |
| Payable | 200 |
| CurrencyRate | 80 |
| LiquidityScenario | 3 |
| ForecastRun | 3 |
| CashFlowForecast | 1,200 |
| **Total** | **2,504** |

The latest verified validation run reported **28 checks passed and 0 failures**.
Three bank accounts have negative calculated closing balances. These are reported as liquidity warnings, not validation failures.

## Forecast Scenarios

- **Base:** Uses the scheduled cash-flow dates.
- **Delayed Receipt:** Delays forecast receipts by seven days.
- **Stress:** Delays receipts by fourteen days and increases payable amounts by ten percent.

Daily cash positions are calculated using opening balances, ledger activity through the forecast cutoff, and forecast inflows and outflows.

## Important Implementation Notes and Limitations

- The current local dataset uses starter-scale volumes, not the full baseline target.
- The ground-truth file documents five expected edge-case decisions; this does not by itself mean all five anomalies have been injected into the generated input dataset.
- Daily cash positions are currently calculated by the forecasting service in memory.
- Forecast-to-actual comparison is currently aggregated by legal entity, date, and flow type. The current sample has no actual ledger postings after the forecast cutoff, so actual-versus-forecast variance behavior still needs further data-driven verification.
- Validation currently covers the checks implemented in the validation service; it should not be interpreted as proof that every challenge requirement is complete.

## Reproducibility

The synthetic data generator uses the fixed seed `20261022` and supports starter and baseline configurations.

The currently verified local dataset uses starter-scale volumes. Reproducibility across repeated runs and dataset scales has not yet been fully verified. Do not assume that running the generator repeatedly against an existing database is safe.

## Project Status

This is an individual technical challenge implementation. Features and verification status are documented transparently; remaining limitations are listed above.

## License

Add an appropriate license before distributing or reusing this project.
