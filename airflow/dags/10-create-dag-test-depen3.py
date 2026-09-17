# refer Notes/Notes9.txt for more details
# will need a triggerer
from datetime import timedelta
from airflow.decorators import dag, task
from airflow.sensors.time_delta import TimeDeltaSensorAsync
from airflow.utils.dates import days_ago

@dag(
    dag_id='sample_dag_with_timedeltaSensor_v1',
    schedule_interval='@daily',
    start_date=days_ago(5),
    catchup=False
)
def my_dag():
    """
    Removed mode='reschedule' from TimeDeltaSensorAsync. It's already deferrable by design 
    (that's the whole point of the "Async" variant and why it needs the triggerer) — mode 
    is a reschedule-vs-poke setting from the synchronous sensor base class and isn't 
    the mechanism doing the work here. we can leave it in, 
    but it doesn't do anything meaningful for this sensor
    """
    wait = TimeDeltaSensorAsync(
        task_id='wait',
        delta=timedelta(minutes=3),   # shortened for testing — see note below
    )

    @task
    def the_task():
        print("Task executed.")

    wait >> the_task()

dag = my_dag()
