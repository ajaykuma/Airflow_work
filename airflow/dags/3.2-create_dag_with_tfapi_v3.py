#with the TaskFlow API, returning a value from a @task automatically creates an XCom. 
#Passing that returned value into another task also creates the dependency automatically.
#The important difference from the traditional PythonOperator approach is 
#that we don't need to explicitly create XComs.

from airflow.decorators import dag, task
from datetime import datetime, timedelta
import json
import os


# Default configuration

default_args = {
    "owner": "hdu",
    "retries": 5,
    "retry_delay": timedelta(minutes=5)
}


# DAG

@dag(
    dag_id="sample_dag_taskapi_xcom_v1",
    description="Testing TaskFlow API, XCom and JSON file usage",
    default_args=default_args,
    start_date=datetime(2026, 9, 12),
    schedule="@daily",
    catchup=False
)
def customer_etl():

    # -----------------------------------------------------
    # Task 1: Read dev2.json
    # -----------------------------------------------------

    @task
    def read_config():

        config_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "configs",
            "dev2.json"
        )

        with open(config_path, "r") as file:
            config = json.load(file)

        print("Configuration:")
        print(config)

        return config


    # -----------------------------------------------------
    # Task 2: Read sample-file.json
    # -----------------------------------------------------

    @task
    def read_customer():

        customer_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "configs",
            "sample-file.json"
        )

        with open(customer_path, "r") as file:
            customer = json.load(file)

        print("Customer data:")
        print(customer)

        return customer


    # -----------------------------------------------------
    # Task 3: Use values returned by previous tasks
    # -----------------------------------------------------

    @task
    def create_greeting(config, customer):

        title = customer["title"]
        first_name = customer["first"]
        last_name = customer["last"]
        package = customer["package"]

        owner = config["owner"]
        retries = config["retries"]

        greeting = (
            f"Hello {title} {first_name} {last_name}, "
            f"welcome to our {package} package."
        )

        print(greeting)

        print(f"Airflow owner: {owner}")
        print(f"Configured retries: {retries}")

        return greeting


    # -----------------------------------------------------
    # Task 4: Demonstrate XCom value consumption
    # -----------------------------------------------------

    @task
    def display_result(greeting):

        print("Final result received through XCom:")
        print(greeting)


    # -----------------------------------------------------
    # Task dependencies
    # -----------------------------------------------------

    config = read_config()

    customer = read_customer()

    greeting = create_greeting(
        config=config,
        customer=customer
    )

    display_result(greeting)


# Create DAG
customer_dag = customer_etl()
