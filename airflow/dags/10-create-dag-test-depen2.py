# refer Notes/Notes9.txt for more details
#without need of trigerrer
from datetime import timedelta
from airflow.decorators import dag, task
from airflow.sensors.time_delta import TimeDeltaSensor
from airflow.utils.dates import days_ago

# default_args = {

#     'owner': 'hdu',
#     'retries': 5,
#     'retry_delay': timedelta(minutes=5)
# }

@dag(dag_id = 'sample_dag_with_timedeltaSensor_v0',
        schedule_interval='@daily', 
     start_date=days_ago(5), 
     catchup=False)

def my_dag():
    wait = TimeDeltaSensor(
        task_id='wait',
        delta=timedelta(minutes=15),
        mode='reschedule',
    )

    @task
    def the_task(wait):
        print("Task executed.")

    the_task(wait)

dag = my_dag()