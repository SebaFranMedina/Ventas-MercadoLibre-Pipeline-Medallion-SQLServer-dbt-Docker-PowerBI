# Design decisions

* **SQL Server instead of PostgreSQL**: chosen to broaden the portfolio (other projects already use PostgreSQL) and because Power BI integrates natively with it.
* **No Spark**: ~22k rows / two months of sales. Spark would add cost and complexity with no benefit; the design (medallion, dbt) scales if volume grows.
* **No orchestrator (yet)**: one script run by Docker Compose. Airflow would be a natural extension for scheduled monthly loads.
* **PII hashed at ingestion, not in SQL**: personal data never reaches the database. Needs a stable `PII_SECRET`; changing it changes every hash.
* **Silver rebuilt as a full table**: simple and safe at this volume; incremental models are the next step.
* **Text columns in bronze**: bronze mirrors the export; typing and cleaning is silver's job.
* **"Atypical addresses"**: defined by thresholds (`atypical_min_orders`, `atypical_min_returned_pct`, dbt vars). The repo does not claim the cause.
* **Zone "GBA"** is approximate (postal codes 1600-1999).
