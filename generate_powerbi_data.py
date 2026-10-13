import sqlite3
import pandas as pd
from rapidfuzz import fuzz, process

print("Step 1/4: Ingesting raw OpenSanctions data...")
csv_file_path = r"C:\Users\jokya\Downloads\Data Analyst Projects\WISE-compliance-data-pipeline\targets.simple.csv"
db_path = r"C:\Users\jokya\Downloads\Data Analyst Projects\WISE-compliance-data-pipeline\wise_compliance_project.db"

# Read raw CSV in chunks and store in SQLite
conn = sqlite3.connect(db_path)
chunk_size = 100000

# Drop old raw table if re-running
conn.execute("DROP TABLE IF EXISTS tbl_opensanctions_raw;")
conn.commit()

for chunk in pd.read_csv(csv_file_path, chunksize=chunk_size, low_memory=False):
    chunk.columns = [c.lower().strip().replace(".", "_") for c in chunk.columns]
    chunk.to_sql("tbl_opensanctions_raw", conn, if_exists="append", index=False)

print("Step 2/4: Cleaning and normalizing sanctions data...")
# Drop old clean table if re-running
conn.execute("DROP TABLE IF EXISTS tbl_sanctions_clean;")

# Simple, foolproof schema creation using guaranteed columns (id, name, countries, schema)
sql_transform = """
CREATE TABLE tbl_sanctions_clean AS
SELECT 
    id,
    name AS name_clean,
    CASE WHEN countries IS NOT NULL THEN countries ELSE 'UNKNOWN' END AS country_code,
    'High Risk - Watchlist' AS risk_category
FROM tbl_opensanctions_raw
WHERE name IS NOT NULL;
"""
conn.execute(sql_transform)
conn.commit()

print("Step 3/4: Running compliance screening and audit engine...")
df_sanctions = pd.read_sql_query(
    "SELECT id, name_clean, risk_category, country_code FROM tbl_sanctions_clean WHERE name_clean IS NOT NULL LIMIT 50000;", 
    conn
)

# Expanded mock customer batch (1,000 records)
import random

first_names = ["Alexander", "Rahul", "Elena", "Viktor", "Johnathan", "Fatima", "Dmitri", "Aarav", "Mei", "Carlos", "Siddharth", "Olga", "Wei", "Zainab", "Lucas"]
last_names = ["Volkov", "Sharma", "Rostova", "Chen", "Smith", "Al-Hassan", "Ivanov", "Patel", "Wong", "Gomez", "Nair", "Smirnova", "Zhang", "Malik", "Silva"]
countries = ["US", "GB", "IN", "CA", "DE", "SG", "AE", "AU", "FR", "RU", "KP"]

mock_customers = []
for i in range(1, 1001):
    mock_customers.append({
        "customer_id": f"CUST-{i:04d}",
        "name": f"{random.choice(first_names)} {random.choice(last_names)}",
        "jurisdiction": random.choice(countries)
    })

audit_results = []
for cust in mock_customers:
    best_match = process.extractOne(
        cust["name"], 
        df_sanctions["name_clean"], 
        scorer=fuzz.token_sort_ratio
    )
    if best_match:
        matched_name, score, idx = best_match
        matched_row = df_sanctions.iloc[idx]
        
        # False positive mitigation rule
        if score >= 85 and cust["jurisdiction"] in str(matched_row["country_code"]):
            decision = "FLAGGED - CONFIRMED RISK"
        elif score >= 85:
            decision = "FALSE POSITIVE - COUNTRY MISMATCH"
        else:
            decision = "PASSED - LOW SCORE"
            
        audit_results.append({
            "customer_id": cust["customer_id"],
            "submitted_name": cust["name"],
            "submitted_jurisdiction": cust["jurisdiction"],
            "matched_sanction_name": matched_name,
            "matched_country": matched_row["country_code"],
            "name_score": score,
            "risk_category": matched_row["risk_category"],
            "decision": decision
        })

df_audit = pd.DataFrame(audit_results)
df_audit.to_sql("tbl_kyc_screening_audit", conn, if_exists="replace", index=False)

print("Step 4/4: Exporting final audit results to CSV...")
csv_export_path = r"C:\Users\jokya\Downloads\Data Analyst Projects\WISE-compliance-data-pipeline\kyc_screening_audit.csv"
df_audit.to_csv(csv_export_path, index=False)
conn.close()

print("\nSUCCESS! All processing complete. You can now load 'kyc_screening_audit.csv' directly into Power BI.")