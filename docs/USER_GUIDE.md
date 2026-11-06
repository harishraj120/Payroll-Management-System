## Administrator login

On first launch, create an administrator username and a password of at least 10 characters. Confirm the password and select **Create Admin Account**. The application then asks you to sign in. On later launches, use the same credentials. Select **Logout** in the main window to return to the login screen. Passwords are stored as salted PBKDF2 hashes, not as plain text.

# User Guide

## 1. Start the application

Run `python main.py` after installing dependencies and setting up MySQL.

## 2. Employee registration

Open **Employees** and click **Add Employee**. Enter a unique employee code, full name, designation, joining date in `YYYY-MM-DD` format, and basic salary. Optionally add contact information and select a department. The default HRA, DA and tax percentages are 20, 10 and 5, respectively. Click **Save Employee**. The information is validated and stored in MySQL.

## 3. Employee management

Use the search box to locate employees by name, code or designation. Select a row and click **Edit Selected** to change details. Double-clicking a row also opens the editor. **Activate / Deactivate** changes whether an employee is eligible for future payroll runs. Existing payroll snapshots remain unchanged.

## 4. Monthly payroll

Select **Monthly Payroll**, enter a month such as `2026-11`, and click **Generate Payroll**. The application selects employees who are active and whose joining date is on or before the end of that month. It calculates the salary breakdown and stores a monthly snapshot. Each month can have only one payroll run, preventing accidental duplicate payroll creation. Use **View Selected** to inspect the generated items.

## 5. Export employee directory

Go to **Reports & Excel** and click **Export Employees & Open Excel**. A formatted workbook is saved in `exports/`, then opened using the operating system's default application for `.xlsx` files.

## 6. Export monthly payroll

Go to **Reports & Excel**, select a payroll run in the list, then click **Export Selected Payroll & Open Excel**. The workbook includes salary components, totals, an explanation of calculation rules, and a warning that statutory compliance is not implemented.

## 7. Export an individual payslip

Select a payroll run and click **Export Selected Employee Payslip**. Choose the employee from the dropdown, then click **Export & Open**. The system saves a separate workbook with employee details, earnings, deductions and net pay.

## 8. Troubleshooting

### MySQL connection refused

Confirm the MySQL service is running. Verify `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_USER` and `MYSQL_PASSWORD` in `.env`.

### Unknown database

Run `python setup_database.py` or execute `sql/schema.sql` in MySQL Workbench.

### Access denied for MySQL user

Verify the credentials and that the configured user can create and modify the payroll database. For production use, create a dedicated limited-privilege database user after initialization.

### Excel does not open

Confirm Excel is installed. Right-click any `.xlsx` file in Windows, choose **Open with**, select **Excel**, and set it as the default application. You can also manually open the generated file in `exports/`.

### Tkinter is missing

Install the standard Python distribution including Tcl/Tk support. On Linux, you may need your distribution's `python3-tk` package.

### Payroll already exists

Monthly payroll snapshots cannot be overwritten through the interface. Choose another month or use administrative database procedures with appropriate backup and authorization.

## 9. Limitations and future enhancements

- The system is single-user oriented and does not include authentication or role-based access control.
- Payroll calculations are illustrative, not statutory tax calculations.
- It does not automatically synchronize Excel edits back to MySQL.
- A future version could add attendance tracking, leave management, PDF payslips, audit logs, encrypted backups and secure role-based access.
- The default payroll run uses no additional per-employee deductions beyond the configured demonstration tax; the calculation engine supports additional deductions for future expansion.
