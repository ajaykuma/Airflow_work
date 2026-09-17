## Notes 12 — Multi-Node Airflow Architecture with CeleryExecutor

This note is **setup-specific**.

Unlike the earlier notes, which mainly explain Airflow concepts, this note documents how to build a **multi-node Airflow environment** using:

| Component | Version / Choice |
|---|---|
| Operating System | Ubuntu 22.04 LTS |
| Python | 3.10 |
| Apache Airflow | 2.8.1 |
| Python Environment | `my-env` |
| Executor | `CeleryExecutor` |
| Metadata Database | PostgreSQL |
| Message Broker | RabbitMQ |
| Monitoring | Flower |
| Architecture | Multi-node |

The basic architecture is:

```text
                    ┌─────────────────────┐
                    │     Airflow UI      │
                    │     Webserver       │
                    └──────────┬──────────┘
                               │
                               │
                    ┌──────────▼──────────┐
                    │      Scheduler      │
                    │                     │
                    │   CeleryExecutor    │
                    └───────┬───────┬─────┘
                            │       │
                     Celery │       │ Celery
                     Broker │       │ Broker
                            │       │
                  ┌─────────▼─┐   ┌─▼─────────┐
                  │  Worker 1 │   │  Worker 2 │
                  │           │   │           │
                  │ Airflow   │   │ Airflow   │
                  │ + my-env  │   │ + my-env  │
                  └───────────┘   └───────────┘
                            │       │
                            └───┬───┘
                                │
                         ┌──────▼──────┐
                         │ PostgreSQL  │
                         │ Metadata DB │
                         └─────────────┘
```

---

### 1. Why Multi-Node Airflow?

A simple Airflow installation can execute tasks on the same machine as the scheduler.

For a larger workload, we may want to distribute task execution across multiple machines.

For example:

```text
              Scheduler
                  │
                  ▼
           CeleryExecutor
                  │
          ┌───────┴────────┐
          ▼                ▼
      Worker 1          Worker 2
          │                │
       Task A           Task B
       Task C           Task D
```

This allows multiple worker machines to execute Airflow tasks.

Airflow's executor determines how task instances are executed. Airflow 2.8.1 supports both local and remote executors; `CeleryExecutor` is a remote executor designed to distribute work across workers.

---

### 2. Software Environment

For this setup we use:

```text
Ubuntu 22.04
      │
      ▼
Python 3.10
      │
      ▼
Virtual environment: my-env
      │
      ▼
Apache Airflow 2.8.1
      │
      ├── Celery provider
      ├── PostgreSQL provider
      └── Other required providers
```

The important point is that **Airflow is not installed into the system Python environment**.

Instead, Airflow is installed inside:

```text
my-env
```

This keeps the Airflow Python packages isolated from the operating system's Python packages.

---

## 3. Install Required Ubuntu Packages

Update the package index:

```bash
sudo apt update
```

Install commonly required packages:

```bash
sudo apt install -y \
    python3.10 \
    python3.10-venv \
    python3.10-dev \
    build-essential \
    libssl-dev \
    libffi-dev \
    libpq-dev \
    libsqlite3-dev \
    curl \
    wget \
    git
```

Check Python:

```bash
python3.10 --version
```

Expected:

```text
Python 3.10.x
```

---

## 4. Create the Airflow Virtual Environment

Create a directory for the Airflow installation:

```bash
mkdir -p ~/airflow
```

Create the virtual environment:

```bash
python3.10 -m venv ~/airflow/my-env
```

Activate it:

```bash
source ~/airflow/my-env/bin/activate
```

The shell should now show something similar to:

```text
(my-env) user@ubuntu:~$
```

Verify:

```bash
which python
```

It should point to something similar to:

```text
/home/user/airflow/my-env/bin/python
```

Check:

```bash
python --version
```

Expected:

```text
Python 3.10.x
```

Upgrade pip:

```bash
pip install --upgrade pip setuptools wheel
```

---

## 5. Install Apache Airflow 2.8.1

Airflow recommends using its version-specific constraints file for a reproducible installation.

For our environment:

```text
Airflow = 2.8.1
Python  = 3.10
```

Therefore the constraint file is:

```text
constraints-2.8.1/constraints-3.10.txt
```

Install Airflow with the Celery extra:

```bash
pip install \
    "apache-airflow[celery]==2.8.1" \
    --constraint \
    "https://raw.githubusercontent.com/apache/airflow/constraints-2.8.1/constraints-3.10.txt"
```

The constraints file is important because Airflow has many dependencies, and the project provides tested dependency combinations for each Airflow/Python release.

Verify:

```bash
airflow version
```

Expected:

```text
2.8.1
```

Also check:

```bash
pip check
```

Ideally:

```text
No broken requirements found.
```

---

## 6. Why the Celery Extra Is Important

For Airflow 2.8.1, Celery is provided through the Celery provider.

Airflow documentation notes that from Airflow 2.7.0 onward, the Celery provider is required for `CeleryExecutor`. Installing:

```bash
apache-airflow[celery]
```

installs the required Celery-related dependencies.

Therefore our installation uses:

```bash
apache-airflow[celery]==2.8.1
```

rather than installing Airflow first and trying to configure Celery later without its provider.

---

## 7. Configure AIRFLOW_HOME

Set the Airflow home directory:

```bash
export AIRFLOW_HOME=~/airflow
```

For a permanent configuration, add it to:

```bash
~/.bashrc
```

For example:

```bash
export AIRFLOW_HOME=$HOME/airflow
```

Then reload:

```bash
source ~/.bashrc
```

Check:

```bash
echo $AIRFLOW_HOME
```

Expected:

```text
/home/user/airflow
```

---

## 8. Important: The Virtual Environment Must Be Used

Because Airflow is installed inside:

```text
my-env
```

Airflow commands must execute using that environment.

Activate it:

```bash
source ~/airflow/my-env/bin/activate
```

Then:

```bash
airflow version
```

The important relationship is:

```text
Ubuntu 22.04
      │
      └── Python 3.10
             │
             └── my-env
                    │
                    └── Airflow 2.8.1
```

This becomes especially important in a multi-node environment.

**Every Airflow node that executes Airflow components must have the required Airflow environment available.**

For Celery workers, the `airflow` CLI must also be available on the worker machine.

---

## 9. Multi-Node Requirement

Suppose we have:

```text
Node 1
  ├── Airflow Webserver
  └── Airflow Scheduler

Node 2
  └── Celery Worker

Node 3
  └── Celery Worker
```

Then the Airflow environment should be consistent across these nodes.

Conceptually:

```text
Node 1                    Node 2                    Node 3

Ubuntu 22.04              Ubuntu 22.04              Ubuntu 22.04
Python 3.10               Python 3.10               Python 3.10
my-env                    my-env                    my-env
Airflow 2.8.1             Airflow 2.8.1             Airflow 2.8.1
Celery provider           Celery provider           Celery provider
DAGs                      DAGs                      DAGs
```

The workers need the Airflow installation and dependencies necessary to execute the tasks they receive.

---

## 10. High-Level Architecture

Our final environment can look like:

```text
                         ┌─────────────────┐
                         │    Webserver    │
                         │                 │
                         │ Ubuntu 22.04    │
                         │ Python 3.10     │
                         │ my-env          │
                         │ Airflow 2.8.1   │
                         └────────┬────────┘
                                  │
                                  │
                         ┌────────▼────────┐
                         │    Scheduler    │
                         │                 │
                         │ CeleryExecutor  │
                         └────────┬────────┘
                                  │
                                  │
                         ┌────────▼────────┐
                         │    RabbitMQ     │
                         │   Message       │
                         │     Broker      │
                         └───────┬─────────┘
                                 │
                    ┌────────────┴────────────┐
                    │                         │
             ┌──────▼──────┐          ┌──────▼──────┐
             │   Worker 1  │          │   Worker 2  │
             │              │          │             │
             │ Ubuntu 22.04│          │ Ubuntu 22.04│
             │ Python 3.10 │          │ Python 3.10 │
             │ my-env      │          │ my-env      │
             │ Airflow 2.8.1          │ Airflow 2.8.1
             └──────┬───────┘          └──────┬──────┘
                    │                         │
                    └───────────┬─────────────┘
                                │
                       ┌────────▼────────┐
                       │   PostgreSQL    │
                       │ Metadata DB     │
                       └─────────────────┘
```

---

## 11. Important Difference From the Previous Setup

The old setup used:

```text
RHEL 8.8
Python 3.9.16
Airflow 2.7.3
```

The new learning/setup environment is:

```text
Ubuntu 22.04
Python 3.10
Airflow 2.8.1
Virtual environment: my-env
```

Therefore, commands such as:

```bash
yum install ...
```

are replaced with:

```bash
sudo apt install ...
```

and we no longer need to compile Python 3.9.16 from source if Python 3.10 is already available through the Ubuntu setup.

The Python virtual environment also changes the service configuration: systemd services must explicitly use the Airflow installation from `my-env` rather than assuming that `airflow` is installed globally.

---

## 12. Systemd Consideration

For this setup, a systemd service should not simply assume:

```bash
ExecStart=/usr/local/bin/airflow ...
```

because Airflow is inside:

```text
~/airflow/my-env/
```

Instead, the service should use the executable from the virtual environment.

For example:

```text
/home/user/airflow/my-env/bin/airflow
```

This is particularly important for:

```text
airflow webserver
airflow scheduler
airflow celery worker
airflow celery flower
```

The systemd service should also run as the dedicated Airflow/Linux user rather than `root`.

---

## 13. CeleryExecutor

Once the environment is configured:

```ini
[core]
executor = CeleryExecutor
```

The architecture becomes:

```text
Scheduler
    │
    │
    ▼
CeleryExecutor
    │
    ▼
RabbitMQ
    │
    ├──────────────┐
    ▼              ▼
Worker 1        Worker 2
```

The scheduler does not directly execute every task.

Instead, Celery distributes task execution to the available workers.

Airflow documents `CeleryExecutor` as a mechanism for distributing task instances across multiple worker nodes.

---

## 14. PostgreSQL

PostgreSQL is used as the Airflow metadata database.

The metadata database stores information such as:

```text
DAGs
Task Instances
DAG Runs
Connections
Variables
XComs
Users
Task States
```

The important distinction is:

```text
PostgreSQL
     │
     └── Airflow metadata

RabbitMQ
     │
     └── Celery message broker
```

They perform different jobs.

---

## 15. RabbitMQ

RabbitMQ acts as the Celery message broker.

The basic flow is:

```text
Airflow Scheduler
       │
       │ task message
       ▼
    RabbitMQ
       │
       │ message
       ▼
 Celery Worker
       │
       ▼
   Execute task
```

Therefore RabbitMQ is not the Airflow metadata database.

It is the communication layer used by Celery to distribute work.

---

## 16. Worker Environment

A Celery worker must have access to the Airflow installation and required dependencies.

For example:

```bash
source ~/airflow/my-env/bin/activate
```

Then:

```bash
airflow celery worker
```

The Celery provider documentation also provides the Airflow CLI command for starting workers.

---

## 17. Flower

Flower provides a web interface for monitoring Celery workers.

Start it with:

```bash
airflow celery flower
```

Typical architecture:

```text
             RabbitMQ
                 │
        ┌────────┴────────┐
        │                 │
     Worker 1          Worker 2
        │                 │
        └────────┬────────┘
                 │
              Flower
                 │
                 ▼
          Web monitoring UI
```

Flower is optional, but useful while learning and troubleshooting a Celery-based Airflow environment.

---

## 18. Final Mental Model

The complete setup can be remembered as:

```text
                  AIRFLOW
                     │
          ┌──────────┴──────────┐
          │                     │
      Webserver              Scheduler
                                │
                                ▼
                         CeleryExecutor
                                │
                                ▼
                            RabbitMQ
                                │
                     ┌──────────┴──────────┐
                     │                     │
                     ▼                     ▼
                  Worker 1              Worker 2
                     │                     │
                     └──────────┬──────────┘
                                │
                                ▼
                           PostgreSQL
                          Metadata DB
```

And every Airflow machine uses:

```text
Ubuntu 22.04
     │
Python 3.10
     │
my-env
     │
Airflow 2.8.1
```

---

## 19. Key Takeaways

1. This setup uses **Ubuntu 22.04** instead of RHEL.
2. Python version is **3.10**.
3. Airflow version is **2.8.1**.
4. Airflow is installed inside the virtual environment **`my-env`**.
5. Airflow should be installed using the appropriate **2.8.1 / Python 3.10 constraints file**.
6. `CeleryExecutor` requires the Celery provider in Airflow 2.8.1.
7. PostgreSQL is used for Airflow metadata.
8. RabbitMQ is used as the Celery message broker.
9. Celery workers execute tasks.
10. Flower can be used to monitor Celery workers.
11. Systemd services must explicitly use the Python environment in `my-env`.
12. The same Airflow version, configuration, dependencies, and DAGs should be consistently available across the relevant nodes.

### Simple way to remember the architecture

```text
Ubuntu
  ↓
Python 3.10
  ↓
my-env
  ↓
Airflow 2.8.1
  ↓
CeleryExecutor
  ↓
RabbitMQ
  ↓
Celery Workers
  ↓
Execute Tasks

PostgreSQL → Airflow Metadata
Flower     → Celery Monitoring
```
