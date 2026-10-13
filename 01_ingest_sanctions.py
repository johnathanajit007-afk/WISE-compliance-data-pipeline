import os
import pandas as pd
import sqlite3

# 1. Update this path if your file is saved somewhere other than your Downloads folder
csv_file_path = os.path.expanduser("~/Downloads/targets.simple.csv")
db_name = "wise_compliance_project.db"

# 2. Check if the CSV file exists
if not os.path.exists(csv_file_path):
    print(f"Error: Could not find file at {csv_file_path}")
    print("Please check where targets.simple.csv was saved and update 'csv_file_path'.")
else:
    print(f"File found! Connecting to database: {db_name}...")
    conn = sqlite3.connect(db_name)

    # 3. Process the ~440MB file in chunks of 50,000 rows
    chunk_size = 50000
    chunk_count = 0

    print("Starting ingestion in chunks...")

    for chunk in pd.read_csv(
        csv_file_path, chunksize=chunk_size, low_memory=False
    ):
        # Save chunk into SQL table 'tbl_opensanctions_raw'
        chunk.to_sql(
            "tbl_opensanctions_raw",
            conn,
            if_exists="append" if chunk_count > 0 else "replace",
            index=False,
        )

        chunk_count += 1
        print(f"Processed chunk {chunk_count}: {chunk_count * chunk_size:,} rows loaded...")

    print("\nSUCCESS: All data imported into 'wise_compliance_project.db'!")
    conn.close()