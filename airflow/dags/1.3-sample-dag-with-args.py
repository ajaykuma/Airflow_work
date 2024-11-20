#Refer Notes/Notes3.txt for more details
from airflow import DAG
from datetime import datetime, timedelta
from airflow.operators.bash import BashOperator
import json

file = open("/home/hdu/airflow/dags/configs/dev2.json", 'r')
myconfigs = json.load(file)

default_args = {

    'owner': myconfigs['owner'],
    'retries': myconfigs['retries'],
    'retry_delay': timedelta(minutes=myconfigs['retry_delay'])

}

file.close()

print(default_args)

with DAG (

    dag_id = 'sample_dag_v1',
    description = 'Testing sample dag with args from file',
    default_args=default_args,
    start_date=datetime(2024,11,20,2),
    schedule_interval='@daily'

) as dag:
    task1 = BashOperator(
        task_id ='1st_task',
        bash_command='echo hello wrld, this is the first task of sample DAG '
    )

    task2 = BashOperator(
        task_id ='2nd_task',
        bash_command='echo I am second task and will run after first task '
    )

    task3 = BashOperator(
        task_id ='3rd_task',
        bash_command='echo I am third task and will run after first task '
    )

    
#     #First method
    task1.set_downstream(task2)
    task1.set_downstream(task3)

#     #second method using bit shift operator
#     #task1 >> task2
#     #task1 >> task3

#     #third method
#     # task1 >> [task2,task3]

