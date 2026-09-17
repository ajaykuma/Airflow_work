## Notes 11 — Notifications, Callbacks and SLAs

---

## 1. Why Monitoring Matters

As Airflow workflows become more complex, simply creating DAGs and tasks is not enough.

We also need to know:

- Did a task fail?
- Did a task succeed?
- Should someone be notified?
- Did a task take longer than expected?
- Did the entire DAG complete successfully?
- What information is available when something fails?

Airflow provides several mechanisms for this:

```text
Notifications
Callbacks
Email
SLAs
Logging / Monitoring
```

These features help turn a DAG from a simple workflow into an observable production workflow.

---

## 2. Notifications in Airflow

Notifications allow Airflow to inform users or external systems about workflow events.

Common examples include:

```text
Task failed
Task succeeded
Task retried
DAG failed
DAG succeeded
SLA missed
```

Airflow provides built-in callback mechanisms such as:

```python
on_success_callback
on_failure_callback
on_retry_callback
```

and SLA-related callbacks.

Airflow also provides built-in email notification functionality and an extensible notification/notifier system.

---

## 3. Callback

A callback is a Python function that Airflow invokes when a particular event occurs.

For example:

```python
def custom_failure_function(context):
    print("Task failed")
```

The callback can then be attached to a task:

```python
task = PythonOperator(
    task_id="my_task",
    python_callable=my_function,
    on_failure_callback=custom_failure_function,
)
```

Conceptually:

```text
Task executes
     |
     v
Task fails
     |
     v
on_failure_callback
     |
     v
custom Python function
```

---

## 4. Important Callback Types

Some commonly used task callback types are:

| Callback | When it runs |
|---|---|
| `on_success_callback` | Task succeeds |
| `on_failure_callback` | Task fails |
| `on_retry_callback` | Task is being retried |
| `on_execute_callback` | Immediately before task execution |
| `sla_miss_callback` | SLA is missed |

Airflow 2.7 documentation also notes that callbacks are executed when task state changes through worker execution; state changes made directly through the CLI/UI do not invoke task callbacks in the same way.

---

## 5. Example — Failure and Success Notifications

A simple example:

```python
from datetime import datetime

from airflow import DAG
from airflow.operators.empty import EmptyOperator


def custom_failure_function(context):
    print("A task has failed")
    print("Task:", context["task_instance"].task_id)


def custom_success_function(context):
    print("A task has succeeded")
    print("Task:", context["task_instance"].task_id)


with DAG(
    dag_id="sample_dag_notifications",
    start_date=datetime(2024, 11, 20),
    schedule="@daily",
    catchup=False,
):

    failure_task = EmptyOperator(
        task_id="failure_task",
        on_failure_callback=custom_failure_function,
    )

    success_task = EmptyOperator(
        task_id="success_task",
        on_success_callback=custom_success_function,
    )
```

The important concept is not the `EmptyOperator`.

It is the callback:

```python
on_failure_callback=...
```

or:

```python
on_success_callback=...
```

---

## 6. Understanding the `context`

A callback receives an Airflow context.

Example:

```python
def custom_failure_function(context):

    task_instance = context["task_instance"]

    print("DAG:", task_instance.dag_id)
    print("Task:", task_instance.task_id)
```

The context contains information about the current execution.

This allows callback functions to create useful messages such as:

```text
DAG: sample_dag
Task: extract_data
Run ID: ...
Logical Date: ...
```

The context is especially useful when building custom notification systems.

---

## 7. DAG-Level Callbacks

Callbacks can also be associated with the DAG itself.

For example:

```python
with DAG(
    dag_id="sample_dag",
    start_date=datetime(2024, 11, 20),
    schedule="@daily",
    catchup=False,
    on_failure_callback=custom_failure_function,
):
    ...
```

This allows the callback to react to DAG-level state changes.

A useful distinction is:

```text
Task callback
      |
      v
Specific task event

DAG callback
      |
      v
DAG-level event
```

---

## 8. Example Using XCom + Callbacks

Callbacks can also exist alongside normal task logic and XComs.

For example:

```python
def calculating(ti):

    num1 = ti.xcom_pull(
        task_ids="get_num",
        key="first_num"
    )

    print(num1 * 100)


def get_num(ti):

    ti.xcom_push(
        key="first_num",
        value=25
    )
```

Then:

```python
task3 = PythonOperator(
    task_id="get_num",
    python_callable=get_num,
)

task2 = PythonOperator(
    task_id="calculating",
    python_callable=calculating,
)
```

The dependency:

```text
get_num
   |
   | XCom
   v
calculating
   |
   v
success_task
```

can be combined with:

```python
on_failure_callback=...
```

or:

```python
on_success_callback=...
```

This demonstrates that monitoring functionality can be added without changing the fundamental task dependency structure.

---

## 9. Email Notifications

Airflow also supports email notifications.

A simplified configuration can include:

```python
default_args = {
    "owner": "hdu",
    "start_date": datetime(2024, 11, 20),
    "email_on_failure": True,
    "email": ["noreply@example.com"],
    "retries": 1,
}
```

For example:

```python
with DAG(
    dag_id="sample_dag_email",
    default_args=default_args,
    schedule="@daily",
    catchup=False,
):
    ...
```

If a task fails, Airflow can send an email when email notification is configured appropriately.

---

## 10. SMTP Configuration

For email notifications to work, Airflow needs access to an SMTP server.

Conceptually:

```text
Airflow
   |
   v
SMTP Server
   |
   v
Email recipient
```

Configuration depends on the SMTP server being used.

Typical configuration concepts include:

```text
SMTP host
SMTP port
TLS / SSL settings
Sender email
Authentication
```

The important point is:

> Setting `email_on_failure=True` alone does not magically send email. Airflow must also be configured to communicate with an SMTP service.

---

## 11. Notifications vs Callbacks

These concepts are related but should not be confused.

### Callback

A callback is a Python function executed because a particular Airflow event occurred.

Example:

```python
on_failure_callback=my_function
```

### Notification

A notification is the actual communication sent to a user or external system.

For example:

```text
Task failed
    |
    v
Callback
    |
    v
Slack / Email / PagerDuty / etc.
```

Airflow 2.8 also has an extensible Notifier framework for implementing reusable notification mechanisms.

---

## 12. What is an SLA?

SLA stands for:

> **Service Level Agreement**

In Airflow, an SLA represents an expectation about how quickly a task should complete relative to the DAG run.

For example:

```python
sla=timedelta(seconds=30)
```

means that the task is expected to complete within the defined SLA period.

---

## 13. Important: SLA Does Not Kill the Task

This is one of the most important points.

Suppose:

```python
sla = timedelta(seconds=30)
```

and the task takes:

```text
40 seconds
```

The task has missed its SLA.

But Airflow does **not** automatically terminate the task because the SLA was exceeded.

Instead:

```text
Task starts
    |
    v
30 seconds
    |
    | SLA threshold exceeded
    v
SLA Miss
    |
    v
Task may continue running
```

If the requirement is to actually stop a task after a certain amount of runtime, that is a **timeout** problem rather than an SLA problem.

---

## 14. Example SLA DAG

A simplified version of the original example:

```python
from datetime import datetime, timedelta
import time

from airflow import DAG
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import PythonOperator


def my_custom_func():
    print("Task is sleeping")
    time.sleep(40)


default_args = {
    "owner": "hdu",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}


with DAG(
    dag_id="sample_dag_sla",
    start_date=datetime(2024, 11, 20),
    default_args=default_args,
    schedule=timedelta(minutes=2),
    max_active_runs=1,
    catchup=False,
):

    t0 = EmptyOperator(
        task_id="start",
    )

    sla_task = PythonOperator(
        task_id="sla_task",
        python_callable=my_custom_func,
        sla=timedelta(seconds=30),
    )

    t1 = EmptyOperator(
        task_id="end",
    )

    t0 >> sla_task >> t1
```

The task sleeps for:

```text
40 seconds
```

while its SLA is:

```text
30 seconds
```

Therefore:

```text
40 sec execution
      >
30 sec SLA
      |
      v
SLA Miss
```

The task itself is not automatically cancelled.

---

## 15. Task-Level SLA

An SLA can be specified directly on an individual task.

Example:

```python
sla_task = PythonOperator(
    task_id="sla_task",
    python_callable=my_custom_func,
    sla=timedelta(seconds=30),
)
```

This is often clearer than putting the SLA into `default_args` when only one or a few tasks need the SLA.

---

## 16. SLA Miss Callback

Airflow also supports a callback for SLA misses.

Conceptually:

```text
Task
 |
 | exceeds SLA
 v
SLA Miss
 |
 v
sla_miss_callback
 |
 v
Custom notification / logging
```

A callback can inspect information about:

- DAG
- tasks that missed the SLA
- blocking tasks
- SLA objects
- task instances

Airflow's SLA documentation defines the callback signature and the information supplied to it.

---

## 17. SLA vs Timeout

This distinction is very important.

| Feature | SLA | Timeout |
|---|---|---|
| Purpose | Detect that expected completion time was exceeded | Limit how long execution can continue |
| Cancels task? | No | Can terminate/fail execution depending on timeout type |
| Main use | Monitoring / alerting | Execution control |
| Example | "This should finish within 30 sec" | "Do not allow this to run beyond 30 sec" |

Think:

```text
SLA
=
"Tell me if this takes too long."

Timeout
=
"Stop it if this takes too long."
```

Airflow explicitly distinguishes these behaviors.

---

## 18. SLA Monitoring Flow

A useful mental model is:

```text
                 Task starts
                      |
                      v
                SLA countdown
                      |
          +-----------+-----------+
          |                       |
          v                       v
    Completes in time       Exceeds SLA
          |                       |
          v                       v
       SUCCESS                SLA MISS
                                  |
                    +-------------+-------------+
                    |                           |
                    v                           v
                 UI alert                SLA callback/email
```

---

## 19. Important Airflow 2.8 Note

SLA monitoring is associated with scheduled DAG runs.

The Airflow documentation notes that manually triggered tasks and tasks in event-driven DAGs are not checked for SLA misses in the same way.

This is important when testing SLA examples manually.

If you manually trigger a DAG and do not see the expected SLA behavior, do not immediately assume that the SLA configuration is broken.

---

## 20. Complete Monitoring Mental Model

At this point we have several mechanisms:

```text
                    AIRFLOW MONITORING
                           |
          +----------------+----------------+
          |                |                |
          v                v                v
     CALLBACKS          EMAIL           SLA
          |                |                |
          v                v                v
    Run custom        Notify user       Detect
      Python          externally       late tasks
      logic
```

These mechanisms can also work together.

For example:

```text
Task
 |
 v
Task fails
 |
 +----> on_failure_callback
 |
 +----> email notification
 |
 +----> retry
```

And:

```text
Task
 |
 v
Task runs too long
 |
 v
SLA exceeded
 |
 +----> SLA miss recorded
 |
 +----> notification/callback
```

---

## 21. How Notes 9, 10 and 11 Fit Together

These three notes now form a useful progression.

### Notes 9 — Sensors

Question:

> "How do I wait for something?"

Example:

```text
Wait for file
Wait for API
Wait for another DAG
Wait until a time
```

---

### Notes 10 — Datasets

Question:

> "How do I schedule a DAG when data becomes available?"

Example:

```text
Producer
   |
   v
Dataset
   |
   v
Consumer
```

---

### Notes 11 — Notifications and SLAs

Question:

> "How do I know when my workflow fails, succeeds, or takes too long?"

Example:

```text
Task
 |
 +---- success callback
 |
 +---- failure callback
 |
 +---- email
 |
 +---- SLA monitoring
```

---

## 22. Key Takeaways

### Notifications

Used to communicate workflow events.

### Callbacks

Python functions triggered by Airflow events.

### `on_success_callback`

Runs when the task succeeds.

### `on_failure_callback`

Runs when the task fails.

### `on_retry_callback`

Runs when a task enters retry behavior.

### Email

Airflow can send email notifications when email/SMTP is configured.

### SLA

Represents an expected completion time.

### SLA Miss

Indicates that the task exceeded its expected completion time.

### Timeout

Used when the goal is to actually limit execution time.

---

## 23. Final Mental Model

You can now think of Airflow workflows in this way:

```text
                 AIRFLOW WORKFLOW
                        |
       +----------------+----------------+
       |                |                |
       v                v                v
   SCHEDULING        EXECUTION        MONITORING
       |                |                |
       v                v                v
    Cron/Dataset     Operators        Callbacks
    Timetable        Sensors          Notifications
                     Executors        SLA
                                      Timeout
```

The overall learning progression is:

```text
DAG
 |
 +--> Tasks & Operators
 |
 +--> Dependencies
 |
 +--> XCom
 |
 +--> TaskFlow API
 |
 +--> Scheduling
 |
 +--> Dates / Logical Date
 |
 +--> Executors
 |
 +--> Sensors
 |
 +--> Datasets
 |
 +--> Notifications / Callbacks
 |
 +--> SLAs
```
