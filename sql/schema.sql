CREATE DATABASE IF NOT EXISTS payroll_management
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE payroll_management;

CREATE TABLE IF NOT EXISTS app_users (
 id INT AUTO_INCREMENT PRIMARY KEY,
 username VARCHAR(60) NOT NULL UNIQUE,
 password_hash VARCHAR(255) NOT NULL,
 active BOOLEAN NOT NULL DEFAULT TRUE,
 created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS departments (
 id INT AUTO_INCREMENT PRIMARY KEY,
 name VARCHAR(100) NOT NULL UNIQUE,
 created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS employees (
 id INT AUTO_INCREMENT PRIMARY KEY,
 employee_code VARCHAR(30) NOT NULL UNIQUE,
 full_name VARCHAR(150) NOT NULL,
 email VARCHAR(190) NULL UNIQUE,
 phone VARCHAR(30) NULL,
 department_id INT NULL,
 designation VARCHAR(100) NOT NULL,
 joining_date DATE NOT NULL,
 basic_salary DECIMAL(12,2) NOT NULL,
 hra_percent DECIMAL(5,2) NOT NULL DEFAULT 20.00,
 da_percent DECIMAL(5,2) NOT NULL DEFAULT 10.00,
 tax_percent DECIMAL(5,2) NOT NULL DEFAULT 5.00,
 active BOOLEAN NOT NULL DEFAULT TRUE,
 created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
 updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
 CONSTRAINT fk_employee_department FOREIGN KEY (department_id)
   REFERENCES departments(id) ON DELETE SET NULL,
 CONSTRAINT chk_employee_salary CHECK (basic_salary >= 0),
 CONSTRAINT chk_employee_hra CHECK (hra_percent BETWEEN 0 AND 100),
 CONSTRAINT chk_employee_da CHECK (da_percent BETWEEN 0 AND 100),
 CONSTRAINT chk_employee_tax CHECK (tax_percent BETWEEN 0 AND 100)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS payroll_runs (
 id INT AUTO_INCREMENT PRIMARY KEY,
 payroll_month DATE NOT NULL,
 generated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
 notes VARCHAR(250) NULL,
 UNIQUE KEY uq_payroll_month (payroll_month)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS payroll_items (
 id INT AUTO_INCREMENT PRIMARY KEY,
 run_id INT NOT NULL,
 employee_id INT NOT NULL,
 employee_code VARCHAR(30) NOT NULL,
 employee_name VARCHAR(150) NOT NULL,
 department_name VARCHAR(100) NULL,
 designation VARCHAR(100) NOT NULL,
 basic_salary DECIMAL(12,2) NOT NULL,
 hra_amount DECIMAL(12,2) NOT NULL,
 da_amount DECIMAL(12,2) NOT NULL,
 gross_salary DECIMAL(12,2) NOT NULL,
 tax_amount DECIMAL(12,2) NOT NULL,
 other_deductions DECIMAL(12,2) NOT NULL DEFAULT 0,
 net_salary DECIMAL(12,2) NOT NULL,
 created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
 CONSTRAINT fk_item_run FOREIGN KEY (run_id) REFERENCES payroll_runs(id) ON DELETE CASCADE,
 CONSTRAINT fk_item_employee FOREIGN KEY (employee_id) REFERENCES employees(id),
 UNIQUE KEY uq_run_employee (run_id, employee_id),
 INDEX ix_payroll_employee (employee_id)
) ENGINE=InnoDB;

INSERT IGNORE INTO departments(name) VALUES
 ('Engineering'),('Human Resources'),('Finance'),('Operations'),('Administration');
