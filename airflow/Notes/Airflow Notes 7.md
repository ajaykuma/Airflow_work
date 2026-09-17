# AIRFLOW NOTES 7 

**Your environment:**
- OS: Ubuntu 22.04
- Python: 3.10
- Airflow: 2.8.1
- Virtualenv: `/home/hdu/my-env`
- AIRFLOW_HOME: `/home/hdu/airflow`
- DAGs folder: `/home/hdu/airflow/dags`
- SQL scripts folder: `/home/hdu/airflow/dags/sql`
- MySQL connection id used in DAGs: `mysql_default`
- MySQL app user: `hdu` (password `abcd1234` — change this to something stronger for real use)

---

## EX1: Install and Set Up MySQL on the Host Machine

Run outside the virtualenv, directly on Ubuntu:

```bash
sudo apt update
sudo apt install -y mysql-server libmysqlclient-dev pkg-config
sudo systemctl enable --now mysql
sudo systemctl status mysql
```

> Added `pkg-config` — needed later so the `mysqlclient` Python package can compile against MySQL's headers.

---

## EX2: Log in to MySQL as Root

```bash
sudo mysql
```

(No need to `sudo su` first — `sudo mysql` alone gets you an authenticated root shell on a fresh Ubuntu MySQL install.)

---

## EX3: Configure MySQL Users

```sql
ALTER USER 'root'@'localhost'
IDENTIFIED WITH mysql_native_password
BY 'abcd1234';

CREATE USER 'hdu'@'localhost'
IDENTIFIED WITH mysql_native_password
BY 'abcd1234';

FLUSH PRIVILEGES;

GRANT ALL PRIVILEGES ON *.*
TO 'root'@'localhost'
WITH GRANT OPTION;

GRANT ALL PRIVILEGES ON *.*
TO 'hdu'@'localhost'
WITH GRANT OPTION;

FLUSH PRIVILEGES;
EXIT;
```

---

## EX4: Log in as `hdu` and Create the Database

```bash
mysql -u hdu -p
```

```sql
CREATE DATABASE IF NOT EXISTS airflow;
EXIT;
```

---

## EX5: Install the MySQL Provider and Driver

Outside the virtualenv (system packages, already covered by EX1's `libmysqlclient-dev`), then inside your venv:

```bash
source /home/hdu/my-env/bin/activate
pip install mysqlclient
pip install "apache-airflow-providers-mysql" --constraint \
  "https://raw.githubusercontent.com/apache/airflow/constraints-2.8.1/constraints-3.10.txt"
```

> Added the constraints file, which pins provider versions that are known-compatible with Airflow 2.8.1 on Python 3.10, avoiding dependency resolution surprises.

Verify:

```bash
pip freeze | grep -i mysql
```

You should see both `apache-airflow-providers-mysql` and `mysqlclient` listed.

---

## EX6: Restart Airflow

```bash
ps aux | grep webserver
sudo kill -9 <pid>

ps aux | grep scheduler
sudo kill -9 <pid>

source /home/hdu/my-env/bin/activate
export AIRFLOW_HOME=/home/hdu/airflow

nohup airflow webserver &
nohup airflow scheduler &
```

---

## EX7: Configure the MySQL Connection in Airflow

Via UI (**Admin → Connections → +**):

```text
Connection Id:   mysql_default
Connection Type: MySQL
Host:            localhost
Schema:          airflow
Login:           hdu
Password:        abcd1234
Port:            3306
```

> Set Connection Id to `mysql_default` — two of your three existing DAG files already use `mysql_default`, so standardizing on that avoids editing every DAG. `mysql_default` is also Airflow's built-in default id for MySQL hooks/operators, so it's the more idiomatic choice.

Or via CLI:

```bash
airflow connections add 'mysql_default' \
    --conn-type 'mysql' \
    --conn-host 'localhost' \
    --conn-login 'hdu' \
    --conn-password 'abcd1234' \
    --conn-schema 'airflow' \
    --conn-port 3306
```

Verify:

```bash
airflow connections get mysql_default
```

---

## EX8: SQL Scripts

Folder: `/home/hdu/airflow/dags/sql`

```bash
mkdir -p /home/hdu/airflow/dags/sql
```

### `createdb.sql` — unchanged, this one was already correct

```sql
create database if not exists airflow;
use airflow;
create table if not exists airflow.employees
( emp_id int auto_increment primary key,
	first_name varchar(500) NOT null,
	last_name varchar(500) NOT null,
	hire_date date,
	job_id varchar(225),
	salary DECIMAL(7,2),
	commission_pct DECIMAL(6,2),
	manager_id int, dept_id int );
```

### `loadscr.sql` — unchanged, this one was already correct

```sql
INSERT INTO airflow.employees (`emp_id`,`first_name`,`last_name`, `hire_date`, `job_id`, `salary`, `commission_pct`, `manager_id`, `dept_id`)
VALUES (100,"Steven","King",'1987-06-17',"AD_PRES",24000.00,0.00,0,90),
(101,"Neena","Kochhar",'1987-06-18',"AD_VP",17000.00,0.00,100,90),
(102,"Lex","DeHaan",'1987-06-19',"AD_VP",17000.00,0.00,100,90),
(103,"Alexander","Hunold",'1987-06-20',"IT_PROG",9000.00,0.00,102,60),
(104,"Bruce","Ernst",'1987-06-21',"IT_PROG",6000.00,0.00,103,60),
(105,"David","Austin",'1987-06-22',"IT_PROG",4800.00,0.00,103,60),
(106,"Valli","Pataballa",'1987-06-23',"IT_PROG",4800.00,0.00,103,60),
(107,"Diana","Lorentz",'1987-06-24',"IT_PROG",4200.00,0.00,103,60),
(108,"Nancy","Greenberg",'1987-06-25',"FI_MGR",12000.00,0.00,101,100),
(109,"Daniel","Faviet",'1987-06-26',"FI_ACCOUNT",9000.00,0.00,108,100);
```

### `deletetbl.sql` 

```sql
use airflow;
delete from employees;
```

### `checkdata.sql` — unchanged, already correct

```sql
SELECT DISTINCT (job_id) from airflow.employees ;
SELECT COUNT( DISTINCT (job_id)) from airflow.employees;
SELECT MAX(salary) from airflow.employees;
SELECT MIN(salary) from airflow.employees;
```

---

## EX9: DAG 1 — Create / Clean / Load (`dag_exec_scripts_demo_v0`)

```python
import airflow
from datetime import timedelta
from airflow import DAG
from airflow.providers.mysql.operators.mysql import MySqlOperator
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.utils.dates import days_ago

default_args = {
    'owner': 'hdu',
    'retry_delay': timedelta(minutes=1),
}

dag_exec_scripts = DAG(
    dag_id='dag_exec_scripts_demo_v0',
    default_args=default_args,
    schedule_interval='@once',
    start_date=days_ago(1),
    dagrun_timeout=timedelta(minutes=60),
    description='executing the sql scripts',
)

create_table = MySqlOperator(
    sql="sql/createdb.sql",
    task_id="createtable_task",
    mysql_conn_id="mysql_default",
    dag=dag_exec_scripts
)

clnup_table = MySqlOperator(
    sql="sql/deletetbl.sql",
    task_id="clnuptable_task",
    mysql_conn_id="mysql_default",
    dag=dag_exec_scripts
)

load_data = MySqlOperator(
    sql="sql/loadscr.sql",
    task_id="load_data_task",
    mysql_conn_id="mysql_default",
    dag=dag_exec_scripts
)

create_table >> clnup_table >> load_data
```

---

## EX10: DAG 2 — Read via MySqlHook (`dag_exec_scripts_read_demo_v0`)

```python
import airflow
import csv
import logging
from datetime import timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.mysql.hooks.mysql import MySqlHook
from airflow.utils.dates import days_ago

default_args = {
    'owner': 'hdu',
    'retry_delay': timedelta(minutes=5),
}

def mysql_to_file():
    hook = MySqlHook(mysql_conn_id="mysql_default")
    conn = hook.get_conn()
    cursor = conn.cursor()
    cursor.execute("select * from airflow.employees")
    with open("/home/hdu/airflow/dags/sql/sampleout.csv", "w") as f:
        csv_writer = csv.writer(f)
        csv_writer.writerow([i[0] for i in cursor.description])
        csv_writer.writerows(cursor)
    cursor.close()
    conn.close()
    logging.info("saved output from tbl into a file")

with DAG(
    dag_id='dag_exec_scripts_read_demo_v0',
    default_args=default_args,
    schedule_interval='@once',
    start_date=days_ago(1),
    dagrun_timeout=timedelta(minutes=60),
    description='executing the sql scripts',
) as dag:
    task1 = PythonOperator(
        task_id="mysql_to_file",
        python_callable=mysql_to_file
    )
    task1
```

---

## EX11: DAG 3 — Read with Dynamic Filename (`dag_exec_scripts_read_demo_v1`)

```python
import airflow
import csv
import logging
from datetime import timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.mysql.hooks.mysql import MySqlHook
from airflow.utils.dates import days_ago

default_args = {
    'owner': 'hdu',
    'retry_delay': timedelta(minutes=5),
}

def mysql_to_file(ds_nodash, next_ds_nodash):
    hook = MySqlHook(mysql_conn_id="mysql_default")
    conn = hook.get_conn()
    cursor = conn.cursor()
    cursor.execute("select * from airflow.employees")
    output_file = f"/home/hdu/airflow/dags/sql/sampleout_{ds_nodash}.csv"
    with open(output_file, "w") as f:
        csv_writer = csv.writer(f)
        csv_writer.writerow([i[0] for i in cursor.description])
        csv_writer.writerows(cursor)
    cursor.close()
    conn.close()
    logging.info("saved output from tbl into a file: %s", output_file)

with DAG(
    dag_id='dag_exec_scripts_read_demo_v1',
    default_args=default_args,
    schedule_interval='@once',
    start_date=days_ago(1),
    dagrun_timeout=timedelta(minutes=60),
    description='executing the sql scripts',
) as dag:
    task1 = PythonOperator(
        task_id="mysql_to_file",
        python_callable=mysql_to_file
    )
    task1
```

> If we later want real date filtering here, it would look like:
> ```python
> cursor.execute(
>     "select * from airflow.employees where hire_date >= %s and hire_date < %s",
>     (ds_nodash, next_ds_nodash)
> )
> ```
> Note `ds_nodash` is formatted `YYYYMMDD` with no dashes, so for this to match a `DATE` column correctly we'd typically use `ds`/`next_ds` (dashed, `YYYY-MM-DD`) instead of `ds_nodash` in the query itself, and keep `ds_nodash` only for the filename.

---

## EX12: Sanity-Check Before Running

```bash
source /home/hdu/my-env/bin/activate
export AIRFLOW_HOME=/home/hdu/airflow

python /home/hdu/airflow/dags/dag_exec_scripts_demo_v0.py
python /home/hdu/airflow/dags/dag_exec_scripts_read_demo_v0.py
python /home/hdu/airflow/dags/dag_exec_scripts_read_demo_v1.py

airflow dags list-import-errors
```

No output from the `python` commands and an empty import-errors list means the DAGs parse cleanly.

---

## EX13: Trigger and Verify

Run the create/load DAG first — the read DAGs depend on data existing:

```bash
airflow dags trigger dag_exec_scripts_demo_v0
```

Check it succeeded:

```bash
airflow dags list-runs -d dag_exec_scripts_demo_v0
```

Confirm data landed in MySQL:

```bash
mysql -u hdu -p airflow -e "SELECT * FROM employees;"
```

Then trigger the read DAGs:

```bash
airflow dags trigger dag_exec_scripts_read_demo_v0
airflow dags trigger dag_exec_scripts_read_demo_v1
```

Confirm the CSV files were written:

```bash
ls -l /home/hdu/airflow/dags/sql/
cat /home/hdu/airflow/dags/sql/sampleout.csv
```

You should see `sampleout.csv` (from v0) and `sampleout_<YYYYMMDD>.csv` (from v1).

---
