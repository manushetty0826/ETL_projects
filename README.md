# Banking Data ETL Pipeline

An end-to-end, local ETL pipeline for synthetic banking transactions. It demonstrates extraction from CSV, transformation and validation, and loading into CSV and SQLite outputs.

## Architecture

```text
Synthetic data generator
          |
          v
Raw CSV --> Extract --> Validate and transform --> Cleaned CSV
                                   |                 +-- Rejected CSV
                                   |                 +-- SQLite warehouse
                                   +--> data-quality JSON report
```

## Dataset

The project generates deterministic synthetic records only. It contains no real customer or banking data. Records include account type, channel, transaction type, amount, currency, date, merchant category, and a fraud flag.

## Setup

From the project root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Run

Generate the synthetic source data:

```bash
python generate_banking_data.py
```

Run the complete pipeline:

```bash
python etl_pipeline.py
```

Optional custom paths:

```bash
python etl_pipeline.py \
  --source data/raw/banking_transactions.csv \
  --output data/processed
```

## Outputs

After the run, inspect:

- `data/processed/cleaned_transactions.csv`
- `data/processed/rejected_transactions.csv`
- `data/processed/banking_warehouse.db`
- `data/processed/data_quality_report.json`

The SQLite database contains:

- `transactions`: validated transformed transactions
- `pipeline_summary`: aggregate pipeline statistics

## Test

```bash
python -m unittest discover -s tests -v
```
