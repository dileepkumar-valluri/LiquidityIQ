
import json
from pathlib import Path
from datetime import date, datetime
from decimal import Decimal

import pandas as pd

from backend.app.database import SessionLocal
from backend.app.models import (
    LegalEntity,
    BankAccount,
    LedgerEntry,
    Receivable,
    Payable,
    CurrencyRate,
    LiquidityScenario,
    ForecastRun,
    CashFlowForecast,
)


MODELS = [
    LegalEntity,
    BankAccount,
    LedgerEntry,
    Receivable,
    Payable,
    CurrencyRate,
    LiquidityScenario,
    ForecastRun,
    CashFlowForecast,
]


def serialize_value(value):
    if isinstance(value, (date, datetime)):
        return value.isoformat()

    if isinstance(value, Decimal):
        return str(value)

    return value


def export_dataset():
    output_dir = Path("data/generated")
    output_dir.mkdir(parents=True, exist_ok=True)

    session = SessionLocal()

    try:
        all_data = {}

        for model in MODELS:
            records = session.query(model).all()

            rows = [
                {
                    column.name: serialize_value(
                        getattr(record, column.name)
                    )
                    for column in model.__table__.columns
                }
                for record in records
            ]

            all_data[model.__tablename__] = rows

            csv_path = output_dir / f"{model.__tablename__}.csv"
            json_path = output_dir / f"{model.__tablename__}.json"

            pd.DataFrame(rows).to_csv(csv_path, index=False)

            with open(json_path, "w", encoding="utf-8") as file:
                json.dump(rows, file, indent=4, default=str)

            print(
                f"{model.__tablename__}: {len(rows)} records exported"
            )

        combined_path = output_dir / "liquidityiq_dataset.json"

        with open(combined_path, "w", encoding="utf-8") as file:
            json.dump(all_data, file, indent=4, default=str)

        print("\nDataset export completed!")
        print("Output directory:", output_dir.resolve())

    finally:
        session.close()


if __name__ == "__main__":
    export_dataset()
