import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

# ================== НАСТРОЙКИ ==================
BOT_TOKEN = "8690487490:AAFoBUKGkh2bv6bh3o0Voz3z-OVx_B2VDF7M"
ADMIN_ID = 1346186504

# ⚠️ ЗАМЕНИТЕ НА ID ВАШЕГО КАНАЛА (обязательно с -100 в начале, например: -1001847563920)
CHANNEL_ID = -100XXXXXXXXXX  

# Список ваших разделов в канале. 
# Сначала запустите бота, отправьте /get_topics, узнайте ID тем и впишите их сюда:
TOPICS = {
    "Раздел 1": 1,   # Вместо 1, 2, 3 поставьте реальные ID тем
    "Раздел 2": 2,
    "Раздел 3": 3,
}
# ===============================================

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

class PostState(StatesGroup):
    waiting_for_content = State()

def get_topics_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    for name, thread_id in TOPICS.items():
        keyboard.inline_keyboard.append(
            [InlineKeyboardButton(text=name, callback_data=f"topic_{thread_id}")]
        )
    keyboard.inline_keyboard.append(
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_post")]
    )
    return keyboard

# Команда для получения ID всех тем в канале
@dp.message(F.text == "/get_topics")
async def cmd_get_topics(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    
    try:
        # Получаем список тем из канала
        forum_topics = await bot.get_forum_topics(chat_id=CHANNEL_ID)
        if not forum_topics:
            await message.answer("В канале не найдено активных тем. Убедитесь, что функция 'Темы' включена.")
            return
            
        text = "📋 **Список разделов вашего канала:**\n\n"
        for topic in forum_topics:
            text += f"🔹 **{topic.name}** — ID темы: `{topic.message_thread_id}`\n"
        text += "\nСкопируйте эти ID и вставьте их в код в словарь `TOPICS`!"
        await message.answer(text, parse_mode="Markdown")
    except Exception as e:
        await message.answer(f"❌ Не удалось получить темы. Ошибка: {e}\n\nПроверьте, что бот добавлен в канал как администратор и CHANNEL_ID указан верно.")

# Команда старт
@dp.message(F.text == "/start")
async def cmd_start(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    
    await message.answer(
        "👋 Привет, Админ!\n\n"
        "1. Чтобы узнать ID разделов канала, введи /get_topics\n"
        "2. Чтобы опубликовать пост, просто **скинь мне фото с описанием (размерами)**."
    )
    await state.set_state(PostState.waiting_for_content)

# Прием контента (фото + текст)
@dp.message(PostState.waiting_for_content, F.photo)
async def handle_post_content(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return

    await state.update_data(
        photo_id=message.photo[-1].file_id,
        caption=message.caption or ""
    )
    
    await message.answer("Отлично! Выбери раздел для публикации:", reply_markup=get_topics_keyboard())

# Публикация по кнопке
@dp.callback_query(F.data.startswith("topic_"))
async def publish_post(callback: CallbackQuery, state: FSMContext):
    thread_id = int(callback.data.split("_")[1])
    data = await state.get_data()
    
    photo_id = data.get("photo_id")
    caption = data.get("caption")

    try:
        await bot.send_photo(
            chat_id=CHANNEL_ID,
            photo=photo_id,
            caption=caption,
            message_thread_id=thread_id
        )
        await callback.message.edit_text("✅ Успешно опубликовано в выбранный раздел!")
    except Exception as e:
        await callback.message.edit_text(f"❌ Ошибка при отправке: {e}")
    
    await state.clear()
    await callback.answer()

# Отмена
@dp.callback_query(F.data == "cancel_post")
async def cancel_post(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("🔄 Отменено. Напишите /start, чтобы начать сначала.")
    await callback.answer()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())