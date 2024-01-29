from airflow import DAG
from datetime import datetime, timedelta
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator

default_args = {

    'owner': 'hdu',
    'retries': 5,
    'retry_delay': timedelta(minutes=5)
}

def greet(name,age):
    print(f"Hello world, my name is {name}",
          f"my age is {age} years old")


with DAG (

    dag_id = 'sample_dag_with_python_operator_v1',
    description = 'Testing sample dag with python operator',
    default_args=default_args,
    start_date=datetime(2024,1,15,2),
    schedule_interval='@daily'

) as dag:
    task1 = PythonOperator(
        task_id ='greet',
        python_callable=greet,
        op_kwargs={'name': 'John','age': 25}
    )

    task2 = BashOperator(
        task_id ='2nd_task',
        bash_command='echo hello wrld, this is the second task of sample DAG '
    )

    task1 >> task2