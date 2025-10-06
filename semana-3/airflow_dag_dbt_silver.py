
from datetime import datetime, timedelta
import os
from airflow import DAG
from airflow.operators.bash import BashOperator

# Ajusta estas rutas a donde vive tu proyecto dbt
DBT_PROJECT_DIR = os.environ.get("DBT_PROJECT_DIR", "/opt/airflow/dags/dbt_project_root")
DBT_PROFILES_DIR = os.environ.get("DBT_PROFILES_DIR", "/opt/airflow/dags/dbt_project_root")

default_args = {
    "owner": "data-eng",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="dbt_silver_parallel",
    start_date=datetime(2025, 1, 1),
    schedule_interval="@daily",
    catchup=False,
    default_args=default_args,
    tags=["dbt", "silver", "databricks"],
) as dag:

    # Limpieza opcional
    dbt_clean = BashOperator(
        task_id="dbt_clean",
        bash_command="cd {{params.proj}} && dbt clean",
        params={"proj": DBT_PROJECT_DIR},
        env={"DBT_PROFILES_DIR": DBT_PROFILES_DIR, **os.environ},
    )

    # DEV
    dbt_run_dev = BashOperator(
        task_id="dbt_run_dev",
        bash_command="cd {{params.proj}} && dbt run --select tag:silver --target dev",
        params={"proj": DBT_PROJECT_DIR},
        env={"DBT_PROFILES_DIR": DBT_PROFILES_DIR, **os.environ},
    )

    dbt_test_dev = BashOperator(
        task_id="dbt_test_dev",
        bash_command="cd {{params.proj}} && dbt test --select tag:silver --target dev",
        params={"proj": DBT_PROJECT_DIR},
        env={"DBT_PROFILES_DIR": DBT_PROFILES_DIR, **os.environ},
    )

    # (Gate) Solo si DEV pasa pruebas, ejecuta PROD
    dbt_run_prod = BashOperator(
        task_id="dbt_run_prod",
        bash_command="cd {{params.proj}} && dbt run --select tag:silver --target prod",
        params={"proj": DBT_PROJECT_DIR},
        env={"DBT_PROFILES_DIR": DBT_PROFILES_DIR, **os.environ},
        trigger_rule="all_success",
    )

    dbt_test_prod = BashOperator(
        task_id="dbt_test_prod",
        bash_command="cd {{params.proj}} && dbt test --select tag:silver --target prod",
        params={"proj": DBT_PROJECT_DIR},
        env={"DBT_PROFILES_DIR": DBT_PROFILES_DIR, **os.environ},
    )

    dbt_clean >> dbt_run_dev >> dbt_test_dev >> dbt_run_prod >> dbt_test_prod
