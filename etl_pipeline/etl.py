import pandas as pd
from sqlalchemy import create_engine, text

# =========================================================
# SETTINGS
# =========================================================

FILE_PATH  = "/home/danish/Desktop/data_engineering/nyc-payroll-analytics/Citywide_Payroll_Data__Fiscal_Year_.csv"
CHUNK_SIZE = 100_000

DB_USER     = "postgres"
DB_PASSWORD = "1234"
DB_NAME     = "payroll_db"

MONEY_COLS = [
    "Base Salary",
    "Regular Gross Paid",
    "Total OT Paid",
    "Total Other Pay",
]

# PostgreSQL connection
engine = create_engine(
    f"postgresql://{DB_USER}:{DB_PASSWORD}@localhost:5432/{DB_NAME}",
    pool_size=5,
    max_overflow=2,
)

# =========================================================
# CLEANING FUNCTION
# =========================================================

def clean_chunk(df):

    # Drop unnecessary column
    df = df.drop(columns=["Mid Init"], errors="ignore")

    # Fill missing text values
    text_cols = [
        "Work Location Borough",
        "Last Name",
        "First Name",
        "Title Description",
    ]

    df[text_cols] = df[text_cols].fillna("Unknown")

    # Fill missing numeric values
    df[["Regular Hours", "OT Hours"]] = (
        df[["Regular Hours", "OT Hours"]].fillna(0)
    )

    # Clean money columns
    for col in MONEY_COLS:
        df[col] = (
            df[col]
            .astype(str)
            .str.replace("$", "", regex=False)
            .str.replace(",", "", regex=False)
            .str.strip()
        )

        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # Convert date column
    df["Agency Start Date"] = pd.to_datetime(
        df["Agency Start Date"],
        errors="coerce"
    )

    # Remove bad data
    df = (
        df.drop_duplicates()
          .query("`Base Salary` >= 1")
    )

    # Feature engineering
    df["total_compensation"] = (
        df["Base Salary"]
        + df["Total OT Paid"]
        + df["Total Other Pay"]
    )

    df["has_overtime"] = df["OT Hours"] > 0

    return df


# =========================================================
# STEP 1 — STAGING TABLE
# =========================================================

print("\nSTEP 1 — Loading staging table")

total_rows = 0

for i, chunk in enumerate(
    pd.read_csv(FILE_PATH, chunksize=CHUNK_SIZE, low_memory=False)
):

    mode = "replace" if i == 0 else "append"

    chunk.to_sql(
        "staging_payroll",
        engine,
        if_exists=mode,
        index=False,
        chunksize=5_000,
    )

    total_rows += len(chunk)

print(f"Staging rows loaded : {total_rows:,}")


# =========================================================
# STEP 2 — BUILD DIMENSIONS
# =========================================================

print("\nSTEP 2 — Building dimensions")

unique_data = {
    "agency": set(),
    "title": set(),
    "location": set(),
    "time": set(),
    "employee": set(),
}

for chunk in pd.read_csv(FILE_PATH, chunksize=CHUNK_SIZE, low_memory=False):

    chunk = clean_chunk(chunk)

    unique_data["agency"].update(chunk["Agency Name"].unique())
    unique_data["title"].update(chunk["Title Description"].unique())
    unique_data["location"].update(chunk["Work Location Borough"].unique())
    unique_data["time"].update(chunk["Fiscal Year"].unique())

    employees = zip(
        chunk["Last Name"],
        chunk["First Name"],
        chunk["Agency Start Date"].astype(str),
    )

    unique_data["employee"].update(employees)


# =========================================================
# CREATE DIMENSION DATAFRAMES
# =========================================================

def build_dimension(id_col, value_col, values):

    return pd.DataFrame({
        id_col: range(1, len(values) + 1),
        value_col: sorted(values),
    })


dim_agency = build_dimension(
    "agency_id",
    "agency_name",
    unique_data["agency"]
)

dim_title = build_dimension(
    "title_id",
    "title_description",
    unique_data["title"]
)

dim_location = build_dimension(
    "location_id",
    "borough",
    unique_data["location"]
)

dim_time = build_dimension(
    "time_id",
    "fiscal_year",
    unique_data["time"]
)

# Employee dimension
emp_df = pd.DataFrame(
    sorted(unique_data["employee"]),
    columns=["last_name", "first_name", "agency_start_date"]
)

emp_df.insert(0, "employee_id", range(1, len(emp_df) + 1))

dim_employee = emp_df


# =========================================================
# LOAD DIMENSIONS
# =========================================================

dimensions = {
    "dim_agency": dim_agency,
    "dim_title": dim_title,
    "dim_location": dim_location,
    "dim_time": dim_time,
    "dim_employee": dim_employee,
}

with engine.begin() as conn:

    for table, df in dimensions.items():

        df.to_sql(
            table,
            conn,
            if_exists="replace",
            index=False,
            chunksize=5_000,
        )

        print(f"{table} loaded : {len(df):,} rows")


# =========================================================
# LOOKUP MAPS
# =========================================================

agency_map = dict(zip(
    dim_agency["agency_name"],
    dim_agency["agency_id"]
))

title_map = dict(zip(
    dim_title["title_description"],
    dim_title["title_id"]
))

location_map = dict(zip(
    dim_location["borough"],
    dim_location["location_id"]
))

time_map = dict(zip(
    dim_time["fiscal_year"],
    dim_time["time_id"]
))

employee_map = {
    (r.last_name, r.first_name, str(r.agency_start_date)): r.employee_id
    for r in dim_employee.itertuples()
}


# =========================================================
# STEP 3 — LOAD FACT TABLE
# =========================================================

print("\nSTEP 3 — Loading fact table")

fact_rows = 0

for i, chunk in enumerate(
    pd.read_csv(FILE_PATH, chunksize=CHUNK_SIZE, low_memory=False)
):

    chunk = clean_chunk(chunk)

    # Map IDs
    chunk["agency_id"] = chunk["Agency Name"].map(agency_map)
    chunk["title_id"] = chunk["Title Description"].map(title_map)
    chunk["location_id"] = chunk["Work Location Borough"].map(location_map)
    chunk["time_id"] = chunk["Fiscal Year"].map(time_map)

    emp_keys = list(zip(
        chunk["Last Name"],
        chunk["First Name"],
        chunk["Agency Start Date"].astype(str),
    ))

    chunk["employee_id"] = pd.Series(emp_keys).map(employee_map)

    # Build fact table
    fact_df = pd.DataFrame({
        "employee_id": chunk["employee_id"],
        "agency_id": chunk["agency_id"],
        "title_id": chunk["title_id"],
        "location_id": chunk["location_id"],
        "time_id": chunk["time_id"],
        "base_salary": chunk["Base Salary"],
        "regular_hours": chunk["Regular Hours"],
        "regular_gross_paid": chunk["Regular Gross Paid"],
        "ot_hours": chunk["OT Hours"],
        "total_ot_paid": chunk["Total OT Paid"],
        "total_other_pay": chunk["Total Other Pay"],
        "pay_basis": chunk["Pay Basis"],
        "leave_status": chunk["Leave Status as of June 30"],
        "total_compensation": chunk["total_compensation"],
        "has_overtime": chunk["has_overtime"],
    })

    mode = "replace" if i == 0 else "append"

    fact_df.to_sql(
        "fact_payroll",
        engine,
        if_exists=mode,
        index=False,
        chunksize=5_000,
    )

    fact_rows += len(fact_df)

    print(f"Chunk {i+1} loaded — {fact_rows:,} rows")


# =========================================================
# CREATE INDEXES
# =========================================================

print("\nCreating indexes")

indexes = [
    "agency_id",
    "title_id",
    "location_id",
    "time_id",
    "employee_id",
]

with engine.connect() as conn:

    for col in indexes:

        conn.execute(text(
            f"""
            CREATE INDEX IF NOT EXISTS idx_{col}
            ON fact_payroll({col})
            """
        ))

    conn.commit()

print("Indexes created")


# =========================================================
# FINAL SUMMARY
# =========================================================

print("\nETL COMPLETE")
print("=" * 50)

summary = {
    "staging_payroll": total_rows,
    "dim_agency": len(dim_agency),
    "dim_title": len(dim_title),
    "dim_location": len(dim_location),
    "dim_time": len(dim_time),
    "dim_employee": len(dim_employee),
    "fact_payroll": fact_rows,
}

for table, rows in summary.items():
    print(f"{table:<20} : {rows:,} rows")

print("=" * 50)