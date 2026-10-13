import sqlite3
import pandas as pd
from rapidfuzz import fuzz, process

conn = sqlite3.connect("wise_compliance_project.db")

# Customer batch with country context
customer_batch = [
    {"customer_id": "CUST_201", "submitted_name": "Jams O Wilson", "country": "US"},        
    {"customer_id": "CUST_202", "submitted_name": "Sanavbari Nikitenko", "country": "TJ"},  
    {"customer_id": "CUST_203", "submitted_name": "Abrau Co", "country": "RU"},            
    {"customer_id": "CUST_204", "submitted_name": "Rahul Sharma", "country": "IN"},         
    {"customer_id": "CUST_205", "submitted_name": "Alexander Smith", "country": "GB"},      
    {"customer_id": "CUST_206", "submitted_name": "Matteo Rossi", "country": "IT"},         
]

df_sanctions = pd.read_sql_query(
    "SELECT id, name_clean, risk_category, country_code FROM tbl_sanctions_clean WHERE name_clean IS NOT NULL;", 
    conn
)
sanction_names = df_sanctions['name_clean'].tolist()

results = []

for cust in customer_batch:
    query_name = cust["submitted_name"].upper().strip()
    cust_country = cust["country"].upper()
    
    # 1. Primary Name Match
    match = process.extractOne(query_name, sanction_names, scorer=fuzz.token_sort_ratio)
    
    if match:
        matched_name, name_score, index = match
        matched_row = df_sanctions.iloc[index]
        sanction_countries = str(matched_row["country_code"]).upper()
        
        # 2. Secondary Verification: Country Check
        country_match = cust_country in sanction_countries if sanction_countries != 'NONE' else False
        
        # 3. Decision Logic with False Positive Mitigation
        if name_score >= 85 and country_match:
            decision = "FLAGGED - CONFIRMED RISK"
            priority = "HIGH"
        elif name_score >= 85 and not country_match:
            decision = "FALSE POSITIVE - COUNTRY MISMATCH"
            priority = "LOW"
        elif name_score >= 70:
            decision = "REVIEW - MEDIUM RISK"
            priority = "MEDIUM"
        else:
            decision = "PASSED"
            priority = "LOW"

        results.append({
            "customer_id": cust["customer_id"],
            "submitted_name": cust["submitted_name"],
            "customer_country": cust_country,
            "matched_sanction_name": matched_name,
            "sanction_countries": sanction_countries,
            "name_score": round(name_score, 2),
            "country_match": country_match,
            "decision": decision,
            "priority": priority,
            "risk_category": matched_row["risk_category"],
            "sanction_id": matched_row["id"]
        })

df_results = pd.DataFrame(results)

print("=== REFINED COMPLIANCE SCREENING RESULTS ===")
print(df_results[["customer_id", "submitted_name", "customer_country", "name_score", "country_match", "decision"]])

# Update final audit log table in SQL
df_results.to_sql("tbl_kyc_screening_audit", conn, if_exists="replace", index=False)
conn.close()

print("\nSaved refined audit dataset to 'tbl_kyc_screening_audit'.")