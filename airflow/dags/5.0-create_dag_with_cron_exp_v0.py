# refer Notes/Notes6-0.txt for more details
from airflow import DAG
from datetime import datetime, timedelta

from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator


default_args = {
    'owner': 'hdu',
    'retries': 5,
    'retry_delay': timedelta(minutes=5)
}


with DAG(
    dag_id='dag_with_cron_v0',
    default_args=default_args,
    start_date=datetime(2026, 9, 12),

    # Every day at midnight
    schedule='0 0 * * *',

    catchup=False
) as dag:

    task1 = BashOperator(
        task_id='show_date',
        bash_command='date'
    )

    task2 = BashOperator(
        task_id='show_message',
        bash_command='echo "Running my first cron-based Airflow DAG"'
    )

    task1 >> task2
