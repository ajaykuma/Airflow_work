import airflow
from datetime import timedelta
from airflow import DAG
from airflow.providers.mysql.operators.mysql import MySqlOperator
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.utils.dates import days_ago

default_args = {
    'owner': 'hdu',
    'retry_delay': timedelta(minutes=1),
}

dag_exec_scripts = DAG(
    dag_id='dag_exec_scripts_demo_v0',
    default_args=default_args,
    schedule_interval='@once',
    start_date=days_ago(1),
    dagrun_timeout=timedelta(minutes=60),
    description='executing the sql scripts',
)

create_table = MySqlOperator(
    sql="sql/createdb.sql",
    task_id="createtable_task",
    mysql_conn_id="mysql_default",
    dag=dag_exec_scripts
)

clnup_table = MySqlOperator(
    sql="sql/deletetbl.sql",
    task_id="clnuptable_task",
    mysql_conn_id="mysql_default",
    dag=dag_exec_scripts
)

load_data = MySqlOperator(
    sql="sql/loadscr.sql",
    task_id="load_data_task",
    mysql_conn_id="mysql_default",
    dag=dag_exec_scripts
)

create_table >> clnup_table >> load_data
