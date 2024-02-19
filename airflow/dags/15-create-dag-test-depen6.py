from datetime import timedelta
import dateutil.parser
import airflow
from datetime import datetime
from airflow import DAG
from airflow.operators.dummy_operator import DummyOperator
from airflow.sensors.external_task import ExternalTaskSensor

args = {
'owner': 'hdu',
'depends_on_past': False,
'start_date': datetime(2024, 2, 19),
'email': ['xyz@gmail.com'],
'email_on_failure': False,
'email_on_retry': False,
'retries': 3,
'retry_delay': timedelta(minutes=5),
}


dag = DAG(
dag_id='ExternalWorkflow',
default_args=args,
schedule_interval= '*/10 * * * *',
)

external_task = ExternalTaskSensor(external_task_id ='DependentOperation',
task_id='external_task',
external_dag_id = 'DependentJob',
dag=dag)

newjob = DummyOperator(dag=dag, task_id='newjob')

external_task >> newjob
