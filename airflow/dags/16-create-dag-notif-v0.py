from datetime import datetime
from airflow import DAG
from airflow.operators.dummy import DummyOperator
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator

def custom_failure_function(context):
	"Define custom failure notification behaviour"
	dag_run = context.get('dag_run')
	task_instances = dag_run.get_task_instances()
	print("These task instances failed:", task_instances)

def custom_success_function(context):
	"Define custom success notification behaviour"
	dag_run = context.get('dag_run')
	task_instances = dag_run.get_task_instances()
    #details = dag_run.details()
	print("These task instances succeeded:","\n", task_instances)
	#print("These are details:", details)

default_args = {
	'owner': 'hdu',
	'start_date': datetime(2024,1,30),
	'on_failure_callback': custom_failure_function,
	'retries': 1
	}

def calculating(ti):
    num1 = ti.xcom_pull(task_ids='get_num', key = 'first_num')
    print(num1 * 100)

def get_num(ti):
        ti.xcom_push(key='first_num', value=25)
		
with DAG('sample_dag_noti2',
	default_args=default_args,
	schedule_interval='@daily',
	catchup=False) as dag:

	failure_task = DummyOperator(
	   task_id='failure_task')

	success_task = DummyOperator(
        task_id = 'Success_task',
        on_success_callback=custom_success_function
	)                                                                              
    
	task2 = PythonOperator(
        task_id = 'calculating',
        python_callable=calculating
	)

	task3 = PythonOperator(
              task_id = 'get_num',
              python_callable=get_num
	)    
    
failure_task >> task3 >> task2 >> success_task