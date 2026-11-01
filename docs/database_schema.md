# LiquidityIQ — Database Schema Design

## 1. Project Overview

LiquidityIQ is a Short-Term Liquidity Forecasting and Scenario Analysis System.

The database consolidates legal entities, bank accounts, ledger transactions, receivables, payables, currency exchange rates, liquidity scenarios and forecast runs.

The database is designed to maintain referential integrity, financial traceability, historical records and reproducible forecasts.

## 2. Core Database Entities

The system contains the following nine core entities.

### 2.1 LegalEntity
- Primary Key: `entity_id`
- Purpose: Stores company legal entities.
- Important fields: entity_name, registration_number, base_currency, country, status.
- Relationship: One legal entity can have multiple bank accounts, receivables, payables and bank-account ledger entries through its accounts.

### 2.2 BankAccount
- Primary Key: `bank_account_id`
- Foreign Key: `entity_id` references LegalEntity.
- Purpose: Stores bank account information.
- Important fields: bank_name, account_reference, currency, opening_balance, account_status.
- Relationship: One legal entity can own multiple bank accounts. One bank account can have multiple ledger entries.

### 2.3 LedgerEntry
- Primary Key: `ledger_entry_id`
- Foreign Key: `bank_account_id` references BankAccount.
- Purpose: Stores actual financial transactions.
- Important fields: transaction_date, posting_date, transaction_type, amount, currency, description.
- Relationship: One bank account can have multiple ledger entries.

### 2.4 CashFlowForecast
- Primary Key: `forecast_item_id`
- Foreign Keys:
  - `forecast_run_id` references ForecastRun.
  - `bank_account_id` references BankAccount (optional).
  - `receivable_id` references Receivable (optional).
  - `payable_id` references Payable (optional).
  - `currency_rate_id` references CurrencyRate (optional).
- Purpose: Stores individual expected cash inflows and outflows.
- Important fields: expected_date, amount, currency, flow_type, forecast_status.
- Relationship: One forecast run can contain multiple forecast items. A forecast item may originate from a receivable, payable or an independently defined forecast.

### 2.5 Receivable
- Primary Key: `receivable_id`
- Foreign Key: `entity_id` references LegalEntity.
- Purpose: Stores expected incoming customer payments.
- Important fields: customer_reference, invoice_date, due_date, expected_amount, currency, status.
- Relationship: One legal entity can have multiple receivables.

### 2.6 Payable
- Primary Key: `payable_id`
- Foreign Key: `entity_id` references LegalEntity.
- Purpose: Stores expected outgoing payments.
- Important fields: vendor_reference, invoice_date, due_date, expected_amount, currency, status.
- Relationship: One legal entity can have multiple payables.

### 2.7 CurrencyRate
- Primary Key: `currency_rate_id`
- Purpose: Stores exchange rates between currency pairs.
- Important fields: base_currency, quote_currency, exchange_rate, effective_date, source.
- Relationship: A currency rate can be referenced by multiple forecast items when the same rate applies.

### 2.8 LiquidityScenario
- Primary Key: `scenario_id`
- Purpose: Stores the assumptions for liquidity scenarios.
- Important fields: scenario_name, description, scenario_type, assumptions, created_at.
- Required scenarios:
  - Base
  - Delayed Receipt
  - Stress
- Relationship: One scenario can have multiple forecast runs.

### 2.9 ForecastRun
- Primary Key: `forecast_run_id`
- Foreign Keys:
  - `scenario_id` references LiquidityScenario.
- Purpose: Stores individual forecast execution versions.
- Important fields: run_date, forecast_cutoff_date, reporting_currency, run_status, random_seed, created_at.
- Relationship: One scenario can have multiple forecast runs. One forecast run can contain multiple cash flow forecast items.

## 3. Relationship Cardinalities

| Parent Entity | Child Entity | Cardinality |
|---|---|---|
| LegalEntity | BankAccount | One-to-Many |
| BankAccount | LedgerEntry | One-to-Many |
| LegalEntity | Receivable | One-to-Many |
| LegalEntity | Payable | One-to-Many |
| LiquidityScenario | ForecastRun | One-to-Many |
| ForecastRun | CashFlowForecast | One-to-Many |
| BankAccount | CashFlowForecast | One-to-Many, optional |
| Receivable | CashFlowForecast | One-to-Many, optional |
| Payable | CashFlowForecast | One-to-Many, optional |
| CurrencyRate | CashFlowForecast | One-to-Many, optional |

## 4. Data Integrity Rules

1. Every entity must have a unique, immutable primary key.
2. Every foreign key must reference an existing parent record.
3. Amounts must be stored using appropriate fixed-precision decimal types.
4. Currency codes must use a consistent format.
5. Effective dates and transaction dates must be validated.
6. Forecast runs must preserve their original assumptions and cutoff dates.
7. Actual transactions must not leak into forecasts beyond the applicable cutoff.
8. Missing FX rates must be identified rather than silently assumed.
9. Duplicate cash flows must be detectable.
10. Historical state changes must be preserved as explicit records or events.
11. Ground-truth anomaly labels must be stored separately from input features.
12. Forecast totals and closing balances must be derived from source records.

## 5. Identifier Conventions

| Entity | Identifier Pattern |
|---|---|
| LegalEntity | ENT-000001 |
| BankAccount | BANKACC-ENT-000001-001 |
| LedgerEntry | LED-2026-00000001 |
| CashFlowForecast | CF-2026-000001 |
| ForecastRun | FCAST-2026-01-01-001 |

Identifiers must be deterministic, unique and immutable.

## 6. Financial Reconciliation

The basic cash balance calculation is:

Closing Balance = Opening Balance + Total Inflows - Total Outflows

All multi-currency calculations must use documented exchange-rate rules.

## 7. Forecast Scenarios

### Base
Uses expected receipts and scheduled payments.

### Delayed Receipt
Applies documented delays to selected incoming receivables.

### Stress
Applies documented adverse assumptions, including delayed collections, large payments and FX movements.

Scenario results must be reproducible and differ only according to documented assumptions.

## 8. Historical Traceability

Historical records must not be overwritten when a financial or forecast state changes.

State transitions must be recorded explicitly with relevant identifiers, timestamps and previous/new states.

## 9. Validation Requirements

- Primary-key uniqueness.
- Foreign-key integrity.
- Valid entity relationships.
- Valid currency codes.
- Date ordering.
- Financial reconciliation.
- Duplicate transaction detection.
- Forecast cutoff validation.
- Scenario reproducibility.
- Separation of input data and ground-truth labels.

## 10. Implementation Note

The database implementation must follow the official YottaFlex challenge requirements. Optional