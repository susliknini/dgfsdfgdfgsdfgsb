import os
import glob
import json
import asyncio
from datetime import datetime, timezone, timedelta

from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

API_TOKEN = '8135200043:AAESBYeWTuQqiUScMo2WAr5wdYFkp78pPQg'  # ������ �� ���� �����

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# ������� ��������
user_queries = {}

# ��� ������� �� ���
Moscow_tz = timezone(timedelta(hours=3))

# ������ ������-����������
keyboard = InlineKeyboardMarkup(row_width=1)
keyboard.add(
    InlineKeyboardButton(text="?? ������", callback_data="probiav"),
    InlineKeyboardButton(text="????? �������", callback_data="profile"),
    InlineKeyboardButton(text="?? ������ �����", callback_data="sulik_bl")
)

# ������ ���������� � ������������ � ������� ����
# ����� �������� �� �� ��� ����, ���� �����
user_profiles = {}

@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    await message.answer(
        "?? ������, ������� ����� ���� ����� �������� � ���� ����������� �����(�� ��� �� �����)",
        reply_markup=keyboard
    )
    # ������������� ������ ������������
    user_id = message.from_user.id
    if user_id not in user_queries:
        user_queries[user_id] = 0

@dp.callback_query_handler(lambda c: c.data == 'probiav')
async def handle_probiav(callback: types.CallbackQuery):
    await callback.answer()
    await bot.send_message(callback.from_user.id, "?? ��������� ����� �������� ��� ������ (� �� ��� �����):")

    # ������� ��������� � �������
    @dp.message_handler()
    async def process_number(message: types.Message):
        number = message.text.strip()
        # ����� �������� �������� ������
        await message.answer(f"?? ������� ����� �� ������: {number}")
        # ����� � ����
        found = False
        base_path = 'base'
        for filepath in glob.glob(os.path.join(base_path, '*')):
            # �����������, ��� ����� ������� json
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                # � ������ ���� �����
                if isinstance(data, dict):
                    # ��������������, ��� ���� ���� 'phone'
                    if data.get('phone') == number:
                        found = True
                        await message.answer(f"?? �� ����� � ��\n������: {data}")
                        break
                elif isinstance(data, list):
                    for item in data:
                        if item.get('phone') == number:
                            found = True
                            await message.answer(f"?? �� ����� ������ �� ���!\n������: {item}")
                            break
                    if found:
                        break
            except Exception as e:
                continue
        if not found:
            await message.answer("? �� ������� ������������")
        # ����������� ������� ��������
        user_id = message.from_user.id
        user_queries[user_id] = user_queries.get(user_id, 0) + 1

        # ������� ���������� ����� �� ����������
        # (��� ���������� ������ ������� ��� ���������)
        # ��� ��� �������� � �������� ���

@dp.callback_query_handler(lambda c: c.data == 'profile')
async def handle_profile(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    profile_name = callback.from_user.first_name or "��� �����"
    profile_id = user_id

    now = datetime.now(tz=Moscow_tz).strftime('%Y-%m-%d %H:%M:%S')
    queries = user_queries.get(user_id, 0)
    profile_msg = (
        f"????? ��� �������:\n"
        f"���: {profile_name}\n"
        f"����: {profile_id}\n"
        f"������������\n"
        f"������� �������� ���������: {queries}\n"
        f"����� ������: {now}"
    )
    await callback.answer()
    await bot.send_message(callback.from_user.id, profile_msg)

@dp.callback_query_handler(lambda c: c.data == 'sulik_bl')
async def handle_sulik_b(callback: types.CallbackQuery):
    await callback.answer()
    await bot.send_message(callback.from_user.id, " ������ �����")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
