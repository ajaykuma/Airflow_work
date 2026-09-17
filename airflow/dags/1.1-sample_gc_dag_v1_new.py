import datetime
from airflow import DAG

# pylint: disable=g-import-not-at-top
try:
  from airflow.providers.standard.operators.bash import BashOperator
except ImportError:
  from airflow.operators.bash_operator import BashOperator
# pylint: enable=g-import-not-at-top

default_args = {
    'start_date': datetime.datetime(2026, 9, 15),
    'retries': 1,
    'retry_delay': datetime.timedelta(minutes=5),
}

with DAG(
    dag_id='sample_dag_v1',
    description='Testing sample dag',
    default_args=default_args,
    schedule='*/10 * * * *',
    max_active_runs=2,
    catchup=False,
    dagrun_timeout=datetime.timedelta(minutes=10),
) as dag:

    task1 = BashOperator(
        task_id='1st_task',
        bash_command='echo hello wrld, this is the first task of sample DAG'
    )

    task2 = BashOperator(
        task_id='2nd_task',
        bash_command='echo I am second task and will run after first task'
    )

    task3 = BashOperator(
        task_id='3rd_task',
        bash_command='echo I am third task and will run after first task'
    )

    task1.set_downstream(task2)
    task1.set_downstream(task3)

    #second method using bit shift operator
    #task1 >> task2
    #task1 >> task3

    #third method
    # task1 >> [task2,task3]
