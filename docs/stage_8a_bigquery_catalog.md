# Stage 8A BigQuery Catalog

Stage 8A creates the BigQuery catalog foundation only. It does not create Vertex
AI embeddings, BigQuery Vector Search indexes, or production retrieval paths.

## Prerequisites

- A Google Cloud project with BigQuery enabled.
- Local Application Default Credentials or another credential source supported by
  `google-cloud-bigquery`.
- IAM permissions to create BigQuery datasets and tables in the target project.
- Python dependencies installed from `requirements.txt`.

## Environment

Set these variables before running the script:

```powershell
$env:GCP_PROJECT_ID = "your-project-id"
$env:BIGQUERY_DATASET = "payback_catalog"
$env:BIGQUERY_PRODUCTS_TABLE = "products"
$env:BIGQUERY_LOCATION = "europe-west1"
```

Do not commit real project-specific secrets or service account material.

## Validate Dataset And Table Setup

Use dry-run mode to validate environment variables and the checked-in schema
without making GCP calls:

```powershell
.\.venv312\Scripts\python.exe scripts\gcp\create_bigquery_catalog.py --dry-run
```

## Create Dataset And Table

Run the script without `--dry-run` to create the dataset and table if missing:

```powershell
.\.venv312\Scripts\python.exe scripts\gcp\create_bigquery_catalog.py
```

The script is idempotent. If the dataset or table already exists, it prints
`already exists` and exits successfully.

By default it uses:

```text
infra/gcp/bigquery_products_schema.json
```

To validate or create from a different schema file:

```powershell
.\.venv312\Scripts\python.exe scripts\gcp\create_bigquery_catalog.py --schema-path path\to\schema.json --dry-run
```

## Validate Catalog Load

Use dry-run mode to read the local synthetic catalog, validate the products,
transform them into the BigQuery table shape, and print sample rows without
making GCP calls:

```powershell
.\.venv312\Scripts\python.exe scripts\gcp\load_catalog_to_bigquery.py --dry-run
```

The loader defaults to the configured local catalog path:

```text
app/data/products.json
```

You can point it at another compatible JSON catalog file:

```powershell
.\.venv312\Scripts\python.exe scripts\gcp\load_catalog_to_bigquery.py --catalog-path path\to\products.json --dry-run
```

## Load Catalog Rows

By default the loader uses safe append mode:

```powershell
.\.venv312\Scripts\python.exe scripts\gcp\load_catalog_to_bigquery.py
```

To replace the current table contents, pass `--mode replace`. This uses a
truncate load job and should be run only when replacing the catalog snapshot is
intended:

```powershell
.\.venv312\Scripts\python.exe scripts\gcp\load_catalog_to_bigquery.py --mode replace
```

The loader builds `embedding_text` for future Stage 8B work, but it does not
call Vertex AI, generate embeddings, or create BigQuery Vector Search indexes.

## Verify Loaded Catalog

Use SQL-only mode to print the verification queries without making GCP calls:

```powershell
.\.venv312\Scripts\python.exe scripts\gcp\verify_bigquery_catalog.py --sql-only
```

Run verification against BigQuery after creating the table and loading rows:

```powershell
.\.venv312\Scripts\python.exe scripts\gcp\verify_bigquery_catalog.py
```

The verifier prints:

- total product count,
- count by partner,
- five sample rows,
- count of rows missing `embedding_text`.

It fails clearly if the table does not exist or if the table is empty. The
output is intended to be copied into demo notes, `docs/demo_results.md`, or a
performance report.
