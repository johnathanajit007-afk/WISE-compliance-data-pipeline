import sqlite3
import pandas as pd
from rapidfuzz import fuzz, process

conn = sqlite3.connect("wise_compliance_project.db")

# Real-world test batch with typos, partial names, and clear passes
customer_batch = [
    {"customer_id": "CUST_201", "submitted_name": "Jams O Wilson", "country": "US"},        # Typo
    {"customer_id": "CUST_202", "submitted_name": "Sanavbari Nikitenko", "country": "TJ"},  # Exact
    {"customer_id": "CUST_203", "submitted_name": "Abrau Co", "country": "RU"},            # Slight variation
    {"customer_id": "CUST_204", "submitted_name": "Rahul Sharma", "country": "IN"},         # Common Name / Match
    {"customer_id": "CUST_205", "submitted_name": "Alexander Smith", "country": "GB"},      # Clean Pass / Low Score
    {"customer_id": "CUST_206", "submitted_name": "Matteo Rossi", "country": "IT"},         # Clean Pass / Low Score
]

df_sanctions = pd.read_sql_query("SELECT id, name_clean, risk_category, country_code FROM tbl_sanctions_clean WHERE name_clean IS NOT NULL;", conn)
sanction_names = df_sanctions['name_clean'].tolist()

results = []

for cust in customer_batch:
    query_name = cust["submitted_name"].upper().strip()
    match = process.extractOne(query_name, sanction_names, scorer=fuzz.token_sort_ratio)
    
    if match:
        matched_name, score, index = match
        matched_row = df_sanctions.iloc[index]
        
        # Wise Thresholding Logic
        if score >= 88:
            decision = "FLAGGED - HIGH RISK"
        elif score >= 70:
            decision = "REVIEW - MEDIUM RISK"
        else:
            decision = "PASSED"

        results.append({
            "customer_id": cust["customer_id"],
            "submitted_name": cust["submitted_name"],
            "matched_sanction_name": matched_name,
            "similarity_score": round(score, 2),
            "decision": decision,
            "risk_category": matched_row["risk_category"],
            "sanction_id": matched_row["id"]
        })

df_results = pd.DataFrame(results)

print("=== EXPANDED SCREENING RESULTS ===")
print(df_results[["customer_id", "submitted_name", "matched_sanction_name", "similarity_score", "decision"]])

# Update audit table in SQL
df_results.to_sql("tbl_kyc_screening_audit", conn, if_exists="replace", index=False)
conn.close()

print("\nUpdated 'tbl_kyc_screening_audit' successfully.")