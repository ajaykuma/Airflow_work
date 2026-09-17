# refer Notes/Notes12.txt for more details
from datetime import datetime,timedelta
import time
from airflow import DAG
from airflow.operators.dummy import DummyOperator
from airflow.operators.python import PythonOperator

def my_custom_func(ts,**kwargs):
        print("task is sleeping")
        time.sleep(40)

default_args = {
        'owner': 'hdu',
        'depends_on_past': False,
        'email_on_failure': True,
        'email': 'xxxx',
        'email_on_retry': False,
        'retries': 1,
        'retry_delay': timedelta(minutes=5),
        'execution_timeout': timedelta(seconds=45),
        'sla': timedelta(seconds=30)}

with DAG('sample_dag_sla_v0',
        start_date=datetime(2026,9,15),
        default_args=default_args,
        max_active_runs = 1,
        schedule=timedelta(minutes=2),
        catchup=False
        ) as dag:

        t0 = DummyOperator(
        task_id='start',
        sla=timedelta(seconds=50)

    )

        t1 = DummyOperator(
        task_id='end',
        sla=timedelta(seconds=500)

    )

        sla_task = PythonOperator(
        task_id='sla_task',
        python_callable=my_custom_func,
        sla=timedelta(seconds=35),
        execution_timeout = timedelta(seconds=37)

    )

t0 >> sla_task >> t1
