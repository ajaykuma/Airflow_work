## Notes 8.1 — Understanding `start_date` and `execution_date` / `logical_date`

### 1. Understanding `start_date`

Suppose we have a DAG that should run every day at midnight:

```python
import datetime as dt
from airflow import DAG

dag = DAG(
    dag_id="sample_dag",
    schedule_interval="@daily",
    start_date=dt.datetime(2024, 11, 20),
)
```

### When will the DAG tasks run?

Airflow does **not** immediately run the DAG at its `start_date`.

For a scheduled DAG, Airflow runs the tasks **after the scheduled interval has finished**.

For a daily DAG:

```text
20-Nov 00:00
    |
    |     Data interval
    |
21-Nov 00:00
    |
    ↓
DAG run starts
```

Therefore, the first run represents the interval beginning on **20-Nov-2024**, but the tasks run after that interval has ended.

---

### 2. Why does Airflow work this way?

This behavior is useful for data pipelines.

Suppose we want to ingest all the data for:

```text
20-Nov-2024
```

The complete data may not be available at the beginning of the day.

Instead, the DAG can wait until the daily interval has finished:

```text
20-Nov
│
├── Data is generated throughout the day
│
└── 21-Nov 00:00
       ↓
    DAG runs
       ↓
    Process 20-Nov data
```

This allows the DAG to process a **completed data interval**.

---

### 3. `catchup=False`

By default, Airflow can create runs for unexecuted intervals between the DAG's `start_date` and the current date.

For example:

```python
dag = DAG(
    dag_id="sample_dag",
    schedule_interval="@daily",
    start_date=dt.datetime(2024, 11, 19),
    catchup=False,
)
```

The important setting is:

```python
catchup=False
```

This prevents Airflow from creating all the historical scheduled runs that were missed.

### Concept

```text
start_date in the past
        +
catchup=True
        ↓
Airflow may create historical runs
```

Whereas:

```text
start_date in the past
        +
catchup=False
        ↓
Historical catchup runs are not created
```

---

### 4. Can we automatically set `start_date` to today?

It may seem convenient to write:

```python
start_date=dt.datetime.today()
```

However, Airflow recommends avoiding a **dynamic `start_date`**.

The problem is that `today()` is not necessarily midnight.

For example:

```text
20-Nov-2024 13:45:32
```

If the DAG definition is repeatedly evaluated, the `start_date` can continue moving forward.

For a daily DAG:

```text
start_date + daily interval
```

could therefore remain in the future.

### Better approach

Use a fixed date:

```python
start_date=dt.datetime(2024, 11, 20)
```

and use:

```python
catchup=False
```

when historical runs are not required.

---

## 5. Understanding `execution_date`

Older Airflow material commonly uses:

```text
execution_date
```

In modern Airflow terminology, this is generally referred to as:

```text
logical_date
```

The logical date represents the **start of the data interval**, rather than the actual clock time when the DAG starts executing.

---

### 6. Example

```python
import datetime as dt

from airflow import DAG
from airflow.operators.python import PythonOperator

dag = DAG(
    dag_id="sample_dag",
    schedule_interval="@daily",
    start_date=dt.datetime(2024, 11, 20),
)


def _print_execution_date(ds):
    print(f"The execution date of this flow is {ds}")


print_dag = PythonOperator(
    task_id="print_task",
    python_callable=_print_execution_date,
    dag=dag,
)
```

### What date will be printed during the first run?

The first scheduled run corresponds to the interval beginning on:

```text
20-Nov-2024
```

Therefore:

```text
logical_date = 2024-11-20
```

The important distinction is:

```text
logical_date
     ≠
actual execution time
```

For example:

```text
Logical date:       20-Nov-2024 00:00
                         |
                         | data interval
                         ↓
DAG actually runs:  21-Nov-2024 00:00
```

---

## 7. `start_date` vs `logical_date`

These concepts are related but different.

### `start_date`

`start_date` is defined in the DAG:

```python
start_date=dt.datetime(2024, 11, 20)
```

It establishes when scheduling should begin.

It is part of the DAG definition and remains constant.

### `logical_date`

The `logical_date` belongs to an individual DAG run.

For a daily DAG, the value changes for every run:

```text
Run 1 → logical_date = 2024-11-20
Run 2 → logical_date = 2024-11-21
Run 3 → logical_date = 2024-11-22
Run 4 → logical_date = 2024-11-23
```

Therefore:

```text
start_date
    ↓
Defines when scheduling begins

logical_date
    ↓
Identifies the interval represented by a particular DAG run
```

---

## 8. Why is this important?

This distinction becomes very important when creating dependencies between DAGs or when processing time-based data.

For example:

```text
Data interval:
20-Nov → 21-Nov

DAG execution:
21-Nov 00:00

logical_date:
20-Nov
```

Therefore, be careful when using dates and times to create dependencies or determine which data should be processed.

### Key point

> The logical date of a DAG run is not necessarily the actual time at which the DAG runs.

---

## 9. Important terms

| Term | Meaning |
|---|---|
| `start_date` | Defines the beginning of the DAG's scheduling period |
| `schedule_interval` | Defines how frequently the DAG is scheduled |
| Data interval | Period of data represented by a DAG run |
| `execution_date` | Older Airflow terminology |
| `logical_date` | Modern terminology for the DAG run's logical date |
| `catchup=False` | Prevents creation of historical catchup runs |

---

## 10. Mental model

The easiest way to remember this is:

```text
              start_date
                  ↓
          Scheduling begins
                  ↓
            Data interval
                  ↓
             Interval ends
                  ↓
             DAG runs
                  ↓
          logical_date
       identifies the interval
```

### Most important rule

```text
start_date
    = when scheduling starts

logical_date
    = which interval this DAG run represents

actual execution time
    = when the task really runs
```
