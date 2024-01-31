from airflow import DAG
from datetime import datetime, timedelta
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.operators.mysql_operator import MySqlOperator
from airflow.models.taskinstance import TaskInstance
from airflow.models.dagrun import DagRun

default_args = {

    'owner': 'hdu',
    'retries': 5,
    'retry_delay': timedelta(minutes=5)
}

def calculating(ti):
    num1 = ti.xcom_pull(task_ids='get_num', key = 'first_num')
    print(num1 * 100)

def get_num(ti):
        ti.xcom_push(key='first_num', value=25)

with DAG (

    dag_id = 'Complete_dag',
    description = 'Testing complex dag',
    default_args=default_args,
    #start_date=datetime(2024,1,1),
    #schedule_interval='@daily'
    schedule_interval=None

) as dag:
    task1 = BashOperator(
        task_id ='1st_task',
        bash_command='echo COMPLEX DAG BEGINS '
    )
    
    task2 = PythonOperator(
        task_id ='calculating',
        python_callable=calculating,
    )
    task3 = PythonOperator(
        task_id = 'get_num',
        python_callable=get_num
    )

    create_table = MySqlOperator( sql="sql/createdb.sql",
                             task_id="createtable_task",
                             mysql_conn_id="airflow_db",
                             dag=dag)

    task1 >> task3 >> task2 >> create_table 

    
