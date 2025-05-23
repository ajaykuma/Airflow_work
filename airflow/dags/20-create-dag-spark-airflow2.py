import airflow
from airflow import DAG
#pip install apache-airflow-providers-apache-spark pyspark

from datetime import datetime, timedelta
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
import json


file = open("/home/hdu/.local/dags/configs/dev2.json", 'r')
myconfigs = json.load(file)

default_args = {

    'owner': myconfigs['owner'],
    'retries': myconfigs['retries'],
    'retry_delay': timedelta(minutes=myconfigs['retry_delay'])

}

file.close()

with DAG (

    dag_id = 'sample_dag_v4',
    description = 'Testing sample dag for pyspark',
    default_args=default_args,
    start_date=datetime(2024,11,20,2),
    #start_date=airflow.utils.date.days_ago(1),
        schedule='@daily'

)as dag:
        #only for first time to get providers
    #task1 = BashOperator(
    #    task_id ='get_providers',
    #    bash_command='pip install apache-airflow-providers-apache-spark pyspark '
    #)

    #only for first run to get packages
    task1 = BashOperator(
        task_id ='get_packages',
        bash_command='pip install pandas numpy '
    )

    #only for first time to get providers
    #task1 = BashOperator(
    #    task_id ='get_providers',
    #    bash_command='pip install apache-airflow-providers-apache-spark pyspark '
    #)

    task2 = PythonOperator(
        task_id = 'pyspark_wrk',
        python_callable=lambda: print("pyspark job started")

    )
    
    task3 = SparkSubmitOperator(
        task_id = 'pyspark_job',
        conn_id = 'spark_conn',
        application = 'my-venv/dags/spaApp2.py',
        total_executor_cores=1,
        #packages="io.delta:delta-core_2.12:0.7.0,org.apache.spark:spark-sql-kafka-0-10_2.12:3.0.0",
        #executor_cores=1,
        #executor_memory='1g',
        #driver_memory='1g',
        name='sample_spark_airf_appl2',
       

    )

    task1.set_downstream(task2)
    task2.set_downstream(task3)

    #we can split the spaApp2.py application into multiple tasks for parallelism.


