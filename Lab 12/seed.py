"""Генерация синтетических данных (seed зафиксирован). Запуск: python seed.py [--n 50000]"""
import argparse, json, random
from pymongo import MongoClient
from common import *


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=50000, help="число документов (>= 5000)")
    a = ap.parse_args()
    if a.n < 5000:
        raise SystemExit("По заданию нужно не менее 5000 документов")
    assert_local()
    os.makedirs("data", exist_ok=True); os.makedirs("charts", exist_ok=True)
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000)
    version = client.server_info()["version"]
    coll = client[DB_NAME][COLL_NAME]
    coll.drop()                                   # только учебная коллекция!
    rng = random.Random(SEED)
    rows = [make_doc(rng, i) for i in range(a.n)]
    for i in range(0, len(rows), 5000):
        coll.insert_many(rows[i:i + 5000])
    count = coll.count_documents({})
    print(f"MongoDB {version}; seed={SEED}; документов: {count}")
    json.dump({"mongo_version": version, "seed": SEED, "docs": count},
              open("data/seed_info.json", "w"), indent=2)


if __name__ == "__main__":
    main()
