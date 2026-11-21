"""Общие настройки лабораторной №12 (вариант 01: каталог курсов)."""
import os

SEED = 42
COLL_NAME = "courses"
INDEX_NAME = "dept_sem_idx"
INDEX_KEYS = [("departmentId", 1), ("semester", 1)]
EXPLAIN_QUERY = {"departmentId": 10, "semester": 5}   # запрос из методички


def _load_dotenv(path=".env"):
    if os.path.exists(path):
        for line in open(path, encoding="utf-8"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


_load_dotenv()
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "nosql_lab12")


def make_doc(rng, i):
    return {"departmentId": rng.randint(1, 20),
            "semester": rng.randint(1, 8),
            "title": f"Course {i}",
            "credits": rng.randint(2, 6),
            "teacherId": rng.randint(1, 150)}


def assert_local():
    if not any(h in MONGO_URI for h in ("localhost", "127.0.0.1", "[::1]")):
        raise SystemExit("MONGO_URI указывает не на локальный стенд. "
                         "Нагрузку на чужие серверы запускать нельзя.")
