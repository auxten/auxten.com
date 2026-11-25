"""Demo data for "Giving Your AI Agent a Database Brain" (ClickHouse meetup, Singapore, 2026-11-26).

One fictional user's agent memory (acme / mei), embedded with a real model:
Qwen/Qwen3-Embedding-0.6B, first 128 dimensions, re-normalised. Text is synthetic.

  memory.parquet    id, kind, status, ts, ref, text, emb
  questions.parquet id, question, words, emb   (preset questions; the browser cannot embed text)
  orders.parquet    20,000 synthetic orders: order_id, market, promised, delivered, amount

Run: HF_HUB_OFFLINE=1 python gen_memory.py
"""
import numpy as np, pyarrow as pa, pyarrow.parquet as pq
from datetime import datetime, timedelta

DIM = 128
M = [  # kind, status, date, ref, text
 ("preference","superseded","2026-06-03","","Mei wants weekly status updates as a long email on Friday afternoon."),
 ("preference","active","2026-10-12","","Mei now prefers status updates as three bullets in Slack, posted before 9am on Monday."),
 ("preference","active","2026-08-21","","Mei reads charts on her phone, so keep tables under four columns."),
 ("preference","active","2026-07-15","","Mei writes British English and dislikes exclamation marks."),
 ("preference","active","2026-09-02","","When two options are close, Mei wants one recommendation rather than a list."),
 ("preference","active","2026-05-19","","Mei does not take meetings on Wednesday afternoons because of school pickup."),
 ("preference","superseded","2026-04-08","","Mei likes dashboards in light mode."),
 ("preference","active","2026-09-28","","Mei switched every dashboard to dark mode after the eye exam in September."),
 ("fact","active","2026-03-11","","Mei is the operations lead for South-East Asia at Acme."),
 ("fact","active","2026-10-01","SG","Mei owns the Singapore market since October."),
 ("fact","active","2026-10-01","VN","Mei owns the Vietnam market since October."),
 ("fact","superseded","2026-03-11","ID","Mei owned the Indonesia market until the end of September."),
 ("fact","active","2026-06-30","","Acme closes its books on the third working day of each month."),
 ("fact","active","2026-07-22","","The staging warehouse is refreshed every night at 02:00 Singapore time."),
 ("fact","active","2026-08-05","","Refunds above 500 dollars need approval from finance, usually Arun."),
 ("fact","active","2026-09-17","","The courier API rate limit is 120 requests per minute per region."),
 ("fact","active","2026-02-14","","Mei's manager is Priya, and Priya reads only the first paragraph."),
 ("decision","superseded","2026-05-06","","Team decided to keep exporting orders to spreadsheets every week."),
 ("decision","active","2026-09-09","","Team decided to stop the weekly spreadsheet export and query the Parquet files directly."),
 ("decision","active","2026-08-18","","Late deliveries are counted from the promised date, not from the dispatch date."),
 ("decision","active","2026-10-20","","From November the Vietnam launch budget is tracked separately from Singapore."),
 ("decision","active","2026-07-03","","We do not email customers about delays shorter than one day."),
 ("decision","active","2026-06-11","","Duplicate orders are merged on order_id, keeping the latest version."),
 ("incident","active","2026-09-23","ERR-4417","ERR-4417 was a courier webhook timeout; the fix was to raise the client timeout to 30 seconds."),
 ("incident","active","2026-10-07","ERR-4471","ERR-4471 was an expired signing certificate on the returns portal."),
 ("incident","active","2026-08-30","ERR-4147","ERR-4147 was a duplicate payment callback and was closed without a code change."),
 ("incident","active","2026-07-27","ERR-3902","ERR-3902 came from a full disk on the label printer host in Johor."),
 ("incident","active","2026-10-29","","Deliveries in Ho Chi Minh City were late for two days because of flooding."),
 ("incident","active","2026-06-19","","The night refresh failed twice in June when the source schema added a column."),
 ("incident","active","2026-11-10","","Payment retries doubled on 10 November after the bank changed its 3DS page."),
 ("procedure","active","2026-09-30","","For a courier timeout, check the region queue first, then replay the webhook from the console."),
 ("procedure","active","2026-08-12","","To answer a late delivery question, look up the promised date, the carrier scan and the customer tier."),
 ("procedure","active","2026-07-08","","Before sending numbers to Priya, reconcile them with the finance extract."),
 ("procedure","active","2026-05-27","","Month-end: freeze the refunds sheet, run the duplicate check, then post the summary."),
 ("procedure","active","2026-10-15","","When the rate limit is hit, back off for one minute and split the batch by region."),
 ("task","active","2026-11-18","","Open: draft the Vietnam launch readout for Priya by Friday 27 November."),
 ("task","active","2026-11-20","","Open: ask Arun whether the 620 dollar refund for the Da Nang order was approved."),
 ("task","superseded","2026-10-02","","Open: book the meeting room for the October quarterly review."),
 ("task","active","2026-11-23","","Open: compare courier on-time rate in Singapore before and after the timeout fix."),
]
# Everyday conversation history, so the memory is not only hand-picked highlights.
topics = [
 "asked for yesterday's order count in {c}", "asked why {c} revenue dipped on {d}", "asked to rename a column in the {c} report",
 "asked for the top ten customers in {c}", "asked to translate a customer reply for {c}", "asked how many returns {c} had on {d}",
 "asked for the courier on-time rate in {c}", "asked to check stock of SKU-{n} in {c}", "asked to summarise the {d} stand-up",
 "asked to move the {c} review to {d}", "asked whether SKU-{n} is still on promotion in {c}", "asked for the refund total in {c} on {d}",
]
cities = ["Singapore","Vietnam","Malaysia","Thailand","Indonesia"]
days = ["Monday","Tuesday","Wednesday","Thursday","Friday"]
start = datetime(2026, 8, 1, 1, 30)
for i in range(273):
    t = topics[(i * 7) % len(topics)].format(c=cities[(i * 3) % 5], d=days[(i * 2) % 5], n=1000 + (i * 37) % 900)
    M.append(("history", "active", (start + timedelta(hours=9 * i)).strftime("%Y-%m-%d"), "", f"Mei {t}."))

Q = [
 (1, "How should I send Mei the weekly update?", ["status", "updates", "weekly"]),
 (2, "What was ERR-4417 and how was it fixed?", ["4417"]),
 (3, "A courier call is timing out again. What do we know?", ["courier", "timeout"]),
 (4, "What do I need before I write the Vietnam readout for Priya?", ["Vietnam", "Priya", "readout"]),
]

if __name__ == "__main__":
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer("Qwen/Qwen3-Embedding-0.6B", device="cpu")
    def emb(texts, **kw):
        v = np.asarray(model.encode(texts, batch_size=16, normalize_embeddings=True, **kw), dtype=np.float32)[:, :DIM]
        return v / np.linalg.norm(v, axis=1, keepdims=True)
    mv = emb([m[4] for m in M]); qv = emb([q[1] for q in Q], prompt_name="query")
    f32 = pa.list_(pa.field("element", pa.float32(), nullable=False))
    strs = pa.list_(pa.field("element", pa.string(), nullable=False))
    def table(**cols):  # name=(values, type); nothing is nullable, so the engine sees plain types
        schema = pa.schema([pa.field(k, t, nullable=False) for k, (_, t) in cols.items()])
        return pa.Table.from_arrays([pa.array(v, t) for v, t in cols.values()], schema=schema)
    pq.write_table(table(
        id=(range(1, len(M) + 1), pa.uint32()), kind=([m[0] for m in M], pa.string()),
        status=([m[1] for m in M], pa.string()),
        ts=([datetime.strptime(m[2], "%Y-%m-%d").date() for m in M], pa.date32()),
        ref=([m[3] for m in M], pa.string()), text=([m[4] for m in M], pa.string()),
        emb=(list(mv), f32)), "memory.parquet", compression="zstd")
    pq.write_table(table(
        id=([q[0] for q in Q], pa.uint8()), question=([q[1] for q in Q], pa.string()),
        words=([q[2] for q in Q], strs), emb=(list(qv), f32)), "questions.parquet", compression="zstd")
    rng = np.random.default_rng(26)
    n = 20000
    market = rng.choice(["SG", "VN", "MY", "TH", "ID"], n, p=[.28, .2, .2, .17, .15])
    promised = np.datetime64("2026-11-01") + rng.integers(0, 24, n).astype("timedelta64[D]")
    p_late = np.vectorize({"SG": .06, "VN": .14, "MY": .08, "TH": .09, "ID": .11}.get)(market)
    late = rng.random(n) < p_late
    delivered = promised + np.where(late, rng.integers(1, 5, n), -rng.integers(0, 2, n)).astype("timedelta64[D]")
    pq.write_table(table(
        order_id=(np.arange(1, n + 1), pa.uint32()), market=(list(market), pa.string()),
        promised=(promised.astype("datetime64[D]"), pa.date32()), delivered=(delivered.astype("datetime64[D]"), pa.date32()),
        amount=(np.round(rng.gamma(2.2, 28, n), 2), pa.float64())), "orders.parquet", compression="zstd")
    print(len(M), "memories,", len(Q), "questions,", DIM, "dims")
