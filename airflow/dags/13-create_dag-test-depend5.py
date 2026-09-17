# refer Notes/Notes9.txt for more details
from datetime import timedelta,datetime,time
from airflow.decorators import dag, task
from airflow.sensors.time_sensor import TimeSensor
from airflow.utils.dates import days_ago

# default_args = {

#     'owner': 'hdu',
#     'retries': 5,
#     'retry_delay': timedelta(minutes=5)
# }

@dag(dag_id = 'sample_dag_with_timeSensor_v3',
        schedule_interval='@daily',
     start_date=days_ago(5),
     catchup=False)

def my_dag():
    wait = TimeSensor(
        task_id='wait',
        target_time=time(hour=11, minute=8),
    )

    @task
    def the_task(wait):
        print("Task executed.")

    the_task(wait)

dag = my_dag()
