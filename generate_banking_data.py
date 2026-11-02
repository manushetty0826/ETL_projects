import csv
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path


OUTPUT_FILE = Path(__file__).parent / "data" / "raw" / "banking_transactions.csv"
RANDOM_SEED = 42
ROW_COUNT = 2_000

ACCOUNT_TYPES = ["Checking", "Savings", "Credit", "Loan"]
CHANNELS = ["ATM", "Branch", "Mobile", "Online", "Wire"]
TRANSACTION_TYPES = ["Purchase", "Withdrawal", "Deposit", "Transfer", "Payment"]
MERCHANT_CATEGORIES = [
    "Groceries",
    "Utilities",
    "Travel",
    "Dining",
    "Retail",
    "Healthcare",
    "Salary",
    "Insurance",
    "Entertainment",
]
CURRENCIES = ["USD", "EUR", "GBP"]


def generate_data() -> None:
    random.seed(RANDOM_SEED)
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    start_date = datetime.now(timezone.utc) - timedelta(days=365)

    with OUTPUT_FILE.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(
            [
                "transaction_id",
                "customer_id",
                "account_type",
                "channel",
                "transaction_type",
                "amount",
                "currency",
                "transaction_date",
                "merchant_category",
                "is_fraud",
            ]
        )

        for index in range(ROW_COUNT):
            transaction_type = random.choice(TRANSACTION_TYPES)
            amount = round(random.uniform(5, 5_000), 2)
            if transaction_type == "Deposit" or transaction_type == "Salary":
                amount = round(random.uniform(500, 8_000), 2)

            transaction_date = start_date + timedelta(
                seconds=random.randint(0, 365 * 24 * 60 * 60)
            )
            is_fraud = 1 if random.random() < 0.035 else 0
            if is_fraud:
                amount = round(random.uniform(5_000, 25_000), 2)

            writer.writerow(
                [
                    f"TXN-{index + 1:06d}",
                    f"CUST-{random.randint(1, 300):04d}",
                    random.choice(ACCOUNT_TYPES),
                    random.choice(CHANNELS),
                    transaction_type,
                    amount,
                    random.choice(CURRENCIES),
                    transaction_date.isoformat(),
                    random.choice(MERCHANT_CATEGORIES),
                    is_fraud,
                ]
            )

        # Invalid records exercise the pipeline's data-quality and rejection logic.
        writer.writerow(
            [
                "TXN-BAD-001",
                "",
                "Checking",
                "Online",
                "Payment",
                -100,
                "USD",
                "not-a-date",
                "Utilities",
                0,
            ]
        )
        writer.writerow(
            [
                "TXN-BAD-002",
                "CUST-9999",
                "Unknown",
                "Mobile",
                "Transfer",
                "bad-value",
                "USD",
                datetime.now(timezone.utc).isoformat(),
                "Retail",
                0,
            ]
        )

    print(f"Generated {ROW_COUNT + 2} synthetic transactions at {OUTPUT_FILE}")


if __name__ == "__main__":
    generate_data()
