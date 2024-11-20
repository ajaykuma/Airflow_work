#Refer Notes/Notes5.txt for more details
from airflow import DAG
from datetime import datetime, timedelta
from airflow.operators.python import PythonOperator
from airflow.decorators import dag,task

default_args = {

    'owner': 'hdu',
    'retries': 5,
    'retry_delay': timedelta(minutes=5)
}

@dag (dag_id = 'sample_dag_with_taskflow_api_v1',
    description = 'Testing sample dag with taskflow',
    default_args=default_args,
    start_date=datetime(2024,11,20),schedule_interval='@daily')

#create 3 tasks

def new_etl():

    @task()
    def get_name():
        return 'John'

    @task() 
    def get_age():
	    return 25

    @task()
    def greet(name,age):
        print(f"Hello world, my name is {name} "
          f" and iam {age} years old ")
      
    name = get_name()
    age = get_age()
    greet(name=name,age=age)

greet_dag = new_etl()