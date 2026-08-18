"""Live demo for PyCon JP 2026 - "Rediscovering DataFrames".

The pipeline from slides 14-15: same code, two engines, answers asserted
identical. Then the vector-search and time-series one-liners.

Run gen_demo_data.py first, then:  python demo.py
"""
import os
import time

HERE = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(HERE, 'access_log.parquet')


def pipeline(pd):
    logs = pd.read_parquet(LOG)                        # 10M rows
    slow = logs[logs.url.str.contains('/search/')]
    return round(float(slow.latency_ms.quantile(0.99)), 1)


def timed(label, pd):
    t = time.time()
    p99 = pipeline(pd)
    dt = time.time() - t
    print(f'{label:16s} p99 = {p99}   in {dt:.2f}s')
    return p99, dt


print('=== The swap: one import line ===')
import pandas
import chdb.datastore as datastore

pipeline(pandas)  # warm the page cache so the race is fair
a, t1 = timed('pandas', pandas)
b, t2 = timed('chdb.datastore', datastore)
assert a == b, 'answers differ!'
print(f'identical answers, {t1 / t2:.1f}x faster\n')

print('=== Vector search: a column and a sort ===')
import chdb.datastore as pd
from datastore import F

docs = pd.read_parquet(os.path.join(HERE, 'docs.parquet'))
# plain Python floats: numpy scalars would serialize as np.float32(...) strings
query_vec = [float(x) for x in
             pandas.read_parquet(os.path.join(HERE, 'docs.parquet'))['emb'][1]]
docs['dist'] = F.cosine_distance(docs.emb, F.array(*query_vec))
print(docs.sort_values('dist').head(3), '\n')

print('=== Time series: resample + rolling ===')
d = pd.read_parquet(os.path.join(HERE, 'sensor.parquet'))
print(d.resample('D', on='ts').value.mean().head(3))
d2 = pd.read_parquet(os.path.join(HERE, 'sensor.parquet'))
d2['ma24'] = d2.value.rolling(24).mean()
print(d2.head(3))
