# LiquidityIQ — Data Dictionary

## 1. LegalEntity

**Purpose:** Stores the master information of each legal entity (company or organisation) whose liquidity is being monitored.

**Primary Key:** `entity_id`

| Field | PostgreSQL Type | Required? | Allowed Values / Format | Units | Unique? | Validation |
|---|---|---|---|---|---|---|
| entity_id | VARCHAR(10) | Yes | `ENT-000001` | Identifier | Yes (PK) | Must follow the defined ID format and remain immutable |
| entity_name | VARCHAR(150) | Yes | Non-empty company or organisation name | Text | No | Must not contain only spaces |
| registration_number | VARCHAR(50) | No | Synthetic registration reference | Identifier | Yes, if provided | Must be unique when present |
| country | VARCHAR(100) | Yes | Country name | Text | No | Must not be empty |
| base_currency | CHAR(3) | Yes | Three-letter ISO currency code, such as USD, INR, EUR | Currency code | No | Must be a supported currency |
| status | VARCHAR(20) | Yes | ACTIVE, INACTIVE, SUSPENDED | State | No | Must match one of the allowed values |
| created_at | TIMESTAMPTZ | Yes | Timestamp | Date and time with time zone | No | Set when the record is created |
| updated_at | TIMESTAMPTZ | Yes | Timestamp | Date and time with time zone | No | Must be greater than or equal to created_at |

**Relationships:**
- One LegalEntity can have many BankAccounts.
- One LegalEntity can have many Receivables.
- One LegalEntity can have many Payables.

**Business Rules:**
1. Every LegalEntity must have a unique `entity_id`.
2. Every LegalEntity must have a valid three-letter base currency.
3. BankAccounts, Receivables and Payables must reference an existing LegalEntity.
4. Entity IDs must never change after creation.
5. Use synthetic company information for generated data.

## 2. BankAccount

**Purpose:** Stores bank account details belonging to a LegalEntity.

**Primary Key:** `bank_account_id`

**Foreign Key:** `entity_id` references `LegalEntity(entity_id)`.

| Field | PostgreSQL Type | Required? | Allowed Values / Format | Units | Unique? | Validation |
|---|---|---|---|---|---|---|
| bank_account_id | VARCHAR(30) | Yes | `BANKACC-ENT-000001-001` | Identifier | Yes (PK) | Must follow the defined ID format and remain immutable |
| entity_id | VARCHAR(10) | Yes | Existing LegalEntity ID | Identifier | No | Must reference an existing LegalEntity |
| bank_name | VARCHAR(100) | Yes | Bank name | Text | No | Must not be empty |
| account_reference | VARCHAR(50) | Yes | Synthetic account reference | Identifier | Yes | Must be unique |
| currency | CHAR(3) | Yes | Supported three-letter ISO currency code | Currency code | No | Must be a supported currency |
| opening_balance | NUMERIC(18,2) | Yes | Monetary amount | Account currency | No | Must be zero or positive |
| opening_balance_date | DATE | Yes | Valid calendar date | Date | No | Must not be a future date |
| account_status | VARCHAR(20) | Yes | ACTIVE, INACTIVE, CLOSED | State | No | Must match one of the allowed values |
| created_at | TIMESTAMPTZ | Yes | Timestamp | Date and time with time zone | No | Set when the record is created |
| updated_at | TIMESTAMPTZ | Yes | Timestamp | Date and time with time zone | No | Must be greater than or equal to created_at |

**Relationships:**
- One LegalEntity can have many BankAccounts.
- One BankAccount can have many LedgerEntries.
- One BankAccount can be associated with many CashFlowForecast items.

**Business Rules:**
1. Every BankAccount must belong to an existing LegalEntity.
2. Each bank account must have a unique account reference.
3. Opening balance must be stored in the account's own currency.
4. Opening balance and its date establish the starting point for balance reconciliation.
5. Use synthetic bank and account information in generated data.

## 3. LedgerEntry

**Purpose:** Stores individual financial transactions recorded in a bank account.

**Primary Key:** `ledger_entry_id`

**Foreign Key:** `bank_account_id` references `BankAccount(bank_account_id)`.

| Field | PostgreSQL Type | Required? | Allowed Values / Format | Units | Unique? | Validation |
|---|---|---|---|---|---|---|
| ledger_entry_id | VARCHAR(20) | Yes | `LED-2026-00000001` | Identifier | Yes (PK) | Must follow the defined ID format and remain immutable |
| bank_account_id | VARCHAR(30) | Yes | Existing BankAccount ID | Identifier | No | Must reference an existing BankAccount |
| transaction_date | DATE | Yes | Valid calendar date | Date | No | Must not be later than posting_date |
| posting_date | DATE | Yes | Valid calendar date | Date | No | Must not be earlier than transaction_date |
| transaction_type | VARCHAR(20) | Yes | INFLOW, OUTFLOW | Transaction category | No | Must match one of the allowed values |
| amount | NUMERIC(18,2) | Yes | Positive monetary amount | Account currency | No | Must be greater than zero |
| currency | CHAR(3) | Yes | Supported three-letter ISO currency code | Currency code | No | Must match the bank account currency |
| description | VARCHAR(255) | No | Transaction description | Text | No | Maximum 255 characters |
| created_at | TIMESTAMPTZ | Yes | Timestamp | Date and time with time zone | No | Set when the record is created |

**Relationships:**
- One BankAccount can have many LedgerEntries.
- Each LedgerEntry belongs to exactly one BankAccount.

**Business Rules:**
1. Every ledger entry must reference an existing BankAccount.
2. Store transaction amounts as positive values.
3. Use `transaction_type` to distinguish INFLOW and OUTFLOW.
4. Calculate the signed effect on balance as:
   - INFLOW: add the amount.
   - OUTFLOW: subtract the amount.
5. The transaction currency must match the associated bank account currency.
6. Ledger entries must be retained as historical records rather than silently overwritten.
7. Use deterministic IDs for reproducible data generation.

## 4. Receivable

**Purpose:** Stores amounts that a LegalEntity expects to receive from its customers.

**Primary Key:** `receivable_id`

**Foreign Key:** `entity_id` references `LegalEntity(entity_id)`.

| Field | PostgreSQL Type | Required? | Allowed Values / Format | Units | Unique? | Validation |
|---|---|---|---|---|---|---|
| receivable_id | VARCHAR(20) | Yes | `REC-2026-000001` | Identifier | Yes (PK) | Must follow the defined ID format and remain immutable |
| entity_id | VARCHAR(10) | Yes | Existing LegalEntity ID | Identifier | No | Must reference an existing LegalEntity |
| customer_reference | VARCHAR(50) | Yes | Synthetic customer reference | Identifier | No | Must not be empty |
| invoice_date | DATE | Yes | Valid calendar date | Date | No | Must not be in the future |
| due_date | DATE | Yes | Valid calendar date | Date | No | Must be on or after invoice_date |
| expected_amount | NUMERIC(18,2) | Yes | Positive monetary amount | Receivable currency | No | Must be greater than zero |
| currency | CHAR(3) | Yes | Supported three-letter ISO currency code | Currency code | No | Must be a supported currency |
| status | VARCHAR(20) | Yes | SCHEDULED, PARTIALLY_PAID, PAID, OVERDUE, CANCELLED | State | No | Must match one of the allowed values |
| created_at | TIMESTAMPTZ | Yes | Timestamp | Date and time with time zone | No | Set when the record is created |
| updated_at | TIMESTAMPTZ | Yes | Timestamp | Date and time with time zone | No | Must be greater than or equal to created_at |

**Relationships:**
- One LegalEntity can have many Receivables.
- A Receivable can be associated with CashFlowForecast items.

**Business Rules:**
1. Every Receivable must belong to an existing LegalEntity.
2. The expected amount must be positive.
3. The due date cannot be earlier than the invoice date.
4. Receivables represent expected incoming cash flows.
5. Delayed receipts must be represented through documented scenario assumptions, not by randomly changing the original invoice record.
6. Status changes must be traceable through event history.
7. Use synthetic customer references.

## 5. Payable

**Purpose:** Stores amounts that a LegalEntity is expected to pay to its suppliers or vendors.

**Primary Key:** `payable_id`

**Foreign Key:** `entity_id` references `LegalEntity(entity_id)`.

| Field | PostgreSQL Type | Required? | Allowed Values / Format | Units | Unique? | Validation |
|---|---|---|---|---|---|---|
| payable_id | VARCHAR(20) | Yes | `PAY-2026-000001` | Identifier | Yes (PK) | Must follow the defined ID format and remain immutable |
| entity_id | VARCHAR(10) | Yes | Existing LegalEntity ID | Identifier | No | Must reference an existing LegalEntity |
| vendor_reference | VARCHAR(50) | Yes | Synthetic vendor reference | Identifier | No | Must not be empty |
| invoice_date | DATE | Yes | Valid calendar date | Date | No | Must not be in the future |
| due_date | DATE | Yes | Valid calendar date | Date | No | Must be on or after invoice_date |
| expected_amount | NUMERIC(18,2) | Yes | Positive monetary amount | Payable currency | No | Must be greater than zero |
| currency | CHAR(3) | Yes | Supported three-letter ISO currency code | Currency code | No | Must be a supported currency |
| status | VARCHAR(20) | Yes | SCHEDULED, PARTIALLY_PAID, PAID, OVERDUE, CANCELLED | State | No | Must match one of the allowed values |
| created_at | TIMESTAMPTZ | Yes | Timestamp | Date and time with time zone | No | Set when the record is created |
| updated_at | TIMESTAMPTZ | Yes | Timestamp | Date and time with time zone | No | Must be greater than or equal to created_at |

**Relationships:**
- One LegalEntity can have many Payables.
- A Payable can be associated with CashFlowForecast items.

**Business Rules:**
1. Every Payable must belong to an existing LegalEntity.
2. The expected amount must be positive.
3. The due date cannot be earlier than the invoice date.
4. Payables represent expected outgoing cash flows.
5. Delayed payments and large one-off payments must be represented through documented scenario assumptions.
6. Status changes must be traceable through event history.
7. Use synthetic vendor references.

## 6. CurrencyRate

**Purpose:** Stores foreign exchange rates used to convert cash flows between currencies.

**Primary Key:** `currency_rate_id`

| Field | PostgreSQL Type | Required? | Allowed Values / Format | Units | Unique? | Validation |
|---|---|---|---|---|---|---|
| currency_rate_id | VARCHAR(20) | Yes | `FX-2026-000001` | Identifier | Yes (PK) | Must follow the defined ID format and remain immutable |
| base_currency | CHAR(3) | Yes | Supported ISO currency code | Currency code | No | Must be different from quote_currency |
| quote_currency | CHAR(3) | Yes | Supported ISO currency code | Currency code | No | Must be different from base_currency |
| exchange_rate | NUMERIC(18,8) | Yes | Positive exchange rate | Quote currency per 1 unit of base currency | No | Must be greater than zero |
| effective_date | DATE | Yes | Valid calendar date | Date | No | Must represent the date from which the rate applies |
| source | VARCHAR(100) | Yes | Synthetic or documented rate source | Text | No | Must not be empty |
| created_at | TIMESTAMPTZ | Yes | Timestamp | Date and time with time zone | No | Set when the record is created |

**Unique Constraint:**
- The combination of `base_currency`, `quote_currency`, and `effective_date` must be unique.

**Relationships:**
- One CurrencyRate can be referenced by many CashFlowForecast items.

**Business Rules:**
1. Exchange rates must always be positive.
2. Base and quote currencies must be different.
3. The rate represents how many units of the quote currency equal one unit of the base currency.
4. A forecast must use an applicable rate based on its effective date.
5. Missing exchange rates must be identified as exceptions rather than silently replaced with random values.
6. Historical exchange rates must be retained for reproducibility.
7. Use documented or synthetic exchange-rate data.

## 7. LiquidityScenario

**Purpose:** Stores different business scenarios and their assumptions for short-term liquidity forecasting.

**Primary Key:** `scenario_id`

| Field | PostgreSQL Type | Required? | Allowed Values / Format | Units | Unique? | Validation |
|---|---|---|---|---|---|---|
| scenario_id | VARCHAR(20) | Yes | `SCN-000001` | Identifier | Yes (PK) | Must follow the defined ID format and remain immutable |
| scenario_name | VARCHAR(100) | Yes | BASE, DELAYED_RECEIPT, STRESS | Text | Yes | Must be a supported scenario name |
| description | TEXT | Yes | Explanation of the scenario | Text | No | Must not be empty |
| scenario_type | VARCHAR(30) | Yes | BASELINE, DELAYED_RECEIPT, STRESS | Scenario category | No | Must match one of the allowed values |
| assumptions | JSONB | Yes | Structured scenario assumptions | JSON data | No | Must contain valid JSON |
| created_at | TIMESTAMPTZ | Yes | Timestamp | Date and time with time zone | No | Set when the scenario is created |

**Relationships:**
- One LiquidityScenario can have many ForecastRuns.
- Each ForecastRun belongs to exactly one LiquidityScenario.

**Business Rules:**
1. Every scenario must have a unique scenario ID and name.
2. The BASE scenario uses the original expected cash-flow dates and amounts.
3. The DELAYED_RECEIPT scenario applies documented delays to selected receivables.
4. The STRESS scenario applies documented adverse assumptions, such as delayed receipts and large one-off payments.
5. Scenario assumptions must be stored explicitly so forecast results can be reproduced.
6. Scenarios must not modify the original Receivable, Payable, or LedgerEntry records.

## 8. ForecastRun

**Purpose:** Stores each execution of a liquidity forecast, including its scenario, reporting currency and forecast cutoff.

**Primary Key:** `forecast_run_id`

**Foreign Key:** `scenario_id` references `LiquidityScenario(scenario_id)`.

| Field | PostgreSQL Type | Required? | Allowed Values / Format | Units | Unique? | Validation |
|---|---|---|---|---|---|---|
| forecast_run_id | VARCHAR(30) | Yes | `FCAST-2026-01-01-001` | Identifier | Yes (PK) | Must follow the defined ID format and remain immutable |
| scenario_id | VARCHAR(20) | Yes | Existing LiquidityScenario ID | Identifier | No | Must reference an existing scenario |
| run_date | DATE | Yes | Valid calendar date | Date | No | Must represent the forecast execution date |
| forecast_cutoff_date | DATE | Yes | Valid calendar date | Date | No | Must not be later than run_date |
| reporting_currency | CHAR(3) | Yes | Supported ISO currency code | Currency code | No | Must be a supported currency |
| run_status | VARCHAR(20) | Yes | PENDING, RUNNING, COMPLETED, FAILED | State | No | Must match one of the allowed values |
| random_seed | BIGINT | Yes | Fixed integer seed | Integer | No | Must be stored to support reproducibility |
| created_at | TIMESTAMPTZ | Yes | Timestamp | Date and time with time zone | No | Set when the forecast run is created |

**Relationships:**
- One LiquidityScenario can have many ForecastRuns.
- One ForecastRun can have many CashFlowForecast items.

**Business Rules:**
1. Every ForecastRun must reference an existing LiquidityScenario.
2. The forecast cutoff determines which actual financial records are available to the forecast.
3. Actual records posted after the cutoff must not be used as forecast inputs.
4. Each execution must have a unique forecast run ID.
5. Completed forecast runs must be retained rather than overwritten.
6. The scenario, reporting currency, cutoff date and random seed must be recorded to support reproducibility.
7. A failed run must be marked FAILED rather than presented as a completed forecast.    

## 9. CashFlowForecast

**Purpose:** Stores individual expected cash-flow items generated during a ForecastRun.

**Primary Key:** `forecast_item_id`

**Foreign Keys:**
- `forecast_run_id` references `ForecastRun(forecast_run_id)`.
- `bank_account_id` references `BankAccount(bank_account_id)`.
- `receivable_id` references `Receivable(receivable_id)`.
- `payable_id` references `Payable(payable_id)`.
- `currency_rate_id` references `CurrencyRate(currency_rate_id)`.

| Field | PostgreSQL Type | Required? | Allowed Values / Format | Units | Unique? | Validation |
|---|---|---|---|---|---|---|
| forecast_item_id | VARCHAR(20) | Yes | `CF-2026-000001` | Identifier | Yes (PK) | Must follow the defined ID format and remain immutable |
| forecast_run_id | VARCHAR(30) | Yes | Existing ForecastRun ID | Identifier | No | Must reference an existing ForecastRun |
| bank_account_id | VARCHAR(30) | No | Existing BankAccount ID | Identifier | No | Must reference an existing BankAccount when provided |
| receivable_id | VARCHAR(20) | No | Existing Receivable ID | Identifier | No | Must reference an existing Receivable when provided |
| payable_id | VARCHAR(20) | No | Existing Payable ID | Identifier | No | Must reference an existing Payable when provided |
| currency_rate_id | VARCHAR(20) | No | Existing CurrencyRate ID | Identifier | No | Must reference an existing CurrencyRate when required |
| expected_date | DATE | Yes | Valid calendar date | Date | No | Must be on or after the forecast cutoff date |
| amount | NUMERIC(18,2) | Yes | Positive monetary amount | Forecast item currency | No | Must be greater than zero |
| currency | CHAR(3) | Yes | Supported ISO currency code | Currency code | No | Must be a supported currency |
| flow_type | VARCHAR(20) | Yes | INFLOW, OUTFLOW | Cash-flow category | No | Must match one of the allowed values |
| forecast_status | VARCHAR(20) | Yes | EXPECTED, DELAYED, CANCELLED | State | No | Must match one of the allowed values |
| created_at | TIMESTAMPTZ | Yes | Timestamp | Date and time with time zone | No | Set when the forecast item is created |

**Relationships:**
- One ForecastRun can have many CashFlowForecast items.
- One BankAccount can be associated with many CashFlowForecast items.
- One Receivable can be associated with many CashFlowForecast items.
- One Payable can be associated with many CashFlowForecast items.
- One CurrencyRate can be referenced by many CashFlowForecast items.

**Business Rules:**
1. Every forecast item must belong to an existing ForecastRun.
2. A forecast item can reference a Receivable, a Payable, or neither when it represents an independent cash-flow assumption.
3. A forecast item must not reference both a Receivable and a Payable.
4. INFLOW represents expected incoming money; OUTFLOW represents expected outgoing money.
5. The amount must always be positive. The flow_type determines whether it is added to or subtracted from the cash position.
6. Currency conversion must use an applicable CurrencyRate when the item currency differs from the reporting currency.
7. Missing required exchange rates must be recorded as exceptions.
8. Forecast items must retain their original forecast run association and must not silently overwrite historical forecast results.
9. Forecast values must be derived from source records and documented scenario assumptions.

---

# 10. Entity Relationships and Constraints

## 10.1 Relationship Cardinality

| Parent Entity | Child Entity | Cardinality | Relationship | Optionality |
|---|---|---|---|---|
| LegalEntity | BankAccount | 1:N | One legal entity can own multiple bank accounts | BankAccount requires LegalEntity |
| LegalEntity | Receivable | 1:N | One legal entity can have multiple receivables | Receivable requires LegalEntity |
| LegalEntity | Payable | 1:N | One legal entity can have multiple payables | Payable requires LegalEntity |
| BankAccount | LedgerEntry | 1:N | One bank account can contain multiple ledger entries | LedgerEntry requires BankAccount |
| LiquidityScenario | ForecastRun | 1:N | One scenario can have multiple forecast runs | ForecastRun requires LiquidityScenario |
| ForecastRun | CashFlowForecast | 1:N | One forecast run can contain multiple forecast items | CashFlowForecast requires ForecastRun |
| BankAccount | CashFlowForecast | 1:N | One bank account can be associated with multiple forecast items | Bank account reference is optional |
| Receivable | CashFlowForecast | 1:N | One receivable can appear in multiple forecast runs | Receivable reference is optional |
| Payable | CashFlowForecast | 1:N | One payable can appear in multiple forecast runs | Payable reference is optional |
| CurrencyRate | CashFlowForecast | 1:N | One currency rate can be used by multiple forecast items | Currency rate reference is optional when conversion is not required |

## 10.2 One-to-One Relationships

No direct 1:1 relationships are defined among the nine core entities in the current data model.

## 10.3 Many-to-Many Relationships

The current core model does not define a direct N:M relationship requiring an additional bridge table.

CashFlowForecast provides the association between ForecastRun and its related cash-flow sources.

If an additional N:M relationship becomes necessary during implementation, it must be represented using a dedicated bridge table with appropriate foreign keys and uniqueness constraints.

## 10.4 Optional Relationships

The following CashFlowForecast references are optional:

- bank_account_id
- receivable_id
- payable_id
- currency_rate_id

A CashFlowForecast item can reference a Receivable, a Payable, or neither when it represents an independent cash-flow assumption.

It must not reference both a Receivable and a Payable at the same time.

A currency_rate_id is required only when currency conversion is necessary.

## 10.5 Effective Dates

| Entity | Date Fields | Purpose |
|---|---|---|
| BankAccount | opening_balance_date | Establishes the starting date for balance reconciliation |
| LedgerEntry | transaction_date, posting_date | Records when a transaction occurred and when it was posted |
| Receivable | invoice_date, due_date | Records invoice creation and expected receipt date |
| Payable | invoice_date, due_date | Records invoice creation and expected payment date |
| CurrencyRate | effective_date | Identifies when an exchange rate applies |
| ForecastRun | run_date, forecast_cutoff_date | Records forecast execution and actual-data cutoff |
| CashFlowForecast | expected_date | Records the expected cash-flow date |

All date relationships must be validated before records are accepted.

## 10.6 Lifecycle States

| Entity | Lifecycle States |
|---|---|
| LegalEntity | ACTIVE, INACTIVE, SUSPENDED |
| BankAccount | ACTIVE, INACTIVE, CLOSED |
| Receivable | SCHEDULED, PARTIALLY_PAID, PAID, OVERDUE, CANCELLED |
| Payable | SCHEDULED, PARTIALLY_PAID, PAID, OVERDUE, CANCELLED |
| LiquidityScenario | Defined by its scenario type and documented assumptions |
| ForecastRun | PENDING, RUNNING, COMPLETED, FAILED |
| CashFlowForecast | EXPECTED, DELAYED, CANCELLED |

Every lifecycle state must use an allowed value. State transitions must be validated and important changes must be retained as explicit historical events.

## 10.7 Foreign-Key and Join Integrity

1. Every foreign key must reference an existing parent record.
2. IDs must be consistent across all generated files and database tables.
3. Parent records must be generated before dependent child records.
4. Foreign-key joins must be validated after data generation.
5. Historical records must not be silently overwritten.
6. Deliberate anomaly cases must retain their issue_type and ground_truth labels without corrupting unrelated records.