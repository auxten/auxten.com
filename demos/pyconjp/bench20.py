"""20-op pandas vs datastore benchmark for PyCon JP slide 11.
Each op: read 10M-row parquet -> compute -> materialize. Parity-checked, best-of-2 after warmup.
"""
import json, os, time
import numpy as np
import pandas as rpd
import chdb.datastore as dstore

PATH = '/tmp/big_orders.parquet'
OUT = os.path.join(os.path.dirname(__file__), 'bench20_results.json')

if not os.path.exists(PATH):
    rng = np.random.default_rng(42)
    n = 10_000_000
    rpd.DataFrame({
        'row_id': np.arange(n, dtype='int64'),
        'user_id': rng.integers(0, 100_000, n),
        'country': rng.choice(['SG', 'JP', 'ID', 'VN', 'TH', 'MY'], n),
        'amount': rng.exponential(50, n).round(2),
    }).to_parquet(PATH)
    print('regenerated', PATH)

OPS = [
    ('Filter (single)',          lambda pd: len(pd.read_parquet(PATH)[lambda d: None] if False else pd.read_parquet(PATH)[pd.read_parquet(PATH).amount > 90])),
]
# simpler explicit builders (df captured per call)
def op(name):
    def deco(fn):
        return (name, fn)
    return deco

def _f01(pd):
    d = pd.read_parquet(PATH); return len(d[d.amount > 90])
def _f02(pd):
    d = pd.read_parquet(PATH); return len(d[(d.amount > 50) & (d.country == 'JP')])
def _f03(pd):
    d = pd.read_parquet(PATH); return d.sort_values(['amount', 'row_id'], ascending=[False, True]).head(5)
def _f04(pd):
    d = pd.read_parquet(PATH); return d.sort_values(['country', 'amount', 'row_id'], ascending=[True, False, True]).head(5)
def _f05(pd):
    d = pd.read_parquet(PATH); return d.groupby('country').amount.count()
def _f06(pd):
    d = pd.read_parquet(PATH); return d.groupby('country').amount.agg(['mean', 'sum', 'count'])
def _f07(pd):
    d = pd.read_parquet(PATH); return d.head(10)
def _f08(pd):
    d = pd.read_parquet(PATH); return d[d.amount > 50].groupby('country').amount.mean()
def _f09(pd):
    d = pd.read_parquet(PATH); return len(d[(d.amount > 20) & (d.amount < 95) & (d.user_id > 1000) & (d.country != 'SG')])
def _f10(pd):
    d = pd.read_parquet(PATH); return d[d.amount > 80][['row_id', 'amount']].sort_values(['amount', 'row_id'], ascending=[False, True]).head(5)
def _f11(pd):
    d = pd.read_parquet(PATH); return d[d.amount > 30].groupby('user_id').amount.sum().sort_values(ascending=False).head(10)
def _f12(pd):
    d = pd.read_parquet(PATH); return d[(d.amount > 10) & (d.amount < 200)].groupby('country').amount.agg(['sum', 'mean']).sort_values('sum', ascending=False)
def _f13(pd):
    d = pd.read_parquet(PATH)
    r = d[d.amount > 10]; r = r[r.amount < 99]; r = r[r.user_id > 500]; r = r[r.user_id < 99000]; r = r[r.country != 'VN']
    return len(r)
def _f14(pd):
    d = pd.read_parquet(PATH)
    return d[(d.amount > 5) & (d.user_id > 100)][['user_id', 'country', 'amount']].groupby('country').amount.agg(['mean', 'count']).sort_values('count', ascending=False).head(3)
def _f15(pd):
    d = pd.read_parquet(PATH); return d[d.country == 'JP'].sort_values(['amount', 'row_id'], ascending=[False, True]).head(10)
def _f16(pd):
    d = pd.read_parquet(PATH); return d[d.amount > 60].sort_values('row_id')[['country', 'amount']].head(10)
def _f17(pd):
    d = pd.read_parquet(PATH); return d[d.amount > 40][['row_id', 'country', 'amount']].sort_values(['amount', 'row_id'], ascending=[False, True]).head(10)
def _f18(pd):
    d = pd.read_parquet(PATH); return round(float(d.amount.where(d.amount < 100, 100).sum()), 1)
def _f19(pd):
    d = pd.read_parquet(PATH); t = d[d.country != 'VN']; return round(float(t.amount.where(t.amount < 100, 100).sum()), 1)
def _f20(pd):
    d = pd.read_parquet(PATH); return round(float(d.amount.mask(d.amount > 100, 100).sum()), 1)

OPS = [
    ('Filter (single)', _f01), ('Filter (multi AND)', _f02),
    ('Sort (single col)', _f03), ('Sort (multi col)', _f04),
    ('GroupBy count', _f05), ('GroupBy agg x3', _f06),
    ('Head / limit', _f07), ('Filter+GroupBy+mean', _f08),
    ('Multi-filter (4x)', _f09), ('Filter+Select+Sort', _f10),
    ('Filter+GroupBy+Sort', _f11), ('Complex pipeline', _f12),
    ('Chain 5 filters', _f13), ('Ultra-complex chain', _f14),
    ('Filter+Sort+Head', _f15), ('Filter+Sort+Select', _f16),
    ('Mixed Filter+Sort', _f17), ('Where (replace)', _f18),
    ('Filter+Where', _f19), ('Mask (replace)', _f20),
]

def canon(x):
    if hasattr(x, 'to_pandas'):
        x = x.to_pandas()
    if isinstance(x, rpd.DataFrame):
        return x.reset_index(drop=True).round(2).to_csv(index=False)
    if isinstance(x, rpd.Series):
        return x.round(2).to_csv()
    return repr(x)

def materialize(x):
    if isinstance(x, (int, float)):
        return x
    return str(x)  # repr triggers lazy execution

results = []
for name, fn in OPS:
    row = {'op': name}
    try:
        row['match'] = canon(fn(rpd)) == canon(fn(dstore))
    except Exception as e:
        row['match'] = False
        row['error'] = f'{type(e).__name__}: {e}'[:200]
    for label, mod in (('pandas', rpd), ('datastore', dstore)):
        try:
            times = []
            for _ in range(2):
                t = time.time(); materialize(fn(mod)); times.append(time.time() - t)
            row[label] = round(min(times) * 1000)
        except Exception as e:
            row[label] = None
            row.setdefault('error', f'{type(e).__name__}: {e}'[:200])
    if row.get('pandas') and row.get('datastore'):
        row['speedup'] = round(row['pandas'] / row['datastore'], 2)
    print(f"{name:24s} match={str(row.get('match')):5s} pandas={row.get('pandas')}ms ds={row.get('datastore')}ms x{row.get('speedup', '-')}"
          + ('  ERR ' + row['error'] if 'error' in row else ''))
    results.append(row)

with open(OUT, 'w') as f:
    json.dump(results, f, indent=1)
wins = sum(1 for r in results if r.get('speedup') and r['speedup'] > 1 and r.get('match'))
ok = sum(1 for r in results if r.get('match'))
print(f'\nDataStore wins {wins}/{len(results)}  ·  parity OK {ok}/{len(results)}  ->  {OUT}')
