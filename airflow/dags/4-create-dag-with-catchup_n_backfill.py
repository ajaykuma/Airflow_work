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
    start_date=datetime(2024,11,20),
    schedule_interval='0 0 * * mon,wed,fri',
    #catchup=True

) as dag:
    task1 = BashOperator(
        task_id = 'task1',
        bash_command = 'echo testing'
    )

task1

#testing backfill
#set catchup=False
#set start_date=datetime(2024,11,20)
#set schedule_interval='@daily'
#airflow dags list
#airflow dags backfill -s 2024-11-10 -e 2024-11-20 <dagid>


