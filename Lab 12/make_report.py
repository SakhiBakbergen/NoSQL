"""Сборка report.pdf из реальных результатов (results.csv, data/*, charts/*).
Запуск: python make_report.py --fio "Иванов И.И." --group "ИС-31" --teacher "Фамилия И.О."
"""
import argparse, ast, json, os
import pandas as pd
import matplotlib
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table,
                                TableStyle, Image, Preformatted)

fd = os.path.join(matplotlib.get_data_path(), "fonts", "ttf")
pdfmetrics.registerFont(TTFont("DV", os.path.join(fd, "DejaVuSans.ttf")))
pdfmetrics.registerFont(TTFont("DV-B", os.path.join(fd, "DejaVuSans-Bold.ttf")))
pdfmetrics.registerFont(TTFont("DV-M", os.path.join(fd, "DejaVuSansMono.ttf")))

P = ParagraphStyle("P", fontName="DV", fontSize=9.5, leading=14, spaceAfter=5)
H1 = ParagraphStyle("H1", parent=P, fontName="DV-B", fontSize=13, spaceBefore=10, spaceAfter=6)
T = ParagraphStyle("T", parent=P, fontName="DV-B", fontSize=16, alignment=1, leading=22)
C = ParagraphStyle("C", parent=P, alignment=1)
CODE = ParagraphStyle("CODE", fontName="DV-M", fontSize=6.6, leading=8.2)


def tbl(data, widths=None, fs=7.5):
    t = Table(data, colWidths=widths, repeatRows=1)
    t.setStyle(TableStyle([("FONTNAME", (0, 0), (-1, -1), "DV"), ("FONTNAME", (0, 0), (-1, 0), "DV-B"),
                           ("FONTSIZE", (0, 0), (-1, -1), fs), ("GRID", (0, 0), (-1, -1), .4, colors.grey),
                           ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8eef7")),
                           ("ALIGN", (1, 1), (-1, -1), "CENTER")]))
    return t


def func_src(path, names):
    src = open(path, encoding="utf-8").read()
    out = []
    for n in ast.parse(src).body:
        if isinstance(n, ast.FunctionDef) and n.name in names:
            out.append(ast.get_source_segment(src, n))
    return "\n\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fio", default="ФИО студента")
    ap.add_argument("--group", default="Группа")
    ap.add_argument("--teacher", default="Преподаватель")
    ap.add_argument("--repo", default="https://github.com/<user>/nosql-lab12")
    a = ap.parse_args()

    res = pd.read_csv("results.csv")
    s = pd.read_csv("data/summary.csv")
    imp = pd.read_csv("data/improvement.csv").set_index("workers")
    meta = json.load(open("data/meta.json"))
    eb = json.load(open("data/explain_no_index.json"))
    ea = json.load(open("data/explain_with_index.json"))
    ex = meta["extra"]
    st = []

    st += [Spacer(1, 4 * cm), Paragraph("Министерство образования", C),
           Spacer(1, 2 * cm), Paragraph("ЛАБОРАТОРНАЯ РАБОТА №12", T),
           Paragraph("Разработка и запуск воспроизводимого benchmark-сценария", T),
           Spacer(1, 1 * cm), Paragraph("Дисциплина: «Проектирование и применение NoSQL-технологий»", C),
           Paragraph("Вариант 01. Каталог курсов (departmentId + semester)", C), Spacer(1, 4 * cm),
           Paragraph(f"Выполнил: {a.fio}, группа {a.group}", C),
           Paragraph(f"Проверил: {a.teacher}", C), Paragraph(f"Репозиторий: {a.repo}", C), PageBreak()]

    st += [Paragraph("1. Цель", H1),
           Paragraph("Разработать воспроизводимый эксперимент производительности коллекции courses (MongoDB): "
                     "измерить latency (P50/P95/P99), throughput и ошибки при 1, 4 и 8 параллельных клиентах, "
                     "сравнить конфигурацию без индекса и с составным индексом {departmentId: 1, semester: 1}, "
                     "обосновать выводы.", P),
           Paragraph("2. Окружение и версии", H1),
           tbl([["Параметр", "Значение"], ["MongoDB", meta["mongo_version"]], ["Python", meta["python"]],
                ["pymongo", meta["pymongo"]], ["ОС", meta["os"]], ["Логических CPU", str(meta["cpu_count"])],
                ["Дата запуска (UTC)", meta["timestamp_utc"][:19]]], [5 * cm, 11 * cm], 8),
           Paragraph("Стенд: собственный локальный MongoDB, нагрузочный клиент на той же машине. "
                     "Рабочие серверы университета не использовались.", P),
           Paragraph("3. Схема данных, seed и workload", H1),
           Paragraph(f"Коллекция courses: {meta['docs']} синтетических документов, seed генератора = {meta['seed']}. "
                     "Поля: departmentId (1–20), semester (1–8), title, credits (2–6), teacherId (1–150). "
                     "Ожидаемая селективность комбинации (departmentId, semester) ≈ 1/160 коллекции.", P),
           Paragraph("Access patterns: AP-01 — поиск курсов подразделения и семестра (главный сценарий, измеряется); "
                     "AP-02 — поиск курса по идентификатору; AP-03 — подсчёт курсов подразделения (не измерялись).", P),
           Paragraph(f"Workload: closed-loop, {meta['requests_per_run']} запросов на запуск "
                     f"find({{departmentId, semester}}).limit(100); набор запросов детерминирован (seed+1) и одинаков для обеих "
                     f"конфигураций; прогрев — {meta['warmup']} запросов отдельно от замера; {meta['repeats']} повтора на "
                     f"каждый уровень клиентов ({', '.join(map(str, meta['workers']))}). Ошибочные операции учитываются в счётчике ошибок; "
                     "процентили считаются по успешным запросам.", P),
           Paragraph("4. Гипотеза и SLO", H1),
           Paragraph("Гипотеза: составной индекс уменьшит число просмотренных документов и P95 чтения AP-01. "
                     "SLO для сравнения: доля ошибок = 0 %, P95 не хуже, чем без индекса, при каждом уровне нагрузки.", P)]

    st += [PageBreak(), Paragraph("5. Код benchmark (ключевые функции)", H1),
           Preformatted(func_src("benchmark.py", ["one", "percentile", "run", "build_queries"]), CODE), PageBreak()]

    def erow(name, e):
        return [name, e["stages"], str(e["indexName"]), str(e["nReturned"]), str(e["totalDocsExamined"]),
                str(e["totalKeysExamined"]), str(e["executionTimeMillis"])]
    st += [Paragraph("6. Планы запроса explain('executionStats')", H1),
           Paragraph("Запрос: find({departmentId: 10, semester: 5}).limit(100).", P),
           tbl([["Конфигурация", "winningPlan", "Индекс", "nReturned", "docsExamined", "keysExamined", "ms"],
                erow("Без индекса", eb), erow("С индексом", ea)],
               [2.6 * cm, 4.2 * cm, 2.6 * cm, 1.7 * cm, 2 * cm, 2 * cm, 1 * cm], 7),
           Spacer(1, 6),
           Paragraph("Вывод по explain сам по себе не доказывает ускорение: IXSCAN подтверждается независимыми "
                     "измерениями latency/throughput (раздел 7).", P),
           Paragraph("7. Результаты (реальные измерения, все повторы)", H1)]
    rows = [["Режим", "Кл.", "Повтор", "RPS", "P50, мс", "P95, мс", "P99, мс", "Ошибки"]]
    names = {"no_index": "Без индекса", "with_index": "С индексом"}
    for _, r in res.sort_values(["mode", "workers", "repeat"], ascending=[False, True, True]).iterrows():
        rows.append([names[r["mode"]], int(r.workers), int(r["repeat"]), f"{r.rps:.0f}", f"{r.p50_ms:.2f}",
                     f"{r.p95_ms:.2f}", f"{r.p99_ms:.2f}", f"{int(r.errors)} ({r.error_rate_pct:.1f}%)"])
    st += [tbl(rows, None, 7), PageBreak()]

    st += [Paragraph("8. Медианы трёх запусков и улучшение P95", H1)]
    rows = [["Режим", "Кл.", "RPS", "P50", "P95 (мед.)", "P99", "P95 по сырым", "Ошибки, %"]]
    for _, r in s.sort_values(["mode", "workers"], ascending=[False, True]).iterrows():
        rows.append([names[r["mode"]], int(r.workers), f"{r.rps_median:.0f}", f"{r.p50_median:.2f}",
                     f"{r.p95_median:.2f}", f"{r.p99_median:.2f}", f"{r.p95_pooled:.2f}", f"{r.error_rate_pct:.2f}"])
    st += [tbl(rows, None, 7.5), Spacer(1, 6),
           Paragraph("Улучшение P95 = (P95_до − P95_после) / P95_до × 100 %, по медиане трёх запусков:", P),
           tbl([["Клиентов", "P95 до, мс", "P95 после, мс", "Улучшение, %", "RPS до", "RPS после"]] +
               [[int(w), f"{r.p95_before:.2f}", f"{r.p95_after:.2f}", f"{r.p95_improvement_pct:.1f}",
                 f"{r.rps_before:.0f}", f"{r.rps_after:.0f}"] for w, r in imp.iterrows()], None, 8),
           Spacer(1, 8),
           Image("charts/p95_by_workers.png", 11 * cm, 7.3 * cm),
           Image("charts/throughput_by_workers.png", 11 * cm, 7.3 * cm), PageBreak()]

    wb, wa = ex["no_index"]["write_cost"]["median_ms"], ex["with_index"]["write_cost"]["median_ms"]
    ib, ia = ex["no_index"]["index_stats"], ex["with_index"]["index_stats"]
    size_a = ia.get("indexSizes", {}).get(os.getenv("INDEX_NAME", "dept_sem_idx"))
    ok = (imp.p95_improvement_pct > 0).all() and ea["totalDocsExamined"] < eb["totalDocsExamined"]
    verdict = ("подтверждена" if ok else "подтверждена не полностью / не подтверждена (см. данные)")
    scale = {m: g.sort_values("workers").rps_median.iloc[-1] / g.sort_values("workers").rps_median.iloc[0]
             for m, g in s.groupby("mode")}
    st += [Paragraph("9. Стоимость записи и размер индекса", H1),
           Paragraph(f"Вставка {ex['no_index']['write_cost']['docs']} документов в scratch-коллекцию (медиана 3 повторов): "
                     f"без индекса {wb:.0f} мс, с индексом {wa:.0f} мс (изменение {((wa - wb) / wb * 100):+.1f} %). "
                     f"Размер индекса {('%.0f КБ' % (size_a / 1024)) if size_a else 'см. data/meta.json'}; "
                     f"размер данных (storageSize) ≈ {(ia.get('storageSize') or 0) / 1024:.0f} КБ.", P),
           Paragraph("10. Интерпретация", H1),
           Paragraph(f"Гипотеза {verdict}: totalDocsExamined снизился с {eb['totalDocsExamined']} до "
                     f"{ea['totalDocsExamined']}, totalKeysExamined — с {eb['totalKeysExamined']} до {ea['totalKeysExamined']}. "
                     f"P95 при {int(imp.index.min())}/…/{int(imp.index.max())} клиентах изменился на "
                     f"{', '.join(f'{v:.1f} %' for v in imp.p95_improvement_pct)} соответственно.", P),
           Paragraph(f"Рост throughput от минимального к максимальному числу клиентов: без индекса ×{scale['no_index']:.2f}, "
                     f"с индексом ×{scale['with_index']:.2f}. Throughput выходит на плато, когда узким местом становится "
                     "ресурс, а не число клиентов: CPU сервера и клиента, пул соединений, сериализация ответов, GIL в Python-клиенте. "
                     "Дальше клиенты лишь ждут в очереди, поэтому латентность (особенно хвост P95/P99) растёт при почти "
                     "неизменном RPS. Throughput — число завершённых операций в секунду, число клиентов — лишь параметр нагрузки.", P),
           Paragraph("11. Ограничения", H1),
           Paragraph("• Closed-loop тест, а не open-loop с фиксированным RPS: при замедлении сервера клиенты тоже замедляются "
                     "(coordinated omission). • Клиент и MongoDB на одной машине конкурируют за CPU. • Потоки Python ограничены GIL. "
                     "• Один тип запроса и равномерное распределение данных; для других распределений результат может отличаться. "
                     "• Небольшие n и 3 повтора дают оценку с заметным разбросом (см. min–max на графиках). "
                     "• Кэш WiredTiger прогрет, данные целиком помещаются в память.", P),
           Paragraph("12. Вывод", H1),
           Paragraph(f"Составной индекс {{departmentId: 1, semester: 1}} {'сократил' if ok else 'не во всех режимах сократил'} "
                     "просмотр документов и изменил P95 (таблица 8). Платой стали дополнительное место под индекс и "
                     "изменение времени записи (раздел 9). Эксперимент воспроизводим: seed, версии, набор запросов и "
                     "сырые данные сохранены в репозитории.", P)]

    SimpleDocTemplate("report.pdf", pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm,
                      topMargin=1.8 * cm, bottomMargin=1.8 * cm,
                      title="Лабораторная работа №12").build(st)
    print("report.pdf создан")


if __name__ == "__main__":
    main()
