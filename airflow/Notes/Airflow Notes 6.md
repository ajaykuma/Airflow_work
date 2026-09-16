## AIRFLOW NOTES 6

## DAG with Catchup and Backfill

In this section, we will work with:

1. Catchup
2. Backfill
3. Scheduling using cron expressions
4. Airflow scheduling presets

---

## EX1: DAG with Catchup Enabled

```python
from airflow import DAG
from datetime import datetime, timedelta
from airflow.decorators import dag, task
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator


default_args = {
    'owner': 'hdu',
    'retries': 5,
    'retry_delay': timedelta(minutes=5)
}


with DAG(
    dag_id='dag_with_catchup_n_backfill_v0',
    default_args=default_args,
    start_date=datetime(2024, 11, 19),
    schedule_interval='@daily',
    catchup=True
) as dag:

    task1 = BashOperator(
        task_id='task1',
        bash_command='echo testing'
    )


task1
```

---

### Catchup

In the above DAG:

```python
catchup=True
```

The DAG has a:

```python
start_date=datetime(2024, 11, 19)
```

and runs:

```python
schedule_interval='@daily'
```

The `catchup` parameter is enabled:

```python
catchup=True
```

Test the DAG and observe its behavior.

---

## EX2: Disable Catchup

Now check the behavior by changing the `catchup` value to:

```python
catchup=False
```

Also change the DAG ID so that this can be tested as a separate version:

```python
dag_id='dag_with_catchup_n_backfill_v1'
```

The relevant DAG configuration becomes:

```python
with DAG(
    dag_id='dag_with_catchup_n_backfill_v1',
    default_args=default_args,
    start_date=datetime(2024, 11, 19),
    schedule_interval='@daily',
    catchup=False
) as dag:
    ...
```

Test the DAG and compare the behavior with the previous example.

After testing, set it back to:

```python
catchup=True
```

for the following backfill experiment.

---

## EX3: Using Backfill

Backfill can be run using an Airflow command.

While working with the DAG, use:

```bash
airflow dags backfill -s 2024-1-10 -e 2024-1-15 <dagid>
```

Where:

```text
-s        Start date
-e        End date
<dagid>   DAG ID
```

Example structure:

```text
airflow dags backfill
        |
        ├── Start date
        ├── End date
        └── DAG ID
```

```
This allows the DAG to be run for the specified date range.
If DAG runs existed,we can see something interesting in CLI/UI
CLI- airflow dags list-runs -d dag_with_catchup_backfill

When DAG runs existed, the same logical-date run was picked up and executed as a backfill,
which means Airflow says-> Give me the DAG runs for this historical period
and executes them as a backfill, instead of separate duplicate runs

For example:
(my-venv) hdu@m2:~/airflow/dags$ airflow dags list-runs -d dag_with_catchup_backfill
dag_id              | run_id             | state   | execution_date     | start_date         | end_date
====================+====================+=========+====================+====================+====================
dag_with_catchup_ba | scheduled__2026-09 | success | 2026-09-11T00:00:0 | 2026-09-15T23:05:0 | 2026-09-15T23:05:09
ckfill              | -11T00:00:00+00:00 |         | 0+00:00            | 6.738652+00:00     | .084434+00:00
dag_with_catchup_ba | scheduled__2026-09 | success | 2026-09-09T00:00:0 | 2026-09-15T23:05:0 | 2026-09-15T23:05:09
ckfill              | -09T00:00:00+00:00 |         | 0+00:00            | 6.652532+00:00     | .078217+00:00
dag_with_catchup_ba | scheduled__2026-09 | success | 2026-09-07T00:00:0 | 2026-09-15T23:05:0 | 2026-09-15T23:05:09
ckfill              | -07T00:00:00+00:00 |         | 0+00:00            | 6.585462+00:00     | .071851+00:00
dag_with_catchup_ba | scheduled__2026-09 | success | 2026-09-04T00:00:0 | 2026-09-15T23:12:0 | 2026-09-15T23:12:08
ckfill              | -04T00:00:00+00:00 |         | 0+00:00            | 3.506912+00:00     | .317118+00:00
dag_with_catchup_ba | scheduled__2026-09 | success | 2026-09-02T00:00:0 | 2026-09-15T23:12:0 | 2026-09-15T23:12:08
ckfill              | -02T00:00:00+00:00 |         | 0+00:00            | 3.483156+00:00     | .313691+00:00

in UI: Look at Run Type before and after Backfill and look at timestamp in Start and End Date.
```
---

# DAG Scheduling with Cron Expressions

The `schedule_interval` parameter can receive:

- A cron expression as a string
- A `datetime.timedelta` object

Example:

```python
schedule_interval='0 0 * * *'
```

or:

```python
schedule_interval='@daily'
```

---

# Understanding a Cron Expression

A standard cron expression contains five fields.

Example:

```text
15  14  1  *  *
```

The fields represent:

```text
MINUTE  HOUR  DAY-OF-MONTH  MONTH  DAY-OF-WEEK
  15      14       1          *        *
```

This can be represented as:

```text
15  14  1  *  *
│   │   │  │  │
│   │   │  │  └── Day of week
│   │   │  └───── Month
│   │   └──────── Day of month
│   └──────────── Hour
└──────────────── Minute
```

---

## Important Note

Use:

```python
schedule_interval=None
```

and **not**:

```python
schedule_interval='None'
```

when you do not want to schedule the DAG.

---

# Scheduling Presets

Airflow provides scheduling presets.

### `None`

```text
None
```

Do not schedule the DAG. This can be used for exclusively externally triggered DAGs.

---

### `@once`

```text
@once
```

Schedule once and only once.

---

### `@hourly`

```text
@hourly
```

Run once every hour at the beginning of the hour.

Equivalent cron expression:

```text
0 * * * *
```

---

### `@daily`

```text
@daily
```

Run once a day at midnight.

Equivalent cron expression:

```text
0 0 * * *
```

---

### `@weekly`

```text
@weekly
```

Run once a week at midnight on Sunday morning.

Equivalent cron expression:

```text
0 0 * * 0
```

---

### `@monthly`

```text
@monthly
```

Run once a month at midnight on the first day of the month.

Equivalent cron expression:

```text
0 0 1 * *
```

---

### `@yearly`

```text
@yearly
```

Run once a year at midnight on January 1.

Equivalent cron expression:

```text
0 0 1 1 *
```

---

# EX4: Creating a DAG Using a Cron Expression

```python
from airflow import DAG
from datetime import datetime, timedelta
from airflow.decorators import dag, task
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator


default_args = {
    'owner': 'hdu',
    'retries': 5,
    'retry_delay': timedelta(minutes=5)
}


with DAG(
    dag_id='dag_with_cron_v0',
    default_args=default_args,
    start_date=datetime(2024, 1, 26),
    schedule_interval='0 0 * * *'
    # schedule_interval='@daily'
) as dag:

    task1 = BashOperator(
        task_id='task1',
        bash_command='echo testing cron expression'
    )


task1
```

The cron expression:

```text
0 0 * * *
```

represents:

```text
Every day at 00:00
```

This can also be represented using:

```python
schedule_interval='@daily'
```

---

# Other Cron Examples

## Run at 3 AM every Tuesday and Friday

```python
schedule_interval='0 3 * * Tue,Fri'
```

Cron breakdown:

```text
0   3   *   *   Tue,Fri
│   │   │   │      │
│   │   │   │      └── Tuesday and Friday
│   │   │   └───────── Every month
│   │   └───────────── Every day of the month
│   └───────────────── 3 AM
└───────────────────── Minute 0
```

Therefore, the DAG is scheduled to run:

```text
Every Tuesday and Friday at 3:00 AM
```
## Run every 15 minutes and system tasks
dag_file_disk_check.py

This uses BashOperator to:
Check how many .py files exist in your DAG directory.
List those files.
Check root filesystem disk usage.
Print a warning if usage exceeds 80%.

## Run 9 am and 6 pm every day
dag_daily_report.py

This uses:
EmptyOperator → start/end markers
PythonOperator → generate a report
EmailOperator → send the report
cron → 09:00 and 18:00

For EmailOperator to actually send an email, we need an Airflow email/SMTP connection configured. Until then, the DAG may fail at the email task even though the PythonOperator works correctly.
