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
    dag_id = "producer",
    schedule='@daily',
    start_date=datetime(2024,1,29),
    catchup=False
):

    @task(outlets=[my_file])
    def the_task_update():
        with open(my_file.uri, "a+") as f:
            f.write("producer update")

    the_task_update()