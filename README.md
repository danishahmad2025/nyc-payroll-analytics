# nyc-payroll-analytics
End-to-end data engineering project analyzing NYC Citywide Payroll data 

# 🏙️ NYC Citywide Payroll Data Warehouse
**By Danish Ekbal Ahmad**

## 📌 Project Overview
An end-to-end Data Engineering pipeline processing **2.2 Million records** of NYC Payroll data. This project transforms raw, unstructured CSV files into a normalized **Star Schema** Data Warehouse using PostgreSQL, enabling high-performance analytics on city spending.

## 🛠️ Tech Stack
- **Language:** Python (Pandas, SQLAlchemy)
- **Database:** PostgreSQL
- **Visualization:** Matplotlib/Seaborn (Custom styled for executive reporting)

## 🏗️ Architecture & Design

### 1. Star Schema Design
I chose a **Star Schema** to optimize for read-heavy analytical queries.
- **Fact Table (`fact_payroll`):** Stores measurable metrics (Salary, OT, Hours) and Foreign Keys.
- **Dimensions:** `dim_agency`, `dim_title`, `dim_location`, `dim_time`, `dim_employee`.
- **Benefit:** Reduces complex joins and speeds up aggregation queries significantly compared to a normalized 3NF schema.

### 2. ETL Pipeline Logic (`etl.py`)
The pipeline is designed for **scalability** and **memory efficiency**.

#### Key Engineering Concepts Used:
1.  **Chunked Processing (Memory Management):**
    *   *Problem:* Loading 2.2M rows into Pandas at once causes MemoryErrors.
    *   *Solution:* I used `pd.read_csv(chunksize=100_000)`. This processes data in small batches, keeping RAM usage low.
2.  **Surrogate Keys (Performance):**
    *   *Problem:* Joining tables on long strings (e.g., "POLICE DEPARTMENT") is slow and storage-heavy.
    *   *Solution:* I generated integer IDs (`agency_id`, `title_id`) for all dimensions. The Fact table stores these integers, making indexing and joining much faster.
3.  **Data Cleaning & Imputation:**
    *   Handled dirty currency formats (removing `$` and `,`).
    *   Imputed missing `Work Location Borough` values with "Unknown" to preserve record integrity.

## 🚀 How to Run

### Prerequisites
- Python 3.x
- PostgreSQL installed
- Libraries: `pandas`, `sqlalchemy`, `psycopg2`, `matplotlib`, `seaborn`

### Execution Steps
1.  **Setup Database:** Create a database named `payroll_db`.
2.  **Run Profiling (Optional):**
    ```bash
    python data_profiling.py
    ```
3.  **Run ETL Pipeline:**
    ```bash
    python etl.py
    ```
    *This script will create the schema, load dimensions, and populate the fact table using chunked loading.*
4.  **Generate Visuals:**
    ```bash
    python analysis.py
    ```

## 📊 Key Insights Generated
- **Total Payroll Trend:** Increased from $22.9B (2014) to $27.1B (2017).
- **Top Spender:** Dept of Education (Pedagogical) at $30.2B.
- **Overtime Burden:** Police Department spent $2.8B on Overtime (highest in the city).
- **Highest Paid Role:** Pension Investment Advisor (~$289k avg base).

## 📂 File Structure
```text
.
├── Citywide_Payroll_Data.csv  # Raw Data
├── data_profiling.py          # Initial data health check
├── etl.py                     # Main ETL logic (Extract, Transform, Load)
├── analysis.py                # SQL Queries & Visualization generation
└── README.md