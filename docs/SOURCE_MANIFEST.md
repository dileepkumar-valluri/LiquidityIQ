# LiquidityIQ — Source Manifest

## 1. Data Sources

| Source | Data Used | Source Type |
|---|---|---|
| Synthetic data generator (`scripts/generate_data.py`) | Legal entities, bank accounts, ledger entries, receivables, payables, FX rates, scenarios, forecast runs and cash-flow forecasts | Generated synthetic data |
| Fixed random seed (`20261022`) | Supports repeatable generation within the implemented generator configuration | Generator configuration |
| `backend/app/models/` | Entity structures, fields, primary keys, foreign keys and constraints | Project implementation |
| `backend/app/services/forecasting.py` | Daily cash positions, FX conversion and scenario calculations | Project implementation |
| `backend/app/services/actual_vs_forecast.py` | Forecast-to-actual comparison logic | Project implementation |
| `backend/app/services/edge_cases.py` | Five labelled financial data-quality edge cases and ground-truth records | Synthetic test fixtures |
| `backend/app/services/validation.py` | Dataset integrity and business-rule validation | Project implementation |

## 2. External Data

The current starter dataset is synthetic. No confidential company financial records or real customer banking records are included.

The generated exchange rates are synthetic and must not be treated as live market rates.

## 3. Synthetic Data Configuration

- Random seed: `20261022`
- Current verified scale: Starter
- Legal entities: 3
- Bank accounts: 15
- Ledger entries: 1,000
- Receivables: 200
- Payables: 200
- Currency rates: 80
- Forecast scenarios: 3
- Forecast runs: 3
- Cash-flow forecast records: 1,200

## 4. Edge-Case Fixtures

Five labelled edge-case types are maintained separately from the main generated input dataset:

1. Opening balance reconciliation mismatch.
2. Missing foreign-exchange rate.
3. Duplicate cash flow.
4. Actual transaction posted after forecast cutoff.
5. Currency aggregation without conversion.

These fixtures are used to verify detection decisions and are not evidence that anomalies have been injected into the production starter dataset.

## 5. Limitations

- Synthetic exchange rates do not represent actual market prices.
- The full baseline dataset has not been verified.
- Reproducibility across repeated runs and scales has not been fully verified.
- Edge-case fixtures are separate from the main dataset.
