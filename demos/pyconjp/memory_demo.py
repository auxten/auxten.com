"""Agent-memory recall in ONE chDB query — vector + metadata + recency, no servers.

Builds a small memory table (memory.parquet), then runs the exact query shown
on the PyCon JP 2026 slide. The embeddings are synthetic 8-dim vectors; the
"query vector" is placed near the 'prefers dark mode' memory of user u1 so the
semantic recall is verifiable: that row must come back first, at distance ~0.

Run:  python memory_demo.py
"""
import time

import chdb
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

DIM = 8
rng = np.random.default_rng(7)

texts_u1 = ['prefers dark mode', 'timezone is JST', 'billing plan: pro',
            'deploys on Fridays', 'asked about S3 costs', 'hates YAML',
            'python 3.13 user', 'okonomiyaki: hiroshima-style']
rows = []
now = pd.Timestamp.utcnow().floor('s')
for u in ('u1', 'u2', 'u3'):
    for i, t in enumerate(texts_u1):
        rows.append({
            'user_id': u,
            'ts': now - pd.Timedelta(days=int(rng.integers(1, 90))),
            'text': t if u == 'u1' else f'{t} ({u})',
            'emb': rng.normal(0, 1, DIM).astype('float32'),
        })

q_vec = rng.normal(0, 1, DIM).astype('float32')
# the memory we expect back first: recent, u1, embedded next to the query
rows[0]['ts'] = now - pd.Timedelta(days=2)
rows[0]['emb'] = (q_vec + rng.normal(0, 0.05, DIM)).astype('float32')
# a decoy: semantically close but too old — the recency filter must drop it
rows[5]['ts'] = now - pd.Timedelta(days=80)
rows[5]['emb'] = (q_vec + rng.normal(0, 0.05, DIM)).astype('float32')

schema = pa.schema([
    pa.field('user_id', pa.string(), nullable=False),
    pa.field('ts', pa.timestamp('s'), nullable=False),
    pa.field('text', pa.string(), nullable=False),
    pa.field('emb', pa.list_(pa.field('item', pa.float32(), nullable=False), DIM), nullable=False),
])
pq.write_table(pa.table({
    'user_id': [r['user_id'] for r in rows],
    'ts': np.array([r['ts'].to_datetime64() for r in rows]).astype('datetime64[s]'),
    'text': [r['text'] for r in rows],
    'emb': [r['emb'] for r in rows],
}, schema=schema), 'memory.parquet')

qv = ', '.join(f'{x:.4f}' for x in q_vec)
sql = f"""
SELECT text, round(cosineDistance(emb, [{qv}]), 3) AS dist
FROM file('memory.parquet')
WHERE user_id = 'u1' AND ts > now() - INTERVAL 30 DAY
ORDER BY cosineDistance(emb, [{qv}])
LIMIT 3
"""
t0 = time.time()
out = chdb.query(sql, 'PrettyCompactNoEscapes').data()
ms = (time.time() - t0) * 1000
print(out)
print(f'{ms:.1f} ms — one query: vector + metadata + recency')

assert 'prefers dark mode' in out.splitlines()[1], 'semantic recall failed'
assert 'hates YAML' not in out, 'recency filter failed (80-day-old decoy leaked)'
print('recall verified: nearest memory first, stale decoy filtered')
