# refer Notes/Notes7-1.txt for more details
import airflow 
import csv
import logging
from datetime import timedelta 
from airflow import DAG 
from airflow.operators.mysql_operator import MySqlOperator
from airflow.operators.python import PythonOperator
from airflow.providers.mysql.hooks.mysql import MySqlHook
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
    'retry_delay': timedelta(minutes=5), }

def mysql_to_file(ds_nodash,next_ds_nodash):
    hook = MySqlHook(mysql_conn_id = "mysql_default")
    conn = hook.get_conn()
    cursor = conn.cursor()
    #cursor.execute("select * from airflow.employees where date >= %s and data <%s"),
    #(ds_nodash,next_ds_nodash)
    cursor.execute("select * from airflow.employees ")
    with open(f"/home/hdu/my-venv/dags/sql/sampleout_{ds_nodash}.csv", "w") as f:
        csv_writer = csv.writer(f)
        csv_writer.writerow([i[0] for i in cursor.description])
        csv_writer.writerows(cursor)
    cursor.close()
    conn.close()
    logging.info("saved output from tbl into a file: %s", f"/home/hdu/my-venv/dags/sql/sampleout_{ds_nodash}.csv")


with DAG( 
    dag_id='dag_exec_scripts_read_demo_v1', 
    default_args=default_args, 
    # schedule_interval='0 0 * * *', 
    schedule_interval='@once', 
    start_date=days_ago(1), 
    dagrun_timeout=timedelta(minutes=60), 
    description='executing the sql scripts', 
) as dag:
    task1 = PythonOperator(
        task_id = "mysql_to_file",
        python_callable=mysql_to_file

    )
    task1


