from airflow import DAG
from datetime import datetime, timedelta
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.sensors.external_task import ExternalTaskSensor

default_args = {

    'owner': 'hdu',
    'retries': 5,
    'retry_delay': timedelta(minutes=5)
}

dag = DAG(

    dag_id = 'sample_dag2_for_cross_dag_chk_v1',
    description = 'Testing sample dag with python operator',
    default_args=default_args,
    start_date=datetime(2024,1,29),
    schedule_interval='@daily'

) 

wait_for_other_dag_task = ExternalTaskSensor(
    task_id='sample_dag1_for_cross_dag_chk_v1',
    external_dag_id='sample_dag1_for_cross_dag_chk_v0',
    external_task_id='greet',
    #mode='reschedule',  # sensor frees up worker when criteria is not met
    #timeout=600,  # timeout in seconds
    # start_date=datetime(2024,1,27,2),
    # schedule_interval='@daily'
    execution_date_fn=lambda dt: dt,
    #execution_delta=timedelta(minutes=1),
    dag=dag
    )

check_compl = BashOperator(
    task_id ='fnl_tsk',
    bash_command='echo cross dependency validation done ',
    dag=dag
    )

wait_for_other_dag_task >> check_compl

#The execution_date_fn is a function that takes the current execution 
#date and returns the execution date to check in the external DAG. 
#In this case, we're using a lambda function to return the 
#same execution date.

#using timedelta to check against a task that runs 1 hr/min earlier 


