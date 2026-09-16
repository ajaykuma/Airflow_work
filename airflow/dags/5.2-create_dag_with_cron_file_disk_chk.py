from airflow import DAG
from datetime import datetime, timedelta
from airflow.operators.bash import BashOperator


default_args = {
    'owner': 'hdu',
    'retries': 2,
    'retry_delay': timedelta(minutes=2)
}


with DAG(
    dag_id='dag_file_disk_check',
    default_args=default_args,
    start_date=datetime(2026, 9, 12),

    # Every 15 minutes
    schedule='*/15 * * * *',
    catchup=False
) as dag:

    file_check = BashOperator(
        task_id='file_check',
        bash_command="""
        echo "================================="
        echo "        FILE CHECK"
        echo "================================="

        echo "DAG directory:"
        echo "/home/hdu/airflow/dags"

        echo ""
        echo "Number of Python DAG files:"
        find /home/hdu/airflow/dags -type f -name "*.py" | wc -l

        echo ""
        echo "Python DAG files:"
        find /home/hdu/airflow/dags -type f -name "*.py" -printf "%f\n"
        """
    )


    disk_check = BashOperator(
        task_id='disk_check',
        bash_command="""
        echo "================================="
        echo "        DISK CHECK"
        echo "================================="

        USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')

        echo "Current disk usage: ${USAGE}%"

        if [ "$USAGE" -gt 80 ]; then
            echo "WARNING: Disk usage is above 80%"
        else
            echo "Disk usage is normal"
        fi

        echo ""
        echo "Disk details:"
        df -h /
        """
    )


    file_check >> disk_check
