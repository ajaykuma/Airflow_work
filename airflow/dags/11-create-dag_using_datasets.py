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
    dag_id = "producer_v1",
    schedule='@daily',
    start_date=datetime(2024,11,20),
    catchup=False
):

    @task(outlets=[my_file])
    def the_task_update():
        with open(my_file.uri, "a+") as f:
            f.write("\n" + "#producer-updated-this-file")

    the_task_update()