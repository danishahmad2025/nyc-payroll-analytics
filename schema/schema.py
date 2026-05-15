from sqlalchemy import create_engine, text

# -----------------------------------------------
# CONNECTION TO POSTGRESQL
# Change these 3 values to match your setup:
#   - yourpassword  : password you set when installing PostgreSQL
#   - localhost     : leave this as it is
#   - 5432          : default PostgreSQL port, leave as it is
#   - nyc_payroll   : name of the database you created in pgAdmin
# -----------------------------------------------

DB_PASSWORD = "1234"
DB_NAME     = "payroll_db"

engine = create_engine(f"postgresql://postgres:{DB_PASSWORD}@localhost:5432/{DB_NAME}")


# -----------------------------------------------
# CREATE ALL TABLES
# Dimension tables are created first because the
# fact table depends on them (foreign keys).
# -----------------------------------------------

create_tables = """

    -- 1. Agency table
    CREATE TABLE IF NOT EXISTS dim_agency (
        agency_id   SERIAL PRIMARY KEY,
        agency_name VARCHAR(255)
    );

    -- 2. Job title table
    CREATE TABLE IF NOT EXISTS dim_title (
        title_id          SERIAL PRIMARY KEY,
        title_description VARCHAR(255)
    );

    -- 3. Location table
    CREATE TABLE IF NOT EXISTS dim_location (
        location_id SERIAL PRIMARY KEY,
        borough     VARCHAR(100)
    );

    -- 4. Time table (fiscal years)
    CREATE TABLE IF NOT EXISTS dim_time (
        time_id     SERIAL PRIMARY KEY,
        fiscal_year INT
    );

    -- 5. Employee table
    CREATE TABLE IF NOT EXISTS dim_employee (
        employee_id       SERIAL PRIMARY KEY,
        last_name         VARCHAR(100),
        first_name        VARCHAR(100),
        agency_start_date DATE
    );

    -- 6. Fact table (main table, links to all dimension tables)
    CREATE TABLE IF NOT EXISTS fact_payroll (
        payroll_id          SERIAL PRIMARY KEY,
        employee_id         INT REFERENCES dim_employee(employee_id),
        agency_id           INT REFERENCES dim_agency(agency_id),
        title_id            INT REFERENCES dim_title(title_id),
        location_id         INT REFERENCES dim_location(location_id),
        time_id             INT REFERENCES dim_time(time_id),
        base_salary         FLOAT,
        regular_hours       FLOAT,
        regular_gross_paid  FLOAT,
        ot_hours            FLOAT,
        total_ot_paid       FLOAT,
        total_other_pay     FLOAT,
        pay_basis           VARCHAR(50),
        leave_status        VARCHAR(100)
    );

"""

# -----------------------------------------------
# RUN THE SQL AND CREATE THE TABLES
# -----------------------------------------------

print("Connecting to PostgreSQL...")

with engine.connect() as conn:
    conn.execute(text(create_tables))
    conn.commit()
    print("All tables created successfully.")

print("Done. You can now open pgAdmin to verify the tables.")