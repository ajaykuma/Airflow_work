# Notes 9 — Working with Sensors

## 1. What is a Sensor?

A **Sensor** in Apache Airflow is a special type of task that waits for a particular condition to become true before allowing the workflow to continue.

For example, a sensor can wait for:

- A specific time to arrive
- A certain amount of time to pass
- A task in another DAG to finish
- A file to appear
- An external event or condition

The basic idea is:

```text
Sensor
   │
   │ condition not satisfied
   ↓
   Wait
   │
   │ condition satisfied
   ↓
Next task
```

Some commonly used sensors include:

```text
ExternalTaskSensor
TimeSensor
TimeSensorAsync
TimeDeltaSensor
TimeDeltaSensorAsync
FileSensor
```

---

# 2. Sensor Modes

Sensors can potentially wait for a long period of time.

One important concept is the difference between a sensor that continuously occupies a worker slot and an asynchronous/rescheduling approach that allows the worker slot to be released while waiting.

For example:

```python
mode='reschedule'
```

means that when the condition is not satisfied, the sensor can give up its worker slot and be checked again later.

Conceptually:

```text
Without reschedule:

Worker
  │
  ├── Sensor waiting
  │
  ├── Sensor waiting
  │
  └── Sensor succeeds
       ↓
     Worker slot occupied
```

With rescheduling:

```text
Worker
  │
  ├── Sensor checks condition
  │
  └── Worker slot released
          ↓
       wait
          ↓
    Sensor checked again
          ↓
       succeeds
```

This becomes especially important when a sensor may wait for a long time.

---

# 3. Triggerer

The **Triggerer** was introduced in Apache Airflow 2.2.0.

It is designed to handle long-running asynchronous tasks more efficiently.

For example:

```text
TimeSensorAsync
```

can wait for a long period without continuously occupying a normal worker slot.

The Triggerer is responsible for running asynchronous triggers and allowing deferrable tasks to wait efficiently.

Conceptually:

```text
                 Scheduler
                     │
                     ↓
                   Task
                     │
                     ↓
              Async / Deferrable
                     │
                     ↓
                 Triggerer
                     │
                     │ waits for event
                     ↓
              Condition satisfied
                     │
                     ↓
                  Worker
                     │
                     ↓
                Task continues
```

### Triggerer configuration

Your original material refers to Triggerer-related configuration such as:

```ini
[scheduler]
triggerer_instances = 2
triggerer_timeout = 300
```

The important idea is that the Triggerer provides infrastructure for efficiently handling asynchronous waiting.

---

# 4. TimeDeltaSensor

The `TimeDeltaSensor` waits for a specified amount of time to pass before succeeding.

The sensor takes a `delta` parameter.

`delta` is a Python `datetime.timedelta` object.

For example:

```python
from datetime import timedelta

from airflow import DAG
from airflow.sensors.time_delta import TimeDeltaSensor
from airflow.utils.dates import days_ago

with DAG(
    'my_dag',
    start_date=days_ago(2)
) as dag:

    wait_5_minutes = TimeDeltaSensor(
        task_id='wait_5_minutes',
        delta=timedelta(minutes=5),
    )
```

Here:

```python
delta=timedelta(minutes=5)
```

means that the sensor waits for **5 minutes** before succeeding.

### Concept

```text
Sensor starts
     │
     ↓
 Wait 5 minutes
     │
     ↓
Sensor succeeds
     │
     ↓
Next task
```

Make sure that the value passed to `delta` represents the amount of time that you actually want the sensor to wait.

---

# 5. TimeDeltaSensorAsync

`TimeDeltaSensorAsync` is an asynchronous version of the time-delta sensor.

It waits for a specified time delta before succeeding, while using asynchronous/deferrable execution so that a worker slot does not need to remain occupied during the waiting period.

Example:

```python
from datetime import timedelta

from airflow.decorators import dag, task
from airflow.sensors.time_delta import TimeDeltaSensorAsync
from airflow.utils.dates import days_ago


@dag(
    schedule_interval='@daily',
    start_date=days_ago(2),
    catchup=False
)
def my_dag():

    wait = TimeDeltaSensorAsync(
        task_id='wait',
        delta=timedelta(minutes=30),
        mode='reschedule',
    )

    @task
    def the_task():
        print("Task executed.")

    the_task(wait)


dag = my_dag()
```

The idea is:

```text
DAG starts
    ↓
TimeDeltaSensorAsync
    ↓
Wait 30 minutes
    ↓
the_task()
```

So `the_task` executes after the required time has passed.

---

# 6. TimeSensor

The `TimeSensor` waits until a particular time of day is reached.

For example:

```python
from datetime import time

from airflow.decorators import dag, task
from airflow.sensors.time_sensor import TimeSensor
from airflow.utils.dates import days_ago


@dag(
    dag_id='sample_dag_with_timeSensor_v0',
    schedule_interval='@daily',
    start_date=days_ago(5),
    catchup=False
)
def my_dag():

    wait = TimeSensor(
        task_id='wait',
        target_time=time(hour=12, minute=45),
        mode='reschedule',
    )

    @task
    def the_task():
        print("Task executed.")

    the_task(wait)


dag = my_dag()
```

The important parameter is:

```python
target_time=time(hour=12, minute=45)
```

The sensor waits until **12:45**.

Conceptually:

```text
DAG starts
    ↓
TimeSensor
    ↓
Wait until 12:45
    ↓
Sensor succeeds
    ↓
the_task()
```

---

# 7. TimeSensorAsync

`TimeSensorAsync` provides an asynchronous way of waiting until a particular time.

Example:

```python
from datetime import time

from airflow.decorators import dag, task
from airflow.sensors.time_sensor import TimeSensorAsync
from airflow.utils.dates import days_ago


@dag(
    dag_id='sample_dag_with_timeSensor_v0',
    schedule_interval='@daily',
    start_date=days_ago(5),
    catchup=False
)
def my_dag():

    wait = TimeSensorAsync(
        task_id='wait',
        target_time=time(hour=12, minute=45),
    )

    @task
    def the_task():
        print("Task executed.")

    the_task(wait)


dag = my_dag()
```

The workflow is:

```text
DAG
 │
 ↓
TimeSensorAsync
 │
 │ Wait until 12:45
 ↓
the_task()
```

The key difference is that the asynchronous version is designed to avoid unnecessarily occupying a normal worker while waiting.

---

# 8. ExternalTaskSensor

The `ExternalTaskSensor` is used when one DAG needs to wait for a task or DAG run from another DAG.

This is useful when there are dependencies between separate DAGs.

For example:

```text
DAG 1
  │
  └── greet
        │
        │ completed
        ↓
DAG 2
  │
  └── ExternalTaskSensor
        │
        ↓
     final task
```

The second DAG waits for a task in the first DAG.

---

# 9. Example — DAG 1

The first DAG contains a task called:

```text
greet
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


def greet(age, ti):
    name = ti.xcom_pull(task_ids='get_name')

    print(
        f"Hello world, my name is {name}, "
        f"and I am {age} years old"
    )


def get_name():
    return 'John'


with DAG(
    dag_id='sample_dag1_for_cross_dag_chk_v0',
    description='Testing sample dag with python operator',
    default_args=default_args,
    schedule_interval=None
) as dag:

    task1 = PythonOperator(
        task_id='greet',
        python_callable=greet,
        op_kwargs={'age': 25}
    )

    task2 = PythonOperator(
        task_id='get_name',
        python_callable=get_name,
    )

    task2 >> task1
```

The dependency inside DAG 1 is:

```text
get_name
    ↓
greet
```

---

# 10. Example — DAG 2

DAG 2 depends on the `greet` task in DAG 1.

```python
from airflow import DAG
from datetime import datetime, timedelta

from airflow.operators.bash import BashOperator
from airflow.sensors.external_task import ExternalTaskSensor


default_args = {
    'owner': 'hdu',
    'retries': 5,
    'retry_delay': timedelta(minutes=5)
}


dag = DAG(
    dag_id='sample_dag2_for_cross_dag_chk_v1',
    description='Testing cross DAG dependency',
    default_args=default_args,
    start_date=datetime(2024, 11, 20),
    schedule_interval='@daily'
)


wait_for_other_dag_task = ExternalTaskSensor(
    task_id='task2_sample_dag2_for_cross_dag_chk_v1',

    external_dag_id='sample_dag1_for_cross_dag_chk_v0',

    external_task_id='greet',

    execution_date_fn=lambda dt: dt,

    dag=dag
)


check_compl = BashOperator(
    task_id='fnl_tsk',
    bash_command='echo cross dependency validation done',
    dag=dag
)


wait_for_other_dag_task >> check_compl
```

The important parameters are:

```python
external_dag_id='sample_dag1_for_cross_dag_chk_v0'
```

This identifies the DAG that we are waiting for.

And:

```python
external_task_id='greet'
```

This identifies the task inside that DAG.

Therefore:

```text
sample_dag2
     │
     ↓
ExternalTaskSensor
     │
     │ waits for
     ↓
sample_dag1.greet
     │
     │ completed
     ↓
ExternalTaskSensor succeeds
     │
     ↓
fnl_tsk
```

---

# 11. Important point about dates and ExternalTaskSensor

When using `ExternalTaskSensor`, be careful about dates and scheduling.

For example:

```python
execution_date_fn=lambda dt: dt
```

means the sensor is looking for the corresponding logical date.

This becomes particularly important when the two DAGs have different schedules.

Remember the concept from Notes 8.1:

```text
logical_date
     ≠
actual execution time
```

Therefore, when creating cross-DAG dependencies, always think about **which data interval/logical date the dependency should refer to**.

---

# 12. FileSensor

Another common sensor is the `FileSensor`.

It waits for a file to appear before allowing downstream tasks to execute.

Example:

```python
from airflow import DAG
from airflow.sensors.filesystem import FileSensor
from airflow.utils.dates import days_ago


with DAG(
    'dag_sensor',
    schedule_interval='@daily',
    start_date=days_ago(2),
    catchup=False,
) as dag:

    waiting_for_file = FileSensor(
        task_id='waiting_for_file',
        poke_interval=30,
        timeout=60 * 5,
        mode='reschedule',
        soft_fail=False
    )
```

The important parameters are:

```python
poke_interval=30
```

The sensor checks the condition every 30 seconds.

```python
timeout=60 * 5
```

The sensor times out after 5 minutes.

```python
mode='reschedule'
```

The sensor can release its worker slot between checks.

```python
soft_fail=False
```

If the sensor ultimately fails, the task is treated as a failure rather than being marked as skipped.

### Concept

```text
             FileSensor
                  │
          Does file exist?
             /         \
           No           Yes
           │             │
       Wait 30 sec       ↓
           │          Success
           ↓             │
      Check again        ↓
                     Next task
```

The file path/connection configuration needs to be provided according to the filesystem sensor setup.

---

# 13. Sensor comparison

| Sensor | Waits for |
|---|---|
| `TimeSensor` | A specific time of day |
| `TimeSensorAsync` | A specific time of day asynchronously |
| `TimeDeltaSensor` | A specified amount of time |
| `TimeDeltaSensorAsync` | A specified amount of time asynchronously |
| `ExternalTaskSensor` | A task/DAG run from another DAG |
| `FileSensor` | A file/condition on the filesystem |

---

# 14. Sensors vs normal tasks

A normal task generally does some work:

```text
PythonOperator
     ↓
Do something
     ↓
Finish
```

A sensor primarily waits for a condition:

```text
Sensor
   ↓
Condition satisfied?
   │
   ├── No → Wait/check again
   │
   └── Yes → Continue
```

This is why sensor efficiency is important.

If a sensor waits for several hours, keeping a worker occupied for the entire period can waste resources.

This is where **reschedule mode** and **asynchronous/deferrable execution** become useful.

---

# 15. Key Takeaways

### Sensors

Sensors wait for a condition before allowing the workflow to continue.

### TimeSensor

Waits until a particular time:

```python
target_time=time(hour=12, minute=45)
```

### TimeDeltaSensor

Waits for a specified duration:

```python
delta=timedelta(minutes=5)
```

### ExternalTaskSensor

Waits for a task or DAG run from another DAG:

```python
external_dag_id='sample_dag1'
external_task_id='greet'
```

### FileSensor

Waits for a file/condition to become available.

### `mode='reschedule'`

Allows a sensor to release its worker slot while waiting between checks.

### Async / Deferrable execution

Uses Airflow's Triggerer infrastructure to handle long waits more efficiently.

---

# 16. Overall mental model

```text
                         SENSOR
                            │
             ┌──────────────┼──────────────┐
             ↓              ↓              ↓
          TIME           EXTERNAL         FILE
             │              │              │
             ↓              ↓              ↓
       TimeSensor      ExternalTask     FileSensor
             │            Sensor            │
             ↓              ↓              ↓
       Wait for time    Wait for task   Wait for file
             │              │              │
             └──────────────┼──────────────┘
                            ↓
                     Condition met
                            ↓
                      Next task runs
```

For long-running asynchronous waits:

```text
Sensor
  │
  ↓
Triggerer
  │
  │ waits efficiently
  ↓
Condition satisfied
  │
  ↓
Task resumes
```

### Main concept to remember

> **A sensor does not primarily perform work; it waits for something to become true.**