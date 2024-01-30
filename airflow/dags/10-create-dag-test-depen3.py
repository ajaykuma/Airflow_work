from datetime import timedelta
from airflow.decorators import dag, task
from airflow.sensors.time_delta import TimeDeltaSensorAsync
from airflow.utils.dates import days_ago

# default_args = {

#     'owner': 'hdu',
#     'retries': 5,
#     'retry_delay': timedelta(minutes=5)
# }

@dag(dag_id = 'sample_dag_with_timedeltaSensor_v0',
        schedule_interval='@daily', 
     start_date=days_ago(2), 
     catchup=False)

def my_dag():
    wait = TimeDeltaSensorAsync(
        task_id='wait',
        delta=timedelta(minutes=1),
        mode='reschedule',
    )

    @task
    def the_task(wait):
        print("Task executed.")

    the_task(wait)

dag = my_dag()