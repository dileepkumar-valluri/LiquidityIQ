# LiquidityIQ — Short-Term Liquidity Forecasting & Scenario Analysis

LiquidityIQ is a Python-based liquidity forecasting and scenario analysis system. It models financial entities, generates seeded synthetic financial data, calculates daily cash positions, evaluates liquidity scenarios, validates data integrity, and compares forecasted cash flows with actual ledger activity.

## Key Features

- Relational data model covering nine core financial entities.
- Reproducible synthetic data generation using a fixed seed.
- BASE, DELAYED_RECEIPT, and STRESS liquidity scenarios.
- Foreign exchange rate lookup and reporting-currency conversion.
- Daily cash position calculations.
- Forecast-to-actual comparison.
- Dataset validation and CSV/JSON exports.
- Lifecycle status history.
- Ground-truth definitions and detection for five financial data-quality edge cases.

## Technology Stack

- Python
- PostgreSQL
- SQLAlchemy
- Pandas
- NumPy
- Pytest

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
│   │   ├── routes/
│   │   ├── services/
│   │   └── database.py
│   └── tests/
├── data/
│   ├── generated/
│   │   └── baseline/
│   └── ground_truth/
├── docs/
│   ├── database_schema.md
│   ├── data_dictionary.md
│   ├── SOURCE_MANIFEST.md
│   └── AI_PROMPT_HISTORY.md
├── scripts/
│   └── generate_data.py
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## Setup and Installation

### 1. Clone the repository

```powershell
git clone https://github.com/dileepkumar-valluri/LiquidityIQ.git
cd LiquidityIQ
```

### 2. Create and activate a virtual environment

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
pip install -r requirements.txt
```

### 4. Configure PostgreSQL

Install and start PostgreSQL. Create a database named `liquidityiq`.

Create a local `.env` file using `.env.example` as a reference.

Configure the connection:

```env
DATABASE_URL=postgresql+psycopg://USERNAME:PASSWORD@localhost:5432/liquidityiq
```

Do not commit `.env` or database credentials.

### 5. Create database tables

From the project root, run:

```powershell
python -c "from backend.app.database import Base, engine; import backend.app.models; Base.metadata.create_all(bind=engine); print('Database schema created.'); engine.dispose()"
```

### 6. Configure the Python module path

```powershell
$env:PYTHONPATH = (Get-Location).Path
```

## Synthetic Data Generation

The generator supports two dataset scales:

- `starter`: Smaller dataset for local development and automated tests.
- `baseline`: Challenge-scale synthetic dataset.

Generate the starter dataset:

```powershell
python scripts/generate_data.py --scale starter --seed 20261022
```

Generate the baseline dataset:

```powershell
python scripts/generate_data.py --scale baseline --seed 20261022
```

Run these commands against a freshly created database. Do not assume that running the generator repeatedly against an existing populated database is safe.

## Baseline Dataset

The baseline dataset was generated using seed `20261022`.

| Entity | Records |
|---|---:|
| LegalEntity | 30 |
| BankAccount | 150 |
| LedgerEntry | 100,000 |
| Receivable | 10,000 |
| Payable | 10,000 |
| CurrencyRate | 80 |
| LiquidityScenario | 3 |
| ForecastRun | 3 |
| CashFlowForecast | 60,000 |
| **Total** | **180,266** |

The baseline exports are available in:

```text
data/generated/baseline/
```

The directory contains table-level CSV and JSON exports, a combined JSON export, and a PostgreSQL SQL dump.

To restore the SQL dump into a separate, empty PostgreSQL database:

```powershell
psql -U postgres -d liquidityiq_baseline -f data/generated/baseline/liquidityiq_baseline.sql
```

Create the target database before running the restore command.

## Validation

Run dataset validation against the database configured in `.env`:

```powershell
python -m backend.app.services.validation
```

The baseline validation run reported:

- 33 checks passed.
- 0 validation failures.
- Primary-key uniqueness checks passed.
- Foreign-key integrity checks passed.
- Currency-rate availability and forecast-data checks passed.

The baseline validation also reported 56 bank accounts with negative calculated closing balances. These are liquidity warnings, not automatic validation failures.

## Data Export

Export database tables to CSV and JSON:

```powershell
python -m backend.app.services.export_data
```

The export service writes to:

```text
data/generated/
```

The committed baseline exports are preserved separately in `data/generated/baseline/`. Take care not to overwrite the starter exports when exporting from a different database scale.

## Edge-Case Validation

Ground-truth definitions and edge-case detection can be run with:

```powershell
python -m backend.app.services.edge_cases
```

The five documented edge cases cover:

1. Opening balance reconciliation mismatch.
2. Missing foreign exchange rate.
3. Duplicate cash flow.
4. Actual ledger entry after the forecast cutoff.
5. Mixed-currency mismatch without conversion.

## Forecast Scenarios

- **BASE:** Uses scheduled cash-flow dates and standard payable amounts.
- **DELAYED_RECEIPT:** Delays forecast receipts by seven days.
- **STRESS:** Delays forecast receipts by fourteen days and increases payable amounts by ten percent.

Daily cash positions use opening balances, posted ledger activity through the forecast cutoff, and forecast inflows and outflows.

## Automated Tests

Install the project dependencies and run:

```powershell
python -m pytest backend/tests -v
```

The automated test suite contains 36 tests covering:

- Actual-versus-forecast currency conversion.
- Daily liquidity forecasting.
- Dataset validation and relational integrity.
- Financial data-quality edge cases.
- Foreign exchange conversion.
- Receivable status lifecycle and history.

**Verified test result:** 36 passed in 2.37 seconds against the starter dataset.

The baseline dataset was separately validated with 33 checks passing and zero failures. The 36-test suite includes starter-scale count expectations and should not be interpreted as a baseline-scale test run.

## Implementation Notes and Limitations

- The project currently provides Python data models and forecasting, validation, and export services. A runnable web application entry point is not included.
- The documented ground-truth edge cases and their detection tests do not, by themselves, prove that every anomaly has been injected into the baseline input dataset.
- Daily cash positions are calculated by the forecasting service in memory.
- Forecast-to-actual comparison is aggregated by legal entity, date, and flow type.
- Negative closing balances are reported as liquidity warnings.
- Full end-to-end reproducibility across repeated baseline generation runs has not been independently verified.

## Project Status

This repository contains the individual technical challenge implementation, baseline synthetic dataset, documentation, validation logic, and automated tests. Verification results and known limitations are documented transparently.

## License

No license has been specified for this project.