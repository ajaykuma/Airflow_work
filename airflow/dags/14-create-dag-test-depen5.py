import airflow
from airflow import DAG
from airflow.utils.trigger_rule import TriggerRule
from datetime import datetime, timedelta
import dateutil.parser
from airflow.operators.dummy_operator import DummyOperator

default_global_args = {
'owner': 'hdu',
'email': ['xyz@gmail.com'],
'email_on_failure': True,
'email_on_retry': True,
'start_date': datetime(2024, 11, 19)
}

dag = DAG(
dag_id = 'DependentJob',
default_args = default_global_args,
schedule_interval= '*/10 * * * *',
max_active_runs = 10
)

DependentOperation = DummyOperator(task_id='DependentOperation',
                                   dag=dag,trigger_rule=TriggerRule.ALL_SUCCESS)
