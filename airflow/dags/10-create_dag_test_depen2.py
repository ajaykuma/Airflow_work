# refer Notes/Notes9.txt for more details
# without need of triggerer
from datetime import timedelta
from airflow.decorators import dag, task
from airflow.sensors.time_delta import TimeDeltaSensor
from airflow.utils.dates import days_ago

@dag(
    dag_id='sample_dag_with_timedeltaSensor_v0',
    schedule_interval='@daily',
    start_date=days_ago(5),
    catchup=False
)
def my_dag():
    wait = TimeDeltaSensor(
        task_id='wait',
        delta=timedelta(minutes=2),   # shortened for testing — see note below
        mode='reschedule',
    )

    @task
    def the_task():
        print("Task executed.")

    wait >> the_task()

dag = my_dag()
