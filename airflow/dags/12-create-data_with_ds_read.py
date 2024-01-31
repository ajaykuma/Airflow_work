from datetime import timedelta,datetime
from airflow.decorators import dag, task
from airflow import DAG, datasets, Dataset

my_file = Dataset("/home/hdu/airflow/configs/sample.txt")
# default_args = {

#     'owner': 'hdu',
#     'retries': 5,
#     'retry_delay': timedelta(minutes=5)
# }

with DAG(
    dag_id = "consumer",
    schedule=[my_file],
    start_date=datetime(2024,1,29),
    #dagrun_timeout=timedelta(seconds=10),  
    catchup=False
):

    
    # @task(outlets=[my_file])
    @task()
    def the_task_read():
        with open(my_file.uri, "r") as f:
            print(f.read())

    the_task_read()