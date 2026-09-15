# AIRFLOW NOTES 5
# Using the TaskFlow API

If you write most of your DAGs using plain Python code rather than Operators, the **TaskFlow API** can make it easier to author clean DAGs with less boilerplate by using the `@task` decorator.

TaskFlow takes care of moving inputs and outputs between tasks using XComs.

It can also automatically calculate dependencies. When you call a TaskFlow function inside your DAG file, the function is not executed immediately in the normal way. Instead, you get an object representing the XCom result, called an **XComArg**.

This XComArg can then be used as input to downstream tasks or operators.

Basic flow:

```text
Task 1
  |
  | returns a value
  v
XCom / XComArg
  |
  | automatically passed as input
  v
Task 2
```
This builds on the XCom concepts covered in **Airflow Notes 4**, but allows us to write the DAG in a cleaner and more Pythonic way.

---

# EX1: Basic TaskFlow API

```python
from airflow import DAG
from datetime import datetime, timedelta
from airflow.operators.python import PythonOperator
from airflow.decorators import dag, task


default_args = {
    'owner': 'hdu',
    'retries': 5,
    'retry_delay': timedelta(minutes=5)
}


@dag(
    dag_id='sample_dag_with_taskflow_api_v0',
    description='Testing sample DAG with TaskFlow API v0',
    default_args=default_args,
    start_date=datetime(2024, 11, 20),
    schedule_interval='@daily'
)
def new_etl():

    # Create 3 tasks

    @task()
    def get_name():
        return 'John'


    @task()
    def get_age():
        return 25


    @task()
    def greet(name, age):
        print(
            f"Hello world, my name is {name} "
            f"and I am {age} years old"
        )


    name = get_name()
    age = get_age()

    greet(
        name=name,
        age=age
    )


greet_dag = new_etl()
```

---

## Understanding the Flow

There are three tasks:

```text
get_name
get_age
greet
```

The flow is:

```text
get_name ──┐
           │
           v
         greet
           ^
           │
get_age ────┘
```

### Step 1: Get the name

```python
name = get_name()
```

The `get_name` task produces:

```text
John
```

The result can be passed to another TaskFlow task.

### Step 2: Get the age

```python
age = get_age()
```

The `get_age` task produces:

```text
25
```

### Step 3: Pass the results to `greet`

```python
greet(
    name=name,
    age=age
)
```

The outputs of `get_name()` and `get_age()` are used as inputs to the downstream `greet()` task.

This also defines the dependency:

```text
get_name ──┐
           ├──> greet
get_age ───┘
```

---

# EX2: Returning Multiple Outputs

Now change the name task so that it returns:

- First name
- Last name

Change the DAG version:

```python
dag_id='sample_dag_with_taskflow_api_v1'
```

Use `multiple_outputs=True` with the `@task` decorator.

```python
from airflow import DAG
from datetime import datetime, timedelta
from airflow.operators.python import PythonOperator
from airflow.decorators import dag, task


default_args = {
    'owner': 'hdu',
    'retries': 5,
    'retry_delay': timedelta(minutes=5)
}


@dag(
    dag_id='sample_dag_with_taskflow_api_v1',
    description='Testing sample DAG with TaskFlow API',
    default_args=default_args,
    start_date=datetime(2024, 11, 20),
    schedule_interval='@daily'
)
def new_etl():

    # Create 3 tasks

    @task(multiple_outputs=True)
    def get_name():
        return {
            'first_name': 'John',
            'last_name': 'Morgan'
        }


    @task()
    def get_age():
        return 25


    @task()
    def greet(first_name, last_name, age):
        print(
            f"Hello world, my name is {first_name} {last_name} "
            f"and I am {age} years old"
        )


    name_dict = get_name()
    age = get_age()

    greet(
        first_name=name_dict['first_name'],
        last_name=name_dict['last_name'],
        age=age
    )


greet_dag = new_etl()
```

---

## Understanding `multiple_outputs=True`

The `get_name()` task returns a dictionary:

```python
{
    'first_name': 'John',
    'last_name': 'Morgan'
}
```

The returned values can then be accessed using their keys:

```python
name_dict['first_name']
```

and:

```python
name_dict['last_name']
```

These values are then passed to the `greet()` task:

```python
greet(
    first_name=name_dict['first_name'],
    last_name=name_dict['last_name'],
    age=age
)
```

The workflow is:

```text
              ┌── first_name ──┐
get_name ──────┤                │
              └── last_name ───┤
                               v
                             greet
                               ^
                               |
get_age ────────────────────────┘
```

---

# Key Points

### `@dag`

The `@dag` decorator is used to define the DAG.

Example:

```python
@dag(
    dag_id='sample_dag_with_taskflow_api_v0'
)
def new_etl():
    ...
```

---

### `@task`

The `@task` decorator converts a Python function into an Airflow task.

Example:

```python
@task()
def get_name():
    return 'John'
```

---

### Passing Task Results

A task result can be used as an input to another task:

```python
name = get_name()

greet(name=name, age=age)
```

This allows TaskFlow to manage the movement of task inputs and outputs using XComs.

---

### Dependencies

Dependencies are automatically determined when the output of one TaskFlow task is used as the input of another task.

For example:

```python
name = get_name()
age = get_age()

greet(name=name, age=age)
```

The resulting dependency is:

```text
get_name ──┐
           ├──> greet
get_age ───┘
```
