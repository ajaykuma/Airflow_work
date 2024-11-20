#Refer Notes/Notes4.txt for more details
from airflow import DAG
from datetime import datetime, timedelta
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator

default_args = {

    'owner': 'hdu',
    'retries': 5,
    'retry_delay': timedelta(minutes=5)
}

def greet(age,ti):
    name = ti.xcom_pull(task_ids='get_name')
    print(f"Hello world, my name is {name},"
          f" and I am {age} years old")

def get_name():
    return 'John'

with DAG (

    dag_id = 'sample_dag_with_python_operator_v2',
    description = 'Testing sample dag with python operator',
    default_args=default_args,
    start_date=datetime(2024,11,20,2),
    schedule_interval='@daily'

) as dag:
    task1 = PythonOperator(
        task_id ='greet',
        python_callable=greet,
        op_kwargs={'age': 25}
    )

    task2 = PythonOperator(
        task_id ='get_name',
        python_callable=get_name,
    )

    task2 >> task1
