import asyncio
import logging
import os
import random
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from config import bot_token, admin_chat_ids, mail, phone_numbers
from proxies import proxies
from user_agents import user_agents

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

bot = Bot(token=bot_token)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
dp.middleware.setup(LoggingMiddleware())

class ComplaintStates(StatesGroup):
    text_for_site = State()
    count_for_site = State()

class SupportStates(StatesGroup):
    message = State()

def add_user_to_file(user_id: int):
    try:
        with open('users.txt', 'r') as file:
            users = file.readlines()
        users = [line.strip() for line in users if line.strip()]
        user_ids = [line.split()[0] for line in users if line.split()]
        
        if str(user_id) not in user_ids:
            with open('users.txt', 'a') as file:
                file.write(f"{user_id}\n")
    except Exception as e:
        print(f"Ошибка при добавлении пользователя в файл: {e}")

@dp.message_handler(commands=['start'], state='*')
async def cmd_start(message: types.Message, state: FSMContext):
    await state.finish()
    add_user_to_file(message.from_user.id)
    
    first_name = message.from_user.first_name or ''
    last_name = message.from_user.last_name or ''
    username = f"@{message.from_user.username}" if message.from_user.username else f"id{message.from_user.id}"
    
    welcome_message = f"""
🌟 <b>Добро пожаловать, {first_name} {last_name} {username}!</b> 🌟
Используйте кнопки ниже для работы с ботом.
"""
    
    markup = InlineKeyboardMarkup(row_width=2)
    btn_support = InlineKeyboardButton('📩 Написать поддержку', callback_data='support')
    btn_web_demolition = InlineKeyboardButton('💻 Web-Снос (200)', callback_data='website_complaint')
    markup.add(btn_support, btn_web_demolition)
    
    await message.answer_photo(
        photo=open('welcome_photo.jpg', 'rb') if os.path.exists('welcome_photo.jpg') else None,
        caption=welcome_message,
        reply_markup=markup,
        parse_mode="HTML"
    )

@dp.callback_query_handler(lambda c: c.data == 'support', state='*')
async def support_callback(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
    await callback_query.message.answer('📝 Пожалуйста, напишите ваше сообщение для поддержки:')
    await SupportStates.message.set()

@dp.callback_query_handler(lambda c: c.data == 'website_complaint', state='*')
async def website_complaint_callback(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
    await callback_query.message.answer('🌐 Введите текст для отправки на сайт Telegram:')
    await ComplaintStates.text_for_site.set()

@dp.message_handler(state=ComplaintStates.text_for_site)
async def process_text_for_site_step(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['text_for_site'] = message.text
    await message.answer('🔢 Введите количество отправок (до 200):')
    await ComplaintStates.count_for_site.set()

@dp.message_handler(state=ComplaintStates.count_for_site)
async def process_count_for_site_step(message: types.Message, state: FSMContext):
    try:
        count = int(message.text)
        if count > 200:
            await message.answer('🚫 Количество отправок не должно превышать 200. Повторите ввод:')
            return
        if count <= 0:
            await message.answer('🚫 Количество отправок должно быть больше 0. Повторите ввод:')
            return
    except ValueError:
        await message.answer('🔢 Пожалуйста, введите число. Повторите ввод:')
        return
    
    async with state.proxy() as data:
        text = data['text_for_site']
    
    status_message = await message.answer("🔄 Начинаю отправку...")
    
    success_count = 0
    fail_count = 0
    
    for i in range(count):
        email = random.choice(mail)
        phone = random.choice(phone_numbers)
        proxy = await get_working_proxy()
        
        if not proxy:
            await message.answer('❌ В данный момент отсутствуют работоспособные прокси для отправки.')
            break
        
        success = await send_to_site(text, email, phone, proxy)
        if success:
            success_count += 1
        else:
            fail_count += 1
        
        # Обновляем статус каждые 10 отправок
        if i % 10 == 0 or i == count - 1:
            await bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=status_message.message_id,
                text=(
                    f"🔄 Отправка... ({i+1}/{count})\n"
                    f"✅ Успешно: {success_count}\n"
                    f"❌ Не удачно: {fail_count}\n"
                    f"📝 Текст: {text[:50]}..."
                )
            )
    
    final_message = (
        f"📊 Итоговый результат:\n"
        f"✅ Успешно отправлено: {success_count}\n"
        f"❌ Не удачно отправлено: {fail_count}\n"
        f"📝 Текст: {text[:100]}..."
    )
    
    await bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=status_message.message_id,
        text=final_message
    )
    
    await state.finish()

async def get_working_proxy():
    for proxy in proxies:
        try:
            response = requests.get('https://www.google.com', proxies=proxy, timeout=5)
            if response.status_code == 200:
                return proxy
        except Exception as e:
            logging.error(f'Proxy {proxy} is not working: {e}')
    return None

async def send_to_site(text, email, phone, proxy):
    url = "https://telegram.org/support"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": random.choice(user_agents)
    }
    data = {
        "message": text,
        "email": email,
        "phone": phone,
        "setln": "ru"
    }
    
    try:
        response = requests.post(url, headers=headers, data=data, proxies=proxy, timeout=10)
        if response.status_code == 200:
            logging.info(f'Data sent to site: {text}, email: {email}, phone: {phone}')
            return True
        else:
            logging.error(f'Error sending data to site: {response.status_code}')
            return False
    except Exception as e:
        logging.error(f'Error sending data to site: {e}')
        return False

@dp.message_handler(state=SupportStates.message)
async def process_support_message(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    username = message.from_user.username or f'id{user_id}'
    text = message.text or message.caption or "Сообщение без текста"

    header = f"📨 Новое сообщение от пользователя @{username} (ID: {user_id}):\n\n"
    
    for admin_id in admin_chat_ids:
        try:
            await bot.send_message(admin_id, f"{header}📝 Текст сообщения:\n{text}")
        except Exception as e:
            logging.error(f"Ошибка при отправке сообщения администратору {admin_id}: {e}")

    await message.answer('✅ Ваше сообщение отправлено в поддержку. Спасибо за обращение!')
    await state.finish()

if __name__ == '__main__':
    # Создаем файл users.txt если его нет
    if not os.path.exists('users.txt'):
        with open('users.txt', 'w') as f:
            pass
    
    executor.start_polling(dp, skip_updates=True)
