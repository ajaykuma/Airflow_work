from airflow import DAG
from datetime import datetime, timedelta
from airflow.operators.python import PythonOperator


default_args = {
    'owner': 'hdu',
    'retries': 5,
    'retry_delay': timedelta(minutes=5)
}


def greet():
    print("Hello world")


with DAG(
    dag_id='sample_dag_with_python_operator_v0',
    description='Testing sample DAG with PythonOperator',
    default_args=default_args,
    start_date=datetime(2026, 9, 13, 2),
    schedule_interval='@daily'
) as dag:

    task1 = PythonOperator(
        task_id='greet',
        python_callable=greet
    )

    task1
