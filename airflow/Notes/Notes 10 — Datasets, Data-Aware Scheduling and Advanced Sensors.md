## Notes 10 — Datasets, Data-Aware Scheduling and Advanced Sensors

---

### 1. What are Datasets?

Until now, most of the DAG scheduling examples have been **time-based**:

```text
@daily
@hourly
cron expression
timedelta(...)
```

Airflow also supports **data-aware scheduling** through **Datasets**.

A Dataset represents some data that is produced or updated by an upstream task.

A downstream DAG can then be scheduled when that Dataset is updated.

This allows Airflow to express relationships such as:

```text
Data Engineering DAG
        |
        | produces/updates
        v
     Dataset
        |
        | triggers
        v
Machine Learning DAG
```

For example:

- A data engineering team produces `customer_data.csv`.
- A machine learning team trains a model using that data.
- The ML DAG does not need to run simply because it is 2:00 AM.
- Instead, it can run when the dataset has actually been updated.

Airflow introduced Dataset-based scheduling in **Airflow 2.4**.

---

## 2. Why use Datasets?

Datasets are useful when the availability of data is more important than a particular clock time.

### Without Datasets

A common approach is:

```text
Producer DAG
     |
     | ExternalTaskSensor
     v
Consumer DAG
```

The consumer has to wait for a task or DAG in another workflow.

### With Datasets

The relationship can instead be expressed directly:

```text
Producer Task
     |
     | updates Dataset
     v
Dataset
     |
     | schedules
     v
Consumer DAG
```

This provides several benefits:

### 2.1 Less code for cross-DAG dependencies

Instead of explicitly creating an `ExternalTaskSensor`, a producer can declare a Dataset as an outlet and the consumer can use the same Dataset in its schedule.

### 2.2 Better visibility

Airflow can display relationships between:

```text
DAG → Dataset → DAG
```

The Dataset View provides visibility into these relationships.

### 2.3 Data-aware scheduling

Traditional scheduling asks:

> "When should this DAG run?"

For example:

```text
Every day at midnight
Every hour
Every Monday
```

Dataset scheduling allows us to ask:

> "Has the data this DAG depends on been updated?"

This makes Airflow more **data-aware**.

### 2.4 Avoid unnecessary waiting tasks

A Dataset dependency is a scheduling relationship rather than a sensor task occupying a worker slot.

This can be useful compared with implementing every cross-DAG dependency using sensors.

---

## 3. Important Dataset terminology

There are several terms that are important to understand.

---

### 3.1 Dataset

A Dataset is an object representing a logical piece of data.

It is identified by a URI.

Example:

```python
from airflow.datasets import Dataset

my_dataset = Dataset("s3://my-bucket/customer_data.csv")
```

A Dataset does **not** mean that Airflow understands the contents of the file or database table.

Airflow treats the Dataset as a representation of the data dependency.

Airflow 2.8 allows valid URI-style identifiers as well as simpler strings. Dataset URIs must satisfy Airflow's URI restrictions.

### Important

Airflow does **not automatically inspect the underlying data**.

For example:

```python
Dataset("/home/hdu/airflow/configs/sample.txt")
```

does not mean Airflow automatically knows whether the file actually changed.

The DAG author declares that a particular task produces an update to that Dataset.

---

## 4. Dataset Event

A **Dataset Event** represents an update to a Dataset.

Conceptually:

```text
Producer task completes successfully
             |
             v
       Dataset updated
             |
             v
      Dataset Event
             |
             v
    Consumer DAG scheduled
```

A Dataset is therefore the object representing the data dependency, while a Dataset Event represents an occurrence/update of that Dataset.

A Dataset is marked as updated when the producer task completes successfully. If the producer fails or is skipped, the Dataset is not updated and the consumer DAG is not scheduled.

---

## 5. Producer Task

A **producer task** is a task that declares one or more Datasets in its `outlets`.

Example:

```python
@task(outlets=[my_dataset])
def produce_data():
    ...
```

or with a traditional operator:

```python
BashOperator(
    task_id="produce_data",
    bash_command="...",
    outlets=[my_dataset],
)
```

The important point is:

```text
outlets = Datasets produced/updated by the task
```

Airflow does not inspect the task's implementation to determine whether it really modified the underlying data.

If a task declares:

```python
outlets=[my_dataset]
```

Airflow treats that task as a producer for that Dataset.

---

## 6. Consumer DAG

A DAG can use a Dataset as its schedule.

Example:

```python
with DAG(
    dag_id="consumer",
    schedule=[my_dataset],
    start_date=datetime(2024, 11, 20),
    catchup=False,
):
    ...
```

Now the DAG is triggered by updates to the Dataset.

The basic relationship is:

```text
                 PRODUCER
                    |
                    v
              producer task
                    |
                 outlets
                    |
                    v
                Dataset
                    |
                schedule
                    |
                    v
                 CONSUMER
                    |
                    v
              consumer task
```

---

## 7. Outlets

`outlets` is a task parameter containing the Dataset or Datasets that a task updates.

Example:

```python
@task(outlets=[my_dataset])
def produce_data():
    ...
```

Think of it as:

```text
outlets = "What data does this task produce/update?"
```

A task can have multiple outlets:

```python
@task(
    outlets=[
        dataset_a,
        dataset_b,
    ]
)
def produce_multiple_datasets():
    ...
```

---

## 8. Inlets

`inlets` represents datasets that a task has access to.

Conceptually:

```text
outlets → data produced by a task

inlets  → data available to a task
```

Example:

```python
@task(inlets=[my_dataset])
def process_data():
    ...
```

An important distinction is that simply declaring an `inlet` does **not** schedule the DAG based on that Dataset.

For scheduling, the Dataset needs to be used in the DAG's `schedule`.

So:

```python
inlets=[my_dataset]
```

and:

```python
schedule=[my_dataset]
```

have different purposes.

---

## 9. Producer and Consumer Example

Let's build a simple example using a local file.

The Dataset will represent:

```text
/home/hdu/airflow/configs/sample.txt
```

First define the Dataset:

```python
from airflow.datasets import Dataset

my_file = Dataset(
    "/home/hdu/airflow/configs/sample.txt"
)
```

---

## 10. Producer DAG

The producer DAG updates the file.

```python
from datetime import datetime

from airflow import DAG
from airflow.decorators import task
from airflow.datasets import Dataset


my_file = Dataset(
    "/home/hdu/airflow/configs/sample.txt"
)


with DAG(
    dag_id="producer",
    schedule="@daily",
    start_date=datetime(2024, 11, 20),
    catchup=False,
):

    @task(outlets=[my_file])
    def the_task_update():

        with open(my_file.uri, "a+") as f:
            f.write("producer update\n")

    the_task_update()
```

The important part is:

```python
@task(outlets=[my_file])
```

This tells Airflow:

> When this task completes successfully, consider `my_file` updated.

---

## 11. Consumer DAG

The consumer DAG uses the same Dataset as its schedule.

```python
from datetime import datetime

from airflow import DAG
from airflow.decorators import task
from airflow.datasets import Dataset


my_file = Dataset(
    "/home/hdu/airflow/configs/sample.txt"
)


with DAG(
    dag_id="consumer",
    schedule=[my_file],
    start_date=datetime(2024, 11, 20),
    catchup=False,
):

    @task
    def the_task_read():

        with open(my_file.uri, "r") as f:
            print(f.read())

    the_task_read()
```

The important difference is:

```python
schedule=[my_file]
```

This tells Airflow:

> Schedule this DAG when `my_file` receives a Dataset update.

---

## 12. How the Producer and Consumer Work Together

The complete flow is:

```text
                 PRODUCER DAG
                      |
                      v
              the_task_update
                      |
                      | outlets=[my_file]
                      v
                +-----------+
                |  Dataset  |
                | my_file   |
                +-----------+
                      |
                      | Dataset Event
                      v
                 CONSUMER DAG
                      |
                      v
                the_task_read
```

### Execution sequence

Initially:

```text
Consumer DAG
     |
     | waiting for Dataset update
     v
No run
```

Then manually trigger or wait for the Producer DAG:

```text
Producer DAG
     |
     v
the_task_update
     |
     v
Dataset updated
     |
     v
Consumer DAG scheduled
     |
     v
the_task_read
```

This is the key idea behind data-aware scheduling.

---

## 13. Important Dataset Behavior

A Dataset update is created when the producer task **successfully completes**.

For example:

```text
Producer SUCCESS
       |
       v
Dataset updated
       |
       v
Consumer scheduled
```

But:

```text
Producer FAILED
       |
       v
No Dataset update
       |
       v
Consumer not triggered
```

Similarly:

```text
Producer SKIPPED
       |
       v
No Dataset update
```

This behavior is important when designing producer/consumer workflows.

---

## 14. Multiple Datasets

A DAG can depend on multiple Datasets.

Example:

```python
schedule=[
    dataset_a,
    dataset_b,
    dataset_c,
]
```

In Airflow 2.8, the consumer DAG is scheduled when **all** of its required Datasets have been updated at least once since its previous run.

Conceptually:

```text
Dataset A ──────┐
                |
Dataset B ──────┼──> Consumer DAG
                |
Dataset C ──────┘
```

The consumer waits until all required data dependencies have been satisfied.

---

## 15. Dataset vs ExternalTaskSensor

Both can implement relationships between workflows, but they express different ideas.

| Feature | ExternalTaskSensor | Dataset |
|---|---|---|
| Main idea | Wait for another task/DAG | Wait for data update |
| Relationship | Task → Task/DAG | Task → Dataset → DAG |
| Worker slot | Sensor may occupy/reschedule a worker slot | Dataset scheduling does not require a waiting task |
| Data-aware | No | Yes |
| UI relationship | Cross-DAG dependency | Dataset relationships |
| Best mental model | "Wait for that task" | "Run when this data is updated" |

This is one reason Datasets are useful for modern data pipelines.

---

## 16. Advanced Sensor Examples

The following examples continue the Sensor topic from Notes 9.

Sensors can monitor external systems such as:

```text
HTTP API
File system
Time
Another DAG
```

Airflow 2.8 includes `HttpSensor`, `FileSensor`, `ExternalTaskSensor`, `TimeSensor`, and `TimeDeltaSensor` among its sensor implementations.

---

## 17. HttpSensor

`HttpSensor` can repeatedly check an HTTP endpoint until the required condition is satisfied.

Imports:

```python
from airflow.providers.http.sensors.http import HttpSensor
from airflow.providers.http.operators.http import SimpleHttpOperator
```

Example:

```python
is_api_available = HttpSensor(
    task_id="is_api_available",
    http_conn_id="user_api",
    endpoint="/api",
    poke_interval=5,
    timeout=20,
)
```

Conceptually:

```text
HttpSensor
    |
    | check every 5 seconds
    v
HTTP API
    |
    +---- not ready ---> wait/check again
    |
    +---- ready -------> downstream task
```

---

## 18. SimpleHttpOperator

Once an API is available, `SimpleHttpOperator` can be used to make an HTTP request.

Example:

```python
from airflow.providers.http.operators.http import SimpleHttpOperator

extract_user = SimpleHttpOperator(
    task_id="extract_user",
    http_conn_id="user_api",
    endpoint="/api",
    method="GET",
    log_response=True,
)
```

A common pattern is:

```text
HttpSensor
     |
     | API available
     v
SimpleHttpOperator
     |
     v
Process API response
```

If a response needs to be converted into Python data, a response filter can be used.

For example:

```python
import json

extract_user = SimpleHttpOperator(
    task_id="extract_user",
    http_conn_id="user_api",
    endpoint="/api",
    method="GET",
    response_filter=lambda response: json.loads(response.text),
    log_response=True,
)
```

---

## 19. FileSensor

`FileSensor` waits for a file to become available.

Example:

```python
from airflow.sensors.filesystem import FileSensor

file_chk = FileSensor(
    task_id="is_file_available",
    fs_conn_id="file_path",
    filepath="mydata.csv",
    poke_interval=5,
    timeout=20,
)
```

Conceptually:

```text
FileSensor
     |
     v
Does mydata.csv exist?
     |
     +---- No ----> wait 5 seconds
     |                 |
     |                 v
     |              check again
     |
     +---- Yes ---> downstream task
```

---

## 20. FileSensor Connection

The filesystem connection provides the base path used by the sensor.

For example, configure a filesystem connection such as:

```text
Connection ID: file_path
Connection Type: File (path)
```

The path can then be supplied through the connection configuration.

The exact path configuration should match the filesystem layout of the machine running the sensor.

---

## 21. Sensor + Dataset Mental Model

Sensors and Datasets solve related but different problems.

### Sensor

```text
Something external must become ready
              |
              v
          Sensor waits
              |
              v
        Continue workflow
```

### Dataset

```text
Upstream task updates data
              |
              v
         Dataset Event
              |
              v
       Consumer DAG starts
```

So a useful rule is:

> **Sensor = wait for a condition.**

> **Dataset = schedule based on a data dependency.**

---

## 22. Key Takeaways

### Dataset

Represents a logical piece of data identified by a URI.

### Dataset Event

Represents an update to a Dataset.

### Producer

A task that declares a Dataset in `outlets`.

### Consumer

A DAG that uses a Dataset in its `schedule`.

### Outlets

Datasets produced/updated by a task.

### Inlets

Datasets available to a task.

### Data-aware scheduling

Allows DAGs to run based on Dataset updates instead of only time.

### Most important concept

```text
Task
 |
 | outlets
 v
Dataset
 |
 | schedule
 v
Consumer DAG
```

This is the core pattern to remember.

---

## 23. Overall Mental Model

At this point, Airflow scheduling can be understood in three ways:

```text
                 AIRFLOW SCHEDULING
                         |
          +--------------+--------------+
          |              |              |
          v              v              v
       TIME           CONDITION        DATA
          |              |              |
          v              v              v
     @daily /       Sensors /       Datasets
       cron          external
                     systems
```

This is an important progression from the earlier notes:

```text
Notes 6
Scheduling
    |
    v
Time-based scheduling

Notes 8
start_date / logical_date
    |
    v
Understanding scheduling dates

Notes 9
Sensors
    |
    v
Waiting for conditions

Notes 10
Datasets
    |
    v
Scheduling based on data updates
```

---

### Key Takeaway

Datasets allow Airflow to move from:

> **"Run this DAG at a particular time."**

to:

> **"Run this DAG when the data it depends on has been updated."**

That is the fundamental idea behind **data-aware scheduling**.
