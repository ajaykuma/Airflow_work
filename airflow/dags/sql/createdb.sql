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
