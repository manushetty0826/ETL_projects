import tempfile
import unittest
from pathlib import Path

import pandas as pd

from etl_pipeline import extract, load, run, transform


class BankingPipelineTests(unittest.TestCase):
    def setUp(self):
        self.raw = pd.DataFrame(
            [
                {
                    "transaction_id": "TXN-001",
                    "customer_id": "CUST-001",
                    "account_type": "Checking",
                    "channel": "Mobile",
                    "transaction_type": "Payment",
                    "amount": "125.50",
                    "currency": "usd",
                    "transaction_date": "2026-01-01T10:00:00Z",
                    "merchant_category": "Utilities",
                    "is_fraud": 0,
                },
                {
                    "transaction_id": "TXN-002",
                    "customer_id": "",
                    "account_type": "Unknown",
                    "channel": "Online",
                    "transaction_type": "Purchase",
                    "amount": -20,
                    "currency": "USD",
                    "transaction_date": "bad-date",
                    "merchant_category": "Retail",
                    "is_fraud": 0,
                },
            ]
        )

    def test_transform_separates_valid_and_rejected_records(self):
        cleaned, rejected = transform(self.raw)

        self.assertEqual(len(cleaned), 1)
        self.assertEqual(len(rejected), 1)
        self.assertEqual(cleaned.iloc[0]["transaction_id"], "TXN-001")
        self.assertEqual(cleaned.iloc[0]["amount"], 125.50)

    def test_load_writes_csv_sqlite_and_report(self):
        cleaned, rejected = transform(self.raw)
        with tempfile.TemporaryDirectory() as directory:
            report = load(cleaned, rejected, Path(directory))
            self.assertEqual(report["valid_records"], 1)
            self.assertEqual(report["rejected_records"], 1)
            self.assertTrue(Path(report["outputs"]["cleaned_csv"]).exists())
            self.assertTrue(Path(report["outputs"]["sqlite_database"]).exists())
            self.assertTrue(Path(report["report"]).exists())

    def test_run_rejects_missing_source(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(FileNotFoundError):
                run(Path(directory) / "missing.csv", Path(directory) / "output")


if __name__ == "__main__":
    unittest.main()
