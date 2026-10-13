import sqlite3
import pandas as pd

conn = sqlite3.connect("wise_compliance_project.db")
cursor = conn.cursor()

print("Creating normalized SQL table 'tbl_sanctions_clean'...")

# 1. Drop existing clean table if re-running
cursor.execute("DROP TABLE IF EXISTS tbl_sanctions_clean;")

# 2. SQL to transform, normalize strings, and clean target entities
sql_transform = """
CREATE TABLE tbl_sanctions_clean AS
SELECT 
    id,
    schema AS entity_type,
    UPPER(TRIM(name)) AS name_clean,
    UPPER(TRIM(aliases)) AS aliases_clean,
    birth_date,
    UPPER(TRIM(countries)) AS country_code,
    sanctions,
    dataset,
    CASE 
        WHEN schema = 'Person' THEN 'Individual'
        WHEN schema IN ('Company', 'Organization', 'LegalEntity') THEN 'Corporate'
        ELSE 'Other Entity'
    END AS risk_category
FROM tbl_opensanctions_raw
WHERE name IS NOT NULL AND TRIM(name) != '';
"""

cursor.execute(sql_transform)
conn.commit()

# 3. Create SQL index on clean names to make fuzzy queries super fast
print("Building SQL index on clean names...")
cursor.execute("CREATE INDEX idx_sanctions_name ON tbl_sanctions_clean(name_clean);")
conn.commit()

# 4. Verify record count in clean table
df_check = pd.read_sql_query("SELECT risk_category, COUNT(*) as count FROM tbl_sanctions_clean GROUP BY risk_category;", conn)
print("\n=== CLEAN DATASET DISTRIBUTION ===")
print(df_check)

conn.close()
print("\nTransformation complete! 'tbl_sanctions_clean' is ready.")