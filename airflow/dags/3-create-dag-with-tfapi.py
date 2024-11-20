#Refer Notes/Notes5.txt for more details
from airflow import DAG
from datetime import datetime, timedelta
from airflow.decorators import dag,task

default_args = {

    'owner': 'hdu',
    'retries': 5,
    'retry_delay': timedelta(minutes=5)
}

@dag(dag_id = 'sample_dag_with_taskflow_api_v0',
    description = 'Testing sample dag with taskflow',
    default_args=default_args,
    start_date=datetime(2024,11,20),schedule_interval='@daily')

#create 3 tasks

def new_etl():

    @task(multiple_outputs=True)
    def get_name():
        return {
             'first_name': 'John',
             'last_name' : 'Morgan'
        }

    @task() 
    def get_age():
	    return 25

    @task()
    def greet(first_name,last_name,age):
        print(f"Hello world, my name is {first_name} {last_name} "
          f" and iam {age} years old ")
      
    name_dict = get_name()
    age = get_age()
    greet(first_name=name_dict['first_name'],last_name=name_dict['last_name'],age=age)

greet_dag = new_etl()