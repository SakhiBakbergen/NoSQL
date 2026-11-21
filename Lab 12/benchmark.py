"""Closed-loop benchmark AP-01: find({departmentId, semester}).limit(100).
Фазы: без индекса -> с индексом {departmentId:1, semester:1}.
Запуск: python benchmark.py [--n 400 --repeats 3 --workers 1 4 8 --warmup 40]
"""
import argparse, csv, json, math, os, platform, random, statistics, sys, time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from time import perf_counter

import pymongo
from pymongo import MongoClient
from pymongo.errors import OperationFailure
from common import *


def build_queries(n, seed):
    """Одинаковый детерминированный набор запросов для обеих конфигураций."""
    rng = random.Random(seed + 1)
    return [{"departmentId": rng.randint(1, 20), "semester": rng.randint(1, 8)}
            for _ in range(n)]


def one(coll, q):
    start = perf_counter()
    try:
        list(coll.find(q).limit(100))
        return ((perf_counter() - start) * 1000, True)
    except Exception:
        return ((perf_counter() - start) * 1000, False)


def percentile(v, p):
    v = sorted(v)
    if not v:
        return float("nan")
    idx = (len(v) - 1) * p / 100
    lo, hi = math.floor(idx), math.ceil(idx)
    return v[lo] + (v[hi] - v[lo]) * (idx - lo)


def run(coll, queries, workers, warmup):
    for q in queries[:warmup]:                    # warm-up отдельно, не входит в замер
        one(coll, q)
    t0 = perf_counter()
    with ThreadPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(lambda q: one(coll, q), queries))
    seconds = perf_counter() - t0
    lat = [ms for ms, ok in results if ok]
    n = len(queries)
    summary = {"workers": workers, "requests": n, "success": len(lat),
               "errors": n - len(lat), "error_rate_pct": (n - len(lat)) / n * 100,
               "duration_s": seconds, "rps": len(lat) / seconds,
               "p50_ms": percentile(lat, 50), "p95_ms": percentile(lat, 95),
               "p99_ms": percentile(lat, 99)}
    return summary, results


def plan_stages(node):
    node = node.get("queryPlan", node)
    out = [node.get("stage", "?")]
    if "inputStage" in node:
        out += plan_stages(node["inputStage"])
    elif "inputStages" in node:
        out += plan_stages(node["inputStages"][0])
    return out


def explain(db, query):
    res = db.command({"explain": {"find": COLL_NAME, "filter": query, "limit": 100},
                      "verbosity": "executionStats"})
    wp = res["queryPlanner"]["winningPlan"]
    es = res["executionStats"]
    node = wp.get("queryPlan", wp)
    idx_name = None
    while node:
        if "indexName" in node:
            idx_name = node["indexName"]
            break
        node = node.get("inputStage")
    return {"query": query, "stages": " > ".join(plan_stages(wp)), "indexName": idx_name,
            "nReturned": es["nReturned"], "totalDocsExamined": es["totalDocsExamined"],
            "totalKeysExamined": es["totalKeysExamined"],
            "executionTimeMillis": es["executionTimeMillis"], "winningPlan": wp}


def index_stats(coll):
    try:
        st = next(coll.aggregate([{"$collStats": {"storageStats": {}}}]))["storageStats"]
        return {"count": st.get("count"), "storageSize": st.get("storageSize"),
                "totalIndexSize": st.get("totalIndexSize"), "indexSizes": st.get("indexSizes")}
    except Exception as e:
        return {"error": str(e)}


def write_cost(db, with_index, n=5000, repeats=3):
    """Стоимость записи: вставка n синтетических документов в отдельную scratch-коллекцию."""
    times = []
    for r in range(repeats):
        scratch = db["courses_write_test"]
        scratch.drop()
        if with_index:
            scratch.create_index(INDEX_KEYS, name=INDEX_NAME)
        rng = random.Random(SEED + 100 + r)
        docs = [make_doc(rng, i) for i in range(n)]
        t0 = perf_counter()
        for i in range(0, n, 500):
            scratch.insert_many(docs[i:i + 500])
        times.append((perf_counter() - t0) * 1000)
        scratch.drop()
    return {"docs": n, "times_ms": times, "median_ms": statistics.median(times)}


def drop_lab_index(coll):
    try:
        coll.drop_index(INDEX_NAME)
        print("Индекс", INDEX_NAME, "удалён")
    except OperationFailure:
        pass                                       # индекса не было


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=400)
    ap.add_argument("--repeats", type=int, default=3)
    ap.add_argument("--workers", type=int, nargs="+", default=[1, 4, 8])
    ap.add_argument("--warmup", type=int, default=40)
    a = ap.parse_args()
    assert_local()
    os.makedirs("data", exist_ok=True); os.makedirs("charts", exist_ok=True)

    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000,
                         maxPoolSize=max(a.workers) + 4)
    db = client[DB_NAME]
    coll = db[COLL_NAME]
    version = client.server_info()["version"]
    docs = coll.count_documents({})
    if docs < 5000:
        raise SystemExit(f"В коллекции {docs} документов; сначала запустите seed.py")
    queries = build_queries(a.n, SEED)
    meta = {"timestamp_utc": datetime.now(timezone.utc).isoformat(), "mongo_version": version,
            "docs": docs, "seed": SEED, "requests_per_run": a.n, "warmup": a.warmup,
            "repeats": a.repeats, "workers": a.workers, "python": sys.version.split()[0],
            "pymongo": pymongo.version, "os": platform.platform(), "cpu_count": os.cpu_count()}
    print(json.dumps(meta, indent=2))

    rows, raw = [], []
    extra = {}
    for mode in ("no_index", "with_index"):
        if mode == "no_index":
            drop_lab_index(coll)
        else:
            coll.create_index(INDEX_KEYS, name=INDEX_NAME)
            print("Индекс создан:", INDEX_NAME)
        ex = explain(db, EXPLAIN_QUERY)
        json.dump(ex, open(f"data/explain_{mode}.json", "w"), indent=2, default=str)
        print(mode, "explain:", {k: v for k, v in ex.items() if k != "winningPlan"})
        extra[mode] = {"index_stats": index_stats(coll), "write_cost": write_cost(db, mode == "with_index")}
        for w in a.workers:
            for rep in range(1, a.repeats + 1):
                s, results = run(coll, queries, w, a.warmup)
                s.update({"mode": mode, "repeat": rep})
                rows.append(s)
                raw += [(mode, w, rep, round(ms, 4), int(ok)) for ms, ok in results]
                print(mode, "workers", w, "repeat", rep,
                      {k: round(v, 2) if isinstance(v, float) else v for k, v in s.items()})
                time.sleep(1)                      # пауза между замерами

    cols = ["mode", "workers", "repeat", "requests", "success", "errors", "error_rate_pct",
            "duration_s", "rps", "p50_ms", "p95_ms", "p99_ms"]
    with open("results.csv", "w", newline="", encoding="utf-8") as f:
        wr = csv.DictWriter(f, fieldnames=cols)
        wr.writeheader()
        for r in rows:
            wr.writerow({c: (round(r[c], 4) if isinstance(r[c], float) else r[c]) for c in cols})
    with open("data/raw_latencies.csv", "w", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["mode", "workers", "repeat", "latency_ms", "ok"])
        wr.writerows(raw)
    meta["extra"] = extra
    json.dump(meta, open("data/meta.json", "w"), indent=2)
    print("Готово: results.csv, data/*.json, data/raw_latencies.csv")


if __name__ == "__main__":
    main()
