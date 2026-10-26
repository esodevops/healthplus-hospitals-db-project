# Run the HealthPlus Airflow pipeline with Docker

This local learning setup uses your existing `dags/healthplus_etl.py` and
`src/` Python modules. You do not need to install Python or PostgreSQL on your
computer. Docker runs both for you.

Airflow runs its components together using `airflow standalone`, with its own
SQLite metadata database in a Docker volume. A separate PostgreSQL container
stores the hospital tables. This setup is for local development, not production.

## 1. Start Docker Desktop

Install Docker Desktop if needed, open it, and wait until Docker is running.
Give Docker at least 4 GB of memory (8 GB is preferable).

Open a terminal and check:

```bash
docker --version
docker compose version
docker info
```

## 2. Open your project

```bash
cd /Users/sulaimon/Desktop/AMDARI-Data-Engineering/healthplus-hospitals-db-project
ls data/raw_data
```

Confirm the folder contains `patients.csv`, `doctors.csv`, `appointments.csv`,
and `billing.csv`.

## 3. Understand the added files

- `Dockerfile` starts with Airflow 3.3.0 and installs the pipeline dependencies
  using the image's tested constraints. Notebook dependencies are unnecessary here.
- `compose.yaml` defines Airflow, PostgreSQL, shared project folders, and storage.
- `.dockerignore` excludes local credentials and unnecessary files from builds.

Docker supplies database settings directly. Your existing `.env` is not mounted
or changed. Inside Docker, `DB_HOST=postgres` refers to the Compose service.
The sample database credentials in Compose are for this local exercise.
PostgreSQL is only accessible inside the Docker network.

## 4. Check the configuration and build

```bash
docker compose config --quiet
docker compose build
```

The first build downloads Airflow and Python packages, so it may take several
minutes. Fix any build error before continuing.

## 5. Start the containers

```bash
docker compose up -d
docker compose ps
docker compose logs -f airflow
```

Wait for Airflow to finish starting. Press `Ctrl+C` to stop watching logs;
the containers continue running. `standalone` initializes Airflow automatically,
so no separate database migration or user-creation command is needed.

## 6. Log in to Airflow

Read the generated password:

```bash
docker compose exec airflow cat /opt/airflow/simple_auth_manager_passwords.json.generated
```

Open [Airflow](http://localhost:8080). Use username `admin` and the password
shown next to `admin` in the command output. If the file does not exist yet,
check the startup logs and wait for initialization to finish.

## 7. Check and run your DAG

```bash
docker compose exec airflow airflow dags list-import-errors
docker compose exec airflow airflow dags list
docker compose exec airflow airflow dags unpause healthplus_dag
docker compose exec airflow airflow dags trigger healthplus_dag
```

The import-error command should report no errors. In the UI, open
`healthplus_dag` and select the new run. Tasks execute in this order:

```text
ingestion_layer -> transformation_layer -> quality_check_layer -> loading_layer
```

Ingestion reads the four source CSV files and writes `data/staging/raw/`.
Transformation writes cleaned CSV files to `data/staging/cleaned/`. Quality
checks validate IDs, ages, and billing amounts. Loading saves final CSV files
to `data/cleaned_data/` and loads four PostgreSQL tables.

All four tasks should turn green. Click a task and open its logs if it fails.
The DAG is manual (`schedule=None`), so it will not run daily automatically.
It allows one active run because tasks share staging files.

## 8. Verify the output

```bash
ls data/cleaned_data
docker compose exec postgres psql -U healthplus -d healthplus_db -c "SELECT 'patients' AS table_name, COUNT(*) FROM patients UNION ALL SELECT 'doctors', COUNT(*) FROM doctors UNION ALL SELECT 'appointments', COUNT(*) FROM appointments UNION ALL SELECT 'billing', COUNT(*) FROM billing;"
```

Expect four cleaned CSV files and four database row counts. The existing load
uses `if_exists="replace"`: each successful rerun replaces these hospital tables.

## 9. Run again, stop, and restart

Run again:

```bash
docker compose exec airflow airflow dags trigger healthplus_dag
```

Stop:

```bash
docker compose down
```

Start again:

```bash
docker compose up -d
```

Named volumes preserve the hospital database, Airflow metadata, logs, and login
password after `down`. The CSV outputs remain in your project. Avoid adding
`--volumes` to `down` unless you intend to delete the stored databases.

Changes to `src/` and `dags/` are mounted directly into the running container.
After changing dependencies in the Dockerfile, rebuild and restart:

```bash
docker compose up -d --build
```

## Troubleshooting

- Cannot connect to Docker: open Docker Desktop and run `docker info` again.
- Port 8080 is occupied: change the Compose port to `127.0.0.1:8081:8080`,
  run `docker compose up -d`, and open `http://localhost:8081`.
- DAG missing: inspect `airflow dags list-import-errors` and the Airflow logs.
- Task fails: inspect its UI logs; confirm the raw files exist and PostgreSQL
  is healthy with `docker compose ps`.
- Linux file permission error: ensure container user UID 50000 can write to
  `data/`; use targeted folder permissions rather than `chmod 777`.
- Email alerts: disabled by default because no alert email is supplied. To use
  the existing callback, configure `AIRFLOW_ALERT_EMAIL` in Compose and an
  Airflow SMTP connection named `smtp_default`, then recreate Airflow.

## Official references

- [Airflow standalone quick start](https://airflow.apache.org/docs/apache-airflow/stable/start.html)
- [Extending the Airflow Docker image](https://airflow.apache.org/docs/docker-stack/build.html)
