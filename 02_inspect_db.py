import pandas as pd
import sqlite3

# Connect to your SQLite database
conn = sqlite3.connect("wise_compliance_project.db")

# 1. Preview first 3 rows using correct column names
df_sample = pd.read_sql_query(
    "SELECT id, schema, name, countries FROM tbl_opensanctions_raw LIMIT 5;",
    conn,
)

print("=== SAMPLE DATA FROM DATABASE ===")
print(df_sample)

conn.close()