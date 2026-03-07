import json
import os

from aiogram import Bot
from aiogram import Router, F
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from aiogram.filters import Command
from aiogram.exceptions import TelegramBadRequest

router = Router()
bot_instance: Bot | None = None
import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

DATA_PATH = "Data.json"
ADMINS_FILE = "admins.json"
# ================= JSON =================

def load_json(path):
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# ================= ДОСТУП =================

def get_owner():
    data = load_json(DATA_PATH)
    return data.get("OWNER_ID")

def is_admin(user_id: int):
    if str(user_id) == str(get_owner()):
        return True

    admins = load_json(ADMINS_FILE)
    return str(user_id) in admins

# ================= SAFE EDIT =================

async def safe_edit(message, text, markup):
    try:
        await message.edit_text(text, reply_markup=markup)
    except TelegramBadRequest:
        pass

# ================= КНОПКИ =================

def admin_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Добавить админа", callback_data="a_add")],
            [InlineKeyboardButton(text="🔰 Передать Создателя", callback_data="a_owner")],
            [InlineKeyboardButton(text="📋 Лист Администрации", callback_data="a_list")],
            [InlineKeyboardButton(text="❌ Снять админа", callback_data="a_del")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_main")]
        ]
    )

# ================= Овнер имя =================

def set_bot(bot: Bot):
    global bot_instance
    bot_instance = bot
# ================= CALLBACK =================

@router.callback_query(F.data.startswith("a_"))
async def admin_callbacks(callback: CallbackQuery):

    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    if callback.data == "a_add":
        text = (
            "➕ <b>Добавить админа</b>\n"
            "Добавить админа:\n"
            "/aadminuser @username\n\n"
        )

    elif callback.data == "a_owner":
        text = (
            "🔰 <b>Передать Создателя</b>\n"
            "Передать владельца:\n"
            "/gowneruser @username\n\n"
        )


    elif callback.data == "a_list":

        text = await build_admin_list()

    elif callback.data == "a_del":
        text = (
            "❌ <b>Снять админа</b>\n"
            "Для удаления админа:\n"
            "/dadminuser @username\n\n"
        )

    await safe_edit(callback.message, text, admin_keyboard())
    await callback.answer()

# ================= ЛИСТ =================

async def build_admin_list():

    owner = get_owner()
    admins = load_json(ADMINS_FILE)

    text = "📋 <b>Лист администрации</b>\n\n"

    # ================= СОЗДАТЕЛЬ =================
    text += "🔰 <b>Создатель:</b>\n\n"

    owner_display = "Не назначен"

    if owner:

        # если хранится ID
        if str(owner).isdigit() and bot_instance:
            try:
                chat = await bot_instance.get_chat(int(owner))
                if chat.username:
                    owner_display = f"@{chat.username}"
                else:
                    owner_display = f"<code>{owner}</code>"
            except:
                owner_display = f"<code>{owner}</code>"

        # если уже @username
        elif str(owner).startswith("@"):
            owner_display = owner
        else:
            owner_display = f"<code>{owner}</code>"

    text += f"1. {owner_display}\n\n"

    # ================= АДМИНЫ =================
    text += "❇️ <b>Админы:</b>\n\n"

    if not admins:
        text += "Нет админов."
    else:
        for i, (admin_id, data) in enumerate(admins.items(), 1):

            username = data.get("username")

            if username:
                admin_display = f"@{username}"
            else:
                admin_display = f"<code>{admin_id}</code>"

            text += f"{i}. {admin_display}\n"

    return text
# ================= КОМАНДЫ =================

@router.message(Command("aadminuser"))
async def add_admin(message: Message):
    if not is_admin(message.from_user.id):
        return

    parts = message.text.split()
    if len(parts) != 2:
        await message.reply("Использование: /aadminuser @username")
        return

    username = parts[1].replace("@", "")

    try:
        user = await bot_instance.get_chat(username)
    except:
        await message.reply("❌ Пользователь не найден.")
        return

    admins = load_json(ADMINS_FILE)

    admins[str(user.id)] = {
        "username": user.username if user.username else ""
    }

    save_json(ADMINS_FILE, admins)

    await message.reply("✅ Админ добавлен.")

@router.message(Command("dadminuser"))
async def remove_admin(message: Message):
    if not is_admin(message.from_user.id):
        return

    parts = message.text.split()
    if len(parts) != 2:
        await message.reply("Использование: /dadminuser @username")
        return

    username = parts[1].replace("@", "")

    admins = load_json(ADMINS_FILE)

    found_id = None

    for admin_id, data in admins.items():
        if data.get("username") == username:
            found_id = admin_id
            break

    if found_id:
        del admins[found_id]
        save_json(ADMINS_FILE, admins)
        await message.reply("✅ Админ снят.")
    else:
        await message.reply("❌ Админ не найден.")

@router.message(Command("gowneruser"))
async def give_owner(message: Message):

    if message.from_user.id != get_owner():
        return

    parts = message.text.split()
    if len(parts) != 2:
        return

    new_owner = parts[1]

    data = load_json(DATA_PATH)
    data["OWNER_ID"] = new_owner
    save_json(DATA_PATH, data)


    await message.reply("🔰 Создатель передан.")


