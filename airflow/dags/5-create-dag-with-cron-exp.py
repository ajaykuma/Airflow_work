# refer Notes/Notes6-0.txt for more details
from airflow import DAG
from datetime import datetime, timedelta
from airflow.decorators import dag,task
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator

default_args = {
    'owner': 'hdu',
    'retries': 5,
    'retry_delay': timedelta(minutes=5)
}

with DAG(
    dag_id = 'dag_with_cron_v0',
    default_args=default_args,
    start_date=datetime(2024,1,26),
    schedule_interval='0 0 * * *'
    #schedule_interval='@daily'

) as dag:
    task1 = BashOperator(
        task_id = 'task1',
        bash_command= 'echo testing cron expression'
    )

task1



