"""Generate demo data for the PyCon JP 2026 talk
"Rediscovering DataFrames: 100x Analytics Without Leaving Pandas".

Creates (in this directory):
  access_log.parquet  10M rows, ~104 MB  (NOT committed - regenerate before the talk)
  sensor.parquet      1,000 hourly readings
  docs.parquet        5 docs with non-nullable Float32 embeddings (vector demo)

Run:  python gen_demo_data.py
"""
import os

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

HERE = os.path.dirname(os.path.abspath(__file__))
rng = np.random.default_rng(7)

# --- access_log.parquet: 10M rows of synthetic web logs -------------------
n = 10_000_000
paths = np.char.add('/api/v2/', rng.choice(
    ['users', 'orders', 'search', 'billing', 'auth', 'export'], n))
ids = rng.integers(1, 10**6, n).astype(str)
pd.DataFrame({
    'url': np.char.add(np.char.add(paths, '/'), ids),
    'status': rng.choice([200, 200, 200, 404, 500], n),
    'latency_ms': rng.exponential(80, n).round(1),
}).to_parquet(os.path.join(HERE, 'access_log.parquet'))
print('access_log.parquet:', n, 'rows')

# --- sensor.parquet: 1,000 hourly readings for resample/rolling -----------
rng2 = np.random.default_rng(42)
pd.DataFrame({
    'ts': pd.date_range('2026-01-01', periods=1000, freq='h'),
    'value': rng2.normal(100, 10, 1000).round(2),
}).to_parquet(os.path.join(HERE, 'sensor.parquet'))
print('sensor.parquet: 1000 rows')

# --- docs.parquet: embeddings for the vector-search demo ------------------
# GOTCHA (on the honesty slide): cosineDistance needs NON-NULLABLE Float32
# arrays. pandas.to_parquet writes Nullable(Float64) - use explicit pyarrow
# schema instead.
texts = ['refund policy', 'api rate limits', 'billing question',
         'login issue', 'shipping delay']
embs = [rng2.normal(0, 1, 8).astype('float32').tolist() for _ in texts]
schema = pa.schema([
    pa.field('id', pa.int64(), nullable=False),
    pa.field('text', pa.string(), nullable=False),
    pa.field('emb', pa.list_(pa.field('item', pa.float32(), nullable=False)),
             nullable=False),
])
pq.write_table(
    pa.table({'id': list(range(5)), 'text': texts, 'emb': embs}, schema=schema),
    os.path.join(HERE, 'docs.parquet'))
print('docs.parquet: 5 rows (Float32 non-nullable embeddings)')
