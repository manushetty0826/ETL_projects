import argparse
import json
import sqlite3
from pathlib import Path

import pandas as pd


VALID_ACCOUNT_TYPES = {"Checking", "Savings", "Credit", "Loan"}
VALID_CHANNELS = {"ATM", "Branch", "Mobile", "Online", "Wire"}
VALID_TRANSACTION_TYPES = {
    "Purchase",
    "Withdrawal",
    "Deposit",
    "Transfer",
    "Payment",
    "Salary",
}


def extract(source: Path) -> pd.DataFrame:
    if not source.exists():
        raise FileNotFoundError(f"Source file not found: {source}")
    return pd.read_csv(source)


def transform(raw: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    cleaned = raw.copy()
    cleaned.columns = [column.strip().lower() for column in cleaned.columns]

    cleaned["transaction_date"] = pd.to_datetime(
        cleaned["transaction_date"], errors="coerce", utc=True
    )
    cleaned["amount"] = pd.to_numeric(cleaned["amount"], errors="coerce")
    cleaned["is_fraud"] = pd.to_numeric(cleaned["is_fraud"], errors="coerce").fillna(0)
    cleaned["is_fraud"] = cleaned["is_fraud"].astype("int64")

    for column in cleaned.select_dtypes(include=["object", "string"]):
        cleaned[column] = cleaned[column].astype("string").str.strip()

    valid_mask = (
        cleaned["transaction_id"].notna()
        & cleaned["customer_id"].notna()
        & cleaned["account_type"].isin(VALID_ACCOUNT_TYPES)
        & cleaned["channel"].isin(VALID_CHANNELS)
        & cleaned["transaction_type"].isin(VALID_TRANSACTION_TYPES)
        & cleaned["amount"].notna()
        & (cleaned["amount"] >= 0)
        & cleaned["currency"].notna()
        & cleaned["transaction_date"].notna()
        & cleaned["merchant_category"].notna()
        & cleaned["is_fraud"].isin([0, 1])
    )

    valid = cleaned.loc[valid_mask].copy()
    rejected = cleaned.loc[~valid_mask].copy()

    valid["currency"] = valid["currency"].str.upper()
    valid["transaction_date"] = valid["transaction_date"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    valid["amount_band"] = pd.cut(
        valid["amount"],
        bins=[-0.01, 100, 1_000, 5_000, float("inf")],
        labels=["Micro", "Small", "Medium", "Large"],
    )
    valid = valid.drop_duplicates(subset=["transaction_id"], keep="first")

    return valid, rejected


def load(
    cleaned: pd.DataFrame,
    rejected: pd.DataFrame,
    output_dir: Path,
) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    cleaned_path = output_dir / "cleaned_transactions.csv"
    rejected_path = output_dir / "rejected_transactions.csv"
    database_path = output_dir / "banking_warehouse.db"

    cleaned.to_csv(cleaned_path, index=False)
    rejected.to_csv(rejected_path, index=False)

    with sqlite3.connect(database_path) as connection:
        cleaned.to_sql("transactions", connection, if_exists="replace", index=False)
        summary = pd.DataFrame(
            [
                {
                    "total_transactions": len(cleaned),
                    "rejected_transactions": len(rejected),
                    "fraud_transactions": int(cleaned["is_fraud"].sum()),
                    "total_amount": float(cleaned["amount"].sum()),
                }
            ]
        )
        summary.to_sql("pipeline_summary", connection, if_exists="replace", index=False)

    report = {
        "input_records": len(cleaned) + len(rejected),
        "valid_records": len(cleaned),
        "rejected_records": len(rejected),
        "fraud_records": int(cleaned["is_fraud"].sum()),
        "total_amount": round(float(cleaned["amount"].sum()), 2),
        "outputs": {
            "cleaned_csv": str(cleaned_path),
            "rejected_csv": str(rejected_path),
            "sqlite_database": str(database_path),
        },
    }
    report_path = output_dir / "data_quality_report.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    report["report"] = str(report_path)
    return report


def run(source: Path, output_dir: Path) -> dict:
    raw = extract(source)
    cleaned, rejected = transform(raw)
    return load(cleaned, rejected, output_dir)


def main() -> None:
    project_dir = Path(__file__).parent
    parser = argparse.ArgumentParser(description="Synthetic banking data ETL pipeline")
    parser.add_argument(
        "--source",
        type=Path,
        default=project_dir / "data" / "raw" / "banking_transactions.csv",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=project_dir / "data" / "processed",
    )
    args = parser.parse_args()

    report = run(args.source, args.output)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
