import os
import glob
import json
import asyncio
from datetime import datetime, timezone, timedelta

from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

API_TOKEN = '8135200043:AAESBYeWTuQqiUScMo2WAr5wdYFkp78pPQg'  # Замени на свой токен

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Счётчик запросов
user_queries = {}

# Для времени по МСК
Moscow_tz = timezone(timedelta(hours=3))

# Создаём инлайн-клавиатуру
keyboard = InlineKeyboardMarkup(row_width=1)
keyboard.add(
    InlineKeyboardButton(text="?? пробив", callback_data="probiav"),
    InlineKeyboardButton(text="????? профиль", callback_data="profile"),
    InlineKeyboardButton(text="?? суслик еблан", callback_data="sulik_bl")
)

# Храним информацию о пользователе в простом виде
# Можно заменить на ДБ или файл, если нужно
user_profiles = {}

@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    await message.answer(
        "?? привет, отправь блять суда номер телефона я кего обязательно найду(но это не точно)",
        reply_markup=keyboard
    )
    # Инициализация данных пользователя
    user_id = message.from_user.id
    if user_id not in user_queries:
        user_queries[user_id] = 0

@dp.callback_query_handler(lambda c: c.data == 'probiav')
async def handle_probiav(callback: types.CallbackQuery):
    await callback.answer()
    await bot.send_message(callback.from_user.id, "?? Отправьте номер телефона для поиска (и не еби мозги):")

    # Ожидаем сообщение с номером
    @dp.message_handler()
    async def process_number(message: types.Message):
        number = message.text.strip()
        # Можно добавить проверку номера
        await message.answer(f"?? Начинаю поиск по номеру: {number}")
        # Поиск в базе
        found = False
        base_path = 'base'
        for filepath in glob.glob(os.path.join(base_path, '*')):
            # Предположим, что файлы формата json
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                # В данных ищем номер
                if isinstance(data, dict):
                    # предполагается, что есть ключ 'phone'
                    if data.get('phone') == number:
                        found = True
                        await message.answer(f"?? ну нашол и чо\nДанные: {data}")
                        break
                elif isinstance(data, list):
                    for item in data:
                        if item.get('phone') == number:
                            found = True
                            await message.answer(f"?? не хотел искать ну лан!\nДанные: {item}")
                            break
                    if found:
                        break
            except Exception as e:
                continue
        if not found:
            await message.answer("? Не найдено соответствий")
        # Увеличиваем счётчик запросов
        user_id = message.from_user.id
        user_queries[user_id] = user_queries.get(user_id, 0) + 1

        # Удаляем обработчик чтобы не захламлять
        # (или используем другое решение для поведения)
        # Тут для простоты — оставить так

@dp.callback_query_handler(lambda c: c.data == 'profile')
async def handle_profile(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    profile_name = callback.from_user.first_name or "Без имени"
    profile_id = user_id

    now = datetime.now(tz=Moscow_tz).strftime('%Y-%m-%d %H:%M:%S')
    queries = user_queries.get(user_id, 0)
    profile_msg = (
        f"????? ваш профиль:\n"
        f"имя: {profile_name}\n"
        f"айди: {profile_id}\n"
        f"————————————\n"
        f"сколько запросов выполнено: {queries}\n"
        f"время сейчас: {now}"
    )
    await callback.answer()
    await bot.send_message(callback.from_user.id, profile_msg)

@dp.callback_query_handler(lambda c: c.data == 'sulik_bl')
async def handle_sulik_b(callback: types.CallbackQuery):
    await callback.answer()
    await bot.send_message(callback.from_user.id, " суслик еблан")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
