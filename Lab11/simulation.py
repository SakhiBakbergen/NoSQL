import random
import hashlib
from collections import Counter
from pymongo import MongoClient
from datetime import datetime, timedelta

# --- ПОДКЛЮЧЕНИЕ К MONGODB ---
try:
    client = MongoClient("mongodb://localhost:27017/")
    db = client["auto_parts_shop"]
    col_inventory = db["inventory"]
    col_sales = db["sales"]
    print("✅ Успешное подключение к MongoDB (База: auto_parts_shop)!")
except Exception as e:
    print(f"❌ Ошибка подключения к MongoDB. Убедитесь, что сервер запущен. Ошибка: {e}")
    exit()

# --- НАСТРОЙКИ ---
SHARDS = 3
categories = {
    0: "Тормозная система",
    1: "Фильтры и масла",
    2: "Элементы подвески",
    3: "Автосвет и оптика",
    4: "Кузовные детали"
}

client_names = [
    "Артем", "Максим", "Руслан", "Александр", "Тимур",
    "Евгений", "Дамир", "Тилек", "Нурлан", "Айбек", "Ербол", "Серик"
]

# Корзина
cart = []
cart_total = 0


def stable_hash(value):
    digest = hashlib.sha256(str(value).encode()).digest()
    return int.from_bytes(digest[:8], 'big')


# Стратегия А: Низкокардинальный ключ по категории товара
def low_card_category(row):
    cat = row.get('category', 0)
    return cat % SHARDS


# Стратегия B: Высококардинальный ключ по ID покупателя с хешированием
def hashed_customer(row):
    return stable_hash(row.get('customerId', 0)) % SHARDS


# Стратегия C: Диапазонный ключ по порядку заказа (event_id)
def range_event(row, max_val=12000):
    ev_id = row.get('event_id', 0)
    return min(ev_id // (max_val // SHARDS), SHARDS - 1)


# --- ФУНКЦИИ РАБОТЫ С БАЗОЙ ---
def init_inventory():
    if col_inventory.count_documents({}) == 0:
        print("📦 Склад автозапчастей пуст. Добавляем начальный ассортимент...")
        start_items = [
            {"cat_id": 0, "name": "Тормозные колодки передние Brembo", "qty": 20, "price": 24000, "desc": "Комплект керамических колодок."},
            {"cat_id": 0, "name": "Тормозной диск вентилируемый", "qty": 10, "price": 32000, "desc": "Перфорированный диск R16."},
            {"cat_id": 1, "name": "Моторное масло Synthetic 5W-40 (4л)", "qty": 45, "price": 18500, "desc": "Всесезонное синтетическое масло."},
            {"cat_id": 1, "name": "Масляный фильтр Bosch", "qty": 60, "price": 4200, "desc": "Высокая степень фильтрации."},
            {"cat_id": 2, "name": "Амортизатор газомасляный KYB", "qty": 14, "price": 29000, "desc": "Стойка подвески передняя."},
            {"cat_id": 2, "name": "Рычаг подвески в сборе", "qty": 8, "price": 37000, "desc": "С шаровой опорой и сайлентблоками."},
            {"cat_id": 3, "name": "Светодиодные LED-лампы H7", "qty": 30, "price": 15000, "desc": "Яркий белый свет 6000K."},
            {"cat_id": 3, "name": "Противотуманные фары линзованные", "qty": 12, "price": 21000, "desc": "Комплект универсальных ПТФ."},
            {"cat_id": 4, "name": "Бампер передний грунтованный", "qty": 5, "price": 45000, "desc": "Под покраску."},
            {"cat_id": 4, "name": "Подкрылок колесной арки", "qty": 25, "price": 6000, "desc": "Пластиковая защита арки."}
        ]
        col_inventory.insert_many(start_items)


def show_stats():
    total_sales = col_sales.count_documents({})
    if total_sales == 0:
        print("\n⚠️ Журнал заказов пуст. Сначала сгенерируйте данные (пункт 1).")
        return

    print("\n--- АНАЛИТИКА РАСПРЕДЕЛЕНИЯ ШАРДОВ (ЛАБОРАТОРНАЯ №11) ---")
    print(f"Всего документов в коллекции sales: {total_sales}")

    all_sales = list(col_sales.find())

    # 30 000 имитируемых запросов для проверки Access Patterns
    queries_uniform = random.choices(all_sales, k=30000)

    # Горячий поток: 60% запросов идут на категорию 0 (Тормозные системы)
    hot_subset = [r for r in all_sales if r.get('category') == 0]
    if hot_subset:
        queries_hot = [random.choice(hot_subset) if random.random() < 0.6 else random.choice(all_sales) for _ in range(30000)]
    else:
        queries_hot = queries_uniform

    strategies = [
        ("category (Низкокардинальный)", low_card_category),
        ("hashed_customerId (Хешированный)", hashed_customer),
        ("range_event (Диапазонный по order_id)", lambda r: range_event(r, max(1, total_sales)))
    ]

    for name, fn in strategies:
        docs_counter = Counter(fn(r) for r in all_sales)
        d = [docs_counter[i] for i in range(SHARDS)]
        doc_max_mean = round(max(d) / (sum(d) / SHARDS), 2) if sum(d) > 0 else 0

        q_uni_counter = Counter(fn(r) for r in queries_uniform)
        q_uni = [q_uni_counter[i] for i in range(SHARDS)]
        q_uni_mm = round(max(q_uni) / (sum(q_uni) / SHARDS), 2) if sum(q_uni) > 0 else 0

        q_hot_counter = Counter(fn(r) for r in queries_hot)
        q_hot = [q_hot_counter[i] for i in range(SHARDS)]
        q_hot_mm = round(max(q_hot) / (sum(q_hot) / SHARDS), 2) if sum(q_hot) > 0 else 0

        print(f"\nКлюч шардирования: {name}")
        print(f"  • Документы по шардам [0, 1, 2]: {d} | Max/mean: {doc_max_mean}")
        print(f"  • Запросы [Uniform]:            {q_uni} | Max/mean: {q_uni_mm}")
        print(f"  • Запросы [Hot (60% перекос)]:  {q_hot} | Max/mean: {q_hot_mm}")
    print("\n--------------------------------------------------------------\n")


def show_inventory():
    print("\n--- СКЛАД АВТОЗАПЧАСТЕЙ ---")
    items = list(col_inventory.find())
    if not items:
        print("Склад пуст.")
    for item in items:
        status = "🟢 В наличии" if item['qty'] > 0 else "🔴 Нет на складе"
        print(f"[{item['cat_id']}] {item['name']} — {item['price']} тенге | Остаток: {item['qty']} шт. | {status}")
        print(f"      Описание: {item.get('desc', '-')}")
    print("---------------------------\n")


def show_cart():
    global cart, cart_total
    print("\n--- ВАША КОРЗИНА ЗАПЧАСТЕЙ ---")
    if not cart:
        print("Корзина пуста.")
        return

    cart_total = 0
    for i, item in enumerate(cart):
        item_total = item['price'] * item['qty']
        cart_total += item_total
        print(f"{i + 1}. {item['name']} | {item['qty']} шт. x {item['price']} тнг = {item_total} тнг")
    print("-" * 35)
    print(f"СУММА К ОПЛАТЕ: {cart_total} тенге\n")


def show_order_history():
    print("\n--- ИСТОРИЯ ЗАКАЗОВ АВТОМАГАЗИНА ---")
    orders = list(col_sales.find({"address": {"$exists": True}}).sort("order_date", -1))
    if not orders:
        print("История пуста.")
        return
    for o in orders:
        print(f"🛠 Заказ от: {o.get('order_date')} | Клиент: {o.get('customerName')} (ID: {o.get('customerId')})")
        print(f"   Товары:  {o.get('items_summary')}")
        print(f"   Сумма:   {o.get('grand_total')} тенге (Доставка: {o.get('delivery_type')})")
        print(f"   Адрес:   {o.get('address')}")
        print("-" * 50)


# --- ГЛАВНОЕ МЕНЮ ---
init_inventory()
print("\n🚗 Добро пожаловать в систему управления магазином автозапчастей (Lab 11 NoSQL)!")

while True:
    print("\n1. Сгенерировать 12 000 синтетических продаж")
    print("2. Добавить запчасть в корзину")
    print("3. Посмотреть корзину")
    print("4. Оформить заказ")
    print("5. Посмотреть склад")
    print("6. Добавить новую позицию на склад")
    print("7. Посмотреть историю заказов")
    print("8. Запустить тест шардирования и показать статистику")
    print("9. Выход")

    choice = input("Выберите пункт меню (1-9): ")

    if choice == '1':
        print("Генерация 12 000 записей о продажах в коллекцию 'sales'...")
        sales_batch = []
        for i in range(12000):
            cat = random.randint(0, 4)
            prod_doc = col_inventory.find_one({"cat_id": cat})
            prod_name = prod_doc["name"] if prod_doc else "Автозапчасть"
            sales_batch.append({
                "customerId": i % 3000,  # 3000 уникальных клиентов
                "customerName": random.choice(client_names),
                "category": cat,
                "productName": prod_name,
                "event_id": i
            })
        col_sales.insert_many(sales_batch)
        print(f"✅ Успешно сгенерировано и записано 12 000 документов!")

    elif choice == '2':
        try:
            print("\nКатегории запчастей:")
            for k, v in categories.items():
                print(f"  {k} - {v}")
            cat_id = int(input("Выберите категорию (0-4): "))

            items = list(col_inventory.find({"cat_id": cat_id}))
            if not items:
                print("В этой категории пока нет товаров.")
                continue

            for i, it in enumerate(items):
                print(f"  {i} - {it['name']} | {it['price']} тнг (Доступно: {it['qty']} шт.)")

            p_idx = int(input("Введите номер товара: "))
            if 0 <= p_idx < len(items):
                chosen = items[p_idx]
                qty = int(input(f"Введите количество (на складе {chosen['qty']}): "))
                if qty <= 0 or qty > chosen['qty']:
                    print("❌ Неверное количество!")
                    continue

                cart.append({
                    "_id": chosen["_id"],
                    "name": chosen["name"],
                    "price": chosen["price"],
                    "qty": qty,
                    "category": cat_id
                })
                print(f"✅ Добавлено в корзину: {chosen['name']} ({qty} шт.)")
        except ValueError:
            print("❌ Ошибка ввода чисел.")

    elif choice == '3':
        show_cart()

    elif choice == '4':
        if not cart:
            print("⚠️ Корзина пуста!")
            continue
        show_cart()
        c_name = input("Ваше имя: ")
        c_id = int(input("Ваш ID клиента (например, 1005): "))
        address = input("Адрес доставки (Город, Улица, Дом): ")

        print("Способ доставки:\n  1. Курьер (1500 тнг)\n  2. Самовывоз со склада (0 тнг)")
        d_type = "Курьер" if input("Выбор (1-2): ") == '1' else "Самовывоз"
        d_price = 1500 if d_type == "Курьер" else 0

        for item in cart:
            col_inventory.update_one({"_id": item["_id"]}, {"$inc": {"qty": -item["qty"]}})

        summary = ", ".join([f"{it['name']} x{it['qty']}" for it in cart])
        grand_total = cart_total + d_price

        last_s = col_sales.find_one(sort=[("event_id", -1)])
        new_ev_id = (last_s["event_id"] + 1) if last_s else 0

        col_sales.insert_one({
            "customerId": c_id,
            "customerName": c_name,
            "items_summary": summary,
            "grand_total": grand_total,
            "address": address,
            "delivery_type": d_type,
            "order_date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "event_id": new_ev_id,
            "category": cart[0]["category"] if cart else 0
        })
        print(f"\n🎉 Заказ успешно оформлен! Сумма к оплате: {grand_total} тенге.")
        cart.clear()

    elif choice == '5':
        show_inventory()

    elif choice == '6':
        try:
            cat_id = int(input("Категория (0-4): "))
            name = input("Название детали: ")
            desc = input("Описание: ")
            price = int(input("Цена в тенге: "))
            qty = int(input("Количество: "))
            col_inventory.insert_one({"cat_id": cat_id, "name": name, "desc": desc, "price": price, "qty": qty})
            print("✅ Запчасть добавлена на склад.")
        except ValueError:
            print("❌ Ошибка ввода.")

    elif choice == '7':
        show_order_history()

    elif choice == '8':
        show_stats()

    elif choice == '9':
        print("Выход...")
        break
    else:
        print("Неверный выбор.")