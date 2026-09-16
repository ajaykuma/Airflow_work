# refer Notes/Notes6-0.txt for more details
"""
--For catchup=True
unpause and check with > airflow dags list-runs -d dag_with_catchup_backfill
--For testing backfill
set catchup=False
set start_date=datetime(2026,9,1)
set schedule_interval='@daily'
airflow dags list
Trigger manually or cli > airflow dags trigger dag_with_catchup_backfill
airflow dags backfill -s 2026-09-01 -e 2026-09-10 <dagid>
"
"""

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
    dag_id = 'dag_with_catchup_backfill',
    default_args=default_args,
    start_date=datetime(2026,9,1),
    #schedule_interval='0 0 * * mon,wed,fri',
    schedule='0 0 * * 1,3,5',   # Mon, Wed, Fri at midnight
    catchup=True

) as dag:
    task1 = BashOperator(
        task_id = 'task1',
        bash_command = 'echo testing simple task'
    )

    task2 = BashOperator(
        task_id='task2',
        bash_command="""
        echo "Testing catchup/backfill"
        echo "Execution date: {{ logical_date }}"
        echo "Run ID: {{ run_id }}"
        echo "Data interval start: {{ data_interval_start }}"
        echo "Data interval end: {{ data_interval_end }}"
        """
    )

    task1 >> task2




