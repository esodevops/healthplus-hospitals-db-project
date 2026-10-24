"""Functions for the HealthPlus ETL workflow."""
import os
import sys
from datetime import timedelta
from pathlib import Path
from dotenv import load_dotenv
import certifi
import pandas as pd
import pendulum
from airflow.sdk import DAG
from airflow.providers.smtp.notifications.smtp import send_smtp_notification
from airflow.providers.standard.operators.python import PythonOperator

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# Tasks run separately, so save their results for the next task to read.
STAGING_DIR = PROJECT_ROOT / "data" / "staging"


def ingestion():
    from src.ingestion import data_ingestion

    data = data_ingestion()
    raw_dir = STAGING_DIR / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    for name, table in data.items():
        table.to_csv(raw_dir / f"{name}.csv", index=False)


def transformation():
    from src.ingestion import data_ingestion
    from src.transform import transform_data
    from src.loading import save_cleaned_data

    data = data_ingestion(STAGING_DIR / "raw")
    cleaned_data = transform_data(data)
    save_cleaned_data(cleaned_data, STAGING_DIR / "cleaned")


def read_cleaned_data():
    """Read the CSV files written by the transformation task."""
    cleaned_dir = STAGING_DIR / "cleaned"
    # Keep phone numbers as text so leading zeros are preserved.
    patients = pd.read_csv(
        cleaned_dir / "patients_cleaned.csv", dtype={"phone_number": str}
    )
    appointments = pd.read_csv(cleaned_dir / "appointments_cleaned.csv")
    billing = pd.read_csv(cleaned_dir / "billing_cleaned.csv")
    doctors = pd.read_csv(cleaned_dir / "doctors_cleaned.csv")
    return {
        "patients": patients,
        "appointments": appointments,
        "billing": billing,
        "doctors": doctors,
    }


def quality():
    from src.quality import check_data_quality

    data = read_cleaned_data()
    check_data_quality(data)


def loading():
    from src.loading import loading_data, save_cleaned_data
    from src.quality import check_data_quality

    data = read_cleaned_data()
    check_data_quality(data)
    save_cleaned_data(data)
    return loading_data(data)

load_dotenv(PROJECT_ROOT / ".env")

os.environ.setdefault("SSL_CERT_FILE", certifi.where())
ALERT_EMAIL = os.getenv("AIRFLOW_ALERT_EMAIL")

dag_failure_notification = send_smtp_notification(
    smtp_conn_id="smtp_default",
    from_email=ALERT_EMAIL,
    to=ALERT_EMAIL,
    subject="[Airflow] DAG {{ dag.dag_id }} failed",
    html_content="""
        <p>DAG <strong>{{ dag.dag_id }}</strong> failed.</p>
        <p>Run: {{ run_id }}</p>
        <p>Failed task: {{ ti.task_id }}</p>
        <p><a href="{{ ti.log_url }}">View task logs</a></p>
    """,
)

def notify_failure(context):
    print("Starting failure email notification.", flush=True)
    dag_failure_notification(context)
    print("SMTP server accepted the failure email.", flush=True)

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=1),
    "on_failure_callback": notify_failure if ALERT_EMAIL else None,
}

with DAG(
    dag_id="healthplus_dag",
    default_args=default_args,
    description="healthplus batch ETL pipeline",
    start_date=pendulum.datetime(2026, 8, 16, tz="Europe/Helsinki"),
    schedule=None,  # Use None for manual execution
    catchup=False,
    tags=["healthplus", "etl"],
    max_active_runs=1,  # Runs share the same staging and output files.
) as dag:

    ingestion_task = PythonOperator(
        task_id="ingestion_layer",
        python_callable=ingestion,
        do_xcom_push=False,
    )

    transformation_task = PythonOperator(
        task_id="transformation_layer",
        python_callable=transformation,
        do_xcom_push=False,
    )

    quality_check_task = PythonOperator(
        task_id="quality_check_layer",
        python_callable=quality,
        do_xcom_push=False,
    )

    loading_task = PythonOperator(
        task_id="loading_layer",
        python_callable=loading,
        do_xcom_push=False,
    )

    ingestion_task >> transformation_task >> quality_check_task >> loading_task
