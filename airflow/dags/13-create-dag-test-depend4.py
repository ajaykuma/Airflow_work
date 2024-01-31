from datetime import timedelta,datetime,time
from airflow.decorators import dag, task
from airflow.sensors.time_sensor import TimeSensorAsync
from airflow.utils.dates import days_ago

# default_args = {

#     'owner': 'hdu',
#     'retries': 5,
#     'retry_delay': timedelta(minutes=5)
# }

@dag(dag_id = 'sample_dag_with_timeSensor_v0',
        schedule_interval='@daily', 
     start_date=days_ago(5), 
     catchup=False)

def my_dag():
    wait = TimeSensorAsync(
        task_id='wait',
        target_time=time(hour=12, minute=45), 
        mode='reschedule',
    )

    @task
    def the_task(wait):
        print("Task executed.")

    the_task(wait)

dag = my_dag()