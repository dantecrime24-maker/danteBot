import os
import logging
import asyncio
import sqlite3
from aiogram import Bot, Dispatcher, executor, types

# 🔑 Токен
API_TOKEN = os.getenv("BOT_TOKEN")

# 🔒 Главный админ
MAIN_ADMIN_ID = 7322925570

# Логирование
logging.basicConfig(level=logging.INFO)

# Инициализация
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# 📂 SQLite база
conn = sqlite3.connect("database.db")
cur = conn.cursor()
cur.execute("""
CREATE TABLE IF NOT EXISTS admins (
    user_id INTEGER PRIMARY KEY
)
""")
cur.execute("""
CREATE TABLE IF NOT EXISTS faqs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER,
    question TEXT,
    answer TEXT
)
""")
conn.commit()

# 📌 Проверка админов
def is_admin(user_id: int) -> bool:
    if user_id == MAIN_ADMIN_ID:
        return True
    cur.execute("SELECT 1 FROM admins WHERE user_id = ?", (user_id,))
    return cur.fetchone() is not None

# ⚙️ Команды
@dp.message_handler(commands=["dante"])
async def cmd_dante(message: types.Message):
    if not is_admin(message.from_user.id):
        return
    await message.answer(
        "📖 Панель Dante\n\n"
        "🔹 /addfaq <вопрос>|<ответ> — добавить FAQ\n"
        "🔹 /listfaq — список FAQ\n"
        "🔹 /delfaq <id> — удалить FAQ\n"
        "🔹 /addadmin <id> — добавить админа\n"
        "🔹 /deladmin <id> — удалить админа\n"
        "🔹 /listadmins — список админов\n"
    )

# 👑 Управление админами
@dp.message_handler(commands=["addadmin"])
async def cmd_addadmin(message: types.Message):
    if message.from_user.id != MAIN_ADMIN_ID:
        return
    try:
        user_id = int(message.get_args())
        cur.execute("INSERT OR IGNORE INTO admins(user_id) VALUES(?)", (user_id,))
        conn.commit()
        await message.answer(f"✅ Пользователь {user_id} теперь админ.")
    except:
        await message.answer("⚠️ Используй: /addadmin <user_id>")

@dp.message_handler(commands=["deladmin"])
async def cmd_deladmin(message: types.Message):
    if message.from_user.id != MAIN_ADMIN_ID:
        return
    try:
        user_id = int(message.get_args())
        if user_id == MAIN_ADMIN_ID:
            await message.answer("❌ Нельзя удалить главного админа.")
            return
        cur.execute("DELETE FROM admins WHERE user_id=?", (user_id,))
        conn.commit()
        await message.answer(f"✅ Пользователь {user_id} больше не админ.")
    except:
        await message.answer("⚠️ Используй: /deladmin <user_id>")

@dp.message_handler(commands=["listadmins"])
async def cmd_listadmins(message: types.Message):
    if not is_admin(message.from_user.id):
        return
    cur.execute("SELECT user_id FROM admins")
    admins = cur.fetchall()
    text = f"👑 Главный админ: {MAIN_ADMIN_ID}\n🛡 Админы:\n"
    for row in admins:
        text += f"- {row[0]}\n"
    await message.answer(text)

# ❓ FAQ
@dp.message_handler(commands=["addfaq"])
async def cmd_addfaq(message: types.Message):
    if not is_admin(message.from_user.id):
        return
    try:
        data = message.get_args().split("|")
        question, answer = data[0].strip(), data[1].strip()
        cur.execute("INSERT INTO faqs(chat_id, question, answer) VALUES(?, ?, ?)", (message.chat.id, question, answer))
        conn.commit()
        await message.answer(f"✅ FAQ добавлен:\n❓ {question}\n💬 {answer}")
    except:
        await message.answer("⚠️ Используй: /addfaq вопрос | ответ")

@dp.message_handler(commands=["listfaq"])
async def cmd_listfaq(message: types.Message):
    if not is_admin(message.from_user.id):
        return
    cur.execute("SELECT id, question FROM faqs WHERE chat_id=?", (message.chat.id,))
    rows = cur.fetchall()
    if not rows:
        await message.answer("❌ FAQ пуст.")
        return
    text = "📖 Список FAQ:\n"
    for row in rows:
        text += f"{row[0]}. {row[1]}\n"
    await message.answer(text)

@dp.message_handler(commands=["delfaq"])
async def cmd_delfaq(message: types.Message):
    if not is_admin(message.from_user.id):
        return
    try:
        faq_id = int(message.get_args())
        cur.execute("DELETE FROM faqs WHERE id=?", (faq_id,))
        conn.commit()
        await message.answer(f"✅ FAQ {faq_id} удалён.")
    except:
        await message.answer("⚠️ Используй: /delfaq <id>")

# 🔎 Ответы на FAQ
@dp.message_handler()
async def auto_faq(message: types.Message):
    cur.execute("SELECT question, answer FROM faqs WHERE chat_id=?", (message.chat.id,))
    for q, a in cur.fetchall():
        if q.lower() in message.text.lower():
            await message.reply(f"💬 {a}")
            break

# 🚀 Запуск
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
