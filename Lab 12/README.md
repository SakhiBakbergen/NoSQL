# Лабораторная работа №12 — воспроизводимый benchmark (вариант 01: каталог курсов)

Сравнение чтения `courses` по `departmentId + semester` **без индекса** и **с составным индексом**
`{departmentId: 1, semester: 1}` при 1, 4 и 8 параллельных клиентах (closed-loop).

## Состав
| Файл | Назначение |
|---|---|
| `seed.py` | генерация синтетических данных (seed=42, по умолчанию 50 000 документов) |
| `benchmark.py` | explain до/после, прогрев, 3 повтора × 1/4/8 клиентов, ошибки, стоимость записи, размер индекса |
| `analyze.py` | медианы, процентили по сырым данным, улучшение P95, графики в `charts/` |
| `make_report.py` | сборка `report.pdf` из реальных результатов |
| `results.csv`, `data/` | результаты, сырые latency, explain, версии окружения |

## Запуск
1. Локальный MongoDB, например: `docker run -d --name mongo-lab12 -p 27017:27017 mongo:7`
2. Окружение (в IntelliJ: Project Structure → SDK → Add Python SDK → Virtualenv, нужен плагин Python):
   ```
   python -m venv .venv
   .venv\Scripts\activate          # Linux/macOS: source .venv/bin/activate
   pip install -r requirements.txt
   ```
3. `cp .env.example .env` (при необходимости поправить `MONGO_URI`).
4. По порядку:
   ```
   python seed.py
   python benchmark.py
   python analyze.py
   python make_report.py --fio "Фамилия И.О." --group "Группа" --teacher "Преподаватель" --repo "ссылка на GitHub"
   ```
Во время теста закройте тяжёлые программы. Для слабой машины: `python benchmark.py --workers 1 2 4` (и укажите это в отчёте).

## Воспроизводимость
Фиксированы seed данных (42) и набор запросов (seed+1); версии MongoDB/Python/pymongo пишутся в `data/meta.json`.
Скрипты работают только с локальным стендом (проверка `MONGO_URI`) и удаляют только коллекцию `courses` и индекс `dept_sem_idx`.
