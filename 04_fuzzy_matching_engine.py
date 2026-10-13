import sqlite3
import pandas as pd
from rapidfuzz import fuzz, process

conn = sqlite3.connect("wise_compliance_project.db")

# 1. Simulated incoming Wise customer transfers/onboarding batch
incoming_customers = [
    {"customer_id": "CUST_101", "submitted_name": "James Wilson", "country": "US"},
    {"customer_id": "CUST_102", "submitted_name": "Sanavbari Nikitenko", "country": "TJ"},
    {"customer_id": "CUST_103", "submitted_name": "Abrau", "country": "RU"},
    {"customer_id": "CUST_104", "submitted_name": "Rahul Sharma", "country": "IN"},
]

print("Loading reference sanction names from SQL database...")
# Pull target names for comparison
df_sanctions = pd.read_sql_query("SELECT id, name_clean, risk_category, country_code FROM tbl_sanctions_clean WHERE name_clean IS NOT NULL;", conn)
sanction_names = df_sanctions['name_clean'].tolist()

print(f"Loaded {len(sanction_names):,} target names for matching.\n")

results = []

# 2. Perform Fuzzy Matching per incoming customer
for cust in incoming_customers:
    query_name = cust["submitted_name"].upper().strip()
    
    # Extract top match score using RapidFuzz
    match = process.extractOne(query_name, sanction_names, scorer=fuzz.token_sort_ratio)
    
    if match:
        matched_name, score, index = match
        matched_row = df_sanctions.iloc[index]
        
        # Categorize risk score based on screening threshold
        if score >= 85:
            decision = "FLAGGED - MANUAL REVIEW"
        elif score >= 70:
            decision = "POTENTIAL MATCH"
        else:
            decision = "PASSED"

        results.append({
            "Customer ID": cust["customer_id"],
            "Submitted Name": cust["submitted_name"],
            "Matched Sanction Name": matched_name,
            "Similarity Score": round(score, 2),
            "Decision": decision,
            "Risk Category": matched_row["risk_category"],
            "Sanction ID": matched_row["id"]
        })

# 3. Output Screening Summary
df_results = pd.DataFrame(results)
print("=== KYC & SANCTIONS SCREENING PIPELINE RESULTS ===")
print(df_results[["Customer ID", "Submitted Name", "Matched Sanction Name", "Similarity Score", "Decision"]])

# 4. Save results to SQL table for Power BI reporting
df_results.to_sql("tbl_kyc_screening_audit", conn, if_exists="replace", index=False)
print("\nResults successfully saved to 'tbl_kyc_screening_audit' table!")

conn.close()