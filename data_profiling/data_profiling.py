import pandas as pd

# -----------------------------------------------
# SETTINGS  (change values here if needed)
# -----------------------------------------------

FILE_PATH  = "/home/danish/Desktop/data_engineering/nyc-payroll-analytics/Citywide_Payroll_Data__Fiscal_Year_.csv"
CHUNK_SIZE = 100_000        # how many rows to read at a time
SALARY_COL = "Base Salary"

CATEGORY_COLS = [
    "Agency Name",
    "Work Location Borough",
    "Title Description",
    "Leave Status as of June 30",
    "Pay Basis",
    "Fiscal Year",
]

# -----------------------------------------------
# STEP 1 — READ THE FILE IN SMALL PIECES
# -----------------------------------------------
# Reading 100,000 rows at a time is called chunking.
# We do this so the whole file is never fully loaded
# into memory at once.

print("Reading file, please wait...")

# These variables collect results from every chunk
total_rows       = 0
empty_cells      = None     # empty cell count per column
duplicate_rows   = 0
salary_total     = 0        # sum of all salaries
salary_count     = 0        # number of valid salary values
salary_min       = None
salary_max       = None
bad_salary       = 0        # values that could not be read as a number
column_types     = None
unique_values    = {col: set() for col in CATEGORY_COLS}


for chunk in pd.read_csv(FILE_PATH, chunksize=CHUNK_SIZE, low_memory=False):

    total_rows += len(chunk)

    # Save column types once from the first chunk
    if column_types is None:
        column_types = chunk.dtypes

    # Count empty cells — add to previous chunk results
    if empty_cells is None:
        empty_cells = chunk.isnull().sum()
    else:
        empty_cells = empty_cells + chunk.isnull().sum()

    # Count duplicate rows in this chunk
    duplicate_rows += chunk.duplicated().sum()

    # --- Salary ---
    # Remove $ and commas, then convert text to number
    before_empty = chunk[SALARY_COL].isna().sum()

    salary = chunk[SALARY_COL].astype(str)
    salary = salary.str.replace("$", "", regex=False)
    salary = salary.str.replace(",", "", regex=False)
    salary = salary.str.strip()
    salary = pd.to_numeric(salary, errors="coerce")

    # Values that became empty after conversion = bad values
    after_empty  = salary.isna().sum()
    bad_salary  += int(after_empty - before_empty)

    # Add up salary numbers from valid rows only
    valid = salary.dropna()
    salary_total += valid.sum()
    salary_count += len(valid)

    if len(valid) > 0:
        chunk_min = valid.min()
        chunk_max = valid.max()
        salary_min = chunk_min if salary_min is None else min(salary_min, chunk_min)
        salary_max = chunk_max if salary_max is None else max(salary_max, chunk_max)

    # Collect unique values for each category column
    for col in CATEGORY_COLS:
        unique_values[col].update(chunk[col].dropna().unique())


print("Done!\n")


# -----------------------------------------------
# STEP 2 — CALCULATE FINAL NUMBERS
# -----------------------------------------------

if salary_count > 0:
    salary_avg = salary_total / salary_count
else:
    salary_avg = 0


# -----------------------------------------------
# STEP 3 — SHOW RESULTS
# -----------------------------------------------

print("=" * 45)
print("BASIC INFO")
print("=" * 45)
print("Total Rows     :", total_rows)
print("Total Columns  :", len(empty_cells))
print("Duplicate Rows :", duplicate_rows)


print("\n" + "=" * 45)
print("COLUMN TYPES")
print("=" * 45)
for col in column_types.index:
    print(col, "->", column_types[col])


print("\n" + "=" * 45)
print("EMPTY CELLS PER COLUMN")
print("=" * 45)
for col in empty_cells.index:
    count = empty_cells[col]
    pct   = round(count / total_rows * 100, 1)
    print(col, "->", count, "empty", f"({pct}%)")


print("\n" + "=" * 45)
print("SALARY STATS")
print("=" * 45)
print("Valid Values :", salary_count)
print("Bad Values   :", bad_salary)
print("Average      :", round(salary_avg, 2))
print("Lowest       :", salary_min)
print("Highest      :", salary_max)


print("\n" + "=" * 45)
print("UNIQUE VALUES PER COLUMN")
print("=" * 45)
for col in CATEGORY_COLS:
    print(col, "->", len(unique_values[col]), "unique values")


print("\n" + "=" * 45)
print("Done.")
print("=" * 45)