"""Peak-RSS per op per engine, each in a fresh subprocess (clean ru_maxrss).
Usage: mem20.py            -> orchestrate all 40 runs, print table + JSON
       mem20.py ENGINE IDX -> run one op once, print peak RSS bytes
"""
import json, os, subprocess, sys

PATH = '/tmp/big_orders.parquet'
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mem20_results.json')
PY = sys.executable

OPS_SRC = '''
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
    d = pd.read_parquet(PATH); t = d.amount.mask(d.amount > 100, 100); return round(float(t.sum()), 1)
OPS = [_f01,_f02,_f03,_f04,_f05,_f06,_f07,_f08,_f09,_f10,_f11,_f12,_f13,_f14,_f15,_f16,_f17,_f18,_f19,_f20]
'''

NAMES = ['Filter (single)', 'Filter (multi AND)', 'Sort (single col)', 'Sort (multi col)',
         'GroupBy count', 'GroupBy agg x3', 'Head / limit', 'Filter+GroupBy+mean',
         'Multi-filter (4x)', 'Filter+Select+Sort', 'Filter+GroupBy+Sort', 'Complex pipeline',
         'Chain 5 filters', 'Ultra-complex chain', 'Filter+Sort+Head', 'Filter+Sort+Select',
         'Mixed Filter+Sort', 'Where (replace)', 'Filter+Where', 'Mask (replace)']

CHILD = '''
import resource, sys
PATH = {path!r}
engine, idx = sys.argv[1], int(sys.argv[2])
if engine == 'pandas':
    import pandas as mod
else:
    import chdb.datastore as mod
{ops}
r = OPS[idx](mod)
s = str(r)  # materialize
print(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
'''

def main():
    results = []
    for i, name in enumerate(NAMES):
        row = {'op': name}
        for engine in ('pandas', 'datastore'):
            code = CHILD.format(path=PATH, ops=OPS_SRC)
            p = subprocess.run([PY, '-c', code, engine, str(i)], capture_output=True, text=True)
            rss = None
            for line in reversed(p.stdout.strip().splitlines()):
                if line.strip().isdigit():
                    rss = int(line.strip())
                    break
            if rss is None:
                row[engine + '_err'] = (p.stderr or p.stdout)[-200:]
            else:
                row[engine + '_mb'] = round(rss / 1e6)
        if row.get('pandas_mb') and row.get('datastore_mb'):
            row['mem_ratio'] = round(row['pandas_mb'] / row['datastore_mb'], 2)
        print(f"{name:24s} pandas={row.get('pandas_mb')}MB ds={row.get('datastore_mb')}MB x{row.get('mem_ratio', '-')}")
        results.append(row)
    with open(OUT, 'w') as f:
        json.dump(results, f, indent=1)
    pm = sorted(r['pandas_mb'] for r in results if r.get('pandas_mb'))
    dm = sorted(r['datastore_mb'] for r in results if r.get('datastore_mb'))
    if pm and dm:
        print(f"\npandas   peak RSS: min {pm[0]} / median {pm[len(pm)//2]} / max {pm[-1]} MB")
        print(f"datastore peak RSS: min {dm[0]} / median {dm[len(dm)//2]} / max {dm[-1]} MB")
    print('->', OUT)

if __name__ == '__main__':
    main()
