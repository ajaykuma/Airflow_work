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
    dag_id = 'dag_with_catchup_n_backfill_v1',
    default_args=default_args,
    start_date=datetime(2024,1,27),
    schedule_interval='@daily',
    catchup=False

) as dag:
    task1 = BashOperator(
        task_id = 'task1',
        bash_command= 'echo testing'
    )

task1
#testing backfill
#airflow dags list
#airflow dags backfill -s 2024-1-10 -e 2024-1-15 <dagid>


