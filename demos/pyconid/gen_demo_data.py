"""Generate the demo data for the PyCon ID 2026 talk
"Federated by Default: Building Agent Data Pipelines Without ETL".

Produces:
  orders.parquet   — 5,000 orders, served from https://auxten.com/demos/pyconid/orders.parquet
  crm_exports.tar  — users_2026q1.csv + users_2026q2.csv (100 users), queried in place with
                     file('crm_exports.tar :: users_*.csv')
                     (tar, not zip: chdb 26.1.0 ships without minizip)

The third source in the talk's join is a pandas DataFrame created at runtime.
Deterministic on purpose: slide outputs must be reproducible.
"""
import tarfile
import pandas as pd

orders = pd.DataFrame({
    "order_id": range(1, 5001),
    "user_id": [i % 100 + 1 for i in range(5000)],
    "amount": [round(9.99 + (i % 37) * 3.5, 2) for i in range(5000)],
    "country": [["ID", "SG", "MY", "TH", "VN"][i % 5] for i in range(5000)],
})
orders.to_parquet("orders.parquet")

tiers = ["free", "pro", "enterprise"]
q1 = pd.DataFrame({
    "user_id": range(1, 51),
    "name": [f"user_{i}" for i in range(1, 51)],
    "tier": [tiers[i % 3] for i in range(50)],
})
q2 = pd.DataFrame({
    "user_id": range(51, 101),
    "name": [f"user_{i}" for i in range(51, 101)],
    "tier": [tiers[i % 3] for i in range(50)],
})
q1.to_csv("users_2026q1.csv", index=False)
q2.to_csv("users_2026q2.csv", index=False)

with tarfile.open("crm_exports.tar", "w") as t:
    t.add("users_2026q1.csv")
    t.add("users_2026q2.csv")

print("orders.parquet:", len(orders), "rows; crm_exports.tar: 2 CSVs, 100 users")
