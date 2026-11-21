"""Медианы трёх запусков, процентили по объединённым сырым данным, графики. Запуск: python analyze.py"""
import os
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

LABEL = {"no_index": "Без индекса", "with_index": "С индексом"}


def build_summary():
    res = pd.read_csv("results.csv")
    raw = pd.read_csv("data/raw_latencies.csv")
    raw = raw[raw.ok == 1]
    out = []
    for (mode, w), g in res.groupby(["mode", "workers"]):
        pooled = raw[(raw["mode"] == mode) & (raw.workers == w)].latency_ms
        out.append({"mode": mode, "workers": w,
                    "rps_median": g.rps.median(), "p50_median": g.p50_ms.median(),
                    "p95_median": g.p95_ms.median(), "p99_median": g.p99_ms.median(),
                    "p95_min": g.p95_ms.min(), "p95_max": g.p95_ms.max(),
                    "rps_min": g.rps.min(), "rps_max": g.rps.max(),
                    "p95_pooled": np.percentile(pooled, 95), "p99_pooled": np.percentile(pooled, 99),
                    "error_rate_pct": g.errors.sum() / g.requests.sum() * 100})
    s = pd.DataFrame(out).sort_values(["mode", "workers"])
    s.to_csv("data/summary.csv", index=False)
    return s


def improvement(s):
    a = s[s["mode"] == "no_index"].set_index("workers")
    b = s[s["mode"] == "with_index"].set_index("workers")
    imp = pd.DataFrame({"p95_before": a.p95_median, "p95_after": b.p95_median,
                        "p95_improvement_pct": (a.p95_median - b.p95_median) / a.p95_median * 100,
                        "rps_before": a.rps_median, "rps_after": b.rps_median})
    imp.to_csv("data/improvement.csv")
    return imp


def charts(s):
    for col, lo, hi, yl, title, fn in [
        ("p95_median", "p95_min", "p95_max", "P95, мс", "P95 по числу клиентов", "p95_by_workers.png"),
        ("rps_median", "rps_min", "rps_max", "Запросов/с", "Throughput по числу клиентов", "throughput_by_workers.png")]:
        plt.figure(figsize=(6, 4))
        for mode, g in s.groupby("mode"):
            plt.errorbar(g.workers, g[col], yerr=[g[col] - g[lo], g[hi] - g[col]],
                         marker="o", capsize=3, label=LABEL[mode])
        plt.xlabel("Число параллельных клиентов")
        plt.ylabel(yl)
        plt.title(title + " (медиана, min–max из 3 повторов)", fontsize=9)
        plt.xticks(sorted(s.workers.unique()))
        plt.grid(alpha=.3)
        plt.legend()
        plt.tight_layout()
        plt.savefig("charts/" + fn, dpi=150)
        plt.close()


if __name__ == "__main__":
    os.makedirs("data", exist_ok=True); os.makedirs("charts", exist_ok=True)
    s = build_summary()
    print(s.round(2).to_string(index=False))
    print(improvement(s).round(2))
    charts(s)
    print("Графики сохранены в charts/")
