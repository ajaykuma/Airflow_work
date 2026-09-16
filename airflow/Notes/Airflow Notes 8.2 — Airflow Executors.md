## Notes 8.2 — Airflow Executors

## 1. What is an Executor?

After understanding **when Airflow schedules and runs tasks**, the next question is:

> How does Airflow actually execute those tasks?

This is the responsibility of the **Executor**.

The Executor determines how and where Airflow tasks are executed.

Airflow contains several executor implementations, including:

```text
airflow/executors/
│
├── __init__.py
├── base_executor.py
├── celery_executor.py
├── celery_kubernetes_executor.py
├── dask_executor.py
├── debug_executor.py
├── executor_constants.py
├── executor_loader.py
├── kubernetes_executor.py
├── local_executor.py
├── local_kubernetes_executor.py
└── sequential_executor.py
```

---

## 2. BaseExecutor

`BaseExecutor` provides common functionality used by the different executor implementations.

Conceptually:

```text
                    BaseExecutor
                         │
          ┌──────────────┼──────────────┐
          ↓              ↓              ↓
    Sequential        Local          Celery
     Executor        Executor        Executor
```

A simplified version contains:

```python
class BaseExecutor(LoggingMixin):

    def __init__(self, parallelism: int = PARALLELISM):
        super().__init__()

        self.parallelism = parallelism
        self.queued_tasks = ...
        self.running = set()
        self.event_buffer = {}
        self.attempts = Counter()
```

### `parallelism`

`parallelism` is an option that controls how many tasks can run concurrently, subject to other Airflow limits and the executor implementation.

---

## 3. Important BaseExecutor functions

Some important functions implemented by `BaseExecutor` are:

```python
def start(self):
    ...

def sync(self):
    ...

def execute_async(
    self,
    key,
    command,
    queue=None,
    executor_config=None,
):
    ...

def end(self):
    ...

def terminate(self):
    ...
```

Their basic purpose is:

| Function | Purpose |
|---|---|
| `start()` | Starts the Executor |
| `sync()` | Synchronizes/checks task execution state |
| `execute_async()` | Submits a task for execution |
| `end()` | Ends executor processing |
| `terminate()` | Terminates the executor |

---

## 4. `validate_airflow_tasks_run_command`

`BaseExecutor` also validates the command that is being submitted.

The command is expected to start with:

```text
airflow tasks run
```

For example:

```text
airflow tasks run sample_dag print_task
```

From this command, the executor can identify:

```text
dag_id
task_id
```

Conceptually:

```text
airflow tasks run sample_dag print_task
              │          │
              │          └── task_id
              └───────────── dag_id
```

This validation is used by several executor implementations, including:

- `CeleryExecutor`
- `KubernetesExecutor`
- `LocalExecutor`
- `SequentialExecutor`

---

## 5. SequentialExecutor

The `SequentialExecutor` is the simplest executor.

```python
class SequentialExecutor(BaseExecutor):

    def __init__(self):
        super().__init__()
        self.commands_to_run = []
```

When `execute_async()` is called, the task is added to:

```text
commands_to_run
```

For example:

```python
def execute_async(
    self,
    key,
    command,
    queue=None,
    executor_config=None,
):
    self.validate_airflow_tasks_run_command(command)
    self.commands_to_run.append((key, command))
```

The `sync()` function then executes the queued commands sequentially.

Conceptually:

```text
Task A
   ↓
Task B
   ↓
Task C
   ↓
Task D
```

Only one task is executed at a time.

### Important point

The SequentialExecutor is intended for simple execution scenarios and does not provide parallel task execution.

It is also the executor that can be used with SQLite, because SQLite does not support the concurrent database access required by executors that run tasks in parallel.

---

## 6. LocalExecutor

The `LocalExecutor` allows tasks to run **in parallel on the same machine**.

```python
class LocalExecutor(BaseExecutor):
    ...
```

It uses Python's multiprocessing capabilities.

The main configuration is:

```text
parallelism
```

Conceptually:

```text
                 LocalExecutor
                      │
          ┌───────────┴───────────┐
          ↓                       ↓
 parallelism = 0          parallelism > 0
          ↓                       ↓
UnlimitedParallelism     LimitedParallelism
```

---

## 7. UnlimitedParallelism

When:

```python
parallelism == 0
```

the LocalExecutor uses:

```text
UnlimitedParallelism
```

Each task can create a new local worker.

Conceptually:

```text
Task A → Worker 1
Task B → Worker 2
Task C → Worker 3
Task D → Worker 4
```

The important functions are:

```text
start()
execute_async()
sync()
end()
```

### `start()`

Initializes worker counters.

### `execute_async()`

Creates a `LocalWorker` and starts it.

The `LocalWorker` is based on Python's multiprocessing functionality.

### `sync()`

Checks the result queue and updates task states.

### `end()`

Continues synchronizing while active workers are still running.

---

## 8. LimitedParallelism

When:

```python
parallelism > 0
```

the LocalExecutor uses:

```text
LimitedParallelism
```

For example:

```python
parallelism = 4
```

means that the executor creates four workers.

Conceptually:

```text
                 Task Queue
                     │
          ┌──────────┼──────────┐
          ↓          ↓          ↓
       Worker 1   Worker 2   Worker 3   Worker 4
```

If more than four tasks are ready:

```text
Task 1 → Worker 1
Task 2 → Worker 2
Task 3 → Worker 3
Task 4 → Worker 4
Task 5 → Queue
Task 6 → Queue
```

Tasks waiting in the queue are executed when a worker becomes available.

---

## 9. CeleryExecutor

The `CeleryExecutor` is designed for **distributed task execution**.

Unlike `LocalExecutor`, where tasks execute on the same machine, Celery can distribute tasks across multiple worker machines.

Conceptually:

```text
                    Airflow
                       │
                CeleryExecutor
                       │
            ┌──────────┼──────────┐
            ↓          ↓          ↓
        Worker 1    Worker 2    Worker 3
        Machine A   Machine B   Machine C
```

This makes CeleryExecutor suitable for larger production environments where tasks need to be distributed across multiple workers.

---

## 10. CeleryExecutor configuration

A Celery application is created using the Celery configuration:

```python
app = Celery(
    conf.get("celery", "CELERY_APP_NAME"),
    config_source=celery_configuration
)
```

The executor maintains information about running tasks and synchronizes their states.

The `sync()` function performs operations such as:

```python
def sync(self):
    self.update_all_task_states()
    self._check_for_timedout_adopted_tasks()
    self._check_for_stalled_tasks()
```

Conceptually:

```text
Celery Worker
      │
      ↓
Task executes
      │
      ↓
Task state changes
      │
      ↓
CeleryExecutor.sync()
      │
      ↓
Airflow updates task state
```

---

## 11. How does CeleryExecutor submit tasks?

The process can be represented as:

```text
Airflow Scheduler
       ↓
BaseExecutor
       ↓
trigger_tasks()
       ↓
_process_tasks()
       ↓
_send_tasks_to_celery()
       ↓
Celery
       ↓
Celery Worker
       ↓
Task executes
```

`BaseExecutor.trigger_tasks()` identifies tasks that are ready to run and passes them for processing.

The Celery executor then sends those tasks to Celery.

---

## 12. `_send_tasks_to_celery()`

The function:

```python
_send_tasks_to_celery()
```

is responsible for sending the tasks to Celery.

When appropriate, Airflow can use multiple processes to send tasks in parallel.

Conceptually:

```text
              Task list
                  │
                  ↓
        _send_tasks_to_celery()
                  │
          ┌───────┴───────┐
          ↓               ↓
       Process 1       Process 2
          │               │
          ↓               ↓
       Celery           Celery
```

---

## 13. `send_task_to_executor()`

The task is ultimately submitted to Celery using:

```python
task_to_run.apply_async(
    args=[command],
    queue=queue
)
```

Conceptually:

```text
Airflow
   │
   │ task command
   ↓
CeleryExecutor
   │
   │ apply_async()
   ↓
Celery Queue
   │
   ├──────────────┐
   ↓              ↓
Worker 1       Worker 2
   │              │
   ↓              ↓
Task A          Task B
```

The Celery worker then executes the task.

---

## 14. Starting a Celery Worker

For CeleryExecutor to execute tasks, Celery workers need to be running.

The Airflow CLI provides:

```bash
airflow celery worker
```

The implementation is located in:

```text
airflow/cli/commands/celery_command.py
```

The worker eventually starts the Celery application using:

```python
celery_app.worker_main(options)
```

The worker can be configured with options such as:

```text
queues
concurrency
hostname
log level
pid file
```

Conceptually:

```text
                 Airflow
                    │
                    ↓
            CeleryExecutor
                    │
                    ↓
              Celery Queue
                    │
          ┌─────────┴─────────┐
          ↓                   ↓
     Celery Worker 1     Celery Worker 2
          │                   │
          ↓                   ↓
       Task A               Task B
```

---

## 15. Executor comparison

| Executor | Where tasks run | Parallel execution | Typical use |
|---|---|---:|---|
| `SequentialExecutor` | Single/local process | No | Simple development/testing |
| `LocalExecutor` | Local machine | Yes | Parallel execution on one machine |
| `CeleryExecutor` | Celery workers | Yes | Distributed execution |
| `KubernetesExecutor` | Kubernetes pods | Yes | Kubernetes-based execution |

---

## 16. Scheduling vs Execution

One of the most important concepts is that **scheduling and execution are different things**.

### Scheduler

The Scheduler determines:

> **WHEN should the task run?**

### Executor

The Executor determines:

> **HOW and WHERE should the task run?**

The overall flow is:

```text
                  DAG
                   │
                   ↓
                Schedule
                   │
                   ↓
             Data Interval
                   │
                   ↓
              Logical Date
                   │
                   ↓
               Scheduler
                   │
                   ↓
                Executor
                   │
          ┌────────┼─────────┐
          ↓        ↓         ↓
        Local    Celery   Kubernetes
          │        │         │
          ↓        ↓         ↓
        Task     Worker      Pod
```

---

## 17. Key Takeaways

### SequentialExecutor

```text
One task at a time
```

### LocalExecutor

```text
Parallel tasks on the same machine
```

### CeleryExecutor

```text
Parallel tasks across Celery workers
```

### KubernetesExecutor

```text
Tasks executed using Kubernetes infrastructure
```

### Most important mental model

```text
Scheduler
   =
WHEN should the task run?

Executor
   =
HOW and WHERE should the task run?
```
