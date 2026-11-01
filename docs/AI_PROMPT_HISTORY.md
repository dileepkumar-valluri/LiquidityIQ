# AI Prompt History - LiquidityIQ

## 1. Purpose

This document records the AI assistance used during
the development of LiquidityIQ for the YottaFlex AI
Associate - AI Forward Deployed Engineer challenge.

## 2. AI Tool Disclosure

- AI tool: ChatGPT
- Usage: Technical guidance, architecture discussion,
  Python implementation, debugging, SQLAlchemy,
  PostgreSQL, validation, forecasting, testing,
  and documentation.
- Candidate responsibility: All generated suggestions
  and code were reviewed, executed, and evaluated
  during local development.

## 3. Development Prompt Log

The following entries summarize the actual AI-assisted
development tasks. They are reconstructed task-level
descriptions, not verbatim copies of every original
conversation message.

### P01 - Database Architecture
Discuss the relational database design for the nine
required LiquidityIQ entities. Identify primary keys,
foreign keys, relationships, cardinality, and optionality.

### P02 - Project Setup
Guide the setup of the Python project, PostgreSQL
database, SQLAlchemy configuration, dependencies,
and directory structure.

### P03 - SQLAlchemy Models
Assist with implementing the nine core entity models,
including columns, data types, constraints, identifiers,
and relationships.

### P04 - Synthetic Master Data
Develop deterministic legal entity and bank account
generation using a fixed random seed and configurable
dataset sizes.

### P05 - Financial Transaction Data
Implement generation of ledger entries, receivables,
payables, currencies, and related financial records
while maintaining referential integrity.

### P06 - Forecast Scenarios
Design BASE, DELAYED_RECEIPT, and STRESS scenarios
using explicit assumptions and reproducible calculations.

### P07 - FX Conversion
Implement historical FX rate lookup, effective-date
selection, and reporting-currency conversion.

### P08 - Daily Liquidity Forecast
Calculate opening balances, inflows, outflows, and
daily closing balances from source financial records.

### P09 - Edge Cases and Ground Truth
Create labelled examples for opening balance mismatch,
missing FX rate, duplicate cash flow, actual after cutoff,
and mixed-currency aggregation.

### P10 - Forecast-to-Actual Comparison
Implement actual-versus-forecast aggregation, currency
conversion, variance calculation, and comparison statuses.

### P11 - Validation
Develop checks for primary keys, foreign keys,
financial amounts, dates, currency consistency,
forecast cutoffs, and duplicate source forecasts.

### P12 - Lifecycle History
Implement explicit status transition validation and
supporting status history records.

### P13 - Debugging and Verification
Use execution outputs and error messages to investigate
implementation issues and verify corrections.

### P14 - Documentation and Submission
Prepare project documentation, data dictionary,
schema documentation, source manifest, README,
CSV/JSON exports, and PostgreSQL SQL seed export.

## 4. Verification Performed

The candidate performed local verification, including:

- Starter dataset generation.
- Primary-key uniqueness checks.
- Ten foreign-key integrity checks.
- Ledger and bank account currency consistency.
- FX rate availability.
- Forecast cutoff validation.
- Forecast flow direction checks.
- Duplicate source forecast checks.
- Edge-case detection for five required cases.
- Daily cash position calculations.
- Lifecycle transition testing.
- PostgreSQL SQL export inspection.

Latest recorded dataset validation:
33 checks passed, 0 failed.

## 5. Limitations and Transparency

This file is a reconstructed development log, not a
verbatim transcript of all prompts submitted to AI tools.

The complete historical conversation export was not
preserved in the repository. Therefore, the entries
above summarize the AI-assisted tasks based on the
available development history.

AI responses were not archived in full.

## 6. Candidate Responsibility

The candidate is responsible for understanding,
reviewing, testing, and explaining the submitted
implementation.

AI assistance was used as a development aid.
The candidate performed local execution and verification
and remains responsible for the final submission.