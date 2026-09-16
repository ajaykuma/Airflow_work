## AIRFLOW NOTES 3

### EX1: Creating a Simple DAG
### DAG folder

Airflow looks for DAG files inside:

```text
AIRFLOW_HOME/dags/
```

Create a Python file:

```text
create-1-sample-dag.py
```

### Basic DAG

```python
from airflow import DAG
from datetime import datetime, timedelta
from airflow.operators.bash import BashOperator


# Define common parameters that will be used
# to initialize operators
default_args = {
    'owner': 'hdu',
    'retries': 5,
    'retry_delay': timedelta(minutes=2)
}


# Create an instance of the DAG using "with"
with DAG(
    dag_id='sample_dag_v0',
    description='Testing sample DAG',
    default_args=default_args,
    start_date=datetime(2024, 1, 20, 2),
    schedule_interval='@daily'
) as dag:

    task1 = BashOperator(
        task_id='1st_task',
        bash_command='echo hello world, this is the first DAG'
    )

    task1
```

### Important points

- `DAG` is the container that defines the workflow.
- `dag_id` uniquely identifies the DAG.
- `default_args` contains common default parameters for tasks.
- `start_date` determines when the DAG can start being scheduled.
- `schedule_interval='@daily'` schedules the DAG once per day.
- `BashOperator` allows us to execute a shell command.
- `task_id` uniquely identifies a task within the DAG.
- `bash_command` is the command that the task executes.

### Add the DAG to Airflow

Copy the DAG file into:

```text
AIRFLOW_HOME/dags/
```

Then refresh/restart Airflow as required by the local setup.

If the following setting is enabled:

```text
dags_are_paused_at_creation = True
```

new DAGs will initially appear as **paused**.
You can then unpause the DAG from the Airflow UI and trigger it manually.

### Checking the DAG in the UI

Once the DAG appears in the Airflow UI:

1. Unpause the DAG.
2. Trigger the DAG.
3. Watch the DAG Run status.
4. Open the DAG Run.
5. Explore the **Grid** or **Graph** view.
6. Click on a task to inspect:
   - Code
   - Logs
   - XCom
   - Other task information

Logs can also be found under:

```text
AIRFLOW_HOME/logs/<dag-id>/
```

### From the command line

List all DAGs:

```bash
airflow dags list
```

Show the DAG structure:

```bash
airflow dags show sample_dag_v0
```

If graphical rendering is required, Graphviz may also need to be installed.
pip install graphviz

---

## EX2: Adding More Tasks and Creating Dependencies

Now add more tasks to the DAG.
Change the DAG ID so that we can keep this as a separate version:

```python
dag_id='sample_dag_v1'
```

### Add more tasks

```python
task2 = BashOperator(
    task_id='2nd_task',
    bash_command='echo I am second task and will run after first task'
)

task3 = BashOperator(
    task_id='3rd_task',
    bash_command='echo I am third task and will run after first task'
)
```

### First method: `set_downstream()`

Set the dependencies:

```python
task1.set_downstream(task2)
task1.set_downstream(task3)
```

This means:

```text
        task1
       /     \
   task2     task3
```

Therefore, `task2` and `task3` can run after `task1` has completed successfully.
Save the DAG and refresh the Airflow UI.
Then test the DAG and observe the sequence of tasks.

### Other ways to define dependencies
#### Method 2: Bit-shift operator

```python
task1 >> task2
task1 >> task3
```

This is equivalent to:

```python
task1.set_downstream(task2)
task1.set_downstream(task3)
```

#### Method 3: Set multiple downstream tasks at once

```python
task1 >> [task2, task3]
```

This creates:

```text
        task1
       /     \
   task2     task3
```

### Note
When experimenting with different versions, change the `dag_id` accordingly if you want to keep multiple versions visible in Airflow.

---

## EX3: Using PythonOperator

Instead of executing a Bash command, we can execute a Python function using `PythonOperator`.

```python
from airflow import DAG
from datetime import datetime, timedelta
from airflow.operators.python import PythonOperator


default_args = {
    'owner': 'hdu',
    'retries': 5,
    'retry_delay': timedelta(minutes=5)
}


def greet():
    print("Hello world")


with DAG(
    dag_id='sample_dag_with_python_operator_v0',
    description='Testing sample DAG with PythonOperator',
    default_args=default_args,
    start_date=datetime(2024, 11, 20, 2),
    schedule_interval='@daily'
) as dag:

    task1 = PythonOperator(
        task_id='greet',
        python_callable=greet
    )

    task1
```

Here:

```python
python_callable=greet
```

tells Airflow which Python function should be executed.

---

### Optional: Passing Parameters to a Python Function

We can pass parameters to the Python function.

Change the function:

```python
def greet(name, age):
    print(
        f"Hello world, my name is {name}, "
        f"and I am {age} years old"
    )
```

Then update the task:

```python
task1 = PythonOperator(
    task_id='greet',
    python_callable=greet,
    op_kwargs={
        'name': 'John',
        'age': 25
    }
)
```

Here, `op_kwargs` is used to pass keyword arguments to the Python function.

---

## Programmatically Unpause a DAG
A DAG can also be unpaused programmatically.

Example:

```python
import airflow.settings
from airflow.models import DagModel


def unpause_dag(dag):
    """
    Programmatically unpause a DAG.

    :param dag: DAG object
    :return: DAG is now unpaused
    """

    session = airflow.settings.Session()

    try:
        qry = session.query(DagModel).filter(
            DagModel.dag_id == dag.dag_id
        )

        d = qry.first()
        d.is_paused = False

        session.commit()

    except:
        session.rollback()

    finally:
        session.close()
```

The basic idea is:

1. Create a database session.
2. Find the `DagModel` using the DAG ID.
3. Set `is_paused` to `False`.
4. Commit the change.
5. Roll back if an error occurs.
6. Close the session.

---

### From the Command Line

A DAG can also be paused/unpaused using the Airflow CLI.

Example:

```bash
airflow dags pause sample_dag_v2
```

The output indicates whether the DAG is paused.

To unpause the DAG, use the corresponding unpause command:

```bash
airflow dags unpause sample_dag_v2
```

---

### Another Programmatic Approach

A DAG model can also be retrieved and updated directly:

```python
from airflow.models import DagModel

dag_id = "dag_name"

dag = DagModel.get_dagmodel(dag_id)

dag.set_is_paused(is_paused=False)
```

To check the pause state:

```python
dag.is_paused()
```

---

### More Information
Airflow REST API documentation:
https://airflow.apache.org/docs/apache-airflow/stable/stable-rest-api-ref.html
