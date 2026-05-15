# =========================================================
# NYC CITYWIDE PAYROLL DATA ANALYSIS
# HIGHLY READABLE & PREMIUM EXECUTIVE CHARTS
# =========================================================

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sqlalchemy import create_engine
import os

# =========================================================
# DATABASE CONNECTION
# =========================================================
USERNAME = "postgres"
PASSWORD = "1234"
HOST = "localhost"
PORT = "5432"
DATABASE = "payroll_db"

engine = create_engine(f"postgresql://{USERNAME}:{PASSWORD}@{HOST}:{PORT}/{DATABASE}")
print("Database Connected Successfully!")

# =========================================================
# FORMATTING UTILITIES (Converts raw metrics to clean text)
# =========================================================
def format_currency(val, pos):
    """Formats large financial numbers cleanly for chart axes."""
    if val >= 1e9:
        return f"${val*1e-9:.1f}B"
    elif val >= 1e6:
        return f"${val*1e-6:.1f}M"
    elif val >= 1e3:
        return f"${val*1e-3:.0f}K"
    return f"${val:.0f}"

# Global Style Settings
sns.set_style("white")  # Complete white background for pristine clarity
plt.rcParams["figure.dpi"] = 150
plt.rcParams["savefig.dpi"] = 300
plt.rcParams["font.sans-serif"] = "Arial"
plt.rcParams["font.family"] = "sans-serif"

# Clean Theme Palette
PRIMARY_BLUE = "#1E3A8A"  # Professional deep navy
HIGHLIGHT_RED = "#B91C1C" # Muted focus red for overtime
SOFT_BLUE = "#3B82F6"     # Secondary accent blue
GRID_GRAY = "#E5E7EB"     # Light clean lines

CHART_FOLDER = "charts"
os.makedirs(CHART_FOLDER, exist_ok=True)

# =========================================================
# 5. YEARLY PAYROLL TREND
# =========================================================
query_yearly_trend = """
SELECT t.fiscal_year, SUM(fp.regular_gross_paid + fp.total_ot_paid + fp.total_other_pay) AS yearly_payroll
FROM fact_payroll fp JOIN dim_time t ON fp.time_id = t.time_id
GROUP BY t.fiscal_year ORDER BY t.fiscal_year;
"""
df_yearly_trend = pd.read_sql(query_yearly_trend, engine)

fig, ax = plt.subplots(figsize=(10, 5))
sns.lineplot(data=df_yearly_trend, x="fiscal_year", y="yearly_payroll", marker="o", color=PRIMARY_BLUE, linewidth=3, markersize=8, ax=ax)

# Style Cleanups
ax.set_title("Yearly Payroll Trend (2014 - 2017)", fontsize=15, pad=20, fontweight="bold", color="#111827")
ax.set_xlabel("Fiscal Year", fontsize=11, labelpad=10)
ax.set_ylabel("Total Payroll", fontsize=11, labelpad=10)
ax.set_xticks(df_yearly_trend["fiscal_year"].astype(int))
ax.set_ylim(0, df_yearly_trend["yearly_payroll"].max() * 1.15)
ax.yaxis.set_major_formatter(plt.FuncFormatter(format_currency))
ax.grid(axis='y', linestyle='--', color=GRID_GRAY)
sns.despine(left=True, bottom=False) # Remove unnecessary borders

# Add direct values above the markers to eliminate eye strain
for x, y in zip(df_yearly_trend["fiscal_year"], df_yearly_trend["yearly_payroll"]):
    ax.text(x, y + (df_yearly_trend["yearly_payroll"].max() * 0.03), format_currency(y, None), ha='center', va='bottom', fontsize=10, fontweight='bold', color=PRIMARY_BLUE)

plt.savefig(f"{CHART_FOLDER}/1_yearly_payroll_trend.png", bbox_inches="tight")
plt.close()

# =========================================================
# 6. TOP 10 AGENCIES
# =========================================================
query_top_agencies = """
SELECT UPPER(TRIM(a.agency_name)) AS cleaned_agency, SUM(fp.regular_gross_paid) AS total_salary
FROM fact_payroll fp JOIN dim_agency a ON fp.agency_id = a.agency_id
GROUP BY UPPER(TRIM(a.agency_name)) ORDER BY total_salary DESC LIMIT 10;
"""
df_top_agencies = pd.read_sql(query_top_agencies, engine)

fig, ax = plt.subplots(figsize=(12, 6))
bars = sns.barplot(data=df_top_agencies, x="total_salary", y="cleaned_agency", color=PRIMARY_BLUE, ax=ax, width=0.7)

ax.set_title("Top 10 Agencies by Total Base Salary Payroll", fontsize=15, pad=20, fontweight="bold", color="#111827")
ax.set_xlabel("Total Salary Expenditures", fontsize=11, labelpad=10)
ax.set_ylabel("")
ax.xaxis.set_major_formatter(plt.FuncFormatter(format_currency))
ax.grid(axis='x', linestyle='--', color=GRID_GRAY)
sns.despine(left=True, bottom=True)

# Direct Labeling at the tip of every bar
for bar in bars.patches:
    width = bar.get_width()
    ax.text(width + (df_top_agencies["total_salary"].max() * 0.01), bar.get_y() + bar.get_height()/2, format_currency(width, None), ha='left', va='center', fontsize=9, fontweight='bold', color="#374151")

plt.savefig(f"{CHART_FOLDER}/2_top_10_agencies.png", bbox_inches="tight")
plt.close()

# =========================================================
# 7. PAYROLL BY BOROUGH
# =========================================================
query_borough = """
SELECT UPPER(TRIM(l.borough)) AS cleaned_borough, SUM(fp.regular_gross_paid) AS total_salary
FROM fact_payroll fp JOIN dim_location l ON fp.location_id = l.location_id
GROUP BY UPPER(TRIM(l.borough)) ORDER BY total_salary DESC;
"""
df_borough = pd.read_sql(query_borough, engine)

fig, ax = plt.subplots(figsize=(10, 5))
bars = sns.barplot(data=df_borough, x="total_salary", y="cleaned_borough", color=SOFT_BLUE, ax=ax, width=0.6)

ax.set_title("Payroll Distribution Grouped by Borough", fontsize=15, pad=20, fontweight="bold", color="#111827")
ax.set_xlabel("Total Salary Allocation", fontsize=11, labelpad=10)
ax.set_ylabel("")
ax.xaxis.set_major_formatter(plt.FuncFormatter(format_currency))
ax.grid(axis='x', linestyle='--', color=GRID_GRAY)
sns.despine(left=True, bottom=True)

for bar in bars.patches:
    width = bar.get_width()
    if width > 0:
        ax.text(width + (df_borough["total_salary"].max() * 0.01), bar.get_y() + bar.get_height()/2, format_currency(width, None), ha='left', va='center', fontsize=9, fontweight='bold', color="#374151")

plt.savefig(f"{CHART_FOLDER}/3_borough_payroll_distribution.png", bbox_inches="tight")
plt.close()

# =========================================================
# 8. TOP JOB TITLES BY AVERAGE SALARY
# =========================================================
query_job_titles = """
SELECT UPPER(TRIM(dt.title_description)) AS cleaned_title, AVG(fp.base_salary) AS avg_salary
FROM fact_payroll fp JOIN dim_title dt ON fp.title_id = dt.title_id
GROUP BY UPPER(TRIM(dt.title_description)) ORDER BY avg_salary DESC LIMIT 10;
"""
df_job_titles = pd.read_sql(query_job_titles, engine)

fig, ax = plt.subplots(figsize=(12, 6))
bars = sns.barplot(data=df_job_titles, x="avg_salary", y="cleaned_title", color="#4B5563", ax=ax, width=0.7)

ax.set_title("Top 10 High Compensation Job Titles (Average Base)", fontsize=15, pad=20, fontweight="bold", color="#111827")
ax.set_xlabel("Average Individual Base Salary", fontsize=11, labelpad=10)
ax.set_ylabel("")
ax.xaxis.set_major_formatter(plt.FuncFormatter(format_currency))
ax.grid(axis='x', linestyle='--', color=GRID_GRAY)
sns.despine(left=True, bottom=True)

for bar in bars.patches:
    width = bar.get_width()
    ax.text(width + (df_job_titles["avg_salary"].max() * 0.01), bar.get_y() + bar.get_height()/2, format_currency(width, None), ha='left', va='center', fontsize=9, fontweight='bold', color="#374151")

plt.savefig(f"{CHART_FOLDER}/4_top_job_titles.png", bbox_inches="tight")
plt.close()

# =========================================================
# 9. OVERTIME ANALYSIS BY AGENCY
# =========================================================
query_overtime_agency = """
SELECT UPPER(TRIM(a.agency_name)) AS cleaned_agency, SUM(fp.total_ot_paid) AS overtime_cost
FROM fact_payroll fp JOIN dim_agency a ON fp.agency_id = a.agency_id
GROUP BY UPPER(TRIM(a.agency_name)) ORDER BY overtime_cost DESC LIMIT 10;
"""
df_overtime_agency = pd.read_sql(query_overtime_agency, engine)

fig, ax = plt.subplots(figsize=(12, 6))
bars = sns.barplot(data=df_overtime_agency, x="overtime_cost", y="cleaned_agency", color=HIGHLIGHT_RED, ax=ax, width=0.7)

ax.set_title("Top 10 Agencies by Total Overtime Expenditure Burden", fontsize=15, pad=20, fontweight="bold", color="#111827")
ax.set_xlabel("Total Overtime Funds Disbursed", fontsize=11, labelpad=10)
ax.set_ylabel("")
ax.xaxis.set_major_formatter(plt.FuncFormatter(format_currency))
ax.grid(axis='x', linestyle='--', color=GRID_GRAY)
sns.despine(left=True, bottom=True)

for bar in bars.patches:
    width = bar.get_width()
    ax.text(width + (df_overtime_agency["overtime_cost"].max() * 0.01), bar.get_y() + bar.get_height()/2, format_currency(width, None), ha='left', va='center', fontsize=9, fontweight='bold', color="#374151")

plt.savefig(f"{CHART_FOLDER}/5_top_overtime_agencies.png", bbox_inches="tight")
plt.close()

# =========================================================
# 10. PAY BASIS ANALYSIS
# =========================================================
query_pay_basis = """
SELECT UPPER(TRIM(pay_basis)) AS cleaned_basis, AVG(base_salary) AS average_salary
FROM fact_payroll GROUP BY UPPER(TRIM(pay_basis)) ORDER BY average_salary DESC;
"""
df_pay_basis = pd.read_sql(query_pay_basis, engine)

fig, ax = plt.subplots(figsize=(10, 4))
bars = sns.barplot(data=df_pay_basis, x="average_salary", y="cleaned_basis", color="#059669", ax=ax, width=0.5)

ax.set_title("Average Base Salary Structure by Pay Basis Type", fontsize=15, pad=20, fontweight="bold", color="#111827")
ax.set_xlabel("Average Salary Metric", fontsize=11, labelpad=10)
ax.set_ylabel("")
ax.xaxis.set_major_formatter(plt.FuncFormatter(format_currency))
ax.grid(axis='x', linestyle='--', color=GRID_GRAY)
sns.despine(left=True, bottom=True)

for bar in bars.patches:
    width = bar.get_width()
    ax.text(width + (df_pay_basis["average_salary"].max() * 0.01), bar.get_y() + bar.get_height()/2, format_currency(width, None), ha='left', va='center', fontsize=9, fontweight='bold', color="#374151")

plt.savefig(f"{CHART_FOLDER}/6_pay_basis_analysis.png", bbox_inches="tight")
plt.close()

# =========================================================
# 11. HEATMAP ANALYSIS
# =========================================================
query_heatmap = """
SELECT t.fiscal_year, UPPER(TRIM(l.borough)) AS cleaned_borough, SUM(fp.regular_gross_paid) AS total_salary
FROM fact_payroll fp JOIN dim_time t ON fp.time_id = t.time_id JOIN dim_location l ON fp.location_id = l.location_id
GROUP BY t.fiscal_year, UPPER(TRIM(l.borough));
"""
df_heatmap_raw = pd.read_sql(query_heatmap, engine)
df_pivot = df_heatmap_raw.pivot(index="cleaned_borough", columns="fiscal_year", values="total_salary").fillna(0)

fig, ax = plt.subplots(figsize=(10, 6))

# Clean format labels inside heatmap blocks (Using millions for text layout compatibility)
annot_labels = df_pivot.applymap(lambda x: f"${x*1e-6:.0f}M" if x > 0 else "$0M")

sns.heatmap(df_pivot, annot=annot_labels, fmt="", cmap="Blues", cbar=False, linewidths=1, linecolor="#FFFFFF", ax=ax, annot_kws={"size": 10, "weight": "bold"})

ax.set_title("Borough Payroll Density Matrix Across Fiscal Years", fontsize=14, pad=20, fontweight="bold", color="#111827")
ax.set_xlabel("Fiscal Operational Year", fontsize=11, labelpad=10)
ax.set_ylabel("")
plt.xticks(rotation=0)

plt.savefig(f"{CHART_FOLDER}/7_borough_yearly_heatmap.png", bbox_inches="tight")
plt.close()

print("\n" + "="*50)
print("SUCCESS! ALL PREMIUM EASY-TO-READ CHARTS SAVED.")
print("="*50)
