
from airflow import DAG
from datetime import datetime, timedelta
from airflow.operators.python import PythonOperator


default_args = {
    'owner': 'hdu',
    'retries': 5,
    'retry_delay': timedelta(minutes=5)
}

def greet(name, age):
    print(
        f"Hello world, my name is {name}, "
        f"and I am {age} years old"
    )


def get_name():
    return 'John'


with DAG(
    dag_id='sample_dag2_with_python_operator_v0',
    description='Testing sample DAG with PythonOperator',
    default_args=default_args,
    start_date=datetime(2024, 11, 20, 2),
    schedule_interval='@daily'
) as dag:

    # Previous task can be kept as an example:
    #
    # task1 = PythonOperator(
    #     task_id='greet',
    #     python_callable=greet,
    #     op_kwargs={'name': 'John', 'age': 25}
    # )

    task2 = PythonOperator(
        task_id='get_name',
        python_callable=get_name
    )

    task2
