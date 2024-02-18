#Refer Notes/Notes4.txt for more details
from airflow import DAG
from datetime import datetime, timedelta
from airflow.operators.python import PythonOperator

#create instaance of DAG using 'with'


#define common parameters which will be to initialize the operatr in default
default_args = {

    'owner': 'hdu',
    'retries': 5,
    'retry_delay': timedelta(minutes=5)
}

def greet(ti):
    first_name = ti.xcom_pull(task_ids='get_name', key = 'first_name')
    last_name = ti.xcom_pull(task_ids='get_name', key = 'last_name')
    age = ti.xcom_pull(task_ids='get_age', key = 'age')
    print(f"Hello world, my name is {first_name} {last_name},"
          f" and iam {age} years old ")

def get_name(ti):
	ti.xcom_push(key='first_name', value='John')
	ti.xcom_push(key='last_name', value='Morgan')

def get_age(ti):
	ti.xcom_push(key='age', value=25)
      
with DAG (

    dag_id = 'sample_dag_with_python_operator_v3',
    description = 'Testing sample dag with python operator',
    default_args=default_args,
    start_date=datetime(2024,1,15,2),
    schedule_interval='@daily'

) as dag:
    task1 = PythonOperator(
        task_id ='greet',
        python_callable=greet
        #op_kwargs={'age': 25}
    )
   
    task2 = PythonOperator(
        task_id = 'get_name',
        python_callable=get_name
    )

    task3 = PythonOperator(
     task_id = 'get_age',
     python_callable=get_age)

    [task2,task3] >> task1

