# refer Notes/Notes7-0.txt for more details
import airflow 
from datetime import timedelta 
from airflow import DAG 
from airflow.operators.mysql_operator import MySqlOperator
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
#from airflow.providers.apache.hive.operators.hive import HiveOperator 
from airflow.utils.dates import days_ago

default_args = { 
    'owner': 'hdu', 
    #'start_date': airflow.utils.dates.days_ago(2), 
    # 'end_date': datetime(), 
    # 'depends_on_past': False, 
    # 'email': ['airflow@example.com'], 
    # 'email_on_failure': False, 
    # 'email_on_retry': False, 
    #'retries': 1, 
    'retry_delay': timedelta(minutes=1), }

dag_exec_scripts = DAG( 
    dag_id='dag_exec_scripts_demo_v0', 
    default_args=default_args, 
    # schedule_interval='0 0 * * *', 
    schedule_interval='@once', 
    start_date=days_ago(1), 
    dagrun_timeout=timedelta(minutes=60), 
    description='executing the sql scripts', )

"""task1 = BashOperator(
        task_id ='get_packages',
        bash_command='pip install pandas numpy '
        dag=dag_exec_scripts
    )"""
            
create_table = MySqlOperator( sql="sql/createdb.sql", 
                             task_id="createtable_task", 
                             mysql_conn_id="mysql_default", 
                             dag=dag_exec_scripts )

clnup_table = MySqlOperator(sql = "sql/deletetbl.sql",
                             task_id="clnuptable_task", 
                              mysql_conn_id="mysql_default", 
                              dag=dag_exec_scripts)

load_data = MySqlOperator( sql="sql/loadscr.sql", 
                          task_id="load_data_task", 
                          mysql_conn_id="mysql_default", 
                          dag=dag_exec_scripts ) 


create_table >> clnup_table >> load_data