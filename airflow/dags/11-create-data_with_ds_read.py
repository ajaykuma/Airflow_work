# refer Notes/Notes11.txt for more details

from datetime import timedelta,datetime
from airflow.decorators import dag, task
from airflow import DAG, datasets, Dataset

my_file = Dataset("/home/hdu/my-venv/dags/configs/sample.json")
# default_args = {

#     'owner': 'hdu',
#     'retries': 5,
#     'retry_delay': timedelta(minutes=5)
# }

with DAG(
    dag_id = "consumer_v1",
    schedule=[my_file],
    start_date=datetime(2024,11,20),
    #dagrun_timeout=timedelta(seconds=10),  
    catchup=False
):

    
    # @task(outlets=[my_file])
    @task()
    def the_task_read():
        with open(my_file.uri, "r") as f:
            print(f.read())

    the_task_read()