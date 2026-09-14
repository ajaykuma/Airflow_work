# AIRFLOW NOTES 4

# Sharing Information Between Tasks

Airflow provides **XComs (Cross-Communication)** to allow tasks to exchange small amounts of information.

Basic concept:

```text
Task 1
  |
  | XCom push
  v
 XCom
  |
  | XCom pull
  v
Task 2
```

By default, a function's return value can be stored in XCom.

---

# EX1: Basic XCom Using PythonOperator

Start with the PythonOperator example from Notes3.

Add a new function to:

```text
create-dag-with-py-operator.py
```

```python
from airflow import DAG
from datetime import datetime, timedelta
from airflow.operators.python import PythonOperator


default_args = {
    'owner': 'hdu',
    'retries': 5,
    'retry_delay': timedelta(minutes=5)
}


def greet(name, age):
    print(
        f"Hello world, my name is {name}, "
        f"and I am {age} years old"
    )


def get_name():
    return 'John'


with DAG(
    dag_id='sample_dag_with_python_operator_v1',
    description='Testing sample DAG with PythonOperator',
    default_args=default_args,
    start_date=datetime(2024, 11, 20, 2),
    schedule_interval='@daily'
) as dag:

    # Previous task can be kept as an example:
    #
    # task1 = PythonOperator(
    #     task_id='greet',
    #     python_callable=greet,
    #     op_kwargs={'name': 'John', 'age': 25}
    # )

    task2 = PythonOperator(
        task_id='get_name',
        python_callable=get_name
    )

    task2
```

The `get_name()` function returns:

```python
'John'
```

This return value is automatically available through XCom.

---

# EX2: Using XComs

Now modify the DAG so that:

- `get_name()` produces the name.
- `greet()` retrieves the name from XCom.

Change the DAG ID:

```python
dag_id='sample_dag_with_python_operator_v2'
```

Modify the `greet()` function:

```python
def greet(age, ti):
    name = ti.xcom_pull(task_ids='get_name')

    print(
        f"Hello world, my name is {name}, "
        f"and I am {age} years old"
    )
```

Here:

```python
ti
```

is the **Task Instance** object.
It is used to access XCom.
The following retrieves the value produced by the `get_name` task:

```python
ti.xcom_pull(task_ids='get_name')
```

### Update the tasks

```python
task1 = PythonOperator(
    task_id='greet',
    python_callable=greet,
    op_kwargs={'age': 25}
)

task2 = PythonOperator(
    task_id='get_name',
    python_callable=get_name
)
```

### Set the dependency

```python
task2 >> task1
```

The workflow is now:

```text
get_name
    |
    | XCom
    v
  greet
```

`get_name` must run before `greet`, because `greet` needs the value produced by `get_name`.

---

# EX3: Pushing Multiple Values into XCom

We can explicitly push multiple values into XCom using:

```python
ti.xcom_push()
```

Change the DAG ID:

```python
dag_id='sample_dag_with_python_operator_v3'
```

Modify `get_name()`:

```python
def get_name(ti):
    ti.xcom_push(
        key='first_name',
        value='John'
    )

    ti.xcom_push(
        key='last_name',
        value='Morgan'
    )
```

Now two separate XCom values are stored:

```text
first_name -> John
last_name  -> Morgan
```

---

## Pulling Multiple Values from XCom

Modify `greet()`:

```python
def greet(age, ti):

    first_name = ti.xcom_pull(
        task_ids='get_name',
        key='first_name'
    )

    last_name = ti.xcom_pull(
        task_ids='get_name',
        key='last_name'
    )

    print(
        f"Hello world, my name is {first_name} {last_name}, "
        f"and I am {age} years old"
    )
```

The values are retrieved using:

```python
ti.xcom_pull(
    task_ids='get_name',
    key='first_name'
)
```

and:

```python
ti.xcom_pull(
    task_ids='get_name',
    key='last_name'
)
```

---

# EX4: Getting Values from Multiple Tasks

Now add another function to provide the age.

Change the DAG ID:

```python
dag_id='sample_dag_with_python_operator_v4'
```

Create a new function:

```python
def get_age(ti):
    ti.xcom_push(
        key='age',
        value=25
    )
```

### Add another task

```python
task3 = PythonOperator(
    task_id='get_age',
    python_callable=get_age
)
```

Now there are two tasks producing information:

```text
get_name ──┐
           ├──> greet
get_age  ──┘
```

### Update `greet()`

Since the age is now also coming from XCom, remove `age` from `op_kwargs`.

```python
def greet(ti):

    first_name = ti.xcom_pull(
        task_ids='get_name',
        key='first_name'
    )

    last_name = ti.xcom_pull(
        task_ids='get_name',
        key='last_name'
    )

    age = ti.xcom_pull(
        task_ids='get_age',
        key='age'
    )

    print(
        f"Hello world, my name is {first_name} {last_name}, "
        f"and I am {age} years old"
    )
```

### Set the dependencies

```python
[task2, task3] >> task1
```

This means both `task2` and `task3` must complete before `task1` runs.

The workflow is:

```text
             ┌──> get_name ──┐
             │                │
             │                v
             │              greet
             │                ^
             │                │
             └──> get_age ────┘
```

---

# Final Code So Far

```python
from airflow import DAG
from datetime import datetime, timedelta
from airflow.operators.python import PythonOperator


default_args = {
    'owner': 'hdu',
    'retries': 5,
    'retry_delay': timedelta(minutes=5)
}


def greet(ti):

    first_name = ti.xcom_pull(
        task_ids='get_name',
        key='first_name'
    )

    last_name = ti.xcom_pull(
        task_ids='get_name',
        key='last_name'
    )

    age = ti.xcom_pull(
        task_ids='get_age',
        key='age'
    )

    print(
        f"Hello world, my name is {first_name} {last_name}, "
        f"and I am {age} years old"
    )


def get_name(ti):

    ti.xcom_push(
        key='first_name',
        value='John'
    )

    ti.xcom_push(
        key='last_name',
        value='Morgan'
    )


def get_age(ti):

    ti.xcom_push(
        key='age',
        value=25
    )


with DAG(
    dag_id='sample_dag_with_python_operator_v4',
    description='Testing sample DAG with PythonOperator',
    default_args=default_args,
    start_date=datetime(2024, 11, 20, 2),
    schedule_interval='@daily'
) as dag:

    task1 = PythonOperator(
        task_id='greet',
        python_callable=greet
    )

    task2 = PythonOperator(
        task_id='get_name',
        python_callable=get_name
    )

    task3 = PythonOperator(
        task_id='get_age',
        python_callable=get_age
    )

    [task2, task3] >> task1
```

---

# Important Note About XCom Size

XCom is intended for **small amounts of data exchanged between tasks**.

Do not use XCom to pass large objects such as:

- Pandas DataFrames
- Large datasets
- Large files
- Other large data structures

For example, a Pandas DataFrame should generally **not** be passed directly through XCom.

Instead, store the larger data somewhere appropriate and use XCom to pass a small reference, such as:

```text
file path
database ID
object-storage key
URL
```
