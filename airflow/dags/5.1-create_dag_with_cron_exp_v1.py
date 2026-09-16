from airflow import DAG
from datetime import datetime, timedelta
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator


default_args = {
    'owner': 'hdu',
    'retries': 2,
    'retry_delay': timedelta(minutes=2)
}


def process_data():
    print("PythonOperator is processing the data...")
    
    numbers = [10, 20, 30, 40, 50]
    
    total = sum(numbers)
    average = total / len(numbers)

    print(f"Numbers  : {numbers}")
    print(f"Total    : {total}")
    print(f"Average  : {average}")


with DAG(
    dag_id='dag_with_cron_operators_v1',
    default_args=default_args,
    start_date=datetime(2026, 9, 12),

    # Every day at midnight
    schedule='0 0 * * *',
    catchup=False
) as dag:

    start = BashOperator(
        task_id='start',
        bash_command='echo "===== DAILY JOB STARTED ====="'
    )

    system_info = BashOperator(
        task_id='system_info',
        bash_command="""
        echo "Hostname:"
        hostname

        echo "Current date:"
        date

        echo "Current user:"
        whoami

        echo "Disk usage:"
        df -h /
        """
    )

    python_processing = PythonOperator(
        task_id='python_processing',
        python_callable=process_data
    )

    finish = BashOperator(
        task_id='finish',
        bash_command='echo "===== DAILY JOB COMPLETED ====="'
    )


    start >> system_info >> python_processing >> finish
