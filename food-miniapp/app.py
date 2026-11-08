import os
import sqlite3
import requests
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)
DB_NAME = "delivery.db"

# Вставь сюда токен своего бота от @BotFather
BOT_TOKEN = os.getenv("BOT_TOKEN", "ВСТАВЬ_СЮДА_ТОКЕН_БОТА")

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS restaurants (
            id INTEGER PRIMARY KEY,
            name TEXT,
            cat TEXT,
            time TEXT,
            rate REAL,
            img TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS dishes (
            id INTEGER PRIMARY KEY,
            rest_id INTEGER,
            name TEXT,
            price INTEGER,
            weight TEXT,
            img TEXT
        )
    """)
    c.execute("SELECT COUNT(*) FROM restaurants")
    if c.fetchone()[0] == 0:
        c.executemany("INSERT INTO restaurants VALUES (?,?,?,?,?,?)", [
            (1, "Burger House", "Бургеры • Фастфуд", "25-35 мин", 4.8, "🍔"),
            (2, "Pizza Napoli", "Пицца • Итальянская", "35-45 мин", 4.9, "🍕"),
            (3, "Osh Markazi", "Узбекская • Плов", "30-40 мин", 4.9, "🥘")
        ])
        c.executemany("INSERT INTO dishes VALUES (?,?,?,?,?,?)", [
            (1, 1, "Двойной Чизбургер", 45000, "320 г", "🍔"),
            (2, 1, "Картофель Фри", 18000, "150 г", "🍟"),
            (3, 2, "Пепперони", 75000, "450 г", "🍕"),
            (4, 2, "Маргарита", 60000, "400 г", "🧀"),
            (5, 3, "Свадебный плов", 42000, "350 г", "🥘"),
            (6, 3, "Ачичук салат", 12000, "150 г", "🥗")
        ])
        conn.commit()
    conn.close()

init_db()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/restaurants")
def get_restaurants():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id, name, cat, time, rate, img FROM restaurants")
    res = [{"id": r[0], "name": r[1], "cat": r[2], "time": r[3], "rate": r[4], "img": r[5]} for r in c.fetchall()]
    conn.close()
    return jsonify(res)

@app.route("/api/dishes/<int:rest_id>")
def get_dishes(rest_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id, name, price, weight, img FROM dishes WHERE rest_id=?", (rest_id,))
    res = [{"id": r[0], "name": r[1], "price": r[2], "weight": r[3], "img": r[4]} for r in c.fetchall()]
    conn.close()
    return jsonify(res)

@app.route("/api/order", methods=["POST"])
def create_order():
    data = request.json
    user_id = data.get("user_id")
    user_name = data.get("user_name", "Клиент")
    address = data.get("address", "Не указан")
    items = data.get("items", [])
    total = data.get("total", 0)

    # Формируем красивый чек для отправки в Telegram
    items_text = "\n".join([f"• {i['name']} x{i['qty']} — {i['price'] * i['qty']:,} сум" for i in items])
    message = (
        f"🧾 <b>Новый заказ!</b>\n\n"
        f"👤 <b>Клиент:</b> {user_name}\n"
        f"📍 <b>Адрес:</b> {address}\n\n"
        f"<b>Состав заказа:</b>\n{items_text}\n\n"
        f"💰 <b>Итого к оплате:</b> {total:,} сум"
    )

    # Если открыто внутри Telegram и указан токен — шлем чек в личку
    if user_id and BOT_TOKEN != "ВСТАВЬ_СЮДА_ТОКЕН_БОТА":
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, json={
            "chat_id": user_id,
            "text": message,
            "parse_mode": "HTML"
        })

    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)